"""
AuthService - Pure business logic for authentication.

No FastAPI imports. No HTTP concepts.
Emits events to EventBus for audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..api.dto import (
    LoginRequestDTO, RegisterRequestDTO, RefreshRequestDTO,
    LoginResponseDTO, UserResponseDTO, TokenResponseDTO,
)
from .event_bus import EventBus, EventType, Event, get_event_bus


# =============================================================================
# Domain Types (primitives - no ORM)
# =============================================================================

@dataclass
class AuthenticatedUser:
    """
    Pure domain user representation. No ORM dependencies.
    Created at the service layer boundary from ORM User.
    """
    id: str
    username: str
    email: Optional[str]
    role_id: Optional[str]
    role_name: Optional[str]
    permission_rules: List[str]  # e.g. ["read:/projects/**", "write:/public/**"]
    is_active: bool
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def to_response(self) -> UserResponseDTO:
        return UserResponseDTO(
            id=self.id,
            username=self.username,
            email=self.email,
            role_id=self.role_id,
            role_name=self.role_name,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login=self.last_login,
        )


@dataclass
class AuthResult:
    access_token: str
    refresh_token: str
    expires_in: int
    user: AuthenticatedUser


# =============================================================================
# AuthService
# =============================================================================

class AuthService:
    """
    Authentication business logic. Stateless (no HTTP/ORM state).

    Responsibilities:
    - Validate credentials against database
    - Issue JWT tokens
    - Create AuthenticatedUser domain objects
    - Emit auth events to EventBus (for audit, analytics, notifications)
    """

    def __init__(
        self,
        db_factory,
        jwt_secret: str,
        jwt_algorithm: str = "HS256",
        access_token_expire_minutes: int = 1440,
        refresh_token_expire_days: int = 30,
        event_bus: Optional[EventBus] = None,
    ):
        self.db_factory = db_factory
        self._jwt_secret = jwt_secret
        self._jwt_algorithm = jwt_algorithm
        self._access_expire = access_token_expire_minutes
        self._refresh_expire = refresh_token_expire_days
        self._event_bus = event_bus or get_event_bus()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def authenticate(self, request: LoginRequestDTO, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> AuthResult:
        """
        Authenticate username+password. Returns tokens + user info.
        Raises ValueError on failure.
        """
        from ..api.dto import LoginResponseDTO, UserResponseDTO
        from ..engine.models import User

        session = self.db_factory()
        try:
            user_orm = session.query(User).filter(User.username == request.username).first()

            if not user_orm or not user_orm.check_password(request.password):
                self._event_bus.publish(Event.create(
                    EventType.AUTH_LOGIN_FAILED,
                    {"username": request.username, "ip_address": ip_address, "user_agent": user_agent},
                ))
                raise ValueError("Invalid username or password")

            if not user_orm.is_active:
                raise ValueError("Account is disabled")

            # Load role + rules while session is open
            role_name = user_orm.role.name if user_orm.role else None
            permission_rules = [rule.to_primitive() for rule in user_orm.role.permission_rules] if user_orm.role else []

            # Update last login
            user_orm.last_login = datetime.utcnow()
            session.commit()

            # Build domain user
            user = AuthenticatedUser(
                id=user_orm.id,
                username=user_orm.username,
                email=user_orm.email,
                role_id=user_orm.role_id,
                role_name=role_name,
                permission_rules=permission_rules,
                is_active=user_orm.is_active,
                created_at=user_orm.created_at,
                last_login=user_orm.last_login,
            )

            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)

            self._event_bus.publish(Event.create(
                EventType.AUTH_LOGIN_SUCCESS,
                {"user_id": user.id, "username": user.username, "ip_address": ip_address, "user_agent": user_agent},
            ))

            return AuthResult(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self._access_expire * 60,
                user=user,
            )
        finally:
            session.close()

    def register(self, request: RegisterRequestDTO, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> UserResponseDTO:
        """
        Register a new user. Returns user info.
        Raises ValueError if username exists.
        """
        from ..engine.models import User, Role

        session = self.db_factory()
        try:
            existing = session.query(User).filter(User.username == request.username).first()
            if existing:
                raise ValueError("Username already exists")

            # Get default viewer role
            if not request.role_id:
                default_role = session.query(Role).filter(Role.name == "viewer").first()
                role_id = default_role.id if default_role else None
            else:
                role_id = request.role_id

            user_orm = User(username=request.username, email=request.email, role_id=role_id)
            user_orm.set_password(request.password)
            session.add(user_orm)
            session.commit()

            role_name = None
            permission_rules: List[str] = []
            if user_orm.role:
                role_name = user_orm.role.name
                permission_rules = [rule.to_primitive() for rule in user_orm.role.permission_rules]

            user = AuthenticatedUser(
                id=user_orm.id,
                username=user_orm.username,
                email=user_orm.email,
                role_id=user_orm.role_id,
                role_name=role_name,
                permission_rules=permission_rules,
                is_active=user_orm.is_active,
                created_at=user_orm.created_at,
                last_login=user_orm.last_login,
            )

            self._event_bus.publish(Event.create(
                EventType.AUTH_REGISTER,
                {"user_id": user.id, "username": user.username, "ip_address": ip_address, "user_agent": user_agent},
            ))

            # Auto-create Private Space for the user
            self._setup_user_space(user.id)

            return user.to_response()
        finally:
            session.close()

    def _setup_user_space(self, user_id: str) -> None:
        """
        After registration, automatically:
        1. Create a Private Space for the user (2GB default quota)
        2. Assign user to the default Team Space (if exists) as member
        """
        try:
            from .space_service import SpaceService
            space_svc = SpaceService(db_factory=self.db_factory)

            # 1. Create Private Space for the user
            private_space = space_svc.create_space(
                name="我的空间",
                owner_id=user_id,
                storage_pool_id=self._get_default_pool_id(),
                parent_id=None,
                max_bytes=2 * 1024 * 1024 * 1024,  # 2GB
                space_type="private",
                description="个人空间",
            )

            # 2. Assign to default Team Space (if any)
            default_team = self._get_default_team_space()
            if default_team:
                try:
                    space_svc.add_member(
                        space_id=default_team["id"],
                        user_id=user_id,
                        requesting_user_id=user_id,
                        role="member",
                    )
                except Exception:
                    pass  # Already a member or no default team
        except Exception:
            pass  # Non-critical: space creation should not block registration

    def _get_default_pool_id(self) -> str:
        """Get the first active storage pool ID, creating one if needed."""
        from .team_service import TeamService
        team_svc = TeamService(db_factory=self.db_factory)
        pools = team_svc.list_pools()
        active_pools = [p for p in pools if p.get("is_active", True)]
        if active_pools:
            return active_pools[0]["id"]
        # Create default pool if none exists
        import os
        from pathlib import Path
        hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
        default_path = str(Path(hermes_home) / "file_manager" / "storage")
        result = team_svc.create_pool(
            name="默认存储",
            base_path=default_path,
            protocol="local",
            total_bytes=0,
            description="系统默认存储池",
        )
        return result["id"]

    def _get_default_team_space(self) -> Optional[dict]:
        """Get the first Team Space (space_type=team) as default team."""
        from ..engine.models import Space
        session = self.db_factory()
        try:
            team = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active"
            ).first()
            return team.to_dict() if team else None
        finally:
            session.close()

    def refresh_tokens(self, request: RefreshRequestDTO) -> AuthResult:
        """
        Refresh access token using a valid refresh token.
        Returns new tokens + user info.
        """
        import jwt
        from ..engine.models import User

        try:
            payload = jwt.decode(request.refresh_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            if payload.get("type") != "refresh":
                raise ValueError("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")
        except jwt.ExpiredSignatureError:
            raise ValueError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid refresh token: {e}")

        session = self.db_factory()
        try:
            user_orm = session.query(User).filter(User.id == user_id).first()
            if not user_orm or not user_orm.is_active:
                raise ValueError("User not found or disabled")

            role_name = user_orm.role.name if user_orm.role else None
            permission_rules = [rule.to_primitive() for rule in user_orm.role.permission_rules] if user_orm.role else []

            user = AuthenticatedUser(
                id=user_orm.id,
                username=user_orm.username,
                email=user_orm.email,
                role_id=user_orm.role_id,
                role_name=role_name,
                permission_rules=permission_rules,
                is_active=user_orm.is_active,
                created_at=user_orm.created_at,
                last_login=user_orm.last_login,
            )

            access_token = self._generate_access_token(user)
            refresh_token = self._generate_refresh_token(user)

            self._event_bus.publish(Event.create(
                EventType.AUTH_TOKEN_REFRESH,
                {"user_id": user.id, "username": user.username},
            ))

            return AuthResult(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self._access_expire * 60,
                user=user,
            )
        finally:
            session.close()

    def get_user_from_token(self, access_token: str) -> AuthenticatedUser:
        """
        Validate access token and return AuthenticatedUser.
        Raises ValueError on invalid/expired token.
        """
        import jwt
        from ..engine.models import User

        try:
            payload = jwt.decode(access_token, self._jwt_secret, algorithms=[self._jwt_algorithm])
            if payload.get("type") != "access":
                raise ValueError("Invalid token type")
            user_id = payload.get("sub")
            if not user_id:
                raise ValueError("Invalid token payload")
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise ValueError(f"Invalid token: {e}")

        session = self.db_factory()
        try:
            user_orm = session.query(User).filter(User.id == user_id).first()
            if not user_orm or not user_orm.is_active:
                raise ValueError("User not found or disabled")

            role_name = user_orm.role.name if user_orm.role else None
            permission_rules = [rule.to_primitive() for rule in user_orm.role.permission_rules] if user_orm.role else []

            return AuthenticatedUser(
                id=user_orm.id,
                username=user_orm.username,
                email=user_orm.email,
                role_id=user_orm.role_id,
                role_name=role_name,
                permission_rules=permission_rules,
                is_active=user_orm.is_active,
                created_at=user_orm.created_at,
                last_login=user_orm.last_login,
            )
        finally:
            session.close()

    def logout(self, user_id: str) -> None:
        """
        Logout user by publishing a logout event for audit.
        Tokens are JWT stateless, so no server-side invalidation needed.
        """
        self._event_bus.publish(Event.create(
            EventType.AUTH_LOGOUT,
            {"user_id": user_id},
        ))

    # -------------------------------------------------------------------------
    # Token Generation (private)
    # -------------------------------------------------------------------------

    def _generate_access_token(self, user: AuthenticatedUser) -> str:
        import jwt
        from datetime import timedelta
        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role_name,
            "exp": datetime.utcnow() + timedelta(minutes=self._access_expire),
            "iat": datetime.utcnow(),
            "type": "access",
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)

    def _generate_refresh_token(self, user: AuthenticatedUser) -> str:
        import jwt
        import secrets
        from datetime import timedelta
        payload = {
            "sub": user.id,
            "exp": datetime.utcnow() + timedelta(days=self._refresh_expire),
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_hex(16),
        }
        return jwt.encode(payload, self._jwt_secret, algorithm=self._jwt_algorithm)
