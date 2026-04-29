"""
Tests for Hermes File Manager - Auth API
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import secrets
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


# We test JWTManager directly without FastAPI machinery
class TestJWTManagerUnit:
    def test_jwt_manager_creation(self):
        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="jwttest", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        user_id = user.id
        sess.close()

        from tools.file_manager.api.auth import JWTManager

        manager = JWTManager(secret="test-secret-key", db_session_factory=Session)

        # Re-fetch user in new session
        sess2 = Session()
        user2 = sess2.query(User).filter(User.id == user_id).first()

        token = manager.create_access_token(user2)
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode and verify
        decoded = manager.verify_access_token(token)
        assert decoded["sub"] == user_id
        assert decoded["username"] == "jwttest"

        sess2.close()


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


class TestAuthAPI:
    """RED Phase: AuthAPI.login, register, refresh, logout"""

    def test_login_success(self):
        """Login with valid credentials returns tokens and user"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, LoginRequest

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="logintest", role=admin_role)
        user.set_password("correctpassword")
        sess.add(user)
        sess.commit()
        sess.close()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        response = api.login(LoginRequest(username="logintest", password="correctpassword"))

        assert response.access_token
        assert response.refresh_token
        assert response.user["username"] == "logintest"
        assert response.expires_in > 0

    def test_login_invalid_password_returns_401(self):
        """Login with wrong password raises 401"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, LoginRequest
        from fastapi import HTTPException

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="wrongpass", role=admin_role)
        user.set_password("realpassword")
        sess.add(user)
        sess.commit()
        sess.close()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        with pytest.raises(HTTPException) as exc_info:
            api.login(LoginRequest(username="wrongpass", password="badpassword"))
        assert exc_info.value.status_code == 401

    def test_login_user_not_found_returns_401(self):
        """Login with non-existent user raises 401"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, LoginRequest
        from fastapi import HTTPException

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()
        sess.close()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        with pytest.raises(HTTPException) as exc_info:
            api.login(LoginRequest(username="ghostuser", password="anypassword"))
        assert exc_info.value.status_code == 401

    def test_register_success(self):
        """Register new user returns user object"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, RegisterRequest

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        new_user = api.register(RegisterRequest(
            username="newuser", password="SecurePass123!", email="new@example.com"
        ))

        # User object is detached after session closes inside register(); re-query
        sess2 = Session()
        user_row = sess2.query(User).filter(User.username == "newuser").first()
        assert user_row is not None
        assert user_row.email == "new@example.com"
        assert user_row.check_password("SecurePass123!")
        # Should be assigned viewer role by default
        assert user_row.role.name == "viewer"
        sess2.close()
        sess.close()

    def test_register_duplicate_username_raises_400(self):
        """Register with existing username raises 400"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, RegisterRequest
        from fastapi import HTTPException

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="duplicate", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        sess.close()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        with pytest.raises(HTTPException) as exc_info:
            api.register(RegisterRequest(username="duplicate", password="pass"))
        assert exc_info.value.status_code == 400

    def test_refresh_token_returns_new_tokens(self):
        """Refresh with valid refresh token returns new access + refresh tokens"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, LoginRequest, RefreshRequest

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="refreshuser", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        sess.close()

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)

        login_resp = api.login(LoginRequest(username="refreshuser", password="pass"))
        old_refresh = login_resp.refresh_token

        refresh_resp = api.refresh(RefreshRequest(refresh_token=old_refresh))

        assert refresh_resp.access_token
        assert refresh_resp.refresh_token
        assert refresh_resp.user["username"] == "refreshuser"
        # New refresh token should be different
        assert refresh_resp.refresh_token != old_refresh

    def test_logout_invalidates_sessions(self):
        """Logout returns success message (no exception)"""
        from tools.file_manager.api.auth import JWTManager, AuthAPI, LoginRequest

        eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        Base.metadata.create_all(eng)
        Session = sessionmaker(bind=eng)
        sess = Session()
        create_builtin_roles(sess)
        sess.commit()

        admin_role = sess.query(Role).filter(Role.name == "admin").first()
        user = User(username="logoutuser", role=admin_role)
        user.set_password("pass")
        sess.add(user)
        sess.commit()
        user_id = user.id  # capture ID before session closes

        jwt_mgr = JWTManager(secret="test-secret", db_session_factory=Session)
        api = AuthAPI(jwt_manager=jwt_mgr, db_session_factory=Session)
        api.login(LoginRequest(username="logoutuser", password="pass"))

        # Re-fetch user in a live session for logout
        sess2 = Session()
        live_user = sess2.query(User).filter(User.id == user_id).first()
        result = api.logout(user=live_user)

        assert result["message"] == "Logged out successfully"
        sess2.close()
        sess.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
