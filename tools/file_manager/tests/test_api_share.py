"""
Tests for Hermes File Manager - Share Service
Tests ShareService with mocked dependencies (permission_checker, storage, event_bus)
Tests ORM SharedLink model directly where appropriate.
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
from tools.file_manager.engine.storage import FileNotFoundError
from tools.file_manager.services.share_service import (
    ShareService, ShareAccessDenied, ShareNotFound, ShareExpired,
    ShareDeactivated, ShareLimitReached, SharePasswordRequired,
    ShareInvalidPassword, ShareValidationError
)
from tools.file_manager.services.permission_context import PermissionContext
from tools.file_manager.services.permission_checker import PermissionChecker, PermissionDecision, Operation
from tools.file_manager.api.dto import CreateShareRequestDTO, ShareLinkResponseDTO
from unittest.mock import MagicMock


# =============================================================================
# ORM Model Test Fixtures (SharedLink tests)
# =============================================================================

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
# ShareService Test Fixtures
# =============================================================================

@pytest.fixture
def mock_storage():
    """Mock storage engine for ShareService tests"""
    storage = MagicMock()
    storage.get_stat.return_value = MagicMock(
        name="test.txt",
        path="/test/file.txt",
        type="file",
        size=100,
    )
    return storage


@pytest.fixture
def mock_permission_checker():
    """Mock permission checker for ShareService tests"""
    checker = MagicMock(spec=PermissionChecker)
    checker.check.return_value = PermissionDecision(allowed=True, reason="ok")
    return checker


@pytest.fixture
def mock_event_bus():
    """Mock event bus for ShareService tests"""
    bus = MagicMock()
    bus.publish.return_value = None
    return bus


@pytest.fixture
def share_service(db_session, mock_storage, mock_permission_checker, mock_event_bus):
    """Create ShareService instance with mocked dependencies"""
    return ShareService(
        db_factory=db_session,
        storage=mock_storage,
        permission_checker=mock_permission_checker,
        event_bus=mock_event_bus,
    )


@pytest.fixture
def admin_ctx():
    """PermissionContext for admin user"""
    return PermissionContext(
        user_id="admin-uid",
        username="admin",
        role_name="admin",
        permission_rules=["read,write:/**"],
    )


@pytest.fixture
def user_ctx():
    """PermissionContext for regular user"""
    return PermissionContext(
        user_id="user-uid",
        username="user",
        role_name="viewer",
        permission_rules=["read:/public/**"],
    )


# =============================================================================
# SharedLink ORM Creation Tests (test SharedLink model directly)
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
# SharedLink ORM Validation Tests (test SharedLink model directly)
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
# Access Count ORM Tests (test SharedLink model directly)
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
# Serialization ORM Tests (test SharedLink.to_dict directly)
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
# ShareService Tests (test ShareService with mocked dependencies)
# =============================================================================

class TestShareServiceCreateShareLink:
    def test_create_share_link_success_admin(self, share_service, admin_ctx):
        """Admin user can create share links (admin bypasses permission check)"""
        request = CreateShareRequestDTO(path="/test/file.txt", permissions="read")

        result = share_service.create_share_link(request, admin_ctx)

        assert result.path == "/test/file.txt"
        assert result.permissions == "read"
        assert result.token is not None
        assert len(result.token) > 0
        assert result.has_password is False
        assert result.access_count == 0

    def test_create_share_link_success_with_permission(self, share_service, user_ctx, mock_permission_checker):
        """Non-admin user with permission can create share links"""
        mock_permission_checker.check.return_value = PermissionDecision(
            allowed=True, reason="Allowed by rule '/**'"
        )
        request = CreateShareRequestDTO(path="/public/file.txt", permissions="read")

        result = share_service.create_share_link(request, user_ctx)

        assert result.path == "/public/file.txt"
        assert result.permissions == "read"

    def test_create_share_link_with_password(self, share_service, admin_ctx):
        """Share link with password is created correctly"""
        request = CreateShareRequestDTO(
            path="/secret/file.txt",
            permissions="read",
            password="secret123"
        )

        result = share_service.create_share_link(request, admin_ctx)

        assert result.path == "/secret/file.txt"
        assert result.has_password is True

    def test_create_share_link_with_expiry(self, share_service, admin_ctx):
        """Share link with expiration is created correctly"""
        request = CreateShareRequestDTO(
            path="/temp/file.txt",
            permissions="read",
            expires_in_days=7
        )

        result = share_service.create_share_link(request, admin_ctx)

        assert result.expires_at is not None
        assert result.expires_at > datetime.utcnow()

    def test_create_share_link_with_max_access(self, share_service, admin_ctx):
        """Share link with max access count is created correctly"""
        request = CreateShareRequestDTO(
            path="/limited/file.txt",
            permissions="read",
            max_access_count=5
        )

        result = share_service.create_share_link(request, admin_ctx)

        assert result.max_access_count == 5

    def test_create_share_link_denied_no_permission(self, share_service, user_ctx, mock_permission_checker):
        """User without permission to path gets ShareAccessDenied"""
        mock_permission_checker.check.return_value = PermissionDecision(
            allowed=False, reason="No rule matches path '/secret/**'"
        )
        request = CreateShareRequestDTO(path="/secret/file.txt", permissions="read")

        with pytest.raises(ShareAccessDenied) as exc_info:
            share_service.create_share_link(request, user_ctx)

        assert "No access to path" in str(exc_info.value)

    def test_create_share_link_invalid_permissions(self, share_service, admin_ctx):
        """Invalid permissions value raises ShareValidationError"""
        request = CreateShareRequestDTO(path="/test/file.txt", permissions="admin_only")

        with pytest.raises(ShareValidationError) as exc_info:
            share_service.create_share_link(request, admin_ctx)

        assert "permissions must be 'read' or 'read_write'" in str(exc_info.value)

    def test_create_share_link_path_not_found(self, share_service, admin_ctx, mock_storage):
        """Non-existent path raises ShareValidationError"""
        mock_storage.get_stat.side_effect = FileNotFoundError("Path not found")
        request = CreateShareRequestDTO(path="/nonexistent/file.txt", permissions="read")

        with pytest.raises(ShareValidationError) as exc_info:
            share_service.create_share_link(request, admin_ctx)

        assert "Path not found" in str(exc_info.value)

    def test_create_share_link_publishes_event(self, share_service, admin_ctx, mock_event_bus):
        """Creating share link publishes event to event bus"""
        request = CreateShareRequestDTO(path="/event/file.txt", permissions="read")

        share_service.create_share_link(request, admin_ctx)

        mock_event_bus.publish.assert_called_once()


class TestShareServiceListShareLinks:
    def test_list_share_links_returns_empty_placeholder(self, share_service, admin_ctx):
        """list_share_links returns empty list (placeholder implementation)"""
        result = share_service.list_share_links(admin_ctx)

        assert result["total"] == 0
        assert result["links"] == []

    def test_list_share_links_with_path_filter(self, share_service, admin_ctx):
        """list_share_links accepts path filter (placeholder returns empty)"""
        result = share_service.list_share_links(admin_ctx, path="/specific/path")

        assert result["total"] == 0
        assert result["links"] == []


class TestShareServiceGetShareLink:
    def test_get_share_link_raises_not_found(self, share_service):
        """get_share_link raises ShareNotFound (placeholder implementation)"""
        with pytest.raises(ShareNotFound):
            share_service.get_share_link("nonexistent_token")


class TestShareServiceAccessShareLink:
    def test_access_share_link_raises_not_found(self, share_service):
        """access_share_link raises ShareNotFound (placeholder implementation)"""
        with pytest.raises(ShareNotFound):
            share_service.access_share_link("nonexistent_token")


class TestShareServiceAccessShareContent:
    def test_access_share_content_raises_not_found(self, share_service):
        """access_share_content raises ShareNotFound (placeholder implementation)"""
        with pytest.raises(ShareNotFound):
            share_service.access_share_content("nonexistent_token")


class TestShareServiceUpdateShareLink:
    def test_update_share_link_raises_not_found(self, share_service, admin_ctx):
        """update_share_link raises ShareNotFound (placeholder implementation)"""
        with pytest.raises(ShareNotFound):
            share_service.update_share_link("nonexistent_token", {}, admin_ctx)


class TestShareServiceDeleteShareLink:
    def test_delete_share_link_raises_not_found(self, share_service, admin_ctx):
        """delete_share_link raises ShareNotFound (placeholder implementation)"""
        with pytest.raises(ShareNotFound):
            share_service.delete_share_link("nonexistent_token", admin_ctx)


# =============================================================================
# ShareService Permission Integration Tests
# =============================================================================

class TestShareServicePermissionIntegration:
    def test_admin_bypasses_permission_check(self, share_service, admin_ctx, mock_permission_checker):
        """Admin role bypasses permission checker - check is still called but admin always allowed"""
        request = CreateShareRequestDTO(path="/any/path.txt", permissions="read")

        result = share_service.create_share_link(request, admin_ctx)

        # Permission check was called
        mock_permission_checker.check.assert_called_once_with(
            Operation.READ, "/any/path.txt", admin_ctx
        )
        # But admin is allowed through
        assert result.path == "/any/path.txt"

    def test_permission_denied_publishes_denied_event(self, share_service, user_ctx, mock_permission_checker, mock_event_bus):
        """When permission is denied, a denied event is published"""
        mock_permission_checker.check.return_value = PermissionDecision(
            allowed=False, reason="Access denied"
        )
        request = CreateShareRequestDTO(path="/denied/file.txt", permissions="read")

        with pytest.raises(ShareAccessDenied):
            share_service.create_share_link(request, user_ctx)

        # Event should be published on denial
        mock_event_bus.publish.assert_called()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
