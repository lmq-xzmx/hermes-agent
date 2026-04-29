"""
Tests for Hermes File Manager - Share API
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import secrets
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, SharedLink, init_db, create_builtin_roles
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
    user = User(username="shareadmin", role=admin_role)
    user.set_password("pass")
    sess = db_session
    sess.add(user)
    sess.commit()
    return user


# =============================================================================
# SharedLink Creation
# =============================================================================

class TestSharedLinkCreation:
    def test_create_share_link_no_password(self, db_session, admin_user):
        link = SharedLink(
            path="/public/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        assert link.id is not None
        assert link.is_active is True
        assert link.access_count == 0

    def test_create_share_link_with_password(self, db_session, admin_user):
        link = SharedLink(
            path="/secret/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        link.set_password("secret123")
        db_session.add(link)
        db_session.commit()

        assert link.check_password("secret123") is True
        assert link.check_password("wrong") is False

    def test_create_share_link_with_expiry(self, db_session, admin_user):
        link = SharedLink(
            path="/temp/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        link.expires_at = datetime.utcnow() + timedelta(days=7)
        db_session.add(link)
        db_session.commit()

        assert link.is_expired() is False
        assert link.is_valid() is True

    def test_create_share_link_with_max_access(self, db_session, admin_user):
        link = SharedLink(
            path="/limited/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
            max_access_count=5,
        )
        db_session.add(link)
        db_session.commit()

        assert link.is_valid() is True
        assert link.access_count == 0


# =============================================================================
# SharedLink Validation
# =============================================================================

class TestSharedLinkValidation:
    def test_link_valid_when_all_conditions_met(self, db_session, admin_user):
        link = SharedLink(
            path="/valid/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        assert link.is_valid() is True

    def test_link_invalid_when_deactivated(self, db_session, admin_user):
        link = SharedLink(
            path="/deactivated/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        link.is_active = False
        db_session.add(link)
        db_session.commit()

        assert link.is_valid() is False

    def test_link_invalid_after_expiry(self, db_session, admin_user):
        link = SharedLink(
            path="/expired/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        link.expires_at = datetime.utcnow() - timedelta(hours=1)
        db_session.add(link)
        db_session.commit()

        assert link.is_expired() is True
        assert link.is_valid() is False

    def test_link_invalid_after_max_access_reached(self, db_session, admin_user):
        link = SharedLink(
            path="/maxed/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
            max_access_count=3,
            access_count=3,
        )
        db_session.add(link)
        db_session.commit()

        assert link.is_valid() is False


# =============================================================================
# Access Count Tracking
# =============================================================================

class TestAccessCount:
    def test_increment_access_count(self, db_session, admin_user):
        link = SharedLink(
            path="/count/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        initial = link.access_count
        link.access_count += 1
        db_session.commit()

        updated = db_session.query(SharedLink).filter(SharedLink.id == link.id).first()
        assert updated.access_count == initial + 1


# =============================================================================
# Serialization
# =============================================================================

class TestSerialization:
    def test_to_dict_excludes_token_by_default(self, db_session, admin_user):
        link = SharedLink(
            path="/serial/file.txt",
            token="my_secret_token_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        d = link.to_dict()
        assert "token" not in d
        assert d["path"] == "/serial/file.txt"
        assert d["permissions"] == "read"

    def test_to_dict_includes_token_when_requested(self, db_session, admin_user):
        link = SharedLink(
            path="/serial2/file.txt",
            token="another_secret_token",
            permissions="read_write",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        d = link.to_dict(include_token=True)
        assert d["token"] == "another_secret_token"

    def test_to_dict_includes_creator_username(self, db_session, admin_user):
        link = SharedLink(
            path="/creator/file.txt",
            token=secrets.token_urlsafe(16),
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        d = link.to_dict()
        assert d["created_by"] == "shareadmin"


# =============================================================================
# ShareAPI Tests
# =============================================================================

from unittest.mock import MagicMock, patch
from tools.file_manager.api.share import ShareAPI, CreateShareRequest, UpdateShareRequest


@pytest.fixture
def mock_storage():
    """Mock storage engine for ShareAPI tests"""
    storage = MagicMock()
    storage.permission_engine = MagicMock()
    storage.permission_engine.check_permission.return_value = MagicMock(allowed=True)
    storage.get_stat.return_value = {
        "name": "test.txt",
        "path": "/test/file.txt",
        "type": "file",
        "size": 100,
    }
    storage.list_directory.return_value = [
        {"name": "file1.txt", "path": "/test/file1.txt", "type": "file"},
        {"name": "subdir", "path": "/test/subdir", "type": "directory"},
    ]
    return storage


@pytest.fixture
def share_api(db_session, mock_storage):
    """Create ShareAPI instance with mocked storage"""
    Session = sessionmaker(bind=db_session.get_bind())
    return ShareAPI(Session, mock_storage)


class TestShareAPIListShareLinks:
    def test_list_share_links_returns_users_links(self, share_api, admin_user, db_session):
        """list_share_links should return all share links created by the user"""
        # Create some test links
        link1 = SharedLink(
            path="/files/doc1.txt",
            token="token_list_1",
            permissions="read",
            created_by=admin_user.id,
        )
        link2 = SharedLink(
            path="/files/doc2.txt",
            token="token_list_2",
            permissions="read_write",
            created_by=admin_user.id,
        )
        db_session.add_all([link1, link2])
        db_session.commit()

        result = share_api.list_share_links(admin_user)

        assert result["total"] == 2
        assert len(result["links"]) == 2

    def test_list_share_links_filter_by_path(self, share_api, admin_user, db_session):
        """list_share_links should filter by path when specified"""
        link1 = SharedLink(
            path="/specific/file.txt",
            token="token_specific_1",
            permissions="read",
            created_by=admin_user.id,
        )
        link2 = SharedLink(
            path="/other/file.txt",
            token="token_specific_2",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add_all([link1, link2])
        db_session.commit()

        result = share_api.list_share_links(admin_user, path="/specific/file.txt")

        assert result["total"] == 1
        assert result["links"][0]["path"] == "/specific/file.txt"

    def test_list_share_links_excludes_other_users_links(self, share_api, admin_user, db_session):
        """list_share_links should not return links created by other users"""
        other_user = User(username="otheruser")
        other_user.set_password("pass")
        db_session.add(other_user)

        link_self = SharedLink(
            path="/files/mine.txt",
            token="token_other_1",
            permissions="read",
            created_by=admin_user.id,
        )
        link_other = SharedLink(
            path="/files/theirs.txt",
            token="token_other_2",
            permissions="read",
            created_by=other_user.id,
        )
        db_session.add_all([link_self, link_other])
        db_session.commit()

        result = share_api.list_share_links(admin_user)

        assert result["total"] == 1
        assert result["links"][0]["path"] == "/files/mine.txt"


class TestShareAPIGetShareLink:
    def test_get_share_link_returns_link_info(self, share_api, admin_user, db_session):
        """get_share_link should return link info for valid token"""
        link = SharedLink(
            path="/get/link.txt",
            token="token_get_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        result = share_api.get_share_link("token_get_123")

        assert result["path"] == "/get/link.txt"
        assert result["permissions"] == "read"
        assert "token" not in result  # Should NOT include token by default

    def test_get_share_link_raises_404_for_invalid_token(self, share_api):
        """get_share_link should raise 404 for non-existent token"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.get_share_link("nonexistent_token")

        assert exc_info.value.status_code == 404


class TestShareAPIAccessShareLink:
    def test_access_share_link_increments_count(self, share_api, admin_user, db_session):
        """access_share_link should increment access_count"""
        link = SharedLink(
            path="/access/file.txt",
            token="token_access_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()
        initial_count = link.access_count

        result = share_api.access_share_link("token_access_123")

        assert result["path"] == "/access/file.txt"
        assert result["permissions"] == "read"
        # Access count should be incremented
        db_session.refresh(link)
        assert link.access_count == initial_count + 1

    def test_access_share_link_requires_password_when_set(self, share_api, admin_user, db_session):
        """access_share_link should require password when link has password_hash"""
        link = SharedLink(
            path="/access/password.txt",
            token="token_pwd_123",
            permissions="read",
            created_by=admin_user.id,
        )
        link.set_password("secret123")
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        # Without password
        with pytest.raises(HTTPException) as exc_info:
            share_api.access_share_link("token_pwd_123")

        assert exc_info.value.status_code == 401

    def test_access_share_link_validates_password(self, share_api, admin_user, db_session):
        """access_share_link should reject wrong password"""
        link = SharedLink(
            path="/access/wrongpwd.txt",
            token="token_wrongpwd_123",
            permissions="read",
            created_by=admin_user.id,
        )
        link.set_password("correct_password")
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.access_share_link("token_wrongpwd_123", password="wrong_password")

        assert exc_info.value.status_code == 401

    def test_access_share_link_rejects_expired_link(self, share_api, admin_user, db_session):
        """access_share_link should reject expired links"""
        link = SharedLink(
            path="/access/expired.txt",
            token="token_expired_123",
            permissions="read",
            created_by=admin_user.id,
        )
        link.expires_at = datetime.utcnow() - timedelta(days=1)
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.access_share_link("token_expired_123")

        assert exc_info.value.status_code == 403

    def test_access_share_link_rejects_deactivated_link(self, share_api, admin_user, db_session):
        """access_share_link should reject deactivated links"""
        link = SharedLink(
            path="/access/deactivated.txt",
            token="token_deact_123",
            permissions="read",
            created_by=admin_user.id,
        )
        link.is_active = False
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.access_share_link("token_deact_123")

        assert exc_info.value.status_code == 403


class TestShareAPIAccessShareContent:
    def test_access_share_content_returns_directory_listing(self, share_api, admin_user, db_session):
        """access_share_content should return directory listing for valid link"""
        link = SharedLink(
            path="/content/dir",
            token="token_content_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        result = share_api.access_share_content("token_content_123")

        assert result["path"] == "/content/dir"
        assert result["permissions"] == "read"
        assert "items" in result


class TestShareAPIUpdateShareLink:
    def test_update_share_link_changes_permissions(self, share_api, admin_user, db_session):
        """update_share_link should update permissions"""
        link = SharedLink(
            path="/update/file.txt",
            token="token_update_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        request = UpdateShareRequest(permissions="read_write")
        result = share_api.update_share_link("token_update_123", request, admin_user)

        assert result["permissions"] == "read_write"

    def test_update_share_link_sets_expiry(self, share_api, admin_user, db_session):
        """update_share_link should update expiration"""
        link = SharedLink(
            path="/update/expiry.txt",
            token="token_update_expiry",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        request = UpdateShareRequest(expires_in_days=30)
        result = share_api.update_share_link("token_update_expiry", request, admin_user)

        assert result["expires_at"] is not None

    def test_update_share_link_deactivates_link(self, share_api, admin_user, db_session):
        """update_share_link should allow deactivating a link"""
        link = SharedLink(
            path="/update/deact.txt",
            token="token_deact_link",
            permissions="read",
            created_by=admin_user.id,
        )
        link.is_active = True
        db_session.add(link)
        db_session.commit()

        request = UpdateShareRequest(is_active=False)
        result = share_api.update_share_link("token_deact_link", request, admin_user)

        assert result["is_active"] is False

    def test_update_share_link_requires_ownership(self, share_api, admin_user, db_session):
        """update_share_link should deny updates from non-owners"""
        other_user = User(username="notowner")
        other_user.set_password("pass")
        db_session.add(other_user)

        link = SharedLink(
            path="/update/owned.txt",
            token="token_owned_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        request = UpdateShareRequest(permissions="read_write")
        with pytest.raises(HTTPException) as exc_info:
            share_api.update_share_link("token_owned_123", request, other_user)

        assert exc_info.value.status_code == 403


class TestShareAPIDeleteShareLink:
    def test_delete_share_link_removes_link(self, share_api, admin_user, db_session):
        """delete_share_link should remove the share link"""
        link = SharedLink(
            path="/delete/file.txt",
            token="token_delete_123",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        result = share_api.delete_share_link("token_delete_123", admin_user)

        assert result["message"] == "Share link deleted"
        # Verify link is deleted from DB
        deleted = db_session.query(SharedLink).filter(SharedLink.token == "token_delete_123").first()
        assert deleted is None

    def test_delete_share_link_requires_ownership(self, share_api, admin_user, db_session):
        """delete_share_link should deny deletion from non-owners"""
        other_user = User(username="notdeleter")
        other_user.set_password("pass")
        db_session.add(other_user)

        link = SharedLink(
            path="/delete/owned.txt",
            token="token_del_owned",
            permissions="read",
            created_by=admin_user.id,
        )
        db_session.add(link)
        db_session.commit()

        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.delete_share_link("token_del_owned", other_user)

        assert exc_info.value.status_code == 403

    def test_delete_share_link_404_for_invalid_token(self, share_api, admin_user):
        """delete_share_link should raise 404 for non-existent token"""
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            share_api.delete_share_link("nonexistent_delete_token", admin_user)

        assert exc_info.value.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
