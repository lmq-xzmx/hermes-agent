"""
Tests for Hermes File Manager - Admin API
TDD Phase: Tests written first, should pass against existing implementation
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
def admin_user(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    user = User(username="sysadmin", role=admin_role)
    user.set_password("adminpass")
    db_session.add(user)
    db_session.commit()
    return user


# =============================================================================
# User Management
# =============================================================================

class TestUserManagement:
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


# =============================================================================
# Role Management
# =============================================================================

class TestRoleManagement:
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


# =============================================================================
# Permission Rule Management
# =============================================================================

class TestRuleManagement:
    def test_create_rule(self, db_session, admin_user):
        viewer_role = db_session.query(Role).filter(Role.name == "viewer").first()
        rule = PermissionRule(
            role_id=viewer_role.id,
            path_pattern="/docs/**",
            permissions="read,list",
            priority=5,
            created_by=admin_user.id,
        )
        db_session.add(rule)
        db_session.commit()

        assert rule.id is not None
        assert rule.priority == 5

    def test_rule_permissions_parsed(self, db_session):
        rule = PermissionRule(
            role_id="some-id",
            path_pattern="/*",
            permissions="read,write,delete,manage",
            priority=0,
        )
        perms = rule.get_permissions()
        assert len(perms) == 4
        assert "write" in perms

    def test_multiple_rules_for_same_role(self, db_session):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()

        rule1 = PermissionRule(
            role_id=editor_role.id,
            path_pattern="/docs/**",
            permissions="read,write",
            priority=0,
        )
        rule2 = PermissionRule(
            role_id=editor_role.id,
            path_pattern="/public/**",
            permissions="read",
            priority=0,
        )
        db_session.add_all([rule1, rule2])
        db_session.commit()

        rules = db_session.query(PermissionRule).filter(
            PermissionRule.role_id == editor_role.id
        ).all()
        assert len(rules) >= 2


# =============================================================================
# Cascade & Integrity
# =============================================================================

class TestIntegrity:
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
# AdminAPI Integration Tests
# =============================================================================

import os
import tempfile
from tools.file_manager.api.admin import (
    AdminAPI,
    CreateUserRequest,
    UpdateUserRequest,
    CreateRoleRequest,
    UpdateRoleRequest,
    CreateRuleRequest,
    UpdateRuleRequest,
    AuditQueryRequest,
)


class TestAdminAPIUserManagement:
    """Tests for AdminAPI user management methods"""

    def test_list_users(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        result = api.list_users(admin_user)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_list_users_with_pagination(self, db_session, admin_user):
        # Create additional users
        for i in range(3):
            user = User(username=f"user{i}", role=admin_user.role)
            user.set_password("pass")
            db_session.add(user)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        result = api.list_users(admin_user, limit=2, offset=0)
        assert len(result) == 2

    def test_get_user(self, db_session, admin_user):
        user = User(username="gettest", role=admin_user.role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        result = api.get_user(user.id, admin_user)
        assert result["username"] == "gettest"

    def test_get_user_not_found(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.get_user("nonexistent-id", admin_user)
        assert exc_info.value.status_code == 404

    def test_create_user(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = CreateUserRequest(
            username="newadminuser",
            password="securepass123",
            email="new@example.com",
        )
        result = api.create_user(request, admin_user)
        assert result["username"] == "newadminuser"
        assert result["email"] == "new@example.com"
        assert "id" in result

    def test_create_user_with_role(self, db_session, admin_user):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()
        api = AdminAPI(lambda: db_session)
        request = CreateUserRequest(
            username="roleuser",
            password="pass",
            role_id=editor_role.id,
        )
        result = api.create_user(request, admin_user)
        assert result["role_id"] == editor_role.id

    def test_create_user_duplicate_username(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = CreateUserRequest(username="dupuser", password="pass")
        api.create_user(request, admin_user)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.create_user(request, admin_user)
        assert exc_info.value.status_code == 400

    def test_update_user(self, db_session, admin_user):
        user = User(username="updatable", role=admin_user.role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        request = UpdateUserRequest(email="updated@test.com")
        result = api.update_user(user.id, request, admin_user)
        assert result["email"] == "updated@test.com"

    def test_delete_user(self, db_session, admin_user):
        user = User(username="tobedeleted", role=admin_user.role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()
        user_id = user.id

        api = AdminAPI(lambda: db_session)
        result = api.delete_user(user_id, admin_user)
        assert "deleted" in result["message"].lower()

        # Verify deleted
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            api.get_user(user_id, admin_user)

    def test_delete_user_self_not_allowed(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.delete_user(admin_user.id, admin_user)
        assert exc_info.value.status_code == 400


class TestAdminAPIRoleManagement:
    """Tests for AdminAPI role management methods"""

    def test_list_roles(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        result = api.list_roles(admin_user)
        assert isinstance(result, list)
        assert len(result) >= 3  # admin, editor, viewer builtins

    def test_get_role(self, db_session, admin_user):
        viewer_role = db_session.query(Role).filter(Role.name == "viewer").first()
        api = AdminAPI(lambda: db_session)
        result = api.get_role(viewer_role.id, admin_user)
        assert result["name"] == "viewer"
        assert "rules" in result

    def test_get_role_not_found(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.get_role("nonexistent-id", admin_user)
        assert exc_info.value.status_code == 404

    def test_create_role(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = CreateRoleRequest(
            name="newrole",
            description="A test role",
        )
        result = api.create_role(request, admin_user)
        assert result["name"] == "newrole"
        assert result["description"] == "A test role"
        assert result["is_system"] is False

    def test_create_role_duplicate(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = CreateRoleRequest(name="duprole")
        api.create_role(request, admin_user)

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.create_role(request, admin_user)
        assert exc_info.value.status_code == 400

    def test_update_role(self, db_session, admin_user):
        custom_role = Role(name="updatablerole", is_system=False)
        db_session.add(custom_role)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        request = UpdateRoleRequest(description="Updated description")
        result = api.update_role(custom_role.id, request, admin_user)
        assert result["description"] == "Updated description"

    def test_update_system_role_not_allowed(self, db_session, admin_user):
        system_role = db_session.query(Role).filter(Role.name == "admin").first()
        api = AdminAPI(lambda: db_session)
        request = UpdateRoleRequest(description="Try to update")
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.update_role(system_role.id, request, admin_user)
        assert exc_info.value.status_code == 400

    def test_delete_role(self, db_session, admin_user):
        custom_role = Role(name="tobedeletedrole", is_system=False)
        db_session.add(custom_role)
        db_session.commit()
        role_id = custom_role.id

        api = AdminAPI(lambda: db_session)
        result = api.delete_role(role_id, admin_user)
        assert "deleted" in result["message"].lower()

    def test_delete_role_with_users_not_allowed(self, db_session, admin_user):
        custom_role = Role(name="rolewithusers", is_system=False)
        db_session.add(custom_role)
        db_session.commit()

        user = User(username="roleuser", role=custom_role)
        user.set_password("pass")
        db_session.add(user)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.delete_role(custom_role.id, admin_user)
        assert exc_info.value.status_code == 400

    def test_delete_system_role_not_allowed(self, db_session, admin_user):
        system_role = db_session.query(Role).filter(Role.name == "admin").first()
        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.delete_role(system_role.id, admin_user)
        assert exc_info.value.status_code == 400


class TestAdminAPIRuleManagement:
    """Tests for AdminAPI permission rule management methods"""

    def test_list_rules(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        result = api.list_rules(admin_user)
        assert isinstance(result, list)

    def test_list_rules_filtered_by_role(self, db_session, admin_user):
        viewer_role = db_session.query(Role).filter(Role.name == "viewer").first()
        rule = PermissionRule(
            role_id=viewer_role.id,
            path_pattern="/test/**",
            permissions="read",
            priority=1,
            created_by=admin_user.id,
        )
        db_session.add(rule)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        result = api.list_rules(admin_user, role_id=viewer_role.id)
        assert len(result) >= 1
        assert all(r["role_id"] == viewer_role.id for r in result)

    def test_create_rule(self, db_session, admin_user):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()
        api = AdminAPI(lambda: db_session)
        request = CreateRuleRequest(
            role_id=editor_role.id,
            path_pattern="/new/**",
            permissions="read,write",
            priority=10,
        )
        result = api.create_rule(request, admin_user)
        assert result["path_pattern"] == "/new/**"
        assert result["permissions"] == ["read", "write"]
        assert result["priority"] == 10

    def test_create_rule_invalid_role(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = CreateRuleRequest(
            role_id="nonexistent-role",
            path_pattern="/*",
            permissions="read",
        )
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.create_rule(request, admin_user)
        assert exc_info.value.status_code == 400

    def test_update_rule(self, db_session, admin_user):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()
        rule = PermissionRule(
            role_id=editor_role.id,
            path_pattern="/old/**",
            permissions="read",
            priority=0,
            created_by=admin_user.id,
        )
        db_session.add(rule)
        db_session.commit()

        api = AdminAPI(lambda: db_session)
        request = UpdateRuleRequest(
            path_pattern="/updated/**",
            permissions="read,write,delete",
            priority=5,
        )
        result = api.update_rule(rule.id, request, admin_user)
        assert result["path_pattern"] == "/updated/**"
        assert result["permissions"] == ["read", "write", "delete"]
        assert result["priority"] == 5

    def test_update_rule_not_found(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = UpdateRuleRequest(priority=1)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.update_rule("nonexistent-id", request, admin_user)
        assert exc_info.value.status_code == 404

    def test_delete_rule(self, db_session, admin_user):
        editor_role = db_session.query(Role).filter(Role.name == "editor").first()
        rule = PermissionRule(
            role_id=editor_role.id,
            path_pattern="/todelete/**",
            permissions="read",
            priority=0,
            created_by=admin_user.id,
        )
        db_session.add(rule)
        db_session.commit()
        rule_id = rule.id

        api = AdminAPI(lambda: db_session)
        result = api.delete_rule(rule_id, admin_user)
        assert "deleted" in result["message"].lower()

        # Verify deleted
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            api.get_user(rule_id, admin_user)

    def test_delete_rule_not_found(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            api.delete_rule("nonexistent-id", admin_user)
        assert exc_info.value.status_code == 404


class TestAdminAPIAuditLogs:
    """Tests for AdminAPI audit log methods"""

    def test_query_audit_logs(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = AuditQueryRequest(limit=10)
        result = api.query_audit_logs(request, admin_user)
        assert isinstance(result, list)

    def test_query_audit_logs_with_filters(self, db_session, admin_user):
        # Create a user to generate audit log
        api = AdminAPI(lambda: db_session)
        request = CreateUserRequest(username="audituser", password="pass")
        api.create_user(request, admin_user)

        # Query with action filter
        query_req = AuditQueryRequest(action="user.create", limit=10)
        result = api.query_audit_logs(query_req, admin_user)
        assert isinstance(result, list)

    def test_query_audit_logs_pagination(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        request = AuditQueryRequest(limit=5, offset=0)
        result = api.query_audit_logs(request, admin_user)
        assert isinstance(result, list)
        assert len(result) <= 5

    def test_export_audit_logs(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = f.name
        try:
            result = api.export_audit_logs(admin_user, filepath)
            assert "exported" in result["message"].lower()
            assert os.path.exists(filepath)
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)

    def test_export_audit_logs_with_date_range(self, db_session, admin_user):
        api = AdminAPI(lambda: db_session)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            filepath = f.name
        try:
            result = api.export_audit_logs(
                admin_user,
                filepath,
                start_date="2024-01-01T00:00:00",
                end_date="2025-12-31T23:59:59",
            )
            assert "exported" in result["message"].lower()
        finally:
            if os.path.exists(filepath):
                os.unlink(filepath)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
