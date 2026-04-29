"""
AuditEventSubscriber - Consumes events from EventBus and persists audit logs.

Registered at startup. Decoupled from business logic entirely via event bus.
"""

from __future__ import annotations

import logging
from typing import Optional

from .event_bus import EventBus, EventType, Event, get_event_bus

logger = logging.getLogger(__name__)


class AuditEventSubscriber:
    """
    Subscribes to the global EventBus and writes audit records to the database.
    This is the only place where audit DB writes happen — all other code
    emits events and never touches the AuditLog table directly.
    """

    def __init__(self, db_factory, event_bus: Optional[EventBus] = None):
        self._db_factory = db_factory
        self._bus = event_bus or get_event_bus()
        self._handlers = {
            EventType.AUTH_LOGIN_SUCCESS: self._on_login_success,
            EventType.AUTH_LOGIN_FAILED: self._on_login_failed,
            EventType.AUTH_REGISTER: self._on_register,
            EventType.AUTH_LOGOUT: self._on_logout,
            EventType.AUTH_TOKEN_REFRESH: self._on_token_refresh,
            EventType.FILE_LIST: self._on_file_op,
            EventType.FILE_READ: self._on_file_op,
            EventType.FILE_WRITE: self._on_file_op,
            EventType.FILE_DELETE: self._on_file_op,
            EventType.FILE_CREATE_DIR: self._on_file_op,
            EventType.FILE_COPY: self._on_file_op,
            EventType.FILE_MOVE: self._on_file_op,
            EventType.SHARE_CREATE: self._on_file_op,
            EventType.SHARE_ACCESS: self._on_file_op,
        }

    def register(self) -> None:
        """Subscribe to all relevant event types."""
        for event_type, handler in self._handlers.items():
            self._bus.subscribe(event_type, handler)
        logger.info("AuditEventSubscriber registered")

    # -------------------------------------------------------------------------
    # Handlers
    # -------------------------------------------------------------------------

    def _on_login_success(self, event: Event) -> None:
        self._write(event, result="success", action="auth.login")

    def _on_login_failed(self, event: Event) -> None:
        self._write(event, result="denied", action="auth.login_failed")

    def _on_register(self, event: Event) -> None:
        self._write(event, result="success", action="auth.register")

    def _on_logout(self, event: Event) -> None:
        self._write(event, result="success", action="auth.logout")

    def _on_token_refresh(self, event: Event) -> None:
        self._write(event, result="success", action="auth.token_refresh")

    def _on_file_op(self, event: Event) -> None:
        # Map event type to action string
        action_map = {
            EventType.FILE_LIST: "file.list",
            EventType.FILE_READ: "file.read",
            EventType.FILE_WRITE: "file.write",
            EventType.FILE_DELETE: "file.delete",
            EventType.FILE_CREATE_DIR: "file.create_dir",
            EventType.FILE_COPY: "file.copy",
            EventType.FILE_MOVE: "file.move",
            EventType.SHARE_CREATE: "share.create",
            EventType.SHARE_ACCESS: "share.access",
        }
        action = action_map.get(event.type, event.type.value)
        self._write(event, result="success", action=action)

    # -------------------------------------------------------------------------
    # DB write
    # -------------------------------------------------------------------------

    def _write(
        self,
        event: Event,
        result: str,
        action: str,
    ) -> None:
        try:
            session = self._db_factory()
            try:
                from ..engine.models import AuditLog, AuditAction
                # Resolve AuditAction enum value
                try:
                    audit_action = AuditAction(audit_action_map.get(action, action))
                except ValueError:
                    audit_action = AuditAction.OTHER

                log_entry = AuditLog(
                    action=audit_action.value,  # String column, not Enum
                    result=result,
                    user_id=event.metadata.get("user_id"),
                    path=event.data.get("path"),
                    ip_address=event.data.get("ip_address"),
                    user_agent=event.data.get("user_agent"),
                    extra=event.data,
                )
                session.add(log_entry)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()
        except Exception:
            # Never let audit failures break business logic
            logger.exception(f"Failed to write audit log for {action}")


# Map event action strings to AuditAction enum values
audit_action_map = {
    "auth.login": "auth_login",
    "auth.login_failed": "auth_login",
    "auth.register": "auth_register",
    "auth.logout": "auth_logout",
    "auth.token_refresh": "auth_login",
    "file.list": "file_list",
    "file.read": "file_read",
    "file.write": "file_write",
    "file.delete": "file_delete",
    "file.create_dir": "file_create",
    "file.copy": "file_copy",
    "file.move": "file_move",
    "share.create": "file_share",
    "share.access": "file_share",
}
