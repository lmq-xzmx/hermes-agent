"""
Tests for Hermes File Manager - Data Models
TDD Phase: RED (write tests first, they should pass against existing impl)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, PermissionRule, AuditLog, SharedLink, UserSession,
    Operation, Permission, AuditAction,
    init_db, create_builtin_roles,
)


@pytest.fixture
def engine():
    """In-memory SQLite engine for testing"""
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    return eng


@pytest.fixture
def session(engine):
    """Create a new database session for a test"""
    Session = sessionmaker(bind=engine)
    sess = Session()
    create_builtin_roles(sess)
    yield sess
    sess.close()


# =============================================================================
# Operation & Permission Enums
# =============================================================================

class TestEnums:
    def test_operation_values(self):
        assert Operation.READ.value == "read"
        assert Operation.WRITE.value == "write"
        assert Operation.DELETE.value == "delete"
        assert Operation.MANAGE.value == "manage"
        assert Operation.LIST.value == "list"

    def test_permission_values(self):
        assert Permission.READ.value == "read"
        assert Permission.WRITE.value == "write"
        assert Permission.DELETE.value == "delete"
        assert Permission.MANAGE.value == "manage"

    def test_audit_action_values(self):
        assert AuditAction.LOGIN.value == "login"
        assert AuditAction.LOGOUT.value == "logout"
        assert AuditAction.LOGIN_FAILED.value == "login_failed"
        assert AuditAction.FILE_READ.value == "file_read"
        assert AuditAction.FILE_WRITE.value == "file_write"
        assert AuditAction.FILE_DELETE.value == "file_delete"
        assert AuditAction.USER_CREATE.value == "user_create"
        assert AuditAction.SHARE_CREATE.value == "share_create"


# =============================================================================
# Role Model
# =============================================================================

class TestRole:
    def test_role_creation(self, session):
        role = Role(name="test_role", description="A test role")
        session.add(role)
        session.commit()
        assert role.id is not None
        assert role.name == "test_role"
        assert role.is_system is False

    def test_role_to_dict(self, session):
        role = Role(name="dict_role", description="For dict test")
        session.add(role)
        session.commit()
        d = role.to_dict()
        assert d["name"] == "dict_role"
        assert d["description"] == "For dict test"
        assert d["is_system"] is False

    def test_builtin_roles_created(self, session):
        """Builtin roles should exist after create_builtin_roles"""
        admin = session.query(Role).filter(Role.name == "admin").first()
        assert admin is not None
        assert admin.is_system is True

        viewer = session.query(Role).filter(Role.name == "viewer").first()
        assert viewer is not None

        editor = session.query(Role).filter(Role.name == "editor").first()
        assert editor is not None

        guest = session.query(Role).filter(Role.name == "guest").first()
        assert guest is not None


# =============================================================================
# User Model
# =============================================================================

class TestUser:
    def test_user_creation(self, session, engine):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="alice", email="alice@example.com", role=admin_role)
        user.set_password("secret123")
        session.add(user)
        session.commit()

        assert user.id is not None
        assert user.username == "alice"
        assert user.email == "alice@example.com"
        assert user.password_hash != "secret123"  # must be hashed

    def test_password_check(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="bob", role=admin_role)
        user.set_password("mypassword")
        session.add(user)
        session.commit()

        assert user.check_password("mypassword") is True
        assert user.check_password("wrongpassword") is False

    def test_password_set_twice_replaces_hash(self, session):
        """Setting a password twice should replace the old hash"""
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="doublepass", role=admin_role)
        session.add(user)
        session.commit()

        user.set_password("firstpass")
        hash1 = user.password_hash
        user.set_password("secondpass")

        assert user.password_hash != hash1
        assert user.check_password("firstpass") is False
        assert user.check_password("secondpass") is True

    def test_user_to_dict_excludes_password(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="carol", role=admin_role)
        user.set_password("secret")
        session.add(user)
        session.commit()

        d = user.to_dict()
        assert "password" not in d
        assert "password_hash" not in d
        assert d["username"] == "carol"

    def test_user_to_dict_with_sensitive(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="dave", role=admin_role)
        user.set_password("secret")
        session.add(user)
        session.commit()

        d = user.to_dict(include_sensitive=True)
        assert "_warning" in d

    def test_unique_username(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user1 = User(username="unique_user", role=admin_role)
        session.add(user1)
        session.commit()

        user2 = User(username="unique_user", role=admin_role)
        session.add(user2)
        with pytest.raises(Exception):  # UNIQUE constraint failure
            session.commit()
        session.rollback()


# =============================================================================
# PermissionRule Model
# =============================================================================

class TestPermissionRule:
    def test_rule_creation(self, session):
        viewer_role = session.query(Role).filter(Role.name == "viewer").first()
        rule = PermissionRule(
            role_id=viewer_role.id,
            path_pattern="/public/**",
            permissions="read,list",
            priority=0,
        )
        session.add(rule)
        session.commit()

        assert rule.id is not None
        assert rule.role_id == viewer_role.id

    def test_get_permissions_parses_string(self, session):
        rule = PermissionRule(
            role_id="some-role",
            path_pattern="/*.txt",
            permissions="read,  write ,delete",
            priority=0,
        )
        perms = rule.get_permissions()
        assert "read" in perms
        assert "write" in perms
        assert "delete" in perms

    def test_has_permission(self, session):
        rule = PermissionRule(
            role_id="some-role",
            path_pattern="/docs/**",
            permissions="read,write",
            priority=0,
        )
        assert rule.has_permission("read") is True
        assert rule.has_permission("write") is True
        assert rule.has_permission("delete") is False

    def test_to_dict(self, session):
        viewer_role = session.query(Role).filter(Role.name == "viewer").first()
        rule = PermissionRule(
            role_id=viewer_role.id,
            path_pattern="/public/**",
            permissions="read,list",
            priority=5,
        )
        session.add(rule)
        session.commit()

        d = rule.to_dict()
        assert d["path_pattern"] == "/public/**"
        assert "read" in d["permissions"]
        assert d["priority"] == 5


# =============================================================================
# AuditLog Model
# =============================================================================

class TestAuditLog:
    def test_audit_log_creation(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="auditor_test", role=admin_role)
        user.set_password("pass")
        session.add(user)
        session.commit()

        log = AuditLog(
            user_id=user.id,
            action=AuditAction.LOGIN.value,
            path="/",
            result="success",
            ip_address="192.168.1.1",
        )
        session.add(log)
        session.commit()

        assert log.id is not None
        assert log.user_id == user.id
        assert log.result == "success"

    def test_audit_log_to_dict(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="log_dict_user", role=admin_role)
        session.add(user)
        session.commit()

        log = AuditLog(
            user_id=user.id,
            action=AuditAction.FILE_READ.value,
            path="/docs/readme.txt",
            result="success",
        )
        session.add(log)
        session.commit()

        d = log.to_dict()
        assert d["username"] == "log_dict_user"
        assert d["path"] == "/docs/readme.txt"
        assert d["action"] == "file_read"


# =============================================================================
# SharedLink Model
# =============================================================================

class TestSharedLink:
    def test_shared_link_no_password(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="sharer", role=admin_role)
        session.add(user)
        session.commit()

        link = SharedLink(
            path="/public/file.txt",
            token="abc123token",
            permissions="read",
            created_by=user.id,
        )
        session.add(link)
        session.commit()

        assert link.check_password("") is True
        assert link.is_valid() is True
        assert link.is_expired() is False

    def test_shared_link_with_password(self, session):
        link = SharedLink(
            path="/secret/file.txt",
            token="secrettoken",
            permissions="read",
        )
        link.set_password("linkpass")
        session.add(link)
        session.commit()

        assert link.check_password("linkpass") is True
        assert link.check_password("wrongpass") is False

    def test_shared_link_expiry(self, session):
        from datetime import datetime, timedelta
        link = SharedLink(
            path="/temp/file.txt",
            token="expiry_token",
            permissions="read",
        )
        # Set expired time (in the past)
        link.expires_at = datetime.utcnow() - timedelta(hours=1)
        session.add(link)
        session.commit()

        assert link.is_expired() is True
        assert link.is_valid() is False

    def test_shared_link_max_access(self, session):
        link = SharedLink(
            path="/limited/file.txt",
            token="limit_token",
            permissions="read",
            max_access_count=2,
            access_count=2,
        )
        session.add(link)
        session.commit()

        assert link.is_valid() is False

    def test_shared_link_to_dict(self, session):
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="share_dict_user", role=admin_role)
        session.add(user)
        session.commit()

        link = SharedLink(
            path="/share/path",
            token="dict_token",
            permissions="read_write",
            created_by=user.id,
        )
        session.add(link)
        session.commit()

        d = link.to_dict()
        assert "token" not in d  # token hidden by default
        assert d["path"] == "/share/path"
        assert d["permissions"] == "read_write"

        d_with_token = link.to_dict(include_token=True)
        assert "token" in d_with_token


# =============================================================================
# Database Initialization
# =============================================================================

class TestDBInit:
    def test_init_db_returns_sessionmaker(self):
        eng = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        sm = init_db("sqlite:///:memory:")
        assert sm is not None
        sess = sm()
        assert sess is not None
        sess.close()

    def test_get_default_storage_path(self):
        from tools.file_manager.engine.models import get_default_storage_path
        path = get_default_storage_path()
        assert isinstance(path, str)
        assert len(path) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
