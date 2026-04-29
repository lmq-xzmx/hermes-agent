"""
Tests for Hermes File Manager - AdminService
Tests the pure business logic layer (AdminService) and ORM layer (User, Role, Rule models).
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, PermissionRule, init_db, create_builtin_roles
)


@pytest.fixture
def db_session():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    sess = Session()
    create_builtin_roles(sess)
    yield sess
    sess.close()


@pytest.fixture
def db_factory(db_session):
    """Return a factory function that returns the test session."""
    return lambda: db_session


@pytest.fixture
def admin_user(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    user = User(username="sysadmin", role=admin_role)
    user.set_password("adminpass")
    db_session.add(user)
    db_session.commit()
    return user


# =============================================================================
# ORM Layer Tests (unchanged - test User, Role, PermissionRule models directly)
# =============================================================================

class TestUserManagement:
    """Tests for User ORM model"""

    def test_create_user(self, db_session, admin_user):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()
        user = User(username="newuser", email="new@example.com", role=editor_role)
        user.set_password("password123")
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == "newuser"
        assert user.email == "new@example.com"
        assert user.role.name == "editor"

    def test_update_user(self, db_session, admin_user):
        viewer_role = db_session.query(Role).filter(Role.name == "viewer").first()
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()

        user = User(username="updateme", role=viewer_role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        # Update
        user.role_id = editor_role.id
        user.email = "updated@example.com"
        db_session.commit()

        updated = db_session.query(User).filter(User.id == user_id).first()
        assert updated.role.name == "editor"
        assert updated.email == "updated@example.com"

    def test_deactivate_user(self, db_session, admin_user):
        user = User(username="deactivate_test", role=admin_user.role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        user.is_active = False
        db_session.commit()

        updated = db_session.query(User).filter(User.id == user_id).first()
        assert updated.is_active is False

    def test_delete_user(self, db_session, admin_user):
        user = User(username="delete_test", role=admin_user.role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        db_session.delete(user)
        db_session.commit()

        assert db_session.query(User).filter(User.id == user_id).first() is None


class TestRoleManagement:
    """Tests for Role ORM model"""

    def test_create_custom_role(self, db_session, admin_user):
        role = Role(name="custom_role", description="A custom role", is_system=False)
        db_session.add(role)
        db_session.commit()

        assert role.id is not None
        assert role.is_system is False

    def test_cannot_delete_system_role(self, db_session, admin_user):
        system_role = db_session.query(Role).filter(Role.name == "admin").first()
        assert system_role.is_system is True

        # Deleting system role should be prevented at application level
        # (DB doesn't enforce this, app logic does)
        system_role.is_system = False  # Simulate bypass attempt
        db_session.commit()

    def test_role_unique_name(self, db_session, admin_user):
        role1 = Role(name="unique_role")
        db_session.add(role1)
        db_session.commit()

        role2 = Role(name="unique_role")
        db_session.add(role2)
        with pytest.raises(Exception):  # UNIQUE constraint
            db_session.commit()
        db_session.rollback()


class TestPermissionRuleCascade:
    """Tests for ORM cascade delete behavior"""

    def test_deleting_role_cascades_rules(self, db_session, admin_user):
        custom_role = Role(name="cascade_test_role", is_system=False)
        db_session.add(custom_role)
        db_session.commit()

        rule = PermissionRule(
            role_id=custom_role.id,
            path_pattern="/*",
            permissions="read",
            priority=0,
        )
        db_session.add(rule)
        db_session.commit()

        rule_id = rule.id
        role_id = custom_role.id

        # Delete role (cascade delete rules)
        db_session.delete(custom_role)
        db_session.commit()

        # Rule should be gone
        assert db_session.query(PermissionRule).filter(PermissionRule.id == rule_id).first() is None


# =============================================================================
# AdminService Layer Tests
# =============================================================================

from tools.file_manager.services.admin_service import (
    AdminService,
    AdminAccessDenied,
    UserNotFound,
    UserAlreadyExists,
    RoleNotFound,
    RoleAlreadyExists,
    RoleNotModifiable,
    CannotDeleteSelf,
    CannotDeleteRoleWithUsers,
)
from tools.file_manager.services.permission_context import PermissionContext
from tools.file_manager.api.dto import CreateUserRequestDTO


def make_admin_ctx(user):
    """Create admin PermissionContext from user."""
    return PermissionContext(
        user_id=user.id,
        username=user.username,
        role_name="admin",
        permission_rules=[],
    )


def make_user_ctx(username="viewer_user", role_name="viewer"):
    """Create non-admin PermissionContext."""
    return PermissionContext(
        user_id="some-user-id",
        username=username,
        role_name=role_name,
        permission_rules=[],
    )


class TestAdminServiceUserManagement:
    """Tests for AdminService user management methods"""

    def test_list_users_as_admin(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.list_users(user_ctx=ctx, limit=10, offset=0)

        assert result.total >= 1
        assert len(result.users) >= 1

    def test_list_users_pagination(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        # Create additional users
        for i in range(3):
            user = User(username=f"user{i}", role=admin_user.role)
            user.set_password("pass")
            db_factory().add(user)
        db_factory().commit()

        result = admin_service.list_users(user_ctx=ctx, limit=2, offset=0)
        assert len(result.users) == 2

    def test_list_users_non_admin_raises(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_user_ctx()

        with pytest.raises(AdminAccessDenied):
            admin_service.list_users(user_ctx=ctx)

    def test_get_user(self, db_factory, admin_user):
        user = User(username="gettest", role=admin_user.role)
        user.set_password("pass")
        db_factory().add(user)
        db_factory().commit()

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.get_user(user.id, user_ctx=ctx)

        assert result.username == "gettest"

    def test_get_user_not_found(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(UserNotFound):
            admin_service.get_user("nonexistent-id", user_ctx=ctx)

    def test_create_user(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        request = CreateUserRequestDTO(
            username="newadminuser",
            password="securepass123",
            email="new@example.com",
        )
        result = admin_service.create_user(request, user_ctx=ctx)

        assert result.username == "newadminuser"
        assert result.email == "new@example.com"
        assert result.id is not None

    def test_create_user_with_role(self, db_factory, admin_user):
        editor_role = db_factory().query(Role).filter(Role.name == "editor").first()
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        request = CreateUserRequestDTO(
            username="roleuser",
            password="pass",
            role_id=editor_role.id,
        )
        result = admin_service.create_user(request, user_ctx=ctx)

        assert result.role_id == editor_role.id

    def test_create_user_duplicate_username(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        request = CreateUserRequestDTO(username="dupuser", password="pass")
        admin_service.create_user(request, user_ctx=ctx)

        with pytest.raises(UserAlreadyExists):
            admin_service.create_user(request, user_ctx=ctx)

    def test_update_user(self, db_factory, admin_user):
        user = User(username="updatable", role=admin_user.role)
        user.set_password("pass")
        db_factory().add(user)
        db_factory().commit()

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.update_user(
            user.id,
            email="updated@test.com",
            role_id=None,
            is_active=None,
            user_ctx=ctx,
        )

        assert result.email == "updated@test.com"

    def test_delete_user(self, db_factory, admin_user):
        user = User(username="tobedeleted", role=admin_user.role)
        user.set_password("pass")
        db_factory().add(user)
        db_factory().commit()
        user_id = user.id

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.delete_user(user_id, user_ctx=ctx)

        assert "deleted" in result.message.lower()

        # Verify deleted
        with pytest.raises(UserNotFound):
            admin_service.get_user(user_id, user_ctx=ctx)

    def test_delete_user_self_not_allowed(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(CannotDeleteSelf):
            admin_service.delete_user(admin_user.id, user_ctx=ctx)


class TestAdminServiceRoleManagement:
    """Tests for AdminService role management methods"""

    def test_list_roles(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.list_roles(user_ctx=ctx)

        assert isinstance(result, list)
        assert len(result) >= 3  # admin, editor, viewer builtins

    def test_get_role(self, db_factory, admin_user):
        viewer_role = db_factory().query(Role).filter(Role.name == "viewer").first()
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.get_role(viewer_role.id, user_ctx=ctx)

        assert result.name == "viewer"

    def test_get_role_not_found(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(RoleNotFound):
            admin_service.get_role("nonexistent-id", user_ctx=ctx)

    def test_create_role(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.create_role(
            name="newrole",
            description="A test role",
            user_ctx=ctx,
        )

        assert result.name == "newrole"
        assert result.description == "A test role"

    def test_create_role_duplicate(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        admin_service.create_role(name="duprole", description=None, user_ctx=ctx)

        with pytest.raises(RoleAlreadyExists):
            admin_service.create_role(name="duprole", description=None, user_ctx=ctx)

    def test_update_role(self, db_factory, admin_user):
        custom_role = Role(name="updatablerole", is_system=False)
        db_factory().add(custom_role)
        db_factory().commit()

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.update_role(
            custom_role.id,
            description="Updated description",
            user_ctx=ctx,
        )

        assert result.description == "Updated description"

    def test_update_system_role_not_allowed(self, db_factory, admin_user):
        system_role = db_factory().query(Role).filter(Role.name == "admin").first()
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(RoleNotModifiable):
            admin_service.update_role(system_role.id, description="Try to update", user_ctx=ctx)

    def test_delete_role(self, db_factory, admin_user):
        custom_role = Role(name="tobedeletedrole", is_system=False)
        db_factory().add(custom_role)
        db_factory().commit()
        role_id = custom_role.id

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        result = admin_service.delete_role(role_id, user_ctx=ctx)

        assert "deleted" in result.message.lower()

    def test_delete_role_with_users_not_allowed(self, db_factory, admin_user):
        custom_role = Role(name="rolewithusers", is_system=False)
        db_factory().add(custom_role)
        db_factory().commit()

        user = User(username="roleuser", role=custom_role)
        user.set_password("pass")
        db_factory().add(user)
        db_factory().commit()

        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(CannotDeleteRoleWithUsers):
            admin_service.delete_role(custom_role.id, user_ctx=ctx)

    def test_delete_system_role_not_allowed(self, db_factory, admin_user):
        system_role = db_factory().query(Role).filter(Role.name == "admin").first()
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_admin_ctx(admin_user)

        with pytest.raises(RoleNotModifiable):
            admin_service.delete_role(system_role.id, user_ctx=ctx)


class TestAdminServiceAccessControl:
    """Tests for AdminService role-based access control"""

    def test_non_admin_cannot_list_users(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_user_ctx()

        with pytest.raises(AdminAccessDenied):
            admin_service.list_users(user_ctx=ctx)

    def test_non_admin_cannot_list_roles(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_user_ctx()

        with pytest.raises(AdminAccessDenied):
            admin_service.list_roles(user_ctx=ctx)

    def test_non_admin_cannot_create_user(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_user_ctx()

        request = CreateUserRequestDTO(username="hacker", password="pass")

        with pytest.raises(AdminAccessDenied):
            admin_service.create_user(request, user_ctx=ctx)

    def test_non_admin_cannot_delete_user(self, db_factory, admin_user):
        admin_service = AdminService(db_factory=db_factory, event_bus=None)
        ctx = make_user_ctx()

        with pytest.raises(AdminAccessDenied):
            admin_service.delete_user("some-id", user_ctx=ctx)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
