"""
Unit Tests for OAuth Service
"""

import pytest
import time
from services.oauth_service import (
    OAuthService,
    OAuthAuthorizationCode,
    OAuthTokenResponse,
    CODE_CHALLENGE_METHOD,
    GRANT_TYPE_AUTHORIZATION_CODE,
    GRANT_TYPE_REFRESH_TOKEN,
)


class TestOAuthServicePKCE:
    """Test PKCE generation and verification"""

    def test_generate_code_verifier_length(self):
        """Code verifier should be 43-128 characters"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        verifier = oauth.generate_code_verifier()
        assert len(verifier) >= 43, "Verifier too short"
        assert len(verifier) <= 128, "Verifier too long"

    def test_generate_code_challenge(self):
        """Code challenge should be Base64url encoded SHA256"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        verifier = "test-verifier-string"
        challenge = oauth.generate_code_challenge(verifier)
        # Should be Base64url without padding
        assert not challenge.endswith("=")
        assert len(challenge) > 0

    def test_verify_code_challenge_valid(self):
        """PKCE verification should succeed with correct verifier"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        verifier = oauth.generate_code_verifier()
        challenge = oauth.generate_code_challenge(verifier)
        assert oauth.verify_code_challenge(verifier, challenge) is True

    def test_verify_code_challenge_invalid(self):
        """PKCE verification should fail with wrong verifier"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        verifier = oauth.generate_code_verifier()
        challenge = oauth.generate_code_challenge(verifier)
        assert oauth.verify_code_challenge("wrong-verifier", challenge) is False

    def test_verify_code_challenge_empty(self):
        """PKCE verification should fail with empty inputs"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        assert oauth.verify_code_challenge("", "challenge") is False
        assert oauth.verify_code_challenge("verifier", "") is False


class TestOAuthAuthorizationCode:
    """Test authorization code creation and validation"""

    def test_create_authorization_code(self):
        """Should create authorization code with correct fields"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        code = oauth.create_authorization_code(
            client_id="test-client",
            redirect_uri="http://localhost/callback",
            scope=["openid", "profile"],
            state="test-state",
            code_challenge="test-challenge",
            code_challenge_method=CODE_CHALLENGE_METHOD,
            user_id="user-123",
            nonce="test-nonce",
        )
        assert code.code is not None
        assert len(code.code) > 40
        assert code.client_id == "test-client"
        assert code.user_id == "user-123"
        assert code.expires_at > time.time()
        assert code.nonce == "test-nonce"


class TestOIDCDiscovery:
    """Test OIDC Discovery endpoint"""

    def test_oidc_discovery_response(self):
        """Discovery document should contain required fields"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        discovery = oauth.get_oidc_discovery()

        assert "issuer" in discovery
        assert "authorization_endpoint" in discovery
        assert "token_endpoint" in discovery
        assert "userinfo_endpoint" in discovery
        assert "jwks_uri" in discovery
        assert "response_types_supported" in discovery
        assert "code_challenge_methods_supported" in discovery
        assert "S256" in discovery["code_challenge_methods_supported"]

    def test_jwks_response(self):
        """JWKS should contain signing keys"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        jwks = oauth.get_jwks()

        assert "keys" in jwks
        assert len(jwks["keys"]) > 0
        key = jwks["keys"][0]
        assert key["kty"] == "oct"
        assert key["alg"] == "HS256"


class TestOAuthClientManagement:
    """Test OAuth client registration and validation"""

    def test_register_client(self):
        """Should register a new client"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        result = oauth.register_client(
            client_id="new-client",
            redirect_uris=["http://localhost/callback"],
            scope=["openid"],
        )
        assert result["client_id"] == "new-client"
        assert "redirect_uris" in result

    def test_validate_client_public_client(self):
        """Should validate registered public client (no redirect_uris = no secret)"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        # Pass empty redirect_uris to get public client (no secret)
        oauth.register_client(
            client_id="public-client",
            redirect_uris=[],
        )
        assert oauth.validate_client("public-client") is True

    def test_validate_client_with_secret(self):
        """Should validate confidential client with secret"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        oauth.register_client(
            client_id="confidential-client",
            redirect_uris=["http://localhost/callback"],
        )
        # Client has a generated secret - need to pass it for validation
        client_info = oauth._clients["confidential-client"]
        assert oauth.validate_client("confidential-client", client_info["client_secret"]) is True

    def test_validate_client_invalid(self):
        """Should reject unknown client"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        assert oauth.validate_client("unknown-client") is False

    def test_validate_authorization_request(self):
        """Should validate authorization request parameters"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        oauth.register_client(
            client_id="test-client",
            redirect_uris=["http://localhost/callback"],
            scope=["openid"],
        )

        is_valid, error = oauth.validate_authorization_request(
            client_id="test-client",
            redirect_uri="http://localhost/callback",
            response_type="code",
            scope=["openid"],
            state="test-state",
            code_challenge="test-challenge",
            code_challenge_method="S256",
        )
        assert is_valid is True
        assert error is None


class TestStateAndNonce:
    """Test state and nonce generation"""

    def test_generate_state(self):
        """State should be random and URL-safe"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        state = oauth.generate_state()
        assert len(state) > 20
        # URL-safe characters only
        assert all(c.isalnum() or c in '-._~' for c in state)

    def test_generate_nonce(self):
        """Nonce should be random"""
        oauth = OAuthService(issuer="http://test.com", jwt_secret="test-secret")
        nonce = oauth.generate_nonce()
        assert len(nonce) > 20
        nonce2 = oauth.generate_nonce()
        assert nonce != nonce2  # Should be unique each time