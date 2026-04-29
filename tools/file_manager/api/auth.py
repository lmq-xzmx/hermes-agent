"""
Authentication API - JWT based auth with session management
"""

from __future__ import annotations

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from functools import wraps

from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..engine.models import User, UserSession, Role, init_db, create_builtin_roles


# ============================================================================
# Pydantic Models
# ============================================================================

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: Dict[str, Any]


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================================================
# JWT Configuration
# ============================================================================

# These should be loaded from config in production
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"


class JWTManager:
    """
    Manages JWT token creation and validation
    
    In production, load JWT_SECRET from environment/config
    """
    
    def __init__(self, secret: str, db_session_factory: Callable[[], Session]):
        self.secret = secret
        self.db = db_session_factory
        self._imports()
    
    def _imports(self):
        """Lazy imports to avoid circular dependencies"""
        global jwt, PyJWT
        import jwt
        import jwt
    
    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a new access token for a user"""
        if expires_delta is None:
            expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        expire = datetime.utcnow() + expires_delta
        
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.name if user.role else None,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }
        
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)
    
    def create_refresh_token(self, user: User) -> str:
        """Create a new refresh token for a user"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user.id,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_hex(16),  # Unique token ID
        }
        
        return jwt.encode(payload, self.secret, algorithm=ALGORITHM)
    
    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode an access token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[ALGORITHM])
            if payload.get("type") != "access":
                raise HTTPException(status_code=401, detail="Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    
    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a refresh token"""
        try:
            payload = jwt.decode(token, self.secret, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                raise HTTPException(status_code=401, detail="Invalid token type")
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid refresh token: {e}")
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user object from access token"""
        payload = self.verify_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        session = self.db()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            return user
        finally:
            session.close()


# ============================================================================
# Auth API
# ============================================================================

class AuthAPI:
    """Authentication API handlers"""
    
    def __init__(
        self,
        jwt_manager: JWTManager,
        db_session_factory: Callable[[], Session],
    ):
        self.jwt = jwt_manager
        self.db_factory = db_session_factory
    
    def login(
        self,
        request: LoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> TokenResponse:
        """Authenticate user and return tokens"""
        session = self.db_factory()
        try:
            # Find user
            user = session.query(User).filter(User.username == request.username).first()
            
            if not user or not user.check_password(request.password):
                # Log failed attempt
                from ..engine.audit import AuditLogger
                audit = AuditLogger(session)
                audit.log_login(
                    user=user,  # None = anonymous
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                )
                raise HTTPException(status_code=401, detail="Invalid username or password")
            
            if not user.is_active:
                raise HTTPException(status_code=403, detail="Account is disabled")
            
            # Create tokens
            access_token = self.jwt.create_access_token(user)
            refresh_token = self.jwt.create_refresh_token(user)
            
            # Store session
            refresh_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            user_session = UserSession(
                user_id=user.id,
                token_hash=refresh_hash,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            )
            session.add(user_session)
            
            # Update last login
            user.last_login = datetime.utcnow()
            session.commit()
            
            # Audit log
            from ..engine.audit import AuditLogger
            audit = AuditLogger(session)
            audit.log_login(user, ip_address=ip_address, user_agent=user_agent)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user.to_dict(),
            )
        finally:
            session.close()
    
    def register(
        self,
        request: RegisterRequest,
        admin_user: Optional[User] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Register a new user (admin only in production)"""
        session = self.db_factory()
        try:
            # Check if username exists
            existing = session.query(User).filter(User.username == request.username).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Get default viewer role if no role specified
            if not request.role_id:
                default_role = session.query(Role).filter(Role.name == "viewer").first()
                role_id = default_role.id if default_role else None
            else:
                role_id = request.role_id
            
            # Create user
            user = User(
                username=request.username,
                email=request.email,
                role_id=role_id,
            )
            user.set_password(request.password)
            
            session.add(user)
            session.commit()
            
            # Audit log
            from ..engine.audit import AuditLogger
            audit = AuditLogger(session)
            audit.log_admin_action(
                action="user_create",
                admin=admin_user,
                target_id=user.id,
                ip_address=ip_address,
                metadata={"username": user.username},
            )
            
            return user
        finally:
            session.close()
    
    def refresh(self, request: RefreshRequest) -> TokenResponse:
        """Refresh access token using refresh token"""
        session = self.db_factory()
        try:
            # Verify refresh token
            payload = self.jwt.verify_refresh_token(request.refresh_token)
            user_id = payload.get("sub")
            
            # Find user
            user = session.query(User).filter(User.id == user_id).first()
            if not user or not user.is_active:
                raise HTTPException(status_code=401, detail="User not found or disabled")
            
            # Verify session exists
            refresh_hash = hashlib.sha256(request.refresh_token.encode()).hexdigest()
            user_session = (
                session.query(UserSession)
                .filter(
                    UserSession.user_id == user_id,
                    UserSession.token_hash == refresh_hash,
                    UserSession.is_active == True,
                )
                .first()
            )
            
            if not user_session:
                raise HTTPException(status_code=401, detail="Session not found or revoked")
            
            if user_session.expires_at < datetime.utcnow():
                raise HTTPException(status_code=401, detail="Session has expired")
            
            # Create new tokens
            access_token = self.jwt.create_access_token(user)
            new_refresh_token = self.jwt.create_refresh_token(user)
            
            # Update session
            old_hash = refresh_hash
            user_session.token_hash = hashlib.sha256(new_refresh_token.encode()).hexdigest()
            user_session.last_activity = datetime.utcnow()
            user_session.expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            session.commit()
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=user.to_dict(),
            )
        finally:
            session.close()
    
    def logout(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, str]:
        """Logout user and invalidate session"""
        session = self.db_factory()
        try:
            # Log logout
            from ..engine.audit import AuditLogger
            audit = AuditLogger(session)
            audit.log_logout(user, ip_address=ip_address, user_agent=user_agent)
            
            # Invalidate all sessions for this user
            session.query(UserSession).filter(
                UserSession.user_id == user.id,
                UserSession.is_active == True,
            ).update({"is_active": False})
            session.commit()
            
            return {"message": "Logged out successfully"}
        finally:
            session.close()


# ============================================================================
# FastAPI Dependencies
# ============================================================================

security = HTTPBearer()


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    FastAPI dependency to get current authenticated user
    """
    # Import here to avoid circular reference and access global store
    import sys
    from pathlib import Path
    _tools_dir = Path(__file__).parent.parent
    if str(_tools_dir) not in sys.path:
        sys.path.insert(0, str(_tools_dir))
    from file_manager.api.auth import JWTManager
    
    # Access jwt_manager from global store
    from tools.file_manager.server import _api_instances
    jwt_manager = _api_instances.get("jwt_manager")
    
    if jwt_manager is None:
        raise HTTPException(status_code=500, detail="Auth not configured")
    
    token = credentials.credentials
    user = jwt_manager.get_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    
    return user


def jwt_required(
    allowed_roles: Optional[list] = None,
):
    """
    Decorator for requiring JWT auth with optional role check
    
    Usage:
        @app.get("/admin")
        @jwt_required(allowed_roles=["admin"])
        def admin_only(user: User = Depends(get_current_user)):
            return {"admin": user.username}
    """
    def dependency(user: User = Depends(get_current_user)) -> User:
        if allowed_roles and user.role and user.role.name not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency


def get_client_info(request: Request) -> Dict[str, Optional[str]]:
    """Extract client IP and user agent from request"""
    if request is None:
        return {"ip_address": None, "user_agent": None}
    # Check for forwarded headers (behind proxy)
    ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.headers.get("X-Real-IP") or
        request.client.host if request.client else None
    )
    user_agent = request.headers.get("User-Agent")
    return {"ip_address": ip, "user_agent": user_agent}
