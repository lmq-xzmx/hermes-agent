"""
Tests for Hermes File Manager - FileService
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from unittest.mock import MagicMock

from tools.file_manager.services.file_service import FileService
from tools.file_manager.services.permission_context import PermissionContext
from tools.file_manager.services.permission_checker import PermissionChecker, PermissionDecision
from tools.file_manager.engine.storage import StorageEngine
from tools.file_manager.api.dto import (
    FileReadRequestDTO, FileWriteRequestDTO, FileDeleteRequestDTO,
    MkDirRequestDTO, FileCopyRequestDTO, FileMoveRequestDTO,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def storage_root():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def storage(storage_root):
    return StorageEngine(storage_root, permission_engine=None)


@pytest.fixture
def checker(storage_root):
    return PermissionChecker(storage_root)


@pytest.fixture
def mock_checker():
    """Mock checker that allows all operations."""
    mock = MagicMock(spec=PermissionChecker)
    mock.check.return_value = PermissionDecision(allowed=True, reason="ok")
    return mock


@pytest.fixture
def file_service(storage, mock_checker):
    return FileService(
        storage=storage,
        permission_checker=mock_checker,
        event_bus=None,
    )


@pytest.fixture
def admin_ctx():
    return PermissionContext(
        user_id="uid1", username="admin", role_name="admin", permission_rules=[]
    )


@pytest.fixture
def viewer_ctx():
    return PermissionContext(
        user_id="uid2", username="viewer", role_name="viewer",
        permission_rules=["read,list:/public/**"]
    )


@pytest.fixture
def deny_checker():
    """Mock checker that denies all operations."""
    mock = MagicMock(spec=PermissionChecker)
    mock.check.return_value = PermissionDecision(allowed=False, reason="denied")
    return mock


# =============================================================================
# FileService List Directory
# =============================================================================

class TestFileServiceListDirectory:
    """Tests for FileService.list_directory method"""

    def test_list_directory_returns_items(self, file_service, admin_ctx, storage):
        """list_directory should return a list of files/directories"""
        storage.write_file("test.txt", "content")
        storage.create_directory("testdir")

        result = file_service.list_directory("/", admin_ctx)

        assert result.path == "/"
        assert result.readable is True
        names = [item.name for item in result.items]
        assert "test.txt" in names
        assert "testdir" in names

    def test_list_directory_permission_denied(self, storage, deny_checker, viewer_ctx):
        """list_directory should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        with pytest.raises(FileAccessDenied):
            file_service.list_directory("/private", viewer_ctx)

    def test_list_directory_not_found(self, file_service, admin_ctx):
        """list_directory should raise FileNotFound for non-existent directories"""
        from tools.file_manager.services.file_service import FileNotFound

        with pytest.raises(FileNotFound):
            file_service.list_directory("/nonexistent", admin_ctx)


# =============================================================================
# FileService Read File
# =============================================================================

class TestFileServiceReadFile:
    """Tests for FileService.read_file method"""

    def test_read_file_returns_content(self, file_service, admin_ctx, storage):
        """read_file should return file content"""
        storage.write_file("readme.txt", "Hello World")

        request = FileReadRequestDTO(path="readme.txt")
        result = file_service.read_file(request, admin_ctx)

        assert result.path == "readme.txt"
        assert result.content == "Hello World"
        assert result.size == 11

    def test_read_file_not_found(self, file_service, admin_ctx):
        """read_file should raise FileNotFound for non-existent files"""
        from tools.file_manager.services.file_service import FileNotFound

        request = FileReadRequestDTO(path="nonexistent.txt")

        with pytest.raises(FileNotFound):
            file_service.read_file(request, admin_ctx)

    def test_read_file_permission_denied(self, storage, deny_checker, viewer_ctx):
        """read_file should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = FileReadRequestDTO(path="/private/file.txt")

        with pytest.raises(FileAccessDenied):
            file_service.read_file(request, viewer_ctx)


# =============================================================================
# FileService Write File
# =============================================================================

class TestFileServiceWriteFile:
    """Tests for FileService.write_file method"""

    def test_write_file_creates_file(self, file_service, admin_ctx, storage):
        """write_file should create a new file"""
        request = FileWriteRequestDTO(path="newfile.txt", content="new content")
        result = file_service.write_file(request, admin_ctx)

        assert result["name"] == "newfile.txt"
        assert storage.read_file("newfile.txt") == "new content"

    def test_write_file_overwrites_existing(self, file_service, admin_ctx, storage):
        """write_file with overwrite=True should replace existing file"""
        storage.write_file("existing.txt", "original")

        request = FileWriteRequestDTO(path="existing.txt", content="updated", overwrite=True)
        file_service.write_file(request, admin_ctx)

        assert storage.read_file("existing.txt") == "updated"

    def test_write_file_permission_denied(self, storage, deny_checker, viewer_ctx):
        """write_file should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = FileWriteRequestDTO(path="/private/file.txt", content="data")

        with pytest.raises(FileAccessDenied):
            file_service.write_file(request, viewer_ctx)


# =============================================================================
# FileService Delete File
# =============================================================================

class TestFileServiceDeleteFile:
    """Tests for FileService.delete_file method"""

    def test_delete_file_removes_file(self, file_service, admin_ctx, storage):
        """delete_file should remove the specified file"""
        storage.write_file("to_delete.txt", "content")

        request = FileDeleteRequestDTO(path="to_delete.txt")
        result = file_service.delete_file(request, admin_ctx)

        assert "message" in result
        with pytest.raises(Exception):  # FileNotFoundError
            storage.read_file("to_delete.txt")

    def test_delete_nonexistent_raises_not_found(self, file_service, admin_ctx):
        """delete_file should raise FileNotFound for non-existent files"""
        from tools.file_manager.services.file_service import FileNotFound

        request = FileDeleteRequestDTO(path="does_not_exist.txt")

        with pytest.raises(FileNotFound):
            file_service.delete_file(request, admin_ctx)

    def test_delete_permission_denied(self, storage, deny_checker, viewer_ctx):
        """delete_file should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = FileDeleteRequestDTO(path="/private/file.txt")

        with pytest.raises(FileAccessDenied):
            file_service.delete_file(request, viewer_ctx)


# =============================================================================
# FileService Create Directory
# =============================================================================

class TestFileServiceCreateDirectory:
    """Tests for FileService.create_directory method"""

    def test_create_directory_creates_dir(self, file_service, admin_ctx, storage):
        """create_directory should create a new directory"""
        request = MkDirRequestDTO(path="newdir")
        result = file_service.create_directory(request, admin_ctx)

        assert result["name"] == "newdir"
        stat = storage.get_stat("newdir")
        assert stat.get("type") == "directory"

    def test_create_directory_already_exists_raises_error(self, file_service, admin_ctx, storage):
        """create_directory should raise FileAlreadyExists if directory already exists"""
        from tools.file_manager.services.file_service import FileAlreadyExists
        storage.create_directory("existing_dir")

        request = MkDirRequestDTO(path="existing_dir")

        with pytest.raises(FileAlreadyExists):
            file_service.create_directory(request, admin_ctx)

    def test_create_directory_permission_denied(self, storage, deny_checker, viewer_ctx):
        """create_directory should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = MkDirRequestDTO(path="/private/newdir")

        with pytest.raises(FileAccessDenied):
            file_service.create_directory(request, viewer_ctx)


# =============================================================================
# FileService Copy File
# =============================================================================

class TestFileServiceCopyFile:
    """Tests for FileService.copy_file method"""

    def test_copy_file_creates_copy(self, file_service, admin_ctx, storage):
        """copy_file should create a copy of the file"""
        storage.write_file("original.txt", "source content")

        request = FileCopyRequestDTO(from_path="original.txt", to_path="copy.txt")
        result = file_service.copy_file(request, admin_ctx)

        assert result["name"] == "copy.txt"
        assert storage.read_file("original.txt") == "source content"
        assert storage.read_file("copy.txt") == "source content"

    def test_copy_file_source_not_found_raises_not_found(self, file_service, admin_ctx):
        """copy_file should raise FileNotFound if source file doesn't exist"""
        from tools.file_manager.services.file_service import FileNotFound

        request = FileCopyRequestDTO(from_path="nonexistent.txt", to_path="copy.txt")

        with pytest.raises(FileNotFound):
            file_service.copy_file(request, admin_ctx)

    def test_copy_file_permission_denied_on_read(self, storage, deny_checker, viewer_ctx):
        """copy_file should raise FileAccessDenied if read not permitted on source"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = FileCopyRequestDTO(from_path="/private/source.txt", to_path="/public/dest.txt")

        with pytest.raises(FileAccessDenied):
            file_service.copy_file(request, viewer_ctx)


# =============================================================================
# FileService Move File
# =============================================================================

class TestFileServiceMoveFile:
    """Tests for FileService.move_file method"""

    def test_move_file_moves_file(self, file_service, admin_ctx, storage):
        """move_file should move/rename a file"""
        storage.write_file("source.txt", "moving content")

        request = FileMoveRequestDTO(from_path="source.txt", to_path="moved.txt")
        result = file_service.move_file(request, admin_ctx)

        assert result["name"] == "moved.txt"
        assert storage.read_file("moved.txt") == "moving content"
        with pytest.raises(Exception):  # FileNotFoundError
            storage.read_file("source.txt")

    def test_move_file_source_not_found_raises_not_found(self, file_service, admin_ctx):
        """move_file should raise FileNotFound if source file doesn't exist"""
        from tools.file_manager.services.file_service import FileNotFound

        request = FileMoveRequestDTO(from_path="nonexistent.txt", to_path="moved.txt")

        with pytest.raises(FileNotFound):
            file_service.move_file(request, admin_ctx)

    def test_move_file_permission_denied_on_delete(self, storage, deny_checker, viewer_ctx):
        """move_file should raise FileAccessDenied if delete not permitted on source"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        request = FileMoveRequestDTO(from_path="/private/source.txt", to_path="/public/dest.txt")

        with pytest.raises(FileAccessDenied):
            file_service.move_file(request, viewer_ctx)


# =============================================================================
# FileService Get Stat
# =============================================================================

class TestFileServiceGetStat:
    """Tests for FileService.get_stat method"""

    def test_get_stat_returns_metadata(self, file_service, admin_ctx, storage):
        """get_stat should return file/directory metadata"""
        storage.write_file("stat_test.txt", "content")

        result = file_service.get_stat("stat_test.txt", admin_ctx)

        assert result.name == "stat_test.txt"
        assert result.path == "stat_test.txt"
        assert result.is_directory is False
        assert result.size == 7

    def test_get_stat_nonexistent_raises_not_found(self, file_service, admin_ctx):
        """get_stat should raise FileNotFound for non-existent paths"""
        from tools.file_manager.services.file_service import FileNotFound

        with pytest.raises(FileNotFound):
            file_service.get_stat("nonexistent.txt", admin_ctx)

    def test_get_stat_permission_denied(self, storage, deny_checker, viewer_ctx):
        """get_stat should raise FileAccessDenied for unauthorized paths"""
        from tools.file_manager.services.file_service import FileAccessDenied
        file_service = FileService(storage=storage, permission_checker=deny_checker, event_bus=None)

        with pytest.raises(FileAccessDenied):
            file_service.get_stat("/private/file.txt", viewer_ctx)


# =============================================================================
# Storage Security (kept from original - tests low-level storage)
# =============================================================================

class TestStorageSecurity:
    """Tests for storage-level security (not FileService)"""

    def test_storage_blocks_parent_traversal(self, storage):
        """Storage should block path traversal attempts"""
        with pytest.raises(PermissionError):
            storage._resolve_user_path("../../../etc/passwd")

    def test_storage_allows_valid_relative_paths(self, storage):
        """Storage should allow valid relative paths"""
        storage.create_directory("safe")
        storage.write_file("safe/file.txt", "content")
        content = storage.read_file("safe/file.txt")
        assert content == "content"


# =============================================================================
# Storage Operations via Admin (kept from original)
# =============================================================================

class TestStorageViaAdmin:
    """Tests for storage operations without permission checks (admin context)"""

    def test_storage_write_via_admin(self, storage):
        result = storage.write_file("admin_file.txt", "admin content")
        assert result["name"] == "admin_file.txt"
        assert storage.read_file("admin_file.txt") == "admin content"

    def test_storage_delete_via_admin(self, storage):
        storage.write_file("to_delete.txt", "content")
        storage.delete_path("to_delete.txt")
        with pytest.raises(Exception):  # FileNotFoundError
            storage.read_file("to_delete.txt")

    def test_storage_copy_via_admin(self, storage):
        storage.write_file("original.txt", "source content")
        result = storage.copy_file("original.txt", "copy.txt")
        assert result["name"] == "copy.txt"
        assert storage.read_file("copy.txt") == "source content"

    def test_storage_move_via_admin(self, storage):
        storage.write_file("move_src.txt", "moving content")
        result = storage.move_file("move_src.txt", "move_dst.txt")
        assert result["name"] == "move_dst.txt"
        assert storage.read_file("move_dst.txt") == "moving content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
