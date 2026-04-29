"""
Tests for Hermes File Manager - Files API
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, PermissionRule, init_db, create_builtin_roles
)
from tools.file_manager.engine.storage import StorageEngine
from tools.file_manager.engine.permission import PermissionEngine, Operation
from tools.file_manager.engine.audit import AuditLogger


@pytest.fixture
def temp_root():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


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
def perm_engine(temp_root):
    return PermissionEngine(temp_root)


@pytest.fixture
def storage(temp_root, perm_engine):
    return StorageEngine(temp_root, perm_engine)


@pytest.fixture
def admin_user(db_session):
    admin_role = db_session.query(Role).filter(Role.name == "admin").first()
    user = User(username="fileadmin", role=admin_role)
    user.set_password("adminpass")
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def viewer_user(db_session):
    viewer_role = db_session.query(Role).filter(Role.name == "viewer").first()
    # Add a rule for /public/**
    rule = PermissionRule(
        role_id=viewer_role.id,
        path_pattern="/public/**",
        permissions="read,list",
        priority=0,
    )
    db_session.add(rule)

    user = User(username="fileviewer", role=viewer_role)
    user.set_password("viewerpass")
    db_session.add(user)
    db_session.commit()
    return user


# =============================================================================
# Permission Engine Integration
# =============================================================================

class TestPermissionCheck:
    def test_admin_can_read_any_path(self, perm_engine, admin_user):
        decision = perm_engine.check_permission(
            admin_user, Operation.READ, "any/path/at/all", []
        )
        assert decision.allowed is True

    def test_viewer_can_read_allowed_path(self, perm_engine, viewer_user, db_session):
        rules = db_session.query(PermissionRule).filter(
            PermissionRule.role_id == viewer_user.role_id
        ).all()

        decision = perm_engine.check_permission(
            viewer_user, Operation.READ, "public/readme.txt", rules
        )
        assert decision.allowed is True

    def test_viewer_cannot_write_to_read_only_path(self, perm_engine, viewer_user, db_session):
        rules = db_session.query(PermissionRule).filter(
            PermissionRule.role_id == viewer_user.role_id
        ).all()

        decision = perm_engine.check_permission(
            viewer_user, Operation.WRITE, "public/readme.txt", rules
        )
        assert decision.allowed is False

    def test_viewer_cannot_read_unauthorized_path(self, perm_engine, viewer_user, db_session):
        rules = db_session.query(PermissionRule).filter(
            PermissionRule.role_id == viewer_user.role_id
        ).all()

        decision = perm_engine.check_permission(
            viewer_user, Operation.READ, "private/secret.txt", rules
        )
        assert decision.allowed is False


# =============================================================================
# Files API Operations
# =============================================================================

class TestStorageViaPermission:
    def test_storage_write_via_admin(self, storage, admin_user):
        result = storage.write_file("admin_file.txt", "admin content")
        assert result["name"] == "admin_file.txt"
        assert storage.read_file("admin_file.txt") == "admin content"

    def test_storage_delete_via_admin(self, storage, admin_user):
        storage.write_file("to_delete.txt", "content")
        storage.delete_path("to_delete.txt")
        import pytest as pt
        with pt.raises(Exception):  # FileNotFoundError
            storage.read_file("to_delete.txt")

    def test_storage_copy_via_admin(self, storage, admin_user):
        storage.write_file("original.txt", "source content")
        result = storage.copy_file("original.txt", "copy.txt")
        assert result["name"] == "copy.txt"
        assert storage.read_file("copy.txt") == "source content"

    def test_storage_move_via_admin(self, storage, admin_user):
        storage.write_file("move_src.txt", "moving content")
        result = storage.move_file("move_src.txt", "move_dst.txt")
        assert result["name"] == "move_dst.txt"
        assert storage.read_file("move_dst.txt") == "moving content"


class TestGlobPatternMatching:
    def test_star_matches_without_slash(self, perm_engine):
        # Pattern *.txt should match file.txt but not subdir/file.txt
        assert perm_engine._path_matches_pattern("readme.txt", "*.txt") is True
        assert perm_engine._path_matches_pattern("doc.md", "*.txt") is False

    def test_double_star_matches_recursively(self, perm_engine):
        # ** in fnmatch/Python:
        # - ** alone = any path (including root-level)
        # - **/ requires at least one leading /
        # - **/docs/*.txt = /docs/ must appear after ≥1 leading /
        # So **/docs/*.txt matches a/docs/file.txt but NOT docs/file.txt (no leading /)
        assert perm_engine._path_matches_pattern("a/docs/file.txt", "**/docs/*.txt") is True
        assert perm_engine._path_matches_pattern("a/b/docs/file.txt", "**/docs/*.txt") is True
        # Root-level files without subdirectories are NOT matched by **/*.txt
        assert perm_engine._path_matches_pattern("c.txt", "**/*.txt") is False
        # **/docs/*.txt does NOT match docs/file.txt (no leading slash before docs)
        assert perm_engine._path_matches_pattern("docs/file.txt", "**/docs/*.txt") is False

    def test_character_class(self, perm_engine):
        assert perm_engine._path_matches_pattern("file1.txt", "file[0-9].txt") is True
        assert perm_engine._path_matches_pattern("fileA.txt", "file[0-9].txt") is False


# =============================================================================
# Storage Security
# =============================================================================

class TestStorageSecurity:
    def test_storage_blocks_parent_traversal(self, storage):
        # Even via storage's internal _resolve_user_path, traversal should be blocked
        with pytest.raises(PermissionError):
            storage._resolve_user_path("../../../etc/passwd")

    def test_storage_allows_valid_relative_paths(self, storage):
        storage.create_directory("safe")
        storage.write_file("safe/file.txt", "content")
        content = storage.read_file("safe/file.txt")
        assert content == "content"


# =============================================================================
# FilesAPI Direct Unit Tests (RED phase - tests define expected behavior)
# =============================================================================

class TestFilesAPIListDirectory:
    """Tests for FilesAPI.list_directory method"""

    def test_list_directory_returns_list_of_items(self, storage, admin_user, db_session):
        """list_directory should return a list of files/directories"""
        from tools.file_manager.api.files import FilesAPI
        from sqlalchemy.orm import sessionmaker

        storage.write_file("test.txt", "content")
        storage.create_directory("testdir")

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        result = api.list_directory("/", user=admin_user)
        
        assert isinstance(result, list)
        # Should contain at least test.txt and testdir
        names = [item.get("name") for item in result]
        assert "test.txt" in names or "testdir" in names

    def test_list_directory_with_permission_denied(self, storage, viewer_user, db_session):
        """list_directory should raise 403 for unauthorized paths"""
        from tools.file_manager.api.files import FilesAPI
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        with pytest.raises(HTTPException) as exc_info:
            api.list_directory("/private_forbidden", user=viewer_user)
        assert exc_info.value.status_code == 403


class TestFilesAPIReadFile:
    """Tests for FilesAPI.read_file method"""

    def test_read_file_returns_content(self, storage, admin_user, db_session):
        """read_file should return file content"""
        from tools.file_manager.api.files import FilesAPI, FileReadRequest
        from sqlalchemy.orm import sessionmaker

        storage.write_file("readme.txt", "Hello World")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileReadRequest(path="readme.txt")
        result = api.read_file(request, user=admin_user)
        
        assert "content" in result
        assert result["content"] == "Hello World"
        assert result["path"] == "readme.txt"

    def test_read_file_not_found(self, storage, admin_user, db_session):
        """read_file should raise 404 for non-existent files"""
        from tools.file_manager.api.files import FilesAPI, FileReadRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileReadRequest(path="nonexistent.txt")
        
        with pytest.raises(HTTPException) as exc_info:
            api.read_file(request, user=admin_user)
        assert exc_info.value.status_code == 404


class TestFilesAPIWriteFile:
    """Tests for FilesAPI.write_file method"""

    def test_write_file_creates_file(self, storage, admin_user, db_session):
        """write_file should create a new file"""
        from tools.file_manager.api.files import FilesAPI, FileWriteRequest
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileWriteRequest(path="newfile.txt", content="new content")
        result = api.write_file(request, user=admin_user)
        
        assert result["name"] == "newfile.txt"
        # Verify file was actually created
        assert storage.read_file("newfile.txt") == "new content"

    def test_write_file_overwrites_existing(self, storage, admin_user, db_session):
        """write_file with overwrite=True should replace existing file"""
        from tools.file_manager.api.files import FilesAPI, FileWriteRequest
        from sqlalchemy.orm import sessionmaker

        storage.write_file("existing.txt", "original")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileWriteRequest(path="existing.txt", content="updated", overwrite=True)
        result = api.write_file(request, user=admin_user)
        
        assert storage.read_file("existing.txt") == "updated"


class TestFilesAPIDeleteFile:
    """Tests for FilesAPI.delete_file method"""

    def test_delete_file_removes_file(self, storage, admin_user, db_session):
        """delete_file should remove the specified file"""
        from tools.file_manager.api.files import FilesAPI, FileDeleteRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        storage.write_file("to_delete.txt", "content")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileDeleteRequest(path="to_delete.txt")
        result = api.delete_file(request, user=admin_user)
        
        assert "message" in result
        # Verify file was actually deleted
        # File should no longer exist after deletion
        from tools.file_manager.engine.storage import FileNotFoundError
        with pytest.raises(FileNotFoundError):
            storage.read_file("to_delete.txt")

    def test_delete_nonexistent_raises_404(self, storage, admin_user, db_session):
        """delete_file should raise 404 for non-existent files"""
        from tools.file_manager.api.files import FilesAPI, FileDeleteRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileDeleteRequest(path="does_not_exist.txt")
        
        with pytest.raises(HTTPException) as exc_info:
            api.delete_file(request, user=admin_user)
        assert exc_info.value.status_code == 404


class TestFilesAPICreateDirectory:
    """Tests for FilesAPI.create_directory method"""

    def test_create_directory_creates_dir(self, storage, admin_user, db_session):
        """create_directory should create a new directory"""
        from tools.file_manager.api.files import FilesAPI, MkDirRequest
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = MkDirRequest(path="newdir")
        result = api.create_directory(request, user=admin_user)
        
        assert result["name"] == "newdir"
        # Verify directory exists in storage
        stat = storage.get_stat("newdir")
        assert stat["type"] == "directory"

    def test_create_directory_already_exists_raises_409(self, storage, admin_user, db_session):
        """create_directory should raise 409 if directory already exists"""
        from tools.file_manager.api.files import FilesAPI, MkDirRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        storage.create_directory("existing_dir")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = MkDirRequest(path="existing_dir")
        
        with pytest.raises(HTTPException) as exc_info:
            api.create_directory(request, user=admin_user)
        assert exc_info.value.status_code == 409


class TestFilesAPICopyFile:
    """Tests for FilesAPI.copy_file method"""

    def test_copy_file_creates_copy(self, storage, admin_user, db_session):
        """copy_file should create a copy of the file"""
        from tools.file_manager.api.files import FilesAPI, FileCopyRequest
        from sqlalchemy.orm import sessionmaker

        storage.write_file("original.txt", "source content")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileCopyRequest(from_path="original.txt", to_path="copy.txt")
        result = api.copy_file(request, user=admin_user)
        
        assert result["name"] == "copy.txt"
        # Verify both files exist with correct content
        assert storage.read_file("original.txt") == "source content"
        assert storage.read_file("copy.txt") == "source content"

    def test_copy_file_source_not_found_raises_404(self, storage, admin_user, db_session):
        """copy_file should raise 404 if source file doesn't exist"""
        from tools.file_manager.api.files import FilesAPI, FileCopyRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileCopyRequest(from_path="nonexistent.txt", to_path="copy.txt")
        
        with pytest.raises(HTTPException) as exc_info:
            api.copy_file(request, user=admin_user)
        assert exc_info.value.status_code == 404


class TestFilesAPIMoveFile:
    """Tests for FilesAPI.move_file method"""

    def test_move_file_moves_file(self, storage, admin_user, db_session):
        """move_file should move/rename a file"""
        from tools.file_manager.api.files import FilesAPI, FileMoveRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        storage.write_file("source.txt", "moving content")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileMoveRequest(from_path="source.txt", to_path="moved.txt")
        result = api.move_file(request, user=admin_user)
        
        assert result["name"] == "moved.txt"
        # Verify file was moved (source no longer exists)
        assert storage.read_file("moved.txt") == "moving content"
        # Source file should no longer exist after move
        from tools.file_manager.engine.storage import FileNotFoundError
        with pytest.raises(FileNotFoundError):
            storage.read_file("source.txt")


class TestFilesAPIGetStat:
    """Tests for FilesAPI.get_stat method"""

    def test_get_stat_returns_metadata(self, storage, admin_user, db_session):
        """get_stat should return file/directory metadata"""
        from tools.file_manager.api.files import FilesAPI
        from sqlalchemy.orm import sessionmaker

        storage.write_file("stat_test.txt", "content")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        result = api.get_stat("stat_test.txt", user=admin_user)
        
        assert "name" in result
        assert result["name"] == "stat_test.txt"
        assert "size" in result or "is_file" in result or "is_directory" in result

    def test_get_stat_nonexistent_raises_404(self, storage, admin_user, db_session):
        """get_stat should raise 404 for non-existent paths"""
        from tools.file_manager.api.files import FilesAPI
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        with pytest.raises(HTTPException) as exc_info:
            api.get_stat("nonexistent.txt", user=admin_user)
        assert exc_info.value.status_code == 404


class TestFilesAPISearchFiles:
    """Tests for FilesAPI.search_files method"""

    def test_search_files_returns_matches(self, storage, admin_user, db_session):
        """search_files should return list of matching files"""
        from tools.file_manager.api.files import FilesAPI, FileSearchRequest
        from sqlalchemy.orm import sessionmaker

        storage.create_directory("searchdir")
        storage.write_file("searchdir/test.txt", "content")
        storage.write_file("searchdir/other.md", "content")
        
        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileSearchRequest(path="searchdir", pattern="*.txt", recursive=True)
        result = api.search_files(request, user=admin_user)
        
        assert isinstance(result, list)
        # Should find test.txt but not other.md
        if len(result) > 0:
            names = [item.get("name") for item in result]
            assert "test.txt" in names

    def test_search_files_nonexistent_path_raises_404(self, storage, admin_user, db_session):
        """search_files should raise 404 for non-existent search path"""
        from tools.file_manager.api.files import FilesAPI, FileSearchRequest
        from fastapi import HTTPException
        from sqlalchemy.orm import sessionmaker

        factory = sessionmaker(bind=db_session.get_bind())
        api = FilesAPI(storage, factory)
        
        request = FileSearchRequest(path="nonexistent_dir", pattern="*.txt")
        
        with pytest.raises(HTTPException) as exc_info:
            api.search_files(request, user=admin_user)
        assert exc_info.value.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
