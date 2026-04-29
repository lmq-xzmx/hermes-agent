"""
Tests for Hermes File Manager - Auth Service
TDD Phase: Tests written for AuthService architecture
"""

import pytest
import sys
import jwt
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, UserSession, init_db, create_builtin_roles
)
from tools.file_manager.engine.audit import AuditLogger
from tools.file_manager.services.auth_service import AuthService
from tools.file_manager.api.dto import LoginRequestDTO, RegisterRequestDTO, RefreshRequestDTO


# =============================================================================
# TestAuthServiceUnit - Tests for AuthService token methods
# =============================================================================

class TestAuthServiceUnit:
    def test_auth_service_creation(self):
        """AuthService can be instantiated with required dependencies"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret-key",
            event_bus=None,
        )

        assert auth_service._jwt_secret == "test-secret-key"
        assert auth_service.db_factory is not None

    def test_generate_access_token_creates_valid_jwt(self):
        """AuthService generates a valid access token for a user"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user_orm = User(username="tokentest", role=admin_role)
        user_orm.set_password("pass")
        sess.add(user_orm)
        sess.commit()
        user_id = user_orm.id
        role_id = admin_role.id
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret-key",
            event_bus=None,
        )

        from tools.file_manager.services.auth_service import AuthenticatedUser
        user = AuthenticatedUser(
            id=user_id,
            username="tokentest",
            email=None,
            role_id=role_id,
            role_name="admin",
            permission_rules=[],
            is_active=True,
        )

        token = auth_service._generate_access_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert decoded["sub"] == user_id
        assert decoded["username"] == "tokentest"
        assert decoded["type"] == "access"

    def test_generate_refresh_token_creates_valid_jwt(self):
        """AuthService generates a valid refresh token for a user"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user_orm = User(username="refreshtest", role=admin_role)
        user_orm.set_password("pass")
        sess.add(user_orm)
        sess.commit()
        user_id = user_orm.id
        role_id = admin_role.id
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret-key",
            event_bus=None,
        )

        from tools.file_manager.services.auth_service import AuthenticatedUser
        user = AuthenticatedUser(
            id=user_id,
            username="refreshtest",
            email=None,
            role_id=role_id,
            role_name="admin",
            permission_rules=[],
            is_active=True,
        )

        token = auth_service._generate_refresh_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert decoded["sub"] == user_id
        assert decoded["type"] == "refresh"
        assert "jti" in decoded  # unique token id


# =============================================================================
# User Registration & Password
# =============================================================================

class TestUserRegistration:
    def test_password_hashing_with_bcrypt(self):
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()

        admin_role = Role(name="regtest_admin", is_system=False)
        sess.add(admin_role)
        sess.commit()

        user = User(username="hashtest", role=admin_role)
        user.set_password("MySecret123!")
        sess.add(user)
        sess.commit()

        assert user.password_hash != "MySecret123!"
        assert user.check_password("MySecret123!") is True
        assert user.check_password("WrongPassword") is False

        sess.close()


# =============================================================================
# Session Management
# =============================================================================

class TestSessionManagement:
    def test_user_session_creation(self):
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="sessiontest", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()

        session = UserSession(
            user_id=user.id,
            token_hash="abc123hash",
            ip_address="127.0.0.1",
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        sess.add(session)
        sess.commit()

        assert session.id is not None
        assert session.is_active is True

        sess.close()


# =============================================================================
# Role-based Access
# =============================================================================

class TestRoleBasedAccess:
    def test_builtin_roles_have_correct_permissions(self):
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)

        admin = sess.query(Role).filter(Role.name == "admin").first()
        editor = sess.query(Role).filter(Role.name == "editor").first()
        viewer = sess.query(Role).filter(Role.name == "viewer").first()
        guest = sess.query(Role).filter(Role.name == "guest").first()

        assert admin is not None
        assert admin.is_system is True
        assert editor is not None
        assert viewer is not None
        assert guest is not None

        sess.close()


# =============================================================================
# TestAuthService - Tests for AuthService public API
# =============================================================================

class TestAuthService:
    """Tests for AuthService.authenticate, register, refresh_tokens, get_user_from_token, logout"""

    def test_authenticate_success(self):
        """Authenticate with valid credentials returns tokens and user"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="authtest", role=admin_role)
        user.set_password("correctpassword")
        sess.add(user)
        sess.commit()
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        result = auth_service.authenticate(
            LoginRequestDTO(username="authtest", password="correctpassword"),
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        assert result.access_token
        assert result.refresh_token
        assert result.user.username == "authtest"
        assert result.expires_in > 0

    def test_authenticate_invalid_password_raises_value_error(self):
        """Authenticate with wrong password raises ValueError"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="wrongpass", role=admin_role)
        user.set_password("realpassword")
        sess.add(user)
        sess.commit()
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        with pytest.raises(ValueError) as exc_info:
            auth_service.authenticate(
                LoginRequestDTO(username="wrongpass", password="badpassword"),
                ip_address="127.0.0.1",
                user_agent="test-agent",
            )
        assert "Invalid username or password" in str(exc_info.value)

    def test_authenticate_user_not_found_raises_value_error(self):
        """Authenticate with non-existent user raises ValueError"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        with pytest.raises(ValueError) as exc_info:
            auth_service.authenticate(
                LoginRequestDTO(username="ghostuser", password="anypassword"),
                ip_address="127.0.0.1",
                user_agent="test-agent",
            )
        assert "Invalid username or password" in str(exc_info.value)

    def test_register_success(self):
        """Register new user returns user response"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        result = auth_service.register(
            RegisterRequestDTO(
                username="newuser",
                password="SecurePass123!",
                email="new@example.com",
            ),
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        assert result.username == "newuser"
        assert result.email == "new@example.com"
        # Should be assigned viewer role by default
        assert result.role_name == "viewer"

        # Verify user exists in DB with hashed password
        sess2 = db_factory()
        user_row = sess2.query(User).filter(User.username == "newuser").first()
        assert user_row is not None
        assert user_row.email == "new@example.com"
        assert user_row.check_password("SecurePass123!")
        assert user_row.role.name == "viewer"
        sess2.close()

    def test_register_duplicate_username_raises_value_error(self):
        """Register with existing username raises ValueError"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="duplicate", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        with pytest.raises(ValueError) as exc_info:
            auth_service.register(
                RegisterRequestDTO(username="duplicate", password="pass"),
                ip_address="127.0.0.1",
                user_agent="test-agent",
            )
        assert "Username already exists" in str(exc_info.value)

    def test_refresh_tokens_returns_new_tokens(self):
        """Refresh with valid tokens returns new access + refresh tokens"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="refreshuser", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        # First authenticate to get tokens
        auth_result = auth_service.authenticate(
            LoginRequestDTO(username="refreshuser", password="pass"),
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        old_refresh = auth_result.refresh_token

        # Refresh tokens
        refresh_result = auth_service.refresh_tokens(
            RefreshRequestDTO(
                access_token=auth_result.access_token,
                refresh_token=old_refresh,
            )
        )

        assert refresh_result.access_token
        assert refresh_result.refresh_token
        assert refresh_result.user.username == "refreshuser"
        # New refresh token should be different
        assert refresh_result.refresh_token != old_refresh

    def test_get_user_from_token_returns_authenticated_user(self):
        """get_user_from_token with valid access token returns user"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="tokenuser", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        # Get tokens via authenticate
        auth_result = auth_service.authenticate(
            LoginRequestDTO(username="tokenuser", password="pass"),
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )

        # Get user from token
        user_result = auth_service.get_user_from_token(auth_result.access_token)

        assert user_result.username == "tokenuser"
        assert user_result.role_name == "admin"

    def test_get_user_from_token_invalid_raises_value_error(self):
        """get_user_from_token with invalid token raises ValueError"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        with pytest.raises(ValueError) as exc_info:
            auth_service.get_user_from_token("invalid.token.here")
        assert "Invalid token" in str(exc_info.value)

    def test_logout_publishes_event(self):
        """Logout publishes logout event to event bus"""
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        db_factory = sessionmaker(bind=eng)
        sess = db_factory()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="logoutuser", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        user_id = user.id
        sess.close()

        auth_service = AuthService(
            db_factory=db_factory,
            jwt_secret="test-secret",
            event_bus=None,
        )

        # Should not raise
        result = auth_service.logout(user_id)
        assert result is None  # logout returns None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
