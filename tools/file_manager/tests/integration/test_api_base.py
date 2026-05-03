"""
Base class for API integration tests.

Provides common utilities for testing REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient


class BaseAPITest:
    """Base class for API integration tests."""

    @pytest.fixture(autouse=True)
    def setup_api_test(self, db_session, tmp_hermes_home):
        """Setup for each API test."""
        from tools.file_manager.server import app

        self.client = TestClient(app)
        self.db = db_session

        yield

        # Cleanup after test
        self.client = None
        self.db = None

    def get(self, path: str, **kwargs):
        """Make GET request."""
        return self.client.get(path, **kwargs)

    def post(self, path: str, **kwargs):
        """Make POST request."""
        return self.client.post(path, **kwargs)

    def put(self, path: str, **kwargs):
        """Make PUT request."""
        return self.client.put(path, **kwargs)

    def delete(self, path: str, **kwargs):
        """Make DELETE request."""
        return self.client.delete(path, **kwargs)

    def login(self, username: str, password: str):
        """Login and get auth token."""
        response = self.post("/api/v1/auth/login", json={
            "username": username,
            "password": password
        })
        if response.status_code == 200:
            return response.json().get("token")
        return None

    def auth_header(self, token: str):
        """Get authorization header."""
        return {"Authorization": f"Bearer {token}"}

    def assert_status(self, response, expected_status: int):
        """Assert response status code."""
        assert response.status_code == expected_status, (
            f"Expected {expected_status}, got {response.status_code}. "
            f"Body: {response.text[:500]}"
        )

    def assert_error_code(self, response, expected_code: str):
        """Assert error response contains expected code."""
        body = response.json()
        assert body.get("code") == expected_code, (
            f"Expected error code '{expected_code}', got '{body.get('code')}'"
        )
