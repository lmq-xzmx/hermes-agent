"""
ShareService - Pure business logic for share link operations.

No FastAPI, no ORM. Uses PermissionChecker (primitives) and StorageEngine.
Emits events to EventBus for audit logging.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from passlib.hash import bcrypt

from .permission_checker import PermissionChecker, PermissionContext, Operation
from .event_bus import EventBus, EventType, Event, get_event_bus
from ..api.dto import (
    CreateShareRequestDTO,
    ShareLinkResponseDTO,
)
from ..engine.storage import StorageEngine, FileNotFoundError


# =============================================================================
# Service Errors (pure domain errors, not HTTP)
# =============================================================================

class ShareNotFound(Exception):
    """Share link not found."""
    pass


class ShareAccessDenied(Exception):
    """Permission denied for share operation."""
    pass


class ShareExpired(Exception):
    """Share link has expired."""
    pass


class ShareDeactivated(Exception):
    """Share link has been deactivated."""
    pass


class ShareLimitReached(Exception):
    """Share link access limit reached."""
    pass


class SharePasswordRequired(Exception):
    """Share link requires password."""
    pass


class ShareInvalidPassword(Exception):
    """Invalid password for share link."""
    pass


class ShareValidationError(Exception):
    """Share validation error (e.g., invalid permissions)."""
    pass


# =============================================================================
# ShareService
# =============================================================================

class ShareService:
    """
    Share link business logic. Stateless.

    Flow:
      API route (thin HTTP) → ShareService (pure logic) → StorageEngine (I/O)

    ShareService:
      - Converts AuthenticatedUser → PermissionContext (primitives)
      - Calls PermissionChecker (pure logic) for auth decisions
      - Calls StorageEngine for actual filesystem operations
      - Emits events to EventBus for audit/analytics
    """

    def __init__(
        self,
        db_factory,
        storage: StorageEngine,
        permission_checker: PermissionChecker,
        event_bus: Optional[EventBus] = None,
    ):
        self.db_factory = db_factory
        self.storage = storage
        self._checker = permission_checker
        self._event_bus = event_bus or get_event_bus()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def create_share_link(
        self,
        request: CreateShareRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> ShareLinkResponseDTO:
        """
        Create a share link for a file/directory.
        Raises ShareAccessDenied / ShareValidationError.
        """
        # Check user has at least read access to the path
        decision = self._checker.check(Operation.READ, request.path, user_ctx)
        if not decision.allowed:
            self._publish_denied("share.create", request.path, user_ctx, ip_address)
            raise ShareAccessDenied(f"No access to path: {request.path}")

        # Verify path exists
        try:
            self.storage.get_stat(request.path)
        except FileNotFoundError:
            raise ShareValidationError(f"Path not found: {request.path}")

        # Validate permissions
        if request.permissions not in ("read", "read_write"):
            raise ShareValidationError("permissions must be 'read' or 'read_write'")

        # Generate unique token
        token = secrets.token_urlsafe(32)

        # Hash password if provided
        password_hash = None
        if request.password:
            password_hash = bcrypt.hash(request.password, rounds=12)

        # Calculate expiration
        expires_at = None
        if request.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)

        # Build response (token is only returned on create)
        response = ShareLinkResponseDTO(
            token=token,
            path=request.path,
            permissions=request.permissions,
            has_password=request.password is not None,
            expires_at=expires_at,
            max_access_count=request.max_access_count,
            access_count=0,
            created_at=datetime.utcnow(),
            created_by=user_ctx.user_id,
        )

        # Publish event
        self._event_bus.publish(Event.create(
            EventType.SHARE_CREATE,
            {
                "path": request.path,
                "permissions": request.permissions,
                "has_password": request.password is not None,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "max_access_count": request.max_access_count,
                "ip_address": ip_address,
            },
            user_id=user_ctx.user_id,
            username=user_ctx.username,
        ))

        return response

    def list_share_links(
        self,
        user_ctx: PermissionContext,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        List share links created by user.
        Returns dict with 'links' list and 'total' count.
        Note: This is a simplified version - full implementation would query DB.
        """
        # For now, return empty list since share links are stored in DB
        # In a full implementation, this would use db_factory to query
        return {
            "links": [],
            "total": 0,
        }

    def get_share_link(
        self,
        token: str,
    ) -> ShareLinkResponseDTO:
        """
        Get share link info (without sensitive data like password hash).
        Note: This requires DB access - full implementation would query db_factory.
        """
        # Placeholder - in full implementation, would query DB
        # This method exists to maintain the API contract
        raise ShareNotFound(f"Share link not found: {token}")

    def access_share_link(
        self,
        token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Access a share link - verify validity and return file info.
        Raises ShareNotFound / ShareDeactivated / ShareExpired / ShareLimitReached /
               SharePasswordRequired / ShareInvalidPassword.
        """
        # In full implementation, would query DB for link
        # For now, raise not found
        raise ShareNotFound(f"Share link not found: {token}")

    def access_share_content(
        self,
        token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get content listing for a share link.
        Raises ShareNotFound / ShareDeactivated / ShareExpired /
               SharePasswordRequired / ShareInvalidPassword.
        """
        # In full implementation, would query DB for link
        raise ShareNotFound(f"Share link not found: {token}")

    def update_share_link(
        self,
        token: str,
        request: Dict[str, Any],
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> ShareLinkResponseDTO:
        """
        Update share link settings.
        Raises ShareNotFound / ShareAccessDenied / ShareValidationError.
        """
        # In full implementation, would query DB for link and verify ownership
        raise ShareNotFound(f"Share link not found: {token}")

    def delete_share_link(
        self,
        token: str,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Delete a share link.
        Raises ShareNotFound / ShareAccessDenied.
        """
        # In full implementation, would query DB for link and verify ownership
        raise ShareNotFound(f"Share link not found: {token}")

    # -------------------------------------------------------------------------
    # Internal helpers (for full implementation with DB)
    # -------------------------------------------------------------------------

    def _validate_share_link(
        self,
        link: Any,
        password: Optional[str] = None,
    ) -> None:
        """
        Validate a share link's state.
        Raises appropriate exceptions if invalid.
        """
        if not link.is_active:
            raise ShareDeactivated("Share link has been deactivated")

        if link.is_expired():
            raise ShareExpired("Share link has expired")

        if link.max_access_count and link.access_count >= link.max_access_count:
            raise ShareLimitReached("Share link access limit reached")

        # Check password
        if link.password_hash:
            if not password:
                raise SharePasswordRequired("Password required")
            if not bcrypt.verify(password, link.password_hash):
                raise ShareInvalidPassword("Invalid password")

    def _is_owner_or_admin(self, link: Any, user_ctx: PermissionContext) -> bool:
        """Check if user is the owner of the share link or an admin."""
        if link.created_by == user_ctx.user_id:
            return True
        if user_ctx.role_name == "admin":
            return True
        return False

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _publish_denied(
        self,
        operation: str,
        path: str,
        ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> None:
        self._event_bus.publish(Event.create(
            EventType.SHARE_ACCESS,
            {"operation": operation, "path": path, "reason": "denied", "ip_address": ip_address},
            user_id=ctx.user_id,
            username=ctx.username,
        ))
