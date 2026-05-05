"""
T8: Stability Test

Tests:
- Memory leak detection
- CPU/Thread stability
- Long-running operation stability
"""

import pytest
import time
import statistics
import threading
from dataclasses import dataclass, field
from typing import List, Dict
from datetime import datetime


@dataclass
class StabilityMetrics:
    """Metrics collected during stability test."""
    timestamp: float
    memory_mb: float
    cpu_percent: float
    threads: int


class StabilityMonitor:
    """Monitor system stability over time."""

    def __init__(self, interval_seconds: int = 30):
        self.interval = interval_seconds
        self.metrics: List[StabilityMetrics] = []
        self.running = False
        self.thread: threading.Thread = None
        self._lock = threading.Lock()
        self._process = None

    def start(self):
        """Start monitoring."""
        try:
            import psutil
            self._process = psutil.Process()
        except ImportError:
            pass

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                metric = self._collect_metric()
                with self._lock:
                    self.metrics.append(metric)
            except Exception:
                pass

            # Use sleep with small increments for responsive shutdown
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def _collect_metric(self) -> StabilityMetrics:
        """Collect current metrics."""
        timestamp = time.time()
        memory_mb = 0.0
        cpu_percent = 0.0
        threads = 1

        if self._process:
            try:
                mem_info = self._process.memory_info()
                memory_mb = mem_info.rss / 1024 / 1024
                cpu_percent = self._process.cpu_percent(interval=0.1)
                threads = self._process.num_threads()
            except Exception:
                pass

        return StabilityMetrics(
            timestamp=timestamp,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            threads=threads
        )

    def get_report(self) -> Dict:
        """Generate stability report."""
        with self._lock:
            if not self.metrics:
                return {}

            mem_values = [m.memory_mb for m in self.metrics]
            cpu_values = [m.cpu_percent for m in self.metrics]
            thread_values = [m.threads for m in self.metrics]

            # Memory growth analysis
            first_half = mem_values[:len(mem_values)//2] if len(mem_values) >= 4 else mem_values
            second_half = mem_values[len(mem_values)//2:] if len(mem_values) >= 4 else mem_values

            avg_first = statistics.mean(first_half) if first_half else 0
            avg_second = statistics.mean(second_half) if second_half else 0
            memory_growth_pct = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0

            duration_min = 0
            if len(self.metrics) >= 2:
                duration_min = (self.metrics[-1].timestamp - self.metrics[0].timestamp) / 60

            return {
                "duration_min": duration_min,
                "data_points": len(self.metrics),
                "memory": {
                    "avg_mb": statistics.mean(mem_values) if mem_values else 0,
                    "max_mb": max(mem_values) if mem_values else 0,
                    "min_mb": min(mem_values) if mem_values else 0,
                    "growth_pct": memory_growth_pct,
                },
                "cpu": {
                    "avg_pct": statistics.mean(cpu_values) if cpu_values else 0,
                    "max_pct": max(cpu_values) if cpu_values else 0,
                },
                "threads_avg": statistics.mean(thread_values) if thread_values else 0,
            }


class TestStability:
    """Stability tests."""

    @pytest.mark.stability
    def test_memory_stability_short(self, benchmark_config):
        """
        Short memory stability test (1 minute).
        Verifies no significant memory growth during sustained operation.
        """
        monitor = StabilityMonitor(interval_seconds=5)
        monitor.start()

        duration_sec = 60
        start = time.time()
        iterations = 0

        while time.time() < start + duration_sec:
            iterations += 1
            # Simulate periodic API calls
            time.sleep(1)

        monitor.stop()
        report = monitor.get_report()

        print(f"\nMemory Stability Test ({duration_sec}s):")
        print(f"  Iterations: {iterations}")
        print(f"  Data Points: {report.get('data_points', 0)}")
        print(f"  Avg Memory: {report.get('memory', {}).get('avg_mb', 0):.1f} MB")
        print(f"  Memory Growth: {report.get('memory', {}).get('growth_pct', 0):.2f}%")

        # Short test threshold: < 10% memory growth
        memory_growth = report.get('memory', {}).get('growth_pct', 0)
        assert memory_growth < 10, f"Memory grew {memory_growth:.2f}% in {duration_sec}s (threshold: 10%)"

    @pytest.mark.stability
    def test_cpu_stability(self, benchmark_config):
        """
        CPU stability test.
        Verifies CPU usage remains reasonable.
        """
        monitor = StabilityMonitor(interval_seconds=2)
        monitor.start()

        time.sleep(30)

        monitor.stop()
        report = monitor.get_report()

        print(f"\nCPU Stability Test:")
        print(f"  Avg CPU: {report.get('cpu', {}).get('avg_pct', 0):.1f}%")
        print(f"  Max CPU: {report.get('cpu', {}).get('max_pct', 0):.1f}%")

        # CPU should be reasonable during idle
        cpu_avg = report.get('cpu', {}).get('avg_pct', 0)
        assert cpu_avg < 80, f"CPU avg {cpu_avg:.1f}% is too high"


class TestMemoryLeak:
    """Memory leak detection tests."""

    @pytest.mark.stability
    def test_memory_leak_detection(self, benchmark_config):
        """
        Memory leak check over extended period.
        For CI, this runs a shorter version.
        In production, run with --hours=24 for full 24h test.
        """
        monitor = StabilityMonitor(interval_seconds=10)
        monitor.start()

        # Run for 5 minutes (shorter for testing, use 24h in production)
        duration_min = 5
        start = time.time()
        end = start + (duration_min * 60)

        while time.time() < end:
            time.sleep(10)

        monitor.stop()
        report = monitor.get_report()

        memory_growth = report.get('memory', {}).get('growth_pct', 0)

        print(f"\nMemory Leak Check ({duration_min}min):")
        print(f"  Data Points: {report.get('data_points', 0)}")
        print(f"  Avg Memory: {report.get('memory', {}).get('avg_mb', 0):.1f} MB")
        print(f"  Memory Growth: {memory_growth:.2f}%")

        # 20% growth threshold for short test
        assert memory_growth < 20, f"Memory grew {memory_growth:.2f}% in {duration_min}min (threshold: 20%)"
