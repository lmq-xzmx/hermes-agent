"""
Tests for Hermes File Manager - Storage Engine
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.storage import (
    StorageEngine, FileNotFoundError, FileExistsError,
    DirectoryNotEmptyError, FileOperationError,
)
from tools.file_manager.engine.permission import PermissionEngine
from tools.file_manager.engine.models import User, Role, PermissionRule, Operation


@pytest.fixture
def storage_root():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def perm_engine(storage_root):
    return PermissionEngine(storage_root)


@pytest.fixture
def storage(storage_root, perm_engine):
    return StorageEngine(storage_root, perm_engine)


@pytest.fixture
def admin_user():
    role = Role(id="admin-id", name="admin", description="Admin")
    return User(id="admin-uid", username="admin", role=role)


# =============================================================================
# Directory Operations
# =============================================================================

class TestListDirectory:
    def test_list_empty_directory(self, storage):
        storage.create_directory("emptydir")
        items = storage.list_directory("emptydir")
        assert items == []

    def test_list_with_files_and_dirs(self, storage):
        storage.create_directory("folder")
        storage.write_file("folder/file1.txt", "content1")
        storage.write_file("folder/file2.txt", "content2")

        items = storage.list_directory("folder")
        names = [i["name"] for i in items]
        assert "file1.txt" in names
        assert "file2.txt" in names

    def test_list_hidden_files_excluded_by_default(self, storage):
        storage.create_directory("hidtest")
        storage.write_file("hidtest/visible.txt", "hi")
        storage.write_file("hidtest/.hidden", "secret")

        items = storage.list_directory("hidtest")
        names = [i["name"] for i in items]
        assert "visible.txt" in names
        assert ".hidden" not in names

    def test_list_includes_hidden_when_requested(self, storage):
        storage.create_directory("hidtest2")
        storage.write_file("hidtest2/.secret", "data")

        items = storage.list_directory("hidtest2", include_hidden=True)
        names = [i["name"] for i in items]
        assert ".secret" in names

    def test_list_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.list_directory("does_not_exist")

    def test_list_sorting_directories_first(self, storage):
        storage.create_directory("alpha")
        storage.create_directory("beta")
        storage.write_file("gamma.txt", "text")

        items = storage.list_directory("")
        types = [i["type"] for i in items]
        assert types[0] == "directory"  # dirs before files
        assert types[-1] == "file"


class TestCreateDirectory:
    def test_create_simple_directory(self, storage):
        result = storage.create_directory("newdir")
        assert result["name"] == "newdir"
        assert result["type"] == "directory"

    def test_create_nested_directory(self, storage):
        result = storage.create_directory("parent/child/grandchild")
        assert result["name"] == "grandchild"

    def test_create_duplicate_raises(self, storage):
        storage.create_directory("dupdir")
        with pytest.raises(FileExistsError):
            storage.create_directory("dupdir")

    def test_created_directory_in_root(self, storage, storage_root):
        storage.create_directory("in_root")
        assert (Path(storage_root) / "in_root").exists()


class TestRemoveDirectory:
    def test_remove_empty_directory(self, storage):
        storage.create_directory("to_remove")
        storage.remove_directory("to_remove")
        # Should not raise

    def test_remove_nonempty_without_recursive_raises(self, storage):
        storage.create_directory("not_empty")
        storage.write_file("not_empty/file.txt", "content")

        with pytest.raises(DirectoryNotEmptyError):
            storage.remove_directory("not_empty", recursive=False)

    def test_remove_recursive(self, storage):
        storage.create_directory("tree/branch/leaf")
        storage.write_file("tree/branch/leaf/file.txt", "content")
        storage.remove_directory("tree", recursive=True)
        # Should not raise

    def test_remove_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.remove_directory("ghost")


# =============================================================================
# File Read/Write
# =============================================================================

class TestWriteFile:
    def test_write_text_file(self, storage):
        result = storage.write_file("hello.txt", "Hello World")
        assert result["name"] == "hello.txt"
        assert result["type"] == "file"
        assert result["size"] == 11

    def test_write_creates_parent_dirs(self, storage):
        storage.write_file("deep/nested/file.txt", "content")
        # Should not raise

    def test_write_overwrite_default(self, storage):
        storage.write_file("over.txt", "v1")
        result = storage.write_file("over.txt", "v2")
        assert result["size"] == 2

    def test_write_no_overwrite(self, storage):
        storage.write_file("keep.txt", "original")
        with pytest.raises(FileExistsError):
            storage.write_file("keep.txt", "new", overwrite=False)

    def test_write_unicode_content(self, storage):
        storage.write_file("unicode.txt", "你好世界 🌍")
        content = storage.read_file("unicode.txt")
        assert "你好世界" in content


class TestReadFile:
    def test_read_existing_file(self, storage):
        storage.write_file("readme.txt", "test content here")
        content = storage.read_file("readme.txt")
        assert content == "test content here"

    def test_read_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read_file("ghost.txt")

    def test_read_with_offset(self, storage):
        storage.write_file("offset.txt", "0123456789")
        content = storage.read_file("offset.txt", offset=3)
        assert content == "3456789"

    def test_read_with_size_limit(self, storage):
        storage.write_file("limit.txt", "0123456789")
        content = storage.read_file("limit.txt", offset=2, size=3)
        assert content == "234"

    def test_read_directory_raises(self, storage):
        storage.create_directory("is_a_dir")
        with pytest.raises(FileOperationError):
            storage.read_file("is_a_dir")


class TestBinaryIO:
    def test_write_read_bytes(self, storage):
        data = bytes(range(256))
        storage.write_file_bytes("binary.bin", data)
        result = storage.read_file_bytes("binary.bin")
        assert result == data

    def test_read_bytes_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.read_file_bytes("ghost.bin")


# =============================================================================
# File Copy/Move/Delete
# =============================================================================

class TestCopyFile:
    def test_copy_file(self, storage):
        storage.write_file("source.txt", "copied content")
        result = storage.copy_file("source.txt", "dest.txt")
        assert result["name"] == "dest.txt"
        assert storage.read_file("dest.txt") == "copied content"

    def test_copy_to_nested_path(self, storage):
        storage.write_file("src.txt", "data")
        storage.copy_file("src.txt", "nested/path/dst.txt")
        assert storage.read_file("nested/path/dst.txt") == "data"

    def test_copy_nonexistent_source_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.copy_file("ghost.txt", "dest.txt")

    def test_copy_overwrite(self, storage):
        storage.write_file("a.txt", "original")
        storage.write_file("b.txt", "newer")
        result = storage.copy_file("a.txt", "b.txt", overwrite=True)
        assert storage.read_file("b.txt") == "original"


class TestMoveFile:
    def test_move_file(self, storage):
        storage.write_file("old.txt", "moved content")
        result = storage.move_file("old.txt", "new.txt")
        assert result["name"] == "new.txt"
        assert storage.read_file("new.txt") == "moved content"
        # Old file should be gone
        import pytest as pt
        with pt.raises(FileNotFoundError):
            storage.read_file("old.txt")

    def test_move_to_different_directory(self, storage):
        storage.create_directory("dst_dir")
        storage.write_file("mobile.txt", "content")
        storage.move_file("mobile.txt", "dst_dir/mobile.txt")
        assert storage.read_file("dst_dir/mobile.txt") == "content"


class TestDeleteFile:
    def test_delete_existing_file(self, storage):
        storage.write_file("todel.txt", "bye")
        storage.delete_file("todel.txt")
        import pytest as pt
        with pt.raises(FileNotFoundError):
            storage.read_file("todel.txt")

    def test_delete_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.delete_file("ghost.txt")


class TestDeletePath:
    def test_delete_path_file(self, storage):
        storage.write_file("del.txt", "content")
        storage.delete_path("del.txt")
        import pytest as pt
        with pt.raises(FileNotFoundError):
            storage.read_file("del.txt")

    def test_delete_path_directory_recursive(self, storage):
        storage.create_directory("del_tree/a/b/c")
        storage.delete_path("del_tree", recursive=True)


# =============================================================================
# Metadata
# =============================================================================

class TestGetStat:
    def test_stat_file(self, storage):
        storage.write_file("stat.txt", "content here")
        stat = storage.get_stat("stat.txt")
        assert stat["name"] == "stat.txt"
        assert stat["type"] == "file"
        assert stat["size"] == 12  # "content here" = 12 bytes

    def test_stat_directory(self, storage):
        storage.create_directory("statdir")
        stat = storage.get_stat("statdir")
        assert stat["name"] == "statdir"
        assert stat["type"] == "directory"

    def test_stat_nonexistent_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.get_stat("ghost")


class TestChecksum:
    def test_sha256_checksum(self, storage):
        storage.write_file("check.txt", "hello")
        cs = storage.get_checksum("check.txt", "sha256")
        # sha256 of "hello" = 2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824
        assert len(cs) == 64
        assert cs.isalnum()


# =============================================================================
# Search
# =============================================================================

class TestSearch:
    def test_search_finds_files(self, storage):
        storage.create_directory("searchdir")
        storage.write_file("searchdir/a.txt", "content")
        storage.write_file("searchdir/b.txt", "content")
        storage.write_file("searchdir/c.md", "content")

        results = storage.search("searchdir", "*.txt", recursive=True)
        assert len(results) == 2

    def test_search_recursive(self, storage):
        storage.create_directory("recurse/sub")
        storage.write_file("recurse/sub/deep.txt", "found")
        results = storage.search("recurse", "*.txt", recursive=True)
        assert len(results) == 1

    def test_search_nonexistent_directory_raises(self, storage):
        with pytest.raises(FileNotFoundError):
            storage.search("ghost", "*.txt")


# =============================================================================
# Path Security
# =============================================================================

class TestPathSecurity:
    def test_path_traversal_blocked(self, storage):
        """Path traversal should raise PermissionError"""
        # The storage engine delegates to PermissionEngine.resolve_path
        # which raises PermissionError for traversal attempts
        from tools.file_manager.engine.permission import PermissionEngine
        pe = storage.permission_engine
        # Writing via traversal should be blocked at resolve step
        with pytest.raises(PermissionError):
            storage._resolve_user_path("../../../etc/passwd")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
