"""
Tests for Hermes File Manager Permission Engine
"""

import pytest
from pathlib import Path
import tempfile
import shutil

import sys
_tools_dir = Path(__file__).parent.parent.parent.parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from tools.file_manager.engine.permission import (
    PermissionEngine, PermissionDecision, Operation, RoleHierarchy
)
from tools.file_manager.engine.models import User, Role, PermissionRule


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory"""
    temp_dir = tempfile.mkdtemp()
    storage_root = Path(temp_dir) / "storage"
    storage_root.mkdir()
    
    # Create some test files
    (storage_root / "public").mkdir()
    (storage_root / "public" / "readme.txt").write_text("public file")
    
    (storage_root / "shared").mkdir()
    (storage_root / "shared" / "docs").mkdir()
    (storage_root / "shared" / "docs" / "guide.txt").write_text("guide")
    
    (storage_root / "private").mkdir()
    (storage_root / "private" / "secret.txt").write_text("secret")
    
    yield str(storage_root)
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def permission_engine(temp_storage):
    """Create a permission engine"""
    return PermissionEngine(temp_storage)


@pytest.fixture
def viewer_role():
    """Create a viewer role"""
    role = Role(id="role-viewer", name="viewer", description="Read-only access")
    return role


@pytest.fixture
def editor_role():
    """Create an editor role"""
    role = Role(id="role-editor", name="editor", description="Read/write access")
    return role


@pytest.fixture
def admin_role():
    """Create an admin role"""
    role = Role(id="role-admin", name="admin", description="Full access")
    return role


def test_path_normalization(permission_engine):
    """Test path normalization prevents traversal"""
    engine = permission_engine
    
    # Normal paths
    assert engine._normalize_path("/shared/docs") == "shared/docs"
    assert engine._normalize_path("shared/docs") == "shared/docs"
    assert engine._normalize_path("/shared//docs/") == "shared/docs"
    
    # Path traversal blocked — ".." raises PermissionError
    import pytest
    with pytest.raises(PermissionError):
        engine._normalize_path("../../../etc/passwd")
    with pytest.raises(PermissionError):
        engine._normalize_path("/shared/../../../etc")
    with pytest.raises(PermissionError):
        engine._normalize_path("shared/./../etc")
    
    # Normal . segments are filtered
    assert engine._normalize_path("shared/./docs") == "shared/docs"
    assert engine._normalize_path("./shared/docs/") == "shared/docs"


def test_glob_pattern_matching(permission_engine):
    """Test glob pattern to regex conversion"""
    engine = permission_engine
    
    # Simple patterns
    assert engine._path_matches_pattern("readme.txt", "*.txt")
    assert not engine._path_matches_pattern("readme.md", "*.txt")
    
    # Directory patterns: * matches anything including / in fnmatch
    # Use shared/docs/** for recursive behavior, shared/docs/* for one level only
    assert engine._path_matches_pattern("shared/docs/guide.txt", "shared/docs/*")
    assert engine._path_matches_pattern("shared/docs/sub/guide.txt", "shared/docs/*")  # * matches /sub/
    
    # Recursive patterns (fnmatch ** matches paths with at least one dir separator)
    assert engine._path_matches_pattern("shared/docs/guide.txt", "shared/**")
    assert engine._path_matches_pattern("shared/docs/sub/guide.txt", "shared/**")
    assert engine._path_matches_pattern("shared/guide.txt", "shared/**")
    # In fnmatch, * matches anything including / (like shell glob)
    assert engine._path_matches_pattern("shared/docs/sub/guide.txt", "shared/docs/*")


def test_admin_bypass(permission_engine, admin_role, temp_storage):
    """Test admin users bypass permission checks"""
    engine = permission_engine
    
    # Create admin user without rules
    user = User(id="admin-1", username="admin", role=admin_role)
    
    # Should allow any operation
    decision = engine.check_permission(user, Operation.READ, "any/path")
    assert decision.allowed
    assert "Admin" in decision.reason


def test_viewer_read_permission(permission_engine, viewer_role):
    """Test viewer role has read permission via rule"""
    engine = permission_engine
    
    # Create viewer rule for public directory
    rule = PermissionRule(
        id="rule-1",
        role_id=viewer_role.id,
        path_pattern="/public/**",
        permissions="read,list",
        priority=0
    )
    
    user = User(id="user-1", username="viewer1", role=viewer_role)
    
    # Read should be allowed
    decision = engine.check_permission(user, Operation.READ, "public/readme.txt", [rule])
    assert decision.allowed
    
    # Write should be denied
    decision = engine.check_permission(user, Operation.WRITE, "public/readme.txt", [rule])
    assert not decision.allowed


def test_editor_write_permission(permission_engine, editor_role):
    """Test editor role can write in allowed paths"""
    engine = permission_engine
    
    rule = PermissionRule(
        id="rule-2",
        role_id=editor_role.id,
        path_pattern="/shared/**",
        permissions="read,write,list",
        priority=0
    )
    
    user = User(id="user-2", username="editor1", role=editor_role)
    
    # Read allowed
    decision = engine.check_permission(user, Operation.READ, "shared/docs/guide.txt", [rule])
    assert decision.allowed
    
    # Write allowed
    decision = engine.check_permission(user, Operation.WRITE, "shared/docs/guide.txt", [rule])
    assert decision.allowed
    
    # Delete should be denied (not in permissions)
    decision = engine.check_permission(user, Operation.DELETE, "shared/docs/guide.txt", [rule])
    assert not decision.allowed


def test_no_matching_rule_denies(permission_engine, viewer_role):
    """Test that no matching rule results in denial"""
    engine = permission_engine
    
    rule = PermissionRule(
        id="rule-3",
        role_id=viewer_role.id,
        path_pattern="/public/**",
        permissions="read,list",
        priority=0
    )
    
    user = User(id="user-3", username="viewer2", role=viewer_role)
    
    # Access outside allowed path should be denied
    decision = engine.check_permission(user, Operation.READ, "private/secret.txt", [rule])
    assert not decision.allowed
    assert "No rule matches" in decision.reason


def test_priority_wins(permission_engine, editor_role):
    """Test higher priority rules override lower"""
    engine = permission_engine
    
    # Low priority rule allows read only
    low_rule = PermissionRule(
        id="rule-low",
        role_id=editor_role.id,
        path_pattern="/shared/docs/**",
        permissions="read",
        priority=0
    )
    
    # High priority rule allows write
    high_rule = PermissionRule(
        id="rule-high",
        role_id=editor_role.id,
        path_pattern="/shared/docs/**",
        permissions="read,write",
        priority=10
    )
    
    user = User(id="user-4", username="editor2", role=editor_role)
    
    decision = engine.check_permission(
        user, Operation.WRITE, "shared/docs/guide.txt", [low_rule, high_rule]
    )
    assert decision.allowed
    assert decision.matched_rule.id == "rule-high"


def test_manage_implies_all(permission_engine, admin_role):
    """Test that 'manage' permission implies all operations"""
    engine = permission_engine
    
    rule = PermissionRule(
        id="rule-manage",
        role_id=admin_role.id,
        path_pattern="/shared/**",
        permissions="manage",
        priority=0
    )
    
    user = User(id="user-5", username="manager1", role=admin_role)
    
    # All operations should be allowed via manage
    for op in [Operation.READ, Operation.WRITE, Operation.DELETE, Operation.MANAGE]:
        decision = engine.check_permission(user, op, "shared/anything", [rule])
        assert decision.allowed


def test_role_hierarchy_permissions():
    """Test RoleHierarchy.get_all_permissions"""
    from tools.file_manager.engine.permission import RoleHierarchy
    
    assert RoleHierarchy.get_all_permissions("admin") == {"read", "write", "delete", "manage", "list"}
    assert RoleHierarchy.get_all_permissions("editor") == {"read", "write", "list"}
    assert RoleHierarchy.get_all_permissions("viewer") == {"read", "list"}
    assert RoleHierarchy.get_all_permissions("guest") == {"read"}


def test_can_manage_role():
    """Test role management permissions"""
    from tools.file_manager.engine.permission import RoleHierarchy
    
    # Admin can manage anyone
    assert RoleHierarchy.can_manage_role("admin", "viewer")
    assert RoleHierarchy.can_manage_role("admin", "admin")
    assert RoleHierarchy.can_manage_role("admin", "editor")
    
    # Editor can manage viewer/guest but not admin or other editors
    assert RoleHierarchy.can_manage_role("editor", "viewer")
    assert RoleHierarchy.can_manage_role("editor", "guest")
    assert not RoleHierarchy.can_manage_role("editor", "admin")
    assert not RoleHierarchy.can_manage_role("editor", "editor")
    
    # Viewer can't manage anyone
    assert not RoleHierarchy.can_manage_role("viewer", "guest")
    assert not RoleHierarchy.can_manage_role("viewer", "admin")


def test_resolve_path_security(permission_engine):
    """Test safe path resolution prevents escape"""
    engine = permission_engine
    
    # Normal path should resolve
    result = engine.resolve_path("public/readme.txt")
    assert "public/readme.txt" in str(result)
    
    # Path with .. now raises PermissionError in normalize_path
    import pytest as pt
    with pt.raises(PermissionError):
        engine.resolve_path("../../../etc/passwd")
    
    with pt.raises(PermissionError):
        engine.resolve_path("public/../../../etc/passwd")


def test_list_accessible_paths(permission_engine, editor_role):
    """Test listing accessible paths for a user"""
    engine = permission_engine
    
    rules = [
        PermissionRule(id="r1", role_id=editor_role.id, path_pattern="/shared/**", permissions="read,write", priority=0),
        PermissionRule(id="r2", role_id=editor_role.id, path_pattern="/public/**", permissions="read", priority=0),
    ]
    
    user = User(id="user-6", username="editor3", role=editor_role)
    
    paths = engine.list_accessible_paths(user, rules)
    
    assert "shared" in paths
    assert "public" in paths


# =============================================================================
# RED Phase: New tests that define expected behavior
# These tests describe WHAT should work — some may fail until implementation is complete
# =============================================================================

def test_check_path_access_read(permission_engine, viewer_role):
    """check_path_access with require_write=False should use READ operation"""
    engine = permission_engine
    rule = PermissionRule(
        id="r1", role_id=viewer_role.id,
        path_pattern="shared/docs/*", permissions="read", priority=10
    )
    user = User(id="u1", username="reader", role=viewer_role)

    decision = engine.check_path_access(user, "shared/docs/file.txt", [rule])
    assert decision.allowed is True
    assert decision.matched_rule == rule


def test_check_path_access_write_enforcement(permission_engine, viewer_role):
    """check_path_access with require_write=True should deny read-only permission"""
    engine = permission_engine
    rule = PermissionRule(
        id="r1", role_id=viewer_role.id,
        path_pattern="shared/docs/*", permissions="read", priority=10
    )
    user = User(id="u1", username="reader", role=viewer_role)

    # Viewer has read-only, not write
    decision = engine.check_path_access(user, "shared/docs/file.txt", [rule], require_write=True)
    assert decision.allowed is False
    assert decision.reason  # reason should explain WHY it was denied


def test_permission_decision_includes_all_fields(permission_engine, editor_role):
    """PermissionDecision should include required_permissions and granted_permissions"""
    engine = permission_engine
    rule = PermissionRule(
        id="r1", role_id=editor_role.id,
        path_pattern="shared/**", permissions="read,write", priority=10
    )
    user = User(id="u1", username="editor1", role=editor_role)

    decision = engine.check_permission(user, Operation.READ, "shared/docs/file.txt", [rule])
    assert decision.allowed is True
    assert "read" in decision.required_permissions
    assert decision.granted_permissions  # should have the permissions from the matched rule


def test_highest_priority_rule_wins(permission_engine, editor_role):
    """When multiple rules match, highest priority should win"""
    engine = permission_engine
    low_priority = PermissionRule(
        id="r1", role_id=editor_role.id,
        path_pattern="shared/**", permissions="read", priority=1
    )
    high_priority = PermissionRule(
        id="r2", role_id=editor_role.id,
        path_pattern="shared/docs/**", permissions="write", priority=100
    )
    user = User(id="u1", username="editor1", role=editor_role)

    decision = engine.check_permission(user, Operation.WRITE, "shared/docs/file.txt", [low_priority, high_priority])
    assert decision.allowed is True
    assert decision.matched_rule == high_priority


def test_role_hierarchy_get_all_permissions(permission_engine):
    """RoleHierarchy.get_all_permissions returns correct permissions per role"""
    perms = RoleHierarchy.get_all_permissions("admin")
    assert "manage" in perms
    assert perms == {"read", "write", "delete", "manage", "list"}

    viewer_perms = RoleHierarchy.get_all_permissions("viewer")
    assert "write" not in viewer_perms
    assert "read" in viewer_perms


def test_can_manage_admin_cannot_be_managed_by_viewer(permission_engine):
    """Non-admin roles cannot manage admin role"""
    assert RoleHierarchy.can_manage_role("viewer", "admin") is False
    assert RoleHierarchy.can_manage_role("editor", "admin") is False
    assert RoleHierarchy.can_manage_role("admin", "admin") is True


def test_pattern_cache_returns_same_result(permission_engine):
    """Pattern matching should be cached and return consistent results"""
    engine = permission_engine
    path = "shared/docs/file.txt"
    pattern = "shared/docs/*"

    result1 = engine._path_matches_pattern(path, pattern)
    result2 = engine._path_matches_pattern(path, pattern)
    result3 = engine._path_matches_pattern(path, pattern)

    assert result1 == result2 == result3
    # Cache should have this entry
    assert (pattern, path) in engine._pattern_cache


def test_normalize_path_blocks_absolute_paths(permission_engine):
    """Absolute paths starting with / should be normalized (leading slash stripped)"""
    engine = permission_engine
    assert engine._normalize_path("/etc/passwd") == "etc/passwd"
    assert engine._normalize_path("//etc//passwd") == "etc/passwd"


def test_normalize_path_allows_deep_nesting(permission_engine):
    """Normalize should handle deeply nested paths"""
    engine = permission_engine
    result = engine._normalize_path("a/b/c/d/e/f/g.txt")
    assert result == "a/b/c/d/e/f/g.txt"


def test_user_without_role_handled_gracefully(permission_engine):
    """User with no role should be handled without crashing"""
    engine = permission_engine
    user_no_role = User(id="u1", username="norole", role=None)
    decision = engine.check_permission(user_no_role, Operation.READ, "public/readme.txt", [])
    assert decision.allowed is False
    assert decision.reason  # should have a reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
