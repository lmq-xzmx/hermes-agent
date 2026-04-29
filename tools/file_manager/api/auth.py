"""
Auth API - Thin HTTP layer wrapping AuthService.

This file contains ONLY:
  - FastAPI route handlers (thin, no business logic)
  - FastAPI dependencies (get_current_user)
  - Pydantic request/response models

All business logic lives in services/auth_service.py.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from ..services.auth_service import AuthService, AuthenticatedUser
from ..services.permission_context import PermissionContext


# ============================================================================
# Pydantic Models (kept here for backward compatibility; prefer dto.py)
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class RefreshRequest(BaseModel):
    access_token: str
    refresh_token: str


# ============================================================================
# Security
# ============================================================================

security = HTTPBearer()


# ============================================================================
# FastAPI Dependency
# ============================================================================

def get_auth_service(request: Request) -> AuthService:
    """FastAPI dependency: get AuthService from app state."""
    from ..server import _api_instances
    return _api_instances.get("auth_service")


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> AuthenticatedUser:
    """
    FastAPI dependency: validate access token and return AuthenticatedUser.

    Uses AuthService (pure business logic) - no ORM coupling here.
    """
    auth_service = get_auth_service(request)
    if auth_service is None:
        raise HTTPException(status_code=500, detail="Auth not configured")

    token = credentials.credentials
    try:
        return auth_service.get_user_from_token(token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


def get_client_info(request: Request) -> dict:
    """Extract client IP and user agent from request."""
    forwarded = request.headers.get("X-Forwarded-For", "")
    ip = forwarded.split(",")[0].strip() if forwarded else request.client.host if request.client else "unknown"
    return {
        "ip_address": ip,
        "user_agent": request.headers.get("User-Agent", ""),
    }


# ============================================================================
# Route Handlers (thin - delegating to AuthService)
# ============================================================================

def login(request: Request, login_req: LoginRequest) -> dict:
    """Authenticate and return tokens."""
    from ..api.middleware import LoginRateLimiter
    limiter = LoginRateLimiter()
    limiter.check_login_attempt(request)

    auth_service = get_auth_service(request)
    client_info = get_client_info(request)

    try:
        result = auth_service.authenticate(
            LoginRequestDTO(username=login_req.username, password=login_req.password),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )
        limiter.record_success(request)
        return LoginResponseDTO(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer",
            expires_in=result.expires_in,
            user=result.user.to_response(),
        ).model_dump()
    except ValueError as e:
        limiter.record_failed_attempt(request)
        raise HTTPException(status_code=401, detail=str(e))


def register(request: Request, reg_req: RegisterRequest) -> dict:
    """Register a new user."""
    auth_service = get_auth_service(request)
    client_info = get_client_info(request)

    try:
        user = auth_service.register(
            RegisterRequestDTO(
                username=reg_req.username,
                password=reg_req.password,
                email=reg_req.email,
                role_id=reg_req.role_id,
            ),
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )
        return user.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def refresh(request: RefreshRequest) -> dict:
    """Refresh access token."""
    auth_service = get_auth_service(request)

    try:
        result = auth_service.refresh_tokens(
            RefreshRequestDTO(
                access_token=request.access_token,
                refresh_token=request.refresh_token,
            )
        )
        return LoginResponseDTO(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer",
            expires_in=result.expires_in,
            user=result.user.to_response(),
        ).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
