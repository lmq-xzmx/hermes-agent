"""
Tests for RBAC Permission Checker (T2)
TDD Phase: RED (write tests first)
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.services.rbac_checker import RBACChecker, RBACDecision
from tools.file_manager.services.permission_context import PermissionContext


class TestRBACDecision:
    """Tests for RBACDecision dataclass."""

    def test_decision_allowed(self):
        decision = RBACDecision(
            allowed=True,
            reason="Admin bypass",
            matched_permission="admin:bypass",
        )
        assert decision.allowed is True
        assert decision.reason == "Admin bypass"
        assert decision.matched_permission == "admin:bypass"

    def test_decision_denied(self):
        decision = RBACDecision(
            allowed=False,
            reason="No permission",
        )
        assert decision.allowed is False
        assert decision.reason == "No permission"
        assert decision.matched_permission is None


class TestRBACCheckerWithContext:
    """Tests for RBACChecker using PermissionContext (no DB)."""

    @pytest.fixture
    def checker(self):
        return RBACChecker(db_factory=None)

    @pytest.fixture
    def admin_ctx(self):
        """Admin context with all permissions."""
        return PermissionContext(
            user_id="user-admin",
            username="admin",
            role_name="admin",
            rbac_permissions=["*:*"],  # Wildcard admin
        )

    @pytest.fixture
    def editor_ctx(self):
        """Editor context with file and space permissions."""
        return PermissionContext(
            user_id="user-editor",
            username="editor",
            role_name="editor",
            rbac_permissions=[
                "file:create",
                "file:read",
                "file:update",
                "file:delete",
                "space:read",
                "space:update",
            ],
        )

    @pytest.fixture
    def viewer_ctx(self):
        """Viewer context with read-only permissions."""
        return PermissionContext(
            user_id="user-viewer",
            username="viewer",
            role_name="viewer",
            rbac_permissions=[
                "file:read",
                "space:read",
            ],
        )

    def test_admin_bypass(self, checker, admin_ctx):
        """Admin should have bypass for any action."""
        # File operations
        result = checker.check_permission(
            user_id="user-admin",
            resource="file",
            action="delete",
            ctx=admin_ctx,
        )
        assert result.allowed is True
        assert "bypass" in result.reason.lower()

        # User management
        result = checker.check_permission(
            user_id="user-admin",
            resource="user",
            action="delete",
            ctx=admin_ctx,
        )
        assert result.allowed is True

    def test_editor_can_manage_files(self, checker, editor_ctx):
        """Editor should be able to create/read/update/delete files."""
        assert checker.check_permission("user-editor", "file", "create", ctx=editor_ctx).allowed
        assert checker.check_permission("user-editor", "file", "read", ctx=editor_ctx).allowed
        assert checker.check_permission("user-editor", "file", "update", ctx=editor_ctx).allowed
        assert checker.check_permission("user-editor", "file", "delete", ctx=editor_ctx).allowed

    def test_editor_cannot_manage_users(self, checker, editor_ctx):
        """Editor should not be able to manage users."""
        result = checker.check_permission(
            user_id="user-editor",
            resource="user",
            action="delete",
            ctx=editor_ctx,
        )
        assert result.allowed is False
        assert "user" in result.reason.lower()

    def test_editor_cannot_create_spaces(self, checker, editor_ctx):
        """Editor should not be able to create spaces."""
        result = checker.check_permission(
            user_id="user-editor",
            resource="space",
            action="create",
            ctx=editor_ctx,
        )
        assert result.allowed is False

    def test_viewer_can_read_files(self, checker, viewer_ctx):
        """Viewer should be able to read files and spaces."""
        assert checker.check_permission(
            user_id="user-viewer",
            resource="file",
            action="read",
            ctx=viewer_ctx,
        ).allowed
        assert checker.check_permission(
            user_id="user-viewer",
            resource="space",
            action="read",
            ctx=viewer_ctx,
        ).allowed

    def test_viewer_cannot_write(self, checker, viewer_ctx):
        """Viewer should not be able to write."""
        assert not checker.check_permission(
            user_id="user-viewer",
            resource="file",
            action="create",
            ctx=viewer_ctx,
        ).allowed
        assert not checker.check_permission(
            user_id="user-viewer",
            resource="file",
            action="update",
            ctx=viewer_ctx,
        ).allowed
        assert not checker.check_permission(
            user_id="user-viewer",
            resource="file",
            action="delete",
            ctx=viewer_ctx,
        ).allowed

    def test_get_user_permissions_from_context(self, checker, editor_ctx):
        """get_user_permissions should return permissions from context."""
        perms = checker.get_user_permissions("user-editor", editor_ctx)
        assert "file:create" in perms
        assert "file:read" in perms
        assert "file:delete" in perms
        assert "space:create" not in perms

    def test_has_role_admin(self, checker, admin_ctx):
        """has_role should correctly identify admin."""
        assert RBACChecker.has_role("user-admin", "admin", admin_ctx) is True
        assert RBACChecker.has_role("user-admin", "editor", admin_ctx) is False

    def test_has_role_editor(self, checker, editor_ctx):
        """has_role should correctly identify editor."""
        assert RBACChecker.has_role("user-editor", "editor", editor_ctx) is True
        assert RBACChecker.has_role("user-editor", "admin", editor_ctx) is False

    def test_no_context_returns_empty_permissions(self, checker):
        """Without context or DB, should return empty set."""
        perms = checker.get_user_permissions("unknown-user", None)
        assert len(perms) == 0

    def test_check_without_context(self, checker):
        """Without context, permission should be denied."""
        result = checker.check_permission(
            user_id="unknown",
            resource="file",
            action="read",
            ctx=None,
        )
        assert result.allowed is False

    def test_wildcard_permission(self):
        """Wildcard resource:* should allow any action on resource."""
        ctx = PermissionContext(
            user_id="user-wildcard",
            username="wildcard_user",
            role_name="custom",
            rbac_permissions=["file:*", "space:read"],
        )
        checker = RBACChecker(db_factory=None)

        assert checker.check_permission("user-wildcard", "file", "create", ctx=ctx).allowed
        assert checker.check_permission("user-wildcard", "file", "delete", ctx=ctx).allowed
        assert checker.check_permission("user-wildcard", "file", "manage", ctx=ctx).allowed
        # But not for space
        assert not checker.check_permission("user-wildcard", "space", "create", ctx=ctx).allowed


class TestPermissionContextRBAC:
    """Tests for PermissionContext RBAC functionality."""

    def test_default_empty_permissions(self):
        """Default context should have empty permission lists."""
        ctx = PermissionContext(
            user_id="test",
            username="testuser",
            role_name="viewer",
        )
        assert ctx.rbac_permissions == []
        assert ctx.permission_rules == []

    def test_get_rbac_permission_set(self):
        """get_rbac_permission_set should return a set."""
        ctx = PermissionContext(
            user_id="test",
            username="testuser",
            role_name="editor",
            rbac_permissions=["file:read", "file:write"],
        )
        perm_set = ctx.get_rbac_permission_set()
        assert isinstance(perm_set, set)
        assert "file:read" in perm_set
        assert "file:write" in perm_set

    def test_empty_context_fields(self):
        """Empty context should have None for optional fields."""
        ctx = PermissionContext(
            user_id="test",
            username="testuser",
            role_name=None,
        )
        assert ctx.role_name is None
        assert ctx.active_space_id is None
        assert ctx.active_team_id is None


class TestRBACLifecycleIntegration:
    """Tests for RBAC integration with lifecycle_engine."""

    def test_check_rbac_permission_allows_admin(self):
        """Admin should pass any RBAC permission check."""
        from tools.file_manager.services.lifecycle_engine import check_rbac_permission, ConstraintContext

        rule = check_rbac_permission("user", "delete")
        ctx = ConstraintContext(
            user_id="admin-user",
            username="admin",
            role_name="admin",
        )
        ctx.extra["rbac_permissions"] = ["*:*"]

        result = rule.check_fn(ctx)
        assert result.passed is True

    def test_check_rbac_permission_denies_without_perm(self):
        """Should deny when user lacks required permission."""
        from tools.file_manager.services.lifecycle_engine import check_rbac_permission, ConstraintContext

        rule = check_rbac_permission("user", "delete")
        ctx = ConstraintContext(
            user_id="viewer-user",
            username="viewer",
            role_name="viewer",
        )
        ctx.extra["rbac_permissions"] = ["file:read", "space:read"]

        result = rule.check_fn(ctx)
        assert result.passed is False
        assert "PERMISSION_DENIED" in str(result.details.get("error_code", ""))

    def test_check_rbac_permission_allows_with_perm(self):
        """Should allow when user has required permission."""
        from tools.file_manager.services.lifecycle_engine import check_rbac_permission, ConstraintContext

        rule = check_rbac_permission("space", "create")
        ctx = ConstraintContext(
            user_id="editor-user",
            username="editor",
            role_name="editor",
        )
        ctx.extra["rbac_permissions"] = ["space:create", "file:read"]

        result = rule.check_fn(ctx)
        assert result.passed is True

    def test_check_rbac_permission_wildcard(self):
        """Wildcard permission should satisfy any action on same resource."""
        from tools.file_manager.services.lifecycle_engine import check_rbac_permission, ConstraintContext

        rule = check_rbac_permission("file", "delete")
        ctx = ConstraintContext(
            user_id="editor-user",
            username="editor",
            role_name="editor",
        )
        ctx.extra["rbac_permissions"] = ["file:*"]

        result = rule.check_fn(ctx)
        assert result.passed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
