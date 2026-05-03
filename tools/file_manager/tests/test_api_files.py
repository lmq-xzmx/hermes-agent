"""
Tests for Hermes File Manager - FileService

Rewritten to use proper workspace context and filesystem setup.
These tests verify file operations with proper space/permission context.
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import (
    init_db, Base, StoragePool, Space, SpaceMember, User, Role
)
from tools.file_manager.services.space_service import SpaceService
from tools.file_manager.services.file_service import FileService
from tools.file_manager.services.permission_checker import PermissionChecker
from tools.file_manager.services.permission_context import PermissionContext
from tools.file_manager.engine.storage import StorageEngine


@pytest.fixture
def tmp_workspace(tmp_path, monkeypatch):
    """Create a temporary workspace with filesystem."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    # Create temp directory for storage
    storage_root = tmp_path / "storage"
    storage_root.mkdir()
    pool_path = storage_root / "pool1"
    pool_path.mkdir()

    yield {
        "root": storage_root,
        "pool": pool_path,
        "tmp": tmp_path,
    }

    # Cleanup
    shutil.rmtree(storage_root, ignore_errors=True)


@pytest.fixture
def db_session(tmp_workspace, monkeypatch):
    """Create an in-memory SQLite DB with all tables."""
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
def storage_pool(db_session, tmp_workspace):
    """Create a storage pool."""
    pool = StoragePool(
        name="Test Pool",
        base_path=str(tmp_workspace["pool"]),
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
def space(db_session, storage_pool):
    """Create a test space."""
    user = db_session.query(User).first()

    space = Space(
        name="Test Space",
        storage_pool_id=storage_pool.id,
        owner_id=user.id,
        max_bytes=1 * 1024**3,
        used_bytes=0,
        space_type="team",
        status="active",
    )
    db_session.add(space)
    db_session.commit()
    db_session.refresh(space)
    return space


@pytest.fixture
def permission_context(db_session, space):
    """Create a permission context for the test user."""
    user = db_session.query(User).first()
    return PermissionContext(
        user_id=user.id,
        username=user.username,
        role_name="user",
        space_id=space.id,
        pool_id=space.storage_pool_id,
        permission_rules=[],
    )


class TestStorageEngine:
    """Tests for low-level StorageEngine operations."""

    def test_write_and_read_file(self, tmp_workspace):
        """Test basic file write and read."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        storage.write_file("/test.txt", "Hello World")
        content = storage.read_file("/test.txt")

        assert content == "Hello World"

    def test_create_and_list_directory(self, tmp_workspace):
        """Test directory creation and listing."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        storage.create_directory("/subdir")
        storage.write_file("/subdir/file.txt", "content")

        items = storage.list_directory("/")
        names = [item["name"] for item in items]

        assert "subdir" in names

    def test_delete_file(self, tmp_workspace):
        """Test file deletion."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        storage.write_file("/to_delete.txt", "content")
        storage.delete_path("/to_delete.txt")

        # File should no longer be readable
        with pytest.raises(Exception):
            storage.read_file("/to_delete.txt")

    def test_copy_file(self, tmp_workspace):
        """Test file copy."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        storage.write_file("/original.txt", "source")
        result = storage.copy_file("/original.txt", "/copy.txt")

        assert result["name"] == "copy.txt"
        assert storage.read_file("/copy.txt") == "source"

    def test_move_file(self, tmp_workspace):
        """Test file move."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        storage.write_file("/source.txt", "content")
        result = storage.move_file("/source.txt", "/moved.txt")

        assert result["name"] == "moved.txt"
        # Moved file should be readable
        assert storage.read_file("/moved.txt") == "content"
        # Source file should not be readable
        with pytest.raises(Exception):
            storage.read_file("/source.txt")

    def test_path_traversal_blocked(self, tmp_workspace):
        """Test that path traversal is blocked."""
        storage = StorageEngine(str(tmp_workspace["root"]))

        with pytest.raises(PermissionError):
            storage._resolve_user_path("../../../etc/passwd")


class TestSpaceServiceFileOperations:
    """Tests for file operations via SpaceService."""

    def test_create_space_creates_directories(self, db_session, storage_pool, tmp_workspace):
        """Test that creating a space also creates its directory structure."""
        user = db_session.query(User).first()

        class FakeFactory:
            def __call__(self):
                return db_session

        service = SpaceService(db_factory=FakeFactory())

        space = service.create_space(
            name="File Test Space",
            owner_id=user.id,
            storage_pool_id=storage_pool.id,
            space_type="team",
            max_bytes=1024 * 1024,
        )

        # Check that the space directory was created
        space_path = Path(tmp_workspace["pool"]) / "spaces" / space["id"]
        assert space_path.exists(), f"Space directory should exist at {space_path}"
