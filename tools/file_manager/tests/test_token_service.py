"""
Unit Tests for Token Service
"""

import pytest
import time
from services.token_service import (
    TokenService,
    TokenClaims,
)


# Use a long enough secret to avoid warnings
TEST_SECRET = "test-secret-key-that-is-long-enough-for-hs256-algorithm"


class TestTokenServiceGeneration:
    """Test token generation"""

    def test_create_access_token_basic(self):
        """Should create a valid access token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user-123",
            username="testuser",
        )
        assert token is not None
        assert len(token) > 50
        assert token.count(".") == 2  # JWT format

    def test_create_access_token_with_teams(self):
        """Should include teams in token claims"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user-123",
            username="testuser",
            teams=["team-a", "team-b"],
        )
        claims = svc.verify_token(token)
        assert claims.sub == "user-123"
        assert "team-a" in claims.teams
        assert "team-b" in claims.teams

    def test_create_access_token_with_capabilities(self):
        """Should include capabilities in token claims"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user-123",
            username="testuser",
            capabilities={
                "craftsman": ["list_spaces", "search_wiki"],
                "apprentice": ["sync_trigger"],
            },
        )
        claims = svc.verify_token(token)
        assert "craftsman" in claims.capabilities
        assert "list_spaces" in claims.capabilities["craftsman"]


class TestTokenServiceVerification:
    """Test token verification"""

    def test_verify_token_valid(self):
        """Should return claims for valid token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user-456",
            username="alice",
            teams=["team-x"],
        )
        claims = svc.verify_token(token)
        assert claims is not None
        assert claims.sub == "user-456"
        assert claims.username == "alice"
        assert "team-x" in claims.teams

    def test_verify_token_invalid(self):
        """Should return None for invalid token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        claims = svc.verify_token("invalid.token.here")
        assert claims is None

    def test_verify_token_wrong_secret(self):
        """Should return None for token signed with different secret"""
        svc1 = TokenService(jwt_secret=TEST_SECRET)
        svc2 = TokenService(jwt_secret="different-secret-key-12345")
        token = svc1.create_access_token(user_id="user", username="test")
        claims = svc2.verify_token(token)
        assert claims is None


class TestTokenServiceCapabilityChecking:
    """Test capability checking"""

    def test_has_capability_true(self):
        """Should return True when capability exists"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user",
            username="test",
            capabilities={"craftsman": ["list_spaces", "search_wiki"]},
        )
        claims = svc.verify_token(token)
        assert svc.has_capability(claims, "craftsman", "list_spaces") is True
        assert svc.has_capability(claims, "craftsman", "search_wiki") is True

    def test_has_capability_false(self):
        """Should return False when capability doesn't exist"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user",
            username="test",
            capabilities={"craftsman": ["list_spaces"]},
        )
        claims = svc.verify_token(token)
        assert svc.has_capability(claims, "craftsman", "admin_only") is False
        assert svc.has_capability(claims, "apprentice", "sync_trigger") is False

    def test_has_capability_with_token_string(self):
        """Should check capabilities using token string directly"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user",
            username="test",
            capabilities={"knowledge": ["read", "write"]},
        )
        assert svc.has_capability(token, "knowledge", "read") is True
        assert svc.has_capability(token, "knowledge", "delete") is False


class TestTokenServiceScopeChecking:
    """Test OAuth scope checking"""

    def test_has_scope_true(self):
        """Should return True when scope is granted"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user",
            username="test",
            scope=["openid", "profile"],
        )
        claims = svc.verify_token(token)
        assert svc.has_scope(claims, "openid") is True
        assert svc.has_scope(claims, "profile") is True

    def test_has_scope_false(self):
        """Should return False when scope is not granted"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user",
            username="test",
            scope=["openid"],
        )
        claims = svc.verify_token(token)
        assert svc.has_scope(claims, "email") is False


class TestTokenServiceRevocation:
    """Test token revocation"""

    def test_revoke_token(self):
        """Should mark token as revoked"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(user_id="user", username="test")
        claims = svc.verify_token(token)
        assert claims is not None

        jti = claims.jti
        assert svc.is_revoked(jti) is False  # Not revoked yet

        result = svc.revoke_token(token)
        assert result is True

        # Should now return True for is_revoked
        assert svc.is_revoked(jti) is True

    def test_is_token_revoked_false_for_valid(self):
        """Should return False for non-revoked token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(user_id="user", username="test")
        claims = svc.verify_token(token)
        assert svc.is_revoked(claims.jti) is False


class TestTokenServiceRefreshToken:
    """Test refresh token rotation"""

    def test_create_refresh_token(self):
        """Should create refresh token with JTI"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        refresh, jti = svc.create_refresh_token(
            user_id="user-123",
            scope=["openid", "offline_access"],
        )
        assert refresh is not None
        assert jti is not None
        assert len(jti) > 10
        # JTI should be stored
        assert jti in svc._refresh_tokens


class TestTokenServiceIntrospection:
    """Test token introspection (RFC 7662)"""

    def test_introspect_active_token(self):
        """Should return active=True for valid token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        token = svc.create_access_token(
            user_id="user-789",
            username="testuser",
            teams=["team-1"],
        )
        result = svc.introspect_token(token)
        assert result["active"] is True
        assert result["sub"] == "user-789"

    def test_introspect_invalid_token(self):
        """Should return active=False for invalid token"""
        svc = TokenService(jwt_secret=TEST_SECRET)
        result = svc.introspect_token("invalid.token")
        assert result["active"] is False