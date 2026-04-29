"""
Event Bus - Decouples audit logging from business logic.

Publishers (services) emit events without knowing who consumes them.
Consumers (audit, analytics, notifications) subscribe to events.

Usage:
    bus = EventBus()
    bus.subscribe(EventType.FILE_READ, my_audit_handler)
    bus.publish(EventType.FILE_READ, {"path": "/docs/readme.txt", ...})
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Dict, List, Any, Optional
from queue import Queue, Empty

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    # Auth events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_REGISTER = "auth.register"
    AUTH_TOKEN_REFRESH = "auth.token_refresh"

    # File events
    FILE_LIST = "file.list"
    FILE_READ = "file.read"
    FILE_WRITE = "file.write"
    FILE_DELETE = "file.delete"
    FILE_CREATE_DIR = "file.create_dir"
    FILE_COPY = "file.copy"
    FILE_MOVE = "file.move"

    # Share events
    SHARE_CREATE = "share.create"
    SHARE_ACCESS = "share.access"

    # Admin events
    ADMIN_USER_CREATE = "admin.user_create"
    ADMIN_USER_UPDATE = "admin.user_update"
    ADMIN_USER_DELETE = "admin.user_delete"
    ADMIN_ROLE_UPDATE = "admin.role_update"


@dataclass
class Event:
    """Immutable event published to the bus."""
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, type: EventType, data: Dict[str, Any], **metadata) -> Event:
        return cls(type=type, timestamp=datetime.utcnow(), data=data, metadata=metadata)


# =============================================================================
# In-process synchronous EventBus (single-process server)
# =============================================================================

class EventBus:
    """
    Thread-safe in-process event bus using a simple observer pattern.

    For multi-process or distributed scenarios, replace this with
    Redis pub/sub, Kafka, etc. by implementing the same interface.
    """

    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Register a handler for an event type."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed handler to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Remove a handler."""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]

    def publish(self, event: Event) -> None:
        """
        Publish an event to all registered handlers synchronously.
        Errors in handlers are logged but do not stop other handlers.
        """
        handlers = []
        with self._lock:
            handlers = list(self._handlers.get(event.type, []))

        for handler in handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.exception(f"Event handler error for {event.type.value}: {exc}")


# =============================================================================
# Default global bus instance (created once at startup)
# =============================================================================

_default_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    """Return the shared global EventBus instance."""
    global _default_bus
    if _default_bus is None:
        _default_bus = EventBus()
    return _default_bus
