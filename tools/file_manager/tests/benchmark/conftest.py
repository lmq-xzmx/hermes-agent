"""
Benchmark Fixtures - T8 Performance Testing

Provides shared fixtures for performance benchmark tests.
"""

import sys
import os
from pathlib import Path

# Add tools/ to path so `from file_manager...` imports work
# benchmark/conftest.py is at: tools/file_manager/tests/benchmark/conftest.py
# We need to add: tools/ (parent of file_manager/)
tools_path = Path(__file__).parent.parent.parent.parent
tools_path_str = str(tools_path)

# Remove if already present, then add at position 0
if tools_path_str in sys.path:
    sys.path.remove(tools_path_str)
sys.path.insert(0, tools_path_str)

# Also ensure current working directory is in path if different
cwd = os.getcwd()
if cwd not in sys.path:
    sys.path.insert(0, cwd)

import pytest
import time
import threading
import statistics
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests."""
    p95_threshold_ms: float = 150.0
    ws_latency_threshold_ms: float = 100.0
    page_load_threshold_s: float = 3.0
    concurrent_users: int = 100
    peak_load_duration_s: int = 60
    stability_duration_h: int = 24


@dataclass
class LatencyResult:
    """Result of a latency measurement."""
    operation: str
    latency_ms: float
    timestamp: float
    success: bool
    error: str = None


@dataclass
class BenchmarkReport:
    """Aggregated benchmark results."""
    name: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies: List[float] = field(default_factory=list)
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    avg_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0

    def compute_stats(self):
        if self.latencies:
            sorted_lat = sorted(self.latencies)
            self.min_ms = min(sorted_lat)
            self.max_ms = max(sorted_lat)
            self.avg_ms = statistics.mean(sorted_lat)
            self.p50_ms = statistics.median(sorted_lat)
            n = len(sorted_lat)
            self.p95_ms = sorted_lat[int(n * 0.95)] if n > 0 else 0
            self.p99_ms = sorted_lat[int(n * 0.99)] if n > 0 else 0


@pytest.fixture
def benchmark_config():
    """Provide benchmark configuration."""
    return BenchmarkConfig()


@pytest.fixture
def latency_collector():
    """Collect latency measurements for benchmark reporting."""
    results: List[LatencyResult] = []
    lock = threading.Lock()

    def record(operation: str, latency_ms: float, success: bool = True, error: str = None):
        with lock:
            results.append(LatencyResult(
                operation=operation,
                latency_ms=latency_ms,
                timestamp=time.time(),
                success=success,
                error=error
            ))

    def get_report(name: str) -> BenchmarkReport:
        with lock:
            latencies = [r.latency_ms for r in results if r.success]
            report = BenchmarkReport(name=name, total_requests=len(results))
            report.successful = len([r for r in results if r.success])
            report.failed = len([r for r in results if not r.success])
            report.latencies = latencies
            report.compute_stats()
            return report

    def clear():
        results.clear()

    return {
        "record": record,
        "get_report": get_report,
        "clear": clear,
        "_results": results
    }


@pytest.fixture
def bench_api_client(tmp_path, monkeypatch):
    """
    Create a REST API test client for benchmarks.
    Uses in-memory database and temporary storage.
    """
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from file_manager.server import app
    from file_manager.engine.models import Base

    # Create temp database
    db_path = tmp_path / "bench.db"
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    # Setup temp hermes home
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def get_test_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override the get_db dependency if it exists
    # Note: The actual get_db dependency may not exist in all server configurations
    if hasattr(app, 'dependency_overrides'):
        try:
            from file_manager.services.database import get_db
            app.dependency_overrides[get_db] = get_test_db
        except ImportError:
            pass  # get_db not defined, skip override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def bench_auth_token(bench_api_client):
    """Get authentication token for benchmark tests."""
    try:
        response = bench_api_client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin123"
        })
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass
    return None
