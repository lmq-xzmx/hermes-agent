"""
Token Service - JWT Token Management

职责：
- Access Token 生成与验证
- Refresh Token 轮换（单次使用）
- Token 撤销（登出）
- Token 检查（能力验证）
"""

from __future__ import annotations

import jwt
import time
import secrets
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# Token Types
# =============================================================================

@dataclass
class TokenClaims:
    """JWT Token claims structure"""
    sub: str              # User ID
    username: str
    email: Optional[str] = None
    teams: List[str] = None
    roles: Dict[str, str] = None
    capabilities: Dict[str, List[str]] = None
    scope: List[str] = None
    exp: int = 3600       # Expiration timestamp
    iat: int = None       # Issued at
    type: str = "access"  # "access" or "refresh"
    jti: str = None       # Token ID for revocation
    aud: str = "hermes-file-manager"


# =============================================================================
# Token Service
# =============================================================================

class TokenService:
    """
    Token management service.

    职责：
    - 生成 Access Token 和 Refresh Token
    - 验证 Token 有效性
    - 刷新 Token
    - 撤销 Token
    - 检查 Token 能力
    """

    def __init__(
        self,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        access_token_expire_minutes: int = 60,
        refresh_token_expire_days: int = 30,
    ):
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._access_expire = access_token_expire_minutes * 60
        self._refresh_expire = refresh_token_expire_days * 86400

        # Revoked tokens set (JTI -> expiration time)
        # In production, use Redis with TTL
        self._revoked: Dict[str, float] = {}

        # Refresh tokens (JTI -> token data)
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}

    # -------------------------------------------------------------------------
    # Token Generation
    # -------------------------------------------------------------------------

    def create_access_token(
        self,
        user_id: str,
        username: str,
        teams: Optional[List[str]] = None,
        roles: Optional[Dict[str, str]] = None,
        capabilities: Optional[Dict[str, List[str]]] = None,
        scope: Optional[List[str]] = None,
        audience: str = "hermes-file-manager",
    ) -> str:
        """
        Create a new Access Token.

        Args:
            user_id: User UUID
            username: Username
            teams: List of team IDs
            roles: {team_id: role} mapping
            capabilities: {category: [capabilities]} mapping
            scope: OAuth scope list
            audience: Token audience

        Returns:
            JWT access token string
        """
        now = int(time.time())

        claims = {
            "sub": user_id,
            "username": username,
            "email": None,
            "teams": teams or [],
            "roles": roles or {},
            "capabilities": capabilities or {},
            "scope": scope or [],
            "exp": now + self._access_expire,
            "iat": now,
            "type": "access",
            "jti": secrets.token_urlsafe(16),
            "aud": audience,
        }

        return jwt.encode(claims, self._jwt_secret, algorithm=self._jwt_algorithm)

    def create_refresh_token(
        self,
        user_id: str,
        scope: Optional[List[str]] = None,
    ) -> tuple[str, str]:
        """
        Create a new Refresh Token and return it with its JTI.

        Returns:
            (refresh_token, jti)
        """
        now = int(time.time())
        jti = secrets.token_urlsafe(16)

        # Store refresh token metadata (in production, use Redis)
        self._refresh_tokens[jti] = {
            "user_id": user_id,
            "scope": scope or [],
            "created_at": now,
            "expires_at": now + self._refresh_expire,
        }

        # Create a signed JWT for the refresh token (contains jti only)
        claims = {
            "sub": user_id,
            "jti": jti,
            "type": "refresh",
            "exp": now + self._refresh_expire,
            "iat": now,
        }

        token = jwt.encode(claims, self._jwt_secret, algorithm=self._jwt_algorithm)
        return token, jti

    # -------------------------------------------------------------------------
    # Token Validation
    # -------------------------------------------------------------------------

    def verify_token(self, token: str) -> Optional[TokenClaims]:
        """
        Verify and decode a token.

        Returns TokenClaims if valid, None if invalid/expired/revoked.
        """
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
                audience="hermes-file-manager",
            )

            # Check if token type is as expected
            token_type = payload.get("type", "access")

            # Check revocation
            jti = payload.get("jti")
            if jti and self.is_revoked(jti):
                logger.warning(f"Token revoked: {jti}")
                return None

            return TokenClaims(
                sub=payload["sub"],
                username=payload.get("username", ""),
                email=payload.get("email"),
                teams=payload.get("teams", []),
                roles=payload.get("roles", {}),
                capabilities=payload.get("capabilities", {}),
                scope=payload.get("scope", []),
                exp=payload.get("exp", 0),
                iat=payload.get("iat", 0),
                type=payload.get("type", "access"),
                jti=payload.get("jti"),
                aud=payload.get("aud", "hermes-file-manager"),
            )

        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid token: {e}")
            return None

    def is_revoked(self, jti: str) -> bool:
        """Check if a token has been revoked"""
        if jti in self._revoked:
            # Check if revocation has expired
            if time.time() > self._revoked[jti]:
                del self._revoked[jti]
                return False
            return True
        return False

    # -------------------------------------------------------------------------
    # Token Refresh
    # -------------------------------------------------------------------------

    def refresh_access_token(self, refresh_token: str) -> Optional[tuple[str, str]]:
        """
        Refresh access token using refresh token.

        Implements single-use refresh token rotation.

        Returns:
            (new_access_token, new_refresh_token) if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                refresh_token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
            )

            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")

            # Verify refresh token exists and is valid
            if jti not in self._refresh_tokens:
                return None

            token_data = self._refresh_tokens[jti]

            # Check expiration
            if time.time() > token_data["expires_at"]:
                del self._refresh_tokens[jti]
                return None

            # Invalidate old refresh token (rotation)
            del self._refresh_tokens[jti]

            # Generate new access token
            new_access = self.create_access_token(
                user_id=payload["sub"],
                username=token_data.get("username", ""),
                teams=token_data.get("teams", []),
                roles=token_data.get("roles", {}),
                capabilities=token_data.get("capabilities", {}),
                scope=token_data["scope"],
            )

            # Generate new refresh token
            new_refresh, new_jti = self.create_refresh_token(
                user_id=payload["sub"],
                scope=token_data["scope"],
            )

            return new_access, new_refresh

        except jwt.InvalidTokenError:
            return None

    # -------------------------------------------------------------------------
    # Token Revocation
    # -------------------------------------------------------------------------

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (access or refresh).

        For access tokens, stores JTI in revoked set with expiration.
        For refresh tokens, removes from storage.

        Returns True if revoked, False if not found.
        """
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=[self._jwt_algorithm],
                options={"verify_exp": False, "verify_aud": False},  # Allow expired tokens for revocation
            )

            jti = payload.get("jti")
            if not jti:
                return False

            # Store revocation with expiration
            exp = payload.get("exp", 0)
            self._revoked[jti] = max(exp, int(time.time()) + 3600)  # At least 1 hour

            # Handle refresh tokens
            if payload.get("type") == "refresh" and jti in self._refresh_tokens:
                del self._refresh_tokens[jti]

            logger.info(f"Revoked token: {jti}")
            return True

        except jwt.InvalidTokenError:
            return False

    def revoke_all_user_tokens(self, user_id: str) -> int:
        """
        Revoke all tokens for a user (logout from all devices).

        Returns number of tokens revoked.
        """
        count = 0

        # Revoke all refresh tokens for this user
        for jti, data in list(self._refresh_tokens.items()):
            if data.get("user_id") == user_id:
                del self._refresh_tokens[jti]
                count += 1

        # Note: Access tokens can only be revoked by JTI
        # For full logout, use blocklist approach

        logger.info(f"Revoked {count} refresh tokens for user {user_id}")
        return count

    # -------------------------------------------------------------------------
    # Token Introspection (RFC 7662)
    # -------------------------------------------------------------------------

    def introspect_token(self, token: str) -> Dict[str, Any]:
        """
        Token introspection as per RFC 7662.

        Returns token metadata or inactive status.
        """
        claims = self.verify_token(token)

        if claims is None:
            return {"active": False}

        return {
            "active": True,
            "sub": claims.sub,
            "username": claims.username,
            "scope": " ".join(claims.scope) if claims.scope else "",
            "exp": claims.exp,
            "iat": claims.iat,
            "type": claims.type,
            "jti": claims.jti,
        }

    # -------------------------------------------------------------------------
    # Capability Checking
    # -------------------------------------------------------------------------

    def has_capability(
        self,
        token_or_claims,
        category: str,
        capability: str,
    ) -> bool:
        """
        Check if token has a specific capability.

        Args:
            token_or_claims: Either a token string or TokenClaims instance
            category: Capability category (craftsman, apprentice, knowledge, butler)
            capability: Capability name

        Returns:
            True if capability is granted
        """
        if isinstance(token_or_claims, str):
            claims = self.verify_token(token_or_claims)
        else:
            claims = token_or_claims

        if claims is None:
            return False

        caps = claims.capabilities or {}
        category_caps = caps.get(category, [])
        return capability in category_caps

    def has_scope(self, token_or_claims, scope: str) -> bool:
        """
        Check if token has a specific OAuth scope.

        Returns:
            True if scope is granted
        """
        if isinstance(token_or_claims, str):
            claims = self.verify_token(token_or_claims)
        else:
            claims = token_or_claims

        if claims is None:
            return False

        return scope in (claims.scope or [])

    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------

    def cleanup_expired(self) -> int:
        """
        Clean up expired revoked tokens and refresh tokens.

        Returns count of cleaned entries.
        """
        now = time.time()
        count = 0

        # Clean revoked tokens
        expired_revoked = [jti for jti, exp in self._revoked.items() if now > exp]
        for jti in expired_revoked:
            del self._revoked[jti]
            count += 1

        # Clean expired refresh tokens
        expired_refresh = [jti for jti, data in self._refresh_tokens.items() if now > data["expires_at"]]
        for jti in expired_refresh:
            del self._refresh_tokens[jti]
            count += 1

        return count


# Global token service instance
_token_service: Optional[TokenService] = None


def get_token_service() -> TokenService:
    """Get global token service instance"""
    global _token_service
    if _token_service is None:
        from ..server import get_config
        config = get_config()
        jwt_secret = config.get("jwt", {}).get("secret", "dev-secret-change-in-production")

        _token_service = TokenService(
            jwt_secret=jwt_secret,
            jwt_algorithm="HS256",
            access_token_expire_minutes=60,
            refresh_token_expire_days=30,
        )
    return _token_service


def setup_token_service(
    jwt_secret: str,
    jwt_algorithm: str = "HS256",
    access_token_expire_minutes: int = 60,
    refresh_token_expire_days: int = 30,
) -> TokenService:
    """Initialize token service with configuration"""
    global _token_service
    _token_service = TokenService(
        jwt_secret=jwt_secret,
        jwt_algorithm=jwt_algorithm,
        access_token_expire_minutes=access_token_expire_minutes,
        refresh_token_expire_days=refresh_token_expire_days,
    )
    return _token_service