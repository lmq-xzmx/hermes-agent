#!/usr/bin/env python3
"""
T8 Benchmark Test Runner

Usage:
    python tests/benchmark/scripts/run_benchmarks.py --type api
    python tests/benchmark/scripts/run_benchmarks.py --type ws
    python tests/benchmark/scripts/run_benchmarks.py --type load
    python tests/benchmark/scripts/run_benchmarks.py --type stability
    python tests/benchmark/scripts/run_benchmarks.py --all
"""

import sys
import subprocess
import argparse
from pathlib import Path


BENCHMARK_DIR = Path(__file__).parent.parent
PROJECT_DIR = BENCHMARK_DIR.parent.parent.parent


def run_pytest_marker(marker: str, report_suffix: str = ""):
    """Run pytest with specific marker."""
    cmd = [
        "python", "-m", "pytest",
        str(BENCHMARK_DIR),
        "-m", marker,
        "-v",
        "--tb=short",
        "--capture=no",
    ]

    print(f"\nRunning: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0


def run_locust_headless(users: int, duration: str, report_name: str):
    """Run Locust in headless mode."""
    reports_dir = BENCHMARK_DIR / "reports" / report_name
    reports_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "locust",
        "-f", str(BENCHMARK_DIR / "locustfile.py"),
        "--host=http://localhost:8080",
        "--users", str(users),
        "--spawn-rate", "10",
        "--run-time", duration,
        "--headless",
        "--csv", str(reports_dir / "locust"),
    ]

    print(f"\nRunning Locust: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser(description="T8 Benchmark Runner")
    parser.add_argument("--type", choices=["api", "ws", "load", "stability", "all"],
                        help="Type of benchmark to run")
    parser.add_argument("--report", action="store_true", help="Generate report")

    args = parser.parse_args()

    if not args.type:
        parser.print_help()
        print("\nExample usage:")
        print("  python tests/benchmark/scripts/run_benchmarks.py --type api")
        print("  python tests/benchmark/scripts/run_benchmarks.py --all")
        return

    success = True

    if args.type == "api" or args.type == "all":
        print("\n=== Running API Latency Benchmarks ===")
        success = run_pytest_marker("benchmark", "api") and success

    if args.type == "ws" or args.type == "all":
        print("\n=== Running WebSocket Benchmarks ===")
        success = run_pytest_marker("ws_benchmark", "ws") and success

    if args.type == "load" or args.type == "all":
        print("\n=== Running Load Tests (Locust) ===")
        print("Note: Locust requires a running server at http://localhost:8080")
        print("Skipping in automated run - use 'locust -f tests/benchmark/locustfile.py' manually")

    if args.type == "stability" or args.type == "all":
        print("\n=== Running Stability Tests ===")
        success = run_pytest_marker("stability", "stability") and success

    if success:
        print("\n=== All benchmarks completed ===")
    else:
        print("\n=== Some benchmarks failed ===")
        sys.exit(1)


if __name__ == "__main__":
    main()
