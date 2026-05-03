"""
Tests for SpaceService and storage pool management.

Rewritten to use Space/SpaceMember/SpaceCredential models instead of
the deprecated Team/TeamMember/TeamCredential models.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Make file_manager importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import (
    init_db, Base, StoragePool, Space, SpaceMember, SpaceCredential, User, Role
)


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    """Create an in-memory SQLite DB with all tables."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    factory = init_db("sqlite:///:memory:")
    session = factory()

    # Seed roles
    user_role = Role(name="user", description="Regular user", is_system=True)
    admin_role = Role(name="admin", description="Admin", is_system=True)
    session.add(user_role)
    session.add(admin_role)
    session.flush()

    # Seed test user
    user = User(username="alice", email="alice@test.local", role_id=user_role.id)
    user.set_password("secret123")
    session.add(user)
    session.commit()
    session.refresh(user)

    return session


@pytest.fixture
def db_factory(db_session):
    """Factory that returns the same session."""
    class Factory:
        def __call__(self):
            return db_session
    return Factory()


@pytest.fixture
def storage_pool(db_session):
    """Create a storage pool for tests."""
    pool = StoragePool(
        name="Test Pool",
        base_path="/tmp/test-pool",
        protocol="local",
        total_bytes=10 * 1024**3,
        free_bytes=10 * 1024**3,
        is_active=True,
    )
    db_session.add(pool)
    db_session.commit()
    db_session.refresh(pool)
    return pool


@pytest.fixture
def space_service(db_factory):
    from tools.file_manager.services.space_service import SpaceService
    return SpaceService(db_factory=db_factory)


class TestStoragePoolModel:
    """Tests for StoragePool model."""

    def test_create_pool(self, db_session):
        pool = StoragePool(
            name="Test Pool",
            base_path="/tmp/test-pool",
            protocol="local",
            total_bytes=10 * 1024**3,
        )
        db_session.add(pool)
        db_session.commit()
        assert pool.id is not None
        assert pool.is_active is True
        assert pool.protocol == "local"

    def test_pool_to_dict(self, db_session):
        pool = StoragePool(name="Dict Pool", base_path="/tmp/dict", protocol="local")
        db_session.add(pool)
        db_session.commit()
        d = pool.to_dict()
        assert d["name"] == "Dict Pool"
        assert d["protocol"] == "local"
        assert d["is_active"] is True


class TestSpaceModel:
    """Tests for Space model (formerly Team)."""

    def test_create_space(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Alpha Space",
            storage_pool_id=storage_pool.id,
            max_bytes=5 * 1024**3,
            used_bytes=0,
            owner_id=user.id,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        assert space.id is not None
        assert space.status == "active"
        assert space.used_bytes == 0

    def test_space_to_dict(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Dict Space",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=1000,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        d = space.to_dict()
        assert d["name"] == "Dict Space"
        assert d["max_bytes"] == 1000
        assert d["used_bytes"] == 0
        assert d["status"] == "active"


class TestSpaceMemberModel:
    """Tests for SpaceMember model (formerly TeamMember)."""

    def test_member_role(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Member Test",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=5 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        member = SpaceMember(
            space_id=space.id,
            user_id=user.id,
            role="owner",
            status="active",
        )
        db_session.add(member)
        db_session.commit()

        assert member.role == "owner"
        d = member.to_dict()
        assert d["role"] == "owner"
        assert d["username"] == "alice"


class TestSpaceCredentialModel:
    """Tests for SpaceCredential model (formerly TeamCredential)."""

    def test_credential_valid(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Cred Test",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=5 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        cred = SpaceCredential(
            space_id=space.id,
            token="abc123token",
            max_uses=5,
            created_by=user.id,
            used_count=0,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is True
        assert cred.used_count == 0

    def test_credential_expired(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Expiry Test",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=5 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        cred = SpaceCredential(
            space_id=space.id,
            token="expired123",
            max_uses=None,
            expires_at=datetime.utcnow() - timedelta(hours=1),
            created_by=user.id,
            used_count=0,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is False

    def test_credential_max_uses_reached(self, db_session, storage_pool):
        user = db_session.query(User).first()

        space = Space(
            name="Max Uses Test",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=5 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()

        cred = SpaceCredential(
            space_id=space.id,
            token="maxuses123",
            max_uses=2,
            used_count=2,
            created_by=user.id,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is False


class TestSpaceService:
    """Tests for SpaceService."""

    def test_create_space(self, space_service, db_session, storage_pool):
        """Test creating a space."""
        user = db_session.query(User).first()

        space = space_service.create_space(
            name="Test Space",
            owner_id=user.id,
            storage_pool_id=storage_pool.id,
            space_type="team",
            max_bytes=1024 * 1024,
        )

        assert space["name"] == "Test Space"
        assert space["owner_id"] == user.id
        assert space["space_type"] == "team"

    def test_add_member(self, space_service, db_session, storage_pool):
        """Test adding a member to a space."""
        owner = db_session.query(User).first()
        owner_id = owner.id

        # Create a second user to add as member
        bob = User(username="bob", email="bob@test.local", role_id=owner.role_id)
        bob.set_password("secret456")
        db_session.add(bob)
        db_session.commit()
        bob_id = bob.id

        space = space_service.create_space(
            name="Member Test Space",
            owner_id=owner_id,
            storage_pool_id=storage_pool.id,
            space_type="team",
            max_bytes=1024 * 1024,
        )

        # Add bob as member
        member = space_service.add_member(
            space_id=space["id"],
            user_id=bob_id,
            requesting_user_id=owner_id,
            role="member",
        )

        assert member is not None
        assert member["user_id"] == bob_id

    def test_list_spaces(self, space_service, db_session, storage_pool):
        """Test listing spaces."""
        user = db_session.query(User).first()

        space_service.create_space(
            name="List Test Space",
            owner_id=user.id,
            storage_pool_id=storage_pool.id,
            space_type="team",
            max_bytes=1024 * 1024,
        )

        spaces = space_service.list_spaces(user_id=user.id)
        assert len(spaces) >= 1
        assert any(s["name"] == "List Test Space" for s in spaces)


class TestStorageAdapters:
    """Tests for storage adapters."""

    def test_local_adapter_basic(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import LocalStorageAdapter

        adapter = LocalStorageAdapter(str(tmp_path / "local_test"))
        assert adapter.exists("/") is True
        assert adapter.is_dir("/") is True

        adapter.write_file("/hello.txt", b"world")
        assert adapter.exists("/hello.txt") is True
        assert adapter.is_file("/hello.txt") is True
        assert adapter.is_dir("/hello.txt") is False
        assert adapter.read_file("/hello.txt") == b"world"

        adapter.mkdir("/subdir")
        assert adapter.is_dir("/subdir") is True
        assert "hello.txt" in adapter.list_dir("/")

        adapter.delete("/hello.txt")
        assert adapter.exists("/hello.txt") is False

        st = adapter.stat("/subdir")
        assert st["type"] == "directory"

        assert adapter.get_free_space() > 0
        assert adapter.get_total_space() > 0

    def test_local_adapter_path_escape_blocked(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import LocalStorageAdapter

        adapter = LocalStorageAdapter(str(tmp_path / "escape_test"))
        with pytest.raises(ValueError, match="Path escape"):
            adapter._resolve("../etc/passwd")

        adapter.write_file("/safe.txt", b"ok")
        assert adapter.exists("/safe.txt") is True

    def test_factory_local(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        adapter = create_storage_adapter(
            protocol="local",
            base_path=str(tmp_path / "factory_test"),
        )
        assert adapter is not None
        assert adapter.exists("/") is True

    def test_factory_unknown_protocol(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        with pytest.raises(ValueError, match="Unknown storage protocol"):
            create_storage_adapter(
                protocol="ftp",
                base_path="/tmp/data",
            )

    def test_factory_smb_missing_host(self):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        with pytest.raises(ValueError, match="host/share"):
            create_storage_adapter(
                protocol="smb",
                base_path="/ambiguous/path",
            )
