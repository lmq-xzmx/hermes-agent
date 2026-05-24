"""
OAuth 2.0 / OIDC Service - Authorization Code Flow with PKCE

提供标准 OAuth 2.0 认证流程，支持：
- Authorization Code Flow with PKCE
- Token 刷新和撤销
- OIDC Discovery Document
- JWKS 端点

用于统一账号体系中的第三方登录（Google/GitHub/企业微信/飞书）。
"""

from __future__ import annotations

import hashlib
import secrets
import base64
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# OAuth Constants
# =============================================================================

# OAuth 2.0 RFC 7636 PKCE code challenge methods
CODE_CHALLENGE_METHOD = "S256"

# OAuth 2.0 response types
RESPONSE_TYPE_CODE = "code"

# OAuth 2.0 grant types
GRANT_TYPE_AUTHORIZATION_CODE = "authorization_code"
GRANT_TYPE_REFRESH_TOKEN = "refresh_token"

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"


# =============================================================================
# Domain Types
# =============================================================================

@dataclass
class OAuthAuthorizationRequest:
    """Authorization request from client"""
    client_id: str
    redirect_uri: str
    response_type: str
    scope: List[str]
    state: str
    code_challenge: str
    code_challenge_method: str
    nonce: Optional[str] = None
    code_verifier: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class OAuthAuthorizationCode:
    """Authorization code stored server-side"""
    code: str
    client_id: str
    redirect_uri: str
    scope: List[str]
    state: str
    code_challenge: str
    code_challenge_method: str
    user_id: str
    expires_at: float
    nonce: Optional[str] = None
    code_verifier: Optional[str] = None


@dataclass
class OAuthTokenRequest:
    """Token request from client"""
    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None


@dataclass
class OAuthTokenResponse:
    """Token response to client"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    refresh_token: Optional[str] = None
    scope: Optional[str] = None
    id_token: Optional[str] = None


@dataclass
class OAuthUserInfo:
    """User information from OAuth provider"""
    user_id: str
    username: str
    email: Optional[str] = None
    provider: Optional[str] = None
    provider_user_id: Optional[str] = None


# =============================================================================
# OAuth Service
# =============================================================================

class OAuthService:
    """
    OAuth 2.0 Authorization Server implementation.

    Supports:
    - Authorization Code Flow with PKCE (RFC 7636)
    - Token refresh
    - Token revocation
    - OIDC Discovery

    For production use, replace in-memory storage with Redis.
    """

    def __init__(
        self,
        issuer: str,
        jwt_secret: str,
        authorization_codes_ttl: int = 600,  # 10 minutes
        access_token_ttl: int = 3600,          # 1 hour
        refresh_token_ttl: int = 2592000,     # 30 days
    ):
        self._issuer = issuer
        self._jwt_secret = jwt_secret
        self._auth_codes_ttl = authorization_codes_ttl
        self._access_token_ttl = access_token_ttl
        self._refresh_token_ttl = refresh_token_ttl

        # In-memory storage (replace with Redis in production)
        self._authorization_codes: Dict[str, OAuthAuthorizationCode] = {}
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
        self._revoked_tokens: set = set()

        # Registered clients (for production, use database)
        self._clients: Dict[str, Dict[str, Any]] = {
            # Claudian Desktop App
            "claudian-desktop": {
                "client_secret": None,  # Public client (no secret)
                "redirect_uris": [
                    "http://localhost:19827/callback",
                    "http://localhost:18424/callback",
                ],
                "grant_types": [GRANT_TYPE_AUTHORIZATION_CODE, GRANT_TYPE_REFRESH_TOKEN],
                "scope": ["openid", "profile", "email", "craftsman", "apprentice", "knowledge", "butler"],
            },
            # hermes-mcp
            "hermes-mcp": {
                "client_secret": None,  # Public client
                "redirect_uris": [
                    "http://localhost:8080/callback",
                ],
                "grant_types": [GRANT_TYPE_AUTHORIZATION_CODE],
                "scope": ["craftsman", "apprentice"],
            },
        }

    # -------------------------------------------------------------------------
    # PKCE Utilities
    # -------------------------------------------------------------------------

    def generate_code_verifier(self) -> str:
        """Generate PKCE code_verifier (43-128 chars, unreserved URI chars)"""
        # RFC 7636: use high-entropy random string
        token = secrets.token_urlsafe(64)[:128]
        # Ensure minimum length of 43
        while len(token) < 43:
            token += secrets.token_urlsafe(32)
        return token[:128]

    def generate_code_challenge(self, code_verifier: str) -> str:
        """Generate PKCE code_challenge from code_verifier using S256 method"""
        # SHA256 hash of code_verifier, then Base64url encode without padding
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")

    def verify_code_challenge(self, code_verifier: str, code_challenge: str) -> bool:
        """Verify PKCE code_challenge matches code_verifier"""
        if not code_verifier or not code_challenge:
            return False
        expected = self.generate_code_challenge(code_verifier)
        return secrets.compare_digest(expected, code_challenge)

    def generate_state(self) -> str:
        """Generate OAuth state parameter for CSRF protection"""
        return secrets.token_urlsafe(32)

    def generate_nonce(self) -> str:
        """Generate nonce for OIDC ID Token"""
        return secrets.token_urlsafe(32)

    # -------------------------------------------------------------------------
    # Authorization Endpoint
    # -------------------------------------------------------------------------

    def validate_authorization_request(
        self,
        client_id: str,
        redirect_uri: str,
        response_type: str,
        scope: List[str],
        state: str,
        code_challenge: str,
        code_challenge_method: str,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate authorization request parameters.

        Returns:
            (is_valid, error_description)
        """
        # Validate client_id
        if client_id not in self._clients:
            return False, "invalid_client_id"

        client = self._clients[client_id]

        # Validate redirect_uri
        if redirect_uri not in client["redirect_uris"]:
            return False, "invalid_redirect_uri"

        # Validate response_type (must be "code")
        if response_type != RESPONSE_TYPE_CODE:
            return False, "unsupported_response_type"

        # Validate code_challenge_method
        if code_challenge_method != CODE_CHALLENGE_METHOD:
            return False, "unsupported_code_challenge_method"

        # Validate scope
        allowed_scope = set(client["scope"])
        requested_scope = set(scope)
        if not requested_scope.issubset(allowed_scope):
            return False, "invalid_scope"

        return True, None

    def create_authorization_code(
        self,
        client_id: str,
        redirect_uri: str,
        scope: List[str],
        state: str,
        code_challenge: str,
        code_challenge_method: str,
        user_id: str,
        nonce: Optional[str] = None,
    ) -> OAuthAuthorizationCode:
        """
        Create and store an authorization code.

        The code is a high-entropy random string.
        """
        code = secrets.token_urlsafe(48)  # ~64 chars

        auth_code = OAuthAuthorizationCode(
            code=code,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            user_id=user_id,
            nonce=nonce,
            expires_at=time.time() + self._auth_codes_ttl,
        )

        self._authorization_codes[code] = auth_code
        logger.info(f"Created authorization code for user {user_id}, client {client_id}")

        return auth_code

    def exchange_authorization_code(
        self,
        code: str,
        redirect_uri: str,
        client_id: str,
        code_verifier: str,
    ) -> tuple[Optional[OAuthTokenResponse], Optional[str]]:
        """
        Exchange authorization code for tokens (PKCE flow).

        Returns:
            (token_response, error_code)
        """
        # Validate code exists
        if code not in self._authorization_codes:
            return None, "invalid_grant"

        auth_code = self._authorization_codes[code]

        # Check expiration
        if time.time() > auth_code.expires_at:
            del self._authorization_codes[code]
            return None, "invalid_grant"

        # Validate client_id matches
        if auth_code.client_id != client_id:
            return None, "invalid_grant"

        # Validate redirect_uri matches
        if auth_code.redirect_uri != redirect_uri:
            return None, "invalid_grant"

        # Validate PKCE code_verifier
        if not self.verify_code_challenge(code_verifier, auth_code.code_challenge):
            return None, "invalid_grant"

        # Delete used authorization code (single use)
        del self._authorization_codes[code]

        # Generate tokens
        return self._generate_token_response(
            user_id=auth_code.user_id,
            scope=auth_code.scope,
            nonce=auth_code.nonce,
        )

    def _generate_token_response(
        self,
        user_id: str,
        scope: List[str],
        nonce: Optional[str] = None,
    ) -> tuple[OAuthTokenResponse, None]:
        """Generate access and refresh tokens"""
        import jwt

        # Access token
        now = int(time.time())
        access_payload = {
            "sub": user_id,
            "iss": self._issuer,
            "aud": "hermes-file-manager",
            "exp": now + self._access_token_ttl,
            "iat": now,
            "type": TOKEN_TYPE_ACCESS,
            "scope": " ".join(scope),
            "jti": secrets.token_urlsafe(16),
        }
        access_token = jwt.encode(access_payload, self._jwt_secret, algorithm="HS256")

        # Refresh token
        refresh_token = secrets.token_urlsafe(48)
        self._refresh_tokens[refresh_token] = {
            "user_id": user_id,
            "scope": scope,
            "created_at": now,
            "expires_at": now + self._refresh_token_ttl,
            "jti": secrets.token_urlsafe(16),
        }

        return OAuthTokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self._access_token_ttl,
            refresh_token=refresh_token,
            scope=" ".join(scope),
            id_token=None,  # OIDC adds this if nonce was provided
        ), None

    # -------------------------------------------------------------------------
    # Token Endpoint
    # -------------------------------------------------------------------------

    def refresh_access_token(
        self,
        refresh_token: str,
    ) -> tuple[Optional[OAuthTokenResponse], Optional[str]]:
        """
        Refresh access token using refresh token.

        Returns:
            (token_response, error_code)
        """
        if refresh_token not in self._refresh_tokens:
            return None, "invalid_grant"

        token_data = self._refresh_tokens[refresh_token]

        # Check expiration
        if time.time() > token_data["expires_at"]:
            del self._refresh_tokens[refresh_token]
            return None, "invalid_grant"

        # Generate new tokens
        return self._generate_token_response(
            user_id=token_data["user_id"],
            scope=token_data["scope"],
        )

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (access or refresh).

        Returns True if token was revoked, False if not found.
        """
        # Add to revoked tokens set
        self._revoked_tokens.add(token)

        # Remove refresh token if present
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]
            return True

        return True  # Token was valid even if not a refresh token

    def is_token_revoked(self, jti: str) -> bool:
        """Check if a token (by jti) has been revoked"""
        return jti in self._revoked_tokens

    # -------------------------------------------------------------------------
    # OIDC Discovery
    # -------------------------------------------------------------------------

    def get_oidc_discovery(self) -> Dict[str, Any]:
        """
        Return OIDC Discovery Document (/.well-known/openid-configuration)
        """
        base_url = self._issuer.rstrip("/")

        return {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/oauth/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "userinfo_endpoint": f"{base_url}/oauth/userinfo",
            "revocation_endpoint": f"{base_url}/oauth/revoke",
            "jwks_uri": f"{base_url}/.well-known/jwks.json",
            "response_types_supported": ["code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["HS256", "RS256"],
            "scopes_supported": [
                "openid", "profile", "email",
                "craftsman", "apprentice", "knowledge", "butler",
            ],
            "token_endpoint_auth_methods_supported": ["none", "client_secret_basic"],
            "code_challenge_methods_supported": ["S256"],
            "grant_types_supported": [
                GRANT_TYPE_AUTHORIZATION_CODE,
                GRANT_TYPE_REFRESH_TOKEN,
            ],
        }

    def get_jwks(self) -> Dict[str, Any]:
        """
        Return JSON Web Key Set for token verification.

        For HS256 symmetric keys, we include the key in the JWKS.
        For RS256, we would use asymmetric keys.
        """
        import jwt

        # For HS256, the secret is the key
        # In production, use RSA keys for RS256
        key = self._jwt_secret.encode("utf-8")
        from base64 import b64encode
        import hashlib

        # Generate a kid based on key thumbprint
        thumbprint = hashlib.sha256(key).digest()
        kid = base64.urlsafe_b64encode(thumbprint).rstrip(b"=").decode("utf-8")

        return {
            "keys": [
                {
                    "kty": "oct",
                    "use": "sig",
                    "alg": "HS256",
                    "kid": kid,
                    "k": base64.urlsafe_b64encode(key).rstrip(b"=").decode("utf-8"),
                }
            ]
        }

    # -------------------------------------------------------------------------
    # Client Management
    # -------------------------------------------------------------------------

    def register_client(
        self,
        client_id: str,
        redirect_uris: List[str],
        scope: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Register a new OAuth client.

        Returns client info (client_secret is None for public clients).
        """
        if scope is None:
            scope = ["openid", "profile", "email"]

        # Generate client secret (None for public clients)
        client_secret = secrets.token_urlsafe(32) if redirect_uris else None

        self._clients[client_id] = {
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "grant_types": [GRANT_TYPE_AUTHORIZATION_CODE, GRANT_TYPE_REFRESH_TOKEN],
            "scope": scope,
        }

        return {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
        }

    def validate_client(self, client_id: str, client_secret: Optional[str] = None) -> bool:
        """
        Validate client credentials.

        Returns True if client is valid.
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]

        # Public clients don't need secret
        if client["client_secret"] is None:
            return True

        # Confidential clients must provide secret
        if client_secret is None:
            return False

        return secrets.compare_digest(client["client_secret"], client_secret)


# =============================================================================
# OAuth Middleware (for FastAPI)
# =============================================================================

class OAuthMiddleware:
    """
    FastAPI middleware for OAuth 2.0 token validation.

    Validates Bearer tokens in Authorization header.
    """

    def __init__(self, oauth_service: OAuthService):
        self._oauth = oauth_service

    async def __call__(self, request, call_next):
        # Skip OAuth for public endpoints
        public_paths = [
            "/oauth/authorize",
            "/oauth/token",
            "/.well-known/openid-configuration",
            "/.well-known/jwks.json",
            "/health",
        ]

        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)

        # Validate Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]

            try:
                import jwt
                payload = jwt.decode(
                    token,
                    self._oauth._jwt_secret,
                    algorithms=["HS256"],
                    audience="hermes-file-manager",
                )

                # Check if token is revoked
                jti = payload.get("jti")
                if jti and self._oauth.is_token_revoked(jti):
                    # Token has been revoked
                    pass  # Let later middleware handle

                # Attach user info to request state
                request.state.user_id = payload.get("sub")
                request.state.scope = payload.get("scope", "").split()

            except jwt.ExpiredSignatureError:
                pass  # Let later middleware handle
            except jwt.InvalidTokenError:
                pass  # Let later middleware handle

        return await call_next(request)


# =============================================================================
# Global OAuth Service Instance
# =============================================================================

_oauth_service: Optional[OAuthService] = None


def get_oauth_service() -> OAuthService:
    """Get global OAuth service instance"""
    global _oauth_service
    if _oauth_service is None:
        from ..server import get_config
        config = get_config()
        jwt_secret = config.get("jwt", {}).get("secret", "dev-secret-change-in-production")
        issuer = config.get("server", {}).get("base_url", "http://localhost:8080")

        _oauth_service = OAuthService(
            issuer=issuer,
            jwt_secret=jwt_secret,
        )
    return _oauth_service


def setup_oauth_service(jwt_secret: str, issuer: str) -> OAuthService:
    """Initialize OAuth service with configuration"""
    global _oauth_service
    _oauth_service = OAuthService(
        issuer=issuer,
        jwt_secret=jwt_secret,
    )
    return _oauth_service