"""
Tests for Hermes File Manager - Trash Service
TDD Phase: Tests for soft-delete / trash / recovery mechanism
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import (
    init_db, Base, User, Role, Space, SpaceMember, StoragePool, DeletedFile
)
from tools.file_manager.services.trash_service import (
    TrashService, TrashItemNotFound, TrashExpired
)
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

    # Create space directories
    space_dir = pool_path / "spaces" / "test-space"
    space_dir.mkdir(parents=True)
    trash_dir = space_dir / "trash"
    trash_dir.mkdir()

    yield {
        "root": storage_root,
        "pool": pool_path,
        "space": space_dir,
        "trash": trash_dir,
        "tmp": tmp_path,
    }

    # Cleanup handled by tmp_path


@pytest.fixture
def db_session(tmp_workspace, monkeypatch):
    """Create an in-memory SQLite DB with all tables."""
    monkeypatch.setattr(Path, "home", lambda: tmp_workspace["tmp"])
    monkeypatch.setenv("HERMES_HOME", str(tmp_workspace["tmp"] / ".hermes"))

    factory = init_db("sqlite:///:memory:")
    session = factory()

    # Seed roles
    user_role = Role(name="user", description="Regular user", is_system=True)
    admin_role = Role(name="admin", description="Admin", is_system=True)
    session.add(user_role)
    session.add(admin_role)
    session.flush()

    # Seed admin user
    admin = User(username="admin", email="admin@test.local", role_id=admin_role.id)
    admin.set_password("admin123")
    session.add(admin)

    # Seed regular user
    user = User(username="alice", email="alice@test.local", role_id=user_role.id)
    user.set_password("secret123")
    session.add(user)
    session.commit()
    session.refresh(admin)
    session.refresh(user)

    # Create storage pool
    pool = StoragePool(
        name="Test Pool",
        base_path=str(tmp_workspace["pool"]),
        protocol="local",
        total_bytes=10 * 1024**3,
        free_bytes=10 * 1024**3,
        is_active=True,
    )
    session.add(pool)
    session.commit()
    session.refresh(pool)

    # Create space
    space = Space(
        name="Test Space",
        storage_pool_id=pool.id,
        owner_id=admin.id,
        max_bytes=1 * 1024**3,
        used_bytes=0,
        space_type="team",
        status="active",
    )
    session.add(space)
    session.commit()
    session.refresh(space)

    # Add admin as owner
    member = SpaceMember(
        space_id=space.id,
        user_id=admin.id,
        role="owner",
        status="active",
    )
    session.add(member)
    session.commit()

    session.admin = admin
    session.user = user
    session.pool = pool
    session.space = space

    yield session
    session.close()


@pytest.fixture
def db_factory(db_session):
    """Factory that returns the same session."""
    class Factory:
        def __call__(self):
            return db_session
    return Factory()


@pytest.fixture
def trash_service(db_factory, tmp_workspace):
    """Create TrashService with DB and storage."""
    storage = StorageEngine(str(tmp_workspace["root"]))

    return TrashService(
        db_factory=db_factory,
        storage=storage,
        default_pool_storage_path=str(tmp_workspace["root"]),
    )


class TestTrashService:
    """Tests for TrashService."""

    def test_list_trash_empty(self, db_session, trash_service):
        """Listing trash for empty space should return empty list."""
        space_id = db_session.space.id

        result = trash_service.list_trash(
            space_id=space_id,
            user_id=db_session.admin.id,
        )

        assert result["space_id"] == space_id
        assert result["total"] == 0
        assert result["items"] == []

    def test_list_trash_with_items(self, db_session, trash_service):
        """Listing trash should return all deleted files."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add deleted files
        for i in range(3):
            deleted = DeletedFile(
                space_id=space_id,
                original_path=f"file{i}.txt",
                name=f"file{i}.txt",
                file_size=1024 * (i + 1),
                deleted_by=user_id,
                deleted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            db_session.add(deleted)
        db_session.commit()

        result = trash_service.list_trash(
            space_id=space_id,
            user_id=user_id,
        )

        assert result["total"] == 3
        assert len(result["items"]) == 3

    def test_list_trash_pagination(self, db_session, trash_service):
        """Listing trash should support pagination."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add 5 deleted files
        for i in range(5):
            deleted = DeletedFile(
                space_id=space_id,
                original_path=f"file{i}.txt",
                name=f"file{i}.txt",
                file_size=1024,
                deleted_by=user_id,
                deleted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            db_session.add(deleted)
        db_session.commit()

        result = trash_service.list_trash(
            space_id=space_id,
            user_id=user_id,
            limit=2,
            offset=0,
        )

        assert result["total"] == 5
        assert len(result["items"]) == 2

    def test_restore_from_trash_success(self, db_session, trash_service):
        """Restoring a valid trash item should remove DeletedFile record."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add a deleted file
        deleted = DeletedFile(
            space_id=space_id,
            original_path="restored_file.txt",
            name="restored_file.txt",
            file_size=1024,
            deleted_by=user_id,
            deleted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(deleted)
        db_session.commit()
        deleted_id = deleted.id

        # Restore it
        result = trash_service.restore_from_trash(
            space_id=space_id,
            deleted_file_id=deleted_id,
            user_id=user_id,
        )

        assert "Restored" in result["message"]
        assert result["original_path"] == "restored_file.txt"

        # Verify record is removed
        remaining = db_session.query(DeletedFile).filter(
            DeletedFile.id == deleted_id
        ).first()
        assert remaining is None

    def test_restore_from_trash_not_found(self, db_session, trash_service):
        """Restoring non-existent item should raise TrashItemNotFound."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        with pytest.raises(TrashItemNotFound):
            trash_service.restore_from_trash(
                space_id=space_id,
                deleted_file_id="nonexistent-id",
                user_id=user_id,
            )

    def test_restore_from_trash_expired(self, db_session, trash_service):
        """Restoring expired item should raise TrashExpired."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add expired deleted file
        deleted = DeletedFile(
            space_id=space_id,
            original_path="expired_file.txt",
            name="expired_file.txt",
            file_size=1024,
            deleted_by=user_id,
            deleted_at=datetime.utcnow() - timedelta(days=31),
            expires_at=datetime.utcnow() - timedelta(days=1),
        )
        db_session.add(deleted)
        db_session.commit()
        deleted_id = deleted.id

        with pytest.raises(TrashExpired):
            trash_service.restore_from_trash(
                space_id=space_id,
                deleted_file_id=deleted_id,
                user_id=user_id,
            )

    def test_permanent_delete_success(self, db_session, trash_service):
        """Permanently deleting should remove the record."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add deleted file
        deleted = DeletedFile(
            space_id=space_id,
            original_path="permanent_delete.txt",
            name="permanent_delete.txt",
            file_size=1024,
            deleted_by=user_id,
            deleted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(deleted)
        db_session.commit()
        deleted_id = deleted.id

        # Permanently delete
        result = trash_service.permanent_delete(
            space_id=space_id,
            deleted_file_id=deleted_id,
            user_id=user_id,
        )

        assert "Permanently deleted" in result["message"]

        # Verify record is removed
        remaining = db_session.query(DeletedFile).filter(
            DeletedFile.id == deleted_id
        ).first()
        assert remaining is None

    def test_permanent_delete_not_found(self, db_session, trash_service):
        """Permanently deleting non-existent item should raise TrashItemNotFound."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        with pytest.raises(TrashItemNotFound):
            trash_service.permanent_delete(
                space_id=space_id,
                deleted_file_id="nonexistent-id",
                user_id=user_id,
            )

    def test_empty_trash_success(self, db_session, trash_service):
        """Emptying trash should remove all DeletedFile records."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add multiple deleted files
        for i in range(5):
            deleted = DeletedFile(
                space_id=space_id,
                original_path=f"file{i}.txt",
                name=f"file{i}.txt",
                file_size=1024,
                deleted_by=user_id,
                deleted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
            )
            db_session.add(deleted)
        db_session.commit()

        # Empty trash
        result = trash_service.empty_trash(
            space_id=space_id,
            user_id=user_id,
        )

        assert result["count"] == 5
        assert "Emptied trash" in result["message"]

        # Verify all records removed
        remaining = db_session.query(DeletedFile).filter(
            DeletedFile.space_id == space_id
        ).count()
        assert remaining == 0

    def test_purge_expired_success(self, db_session, trash_service):
        """Purging expired items should remove expired records only."""
        space_id = db_session.space.id
        user_id = db_session.admin.id

        # Add expired files
        for i in range(3):
            deleted = DeletedFile(
                space_id=space_id,
                original_path=f"expired{i}.txt",
                name=f"expired{i}.txt",
                file_size=1024,
                deleted_by=user_id,
                deleted_at=datetime.utcnow() - timedelta(days=31),
                expires_at=datetime.utcnow() - timedelta(days=1),
            )
            db_session.add(deleted)

        # Add non-expired file
        deleted = DeletedFile(
            space_id=space_id,
            original_path="not_expired.txt",
            name="not_expired.txt",
            file_size=1024,
            deleted_by=user_id,
            deleted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(deleted)
        db_session.commit()

        # Purge expired
        result = trash_service.purge_expired(space_id=space_id)

        assert result["count"] == 3

        # Verify expired files removed, not_expired remains
        remaining = db_session.query(DeletedFile).filter(
            DeletedFile.space_id == space_id
        ).count()
        assert remaining == 1

    def test_deleted_file_to_dict(self, db_session):
        """DeletedFile.to_dict() should return correct format."""
        deleted = DeletedFile(
            space_id="space-123",
            original_path="test/path.txt",
            name="path.txt",
            is_directory=False,
            file_size=4096,
            deleted_by="user-456",
            deleted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(deleted)
        db_session.commit()

        result = deleted.to_dict()

        assert result["space_id"] == "space-123"
        assert result["original_path"] == "test/path.txt"
        assert result["name"] == "path.txt"
        assert result["is_directory"] is False
        assert result["file_size"] == 4096
        assert result["deleted_by"] == "user-456"
        assert "deleted_at" in result
        assert "expires_at" in result
