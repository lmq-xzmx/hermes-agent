"""
Tests for Role Change Lifecycle Management (Identity Lifecycle Management)
TDD Phase: RED
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import (
    Base, User, Role, RoleChangeRecord, Space,
    init_db, create_builtin_roles,
)


@pytest.fixture
def session():
    """Create an in-memory SQLite DB with all tables."""
    factory = init_db("sqlite:///:memory:")
    sess = factory()
    create_builtin_roles(sess)
    sess.commit()
    yield sess
    sess.close()


@pytest.fixture
def db_factory(session):
    class Factory:
        def __call__(self):
            return session
    return Factory()


class TestRoleChangeRecord:
    """Tests for RoleChangeRecord model."""

    def test_create_role_change_record(self, session):
        """Test creating a role change record."""
        # Create a user
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        viewer_role = session.query(Role).filter(Role.name == "viewer").first()

        user = User(username="test_user", role_id=admin_role.id)
        session.add(user)
        session.commit()

        # Create role change record
        record = RoleChangeRecord(
            user_id=user.id,
            changed_by=user.id,
            old_role_id=admin_role.id,
            new_role_id=viewer_role.id,
            asset_snapshot={"owned_spaces": [], "member_spaces": []},
            reason="Testing demotion",
            change_type="demotion",
        )
        session.add(record)
        session.commit()

        assert record.id is not None
        assert record.user_id == user.id
        assert record.change_type == "demotion"
        assert record.rollback_available is True
        assert record.rolled_back is False

    def test_role_change_record_to_dict(self, session):
        """Test RoleChangeRecord.to_dict()"""
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        viewer_role = session.query(Role).filter(Role.name == "viewer").first()

        user = User(username="test_user2", role_id=admin_role.id)
        session.add(user)
        session.commit()

        record = RoleChangeRecord(
            user_id=user.id,
            old_role_id=admin_role.id,
            new_role_id=viewer_role.id,
            change_type="demotion",
            reason="Test",
        )
        session.add(record)
        session.commit()

        d = record.to_dict()
        assert d["user_id"] == user.id
        assert d["change_type"] == "demotion"
        assert d["rollback_available"] is True
        assert d["rolled_back"] is False
        assert "old_role_name" in d
        assert "new_role_name" in d

    def test_capture_asset_snapshot(self, session):
        """Test that asset snapshot captures owned and member spaces."""
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        viewer_role = session.query(Role).filter(Role.name == "viewer").first()

        # Create user and space
        user = User(username="asset_test_user", role_id=admin_role.id)
        session.add(user)
        session.flush()

        space = Space(
            name="Test Space",
            storage_pool_id="dummy-pool-id",
            owner_id=user.id,
            max_bytes=1024,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        session.add(space)
        session.commit()

        # Verify snapshot captures the space
        snapshot = {
            "owned_spaces": [{"id": space.id, "name": space.name}],
            "member_spaces": [],
        }

        record = RoleChangeRecord(
            user_id=user.id,
            old_role_id=admin_role.id,
            new_role_id=viewer_role.id,
            asset_snapshot=snapshot,
            change_type="demotion",
        )
        session.add(record)
        session.commit()

        d = record.to_dict()
        assert len(d["asset_snapshot"]["owned_spaces"]) == 1
        assert d["asset_snapshot"]["owned_spaces"][0]["name"] == "Test Space"


class TestAdminServiceRoleLifecycle:
    """Tests for AdminService role lifecycle management."""

    def test_determine_change_type(self):
        """Test change type determination."""
        from tools.file_manager.services.admin_service import AdminService

        service = AdminService(db_factory=db_factory)

        # Promotion
        assert service._determine_change_type("viewer", "admin") == "promotion"
        assert service._determine_change_type("guest", "viewer") == "promotion"
        assert service._determine_change_type("guest", "admin") == "promotion"

        # Demotion
        assert service._determine_change_type("admin", "viewer") == "demotion"
        assert service._determine_change_type("admin", "guest") == "demotion"
        assert service._determine_change_type("viewer", "guest") == "demotion"

        # Transfer (same level)
        assert service._determine_change_type("viewer", "viewer") == "transfer"

        # Initial assignment
        assert service._determine_change_type(None, "admin") == "initial_assignment"
        assert service._determine_change_type(None, "viewer") == "initial_assignment"

    def test_capture_asset_snapshot_empty(self, session):
        """Test asset snapshot captures user with no spaces."""
        from tools.file_manager.services.admin_service import AdminService

        service = AdminService(db_factory=db_factory)

        # Create user without any spaces
        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="no_assets_user", role_id=admin_role.id)
        session.add(user)
        session.commit()

        snapshot = service._capture_asset_snapshot(session, user.id, "admin")

        assert snapshot["account_type"] == "admin"
        assert snapshot["owned_spaces"] == []
        assert snapshot["member_spaces"] == []

    def test_get_owned_admin_spaces(self, session):
        """Test getting owned admin spaces."""
        from tools.file_manager.services.admin_service import AdminService

        service = AdminService(db_factory=db_factory)

        admin_role = session.query(Role).filter(Role.name == "admin").first()
        user = User(username="owner_user", role_id=admin_role.id)
        session.add(user)
        session.flush()

        space = Space(
            name="Owned Space",
            storage_pool_id="dummy-pool-id",
            owner_id=user.id,
            max_bytes=1024,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        session.add(space)
        session.commit()

        owned = service._get_owned_admin_spaces(session, user.id)
        assert len(owned) == 1
        assert owned[0].name == "Owned Space"


class TestRoleChangeTypes:
    """Tests for different role change scenarios."""

    def test_promotion_priority(self, session):
        """Test that promotion is correctly identified."""
        from tools.file_manager.services.admin_service import AdminService

        service = AdminService(db_factory=db_factory)

        # guest(1) → viewer(10) = promotion
        assert service._determine_change_type("guest", "viewer") == "promotion"

        # viewer(10) → editor(50) = promotion
        assert service._determine_change_type("viewer", "editor") == "promotion"

        # editor(50) → admin(100) = promotion
        assert service._determine_change_type("editor", "admin") == "promotion"

    def test_demotion_priority(self, session):
        """Test that demotion is correctly identified."""
        from tools.file_manager.services.admin_service import AdminService

        service = AdminService(db_factory=db_factory)

        # admin(100) → viewer(10) = demotion
        assert service._determine_change_type("admin", "viewer") == "demotion"

        # viewer(10) → guest(1) = demotion
        assert service._determine_change_type("viewer", "guest") == "demotion"

    def test_account_type_definitions(self, session):
        """Test that account types are correctly defined."""
        admin = session.query(Role).filter(Role.name == "admin").first()
        editor = session.query(Role).filter(Role.name == "editor").first()
        viewer = session.query(Role).filter(Role.name == "viewer").first()
        guest = session.query(Role).filter(Role.name == "guest").first()

        assert admin.account_type == "admin"
        assert editor.account_type == "member"
        assert viewer.account_type == "member"
        assert guest.account_type == "guest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
