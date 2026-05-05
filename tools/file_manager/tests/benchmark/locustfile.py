"""
Locust Load Testing Definition for T8 Performance Benchmarks

Tests:
- 100 concurrent users
- Peak load scenarios
- Sustained load with think time

Run with:
    locust -f tests/benchmark/locustfile.py --host=http://localhost:8080
    locust -f tests/benchmark/locustfile.py --host=http://localhost:8080 --users=100 --spawn-rate=10 --run-time=60s --headless --csv=reports/locust
"""

import random
import time
from locust import HttpUser, task, between, events
from locust.stats import print_stats


class HermesFileManagerUser(HttpUser):
    """Simulated Hermes File Manager user."""

    wait_time = between(1, 3)

    def on_start(self):
        """Login and setup user session."""
        username = f"loadtest_user_{random.randint(1, 1000)}"

        response = self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test123"
        })

        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(10)
    def get_health(self):
        """Check health endpoint."""
        self.client.get("/health")

    @task(5)
    def list_users(self):
        """List users (admin)."""
        if self.token:
            self.client.get("/api/v1/admin/users", headers=self.headers)

    @task(5)
    def list_spaces(self):
        """List user's spaces."""
        if self.token:
            self.client.get("/api/v1/spaces", headers=self.headers)

    @task(3)
    def admin_overview(self):
        """Get admin analytics overview."""
        if self.token:
            self.client.get(
                "/api/v1/admin/analytics/overview",
                headers=self.headers
            )

    @task(3)
    def storage_pools(self):
        """List storage pools."""
        if self.token:
            self.client.get(
                "/api/v1/pools",
                headers=self.headers
            )

    @task(2)
    def quota_heatmap(self):
        """Get quota heatmap."""
        if self.token:
            self.client.get(
                "/api/v1/admin/analytics/quota-heatmap",
                headers=self.headers
            )


class HermesConcurrentUser(HttpUser):
    """Heavy concurrent user for peak load testing."""

    wait_time = between(0.5, 1)

    def on_start(self):
        """Quick login."""
        username = f"concurrent_user_{random.randint(1, 500)}"
        response = self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "test123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task
    def rapid_user_list(self):
        """Rapid admin API calls."""
        if self.token:
            for _ in range(5):
                self.client.get("/api/v1/admin/users", headers=self.headers)
                time.sleep(0.1)


class HermesAnalyticsUser(HttpUser):
    """User specifically testing analytics endpoints."""

    wait_time = between(2, 5)

    def on_start(self):
        username = "analytics_user"
        response = self.client.post("/api/v1/auth/login", json={
            "username": username,
            "password": "admin123"
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(10)
    def get_overview(self):
        """Repeatedly fetch overview (cache hit scenario)."""
        if self.token:
            with self.client.get(
                "/api/v1/admin/analytics/overview",
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()

    @task(5)
    def get_heatmap(self):
        """Fetch quota heatmap."""
        if self.token:
            with self.client.get(
                "/api/v1/admin/analytics/quota-heatmap",
                headers=self.headers,
                catch_response=True
            ) as response:
                if response.status_code == 200:
                    response.success()

    @task(2)
    def get_trends(self):
        """Fetch operation trends."""
        if self.token:
            self.client.get(
                "/api/v1/admin/analytics/operation-trends?days=30",
                headers=self.headers
            )


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track request metrics."""
    if response_time > 150:
        print(f"SLOW REQUEST: {name} took {response_time:.0f}ms")
