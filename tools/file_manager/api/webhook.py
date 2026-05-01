"""
Webhook Publisher - File change event notifications
"""

from __future__ import annotations

import asyncio
import hashlib
import httpx
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
from enum import Enum

import sys
from pathlib import Path as PathType

_file_manager_dir = PathType(__file__).parent.parent
if str(_file_manager_dir) not in sys.path:
    sys.path.insert(0, str(_file_manager_dir))


logger = logging.getLogger(__name__)


class EventType(str, Enum):
    FILE_CREATED = "file.created"
    FILE_UPDATED = "file.updated"
    FILE_DELETED = "file.deleted"
    FILE_SHARED = "file.shared"


class WebhookEvent:
    """Webhook event payload"""

    def __init__(
        self,
        event: EventType,
        path: str,
        user: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.event = event
        self.path = path
        self.user = user
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event.value,
            "path": self.path,
            "user": self.user,
            "timestamp": self.timestamp,
            **self.metadata,
        }


class WebhookPublisher:
    """Publishes file change events to registered webhook subscribers"""

    def __init__(self):
        self._subscribers: List[Dict[str, Any]] = []
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def register(
        self,
        url: str,
        secret: Optional[str] = None,
        events: Optional[List[EventType]] = None,
        enabled: bool = True,
    ) -> str:
        """Register a webhook subscriber.

        Returns subscriber ID.
        """
        import uuid

        subscriber_id = str(uuid.uuid4())[:8]
        subscriber = {
            "id": subscriber_id,
            "url": url,
            "secret": secret,
            "events": events or list(EventType),
            "enabled": enabled,
        }
        self._subscribers.append(subscriber)
        logger.info(f"Registered webhook subscriber: {subscriber_id} -> {url}")
        return subscriber_id

    def unregister(self, subscriber_id: str) -> bool:
        """Unregister a webhook subscriber."""
        for i, sub in enumerate(self._subscribers):
            if sub["id"] == subscriber_id:
                self._subscribers.pop(i)
                logger.info(f"Unregistered webhook subscriber: {subscriber_id}")
                return True
        return False

    def list_subscribers(self) -> List[Dict[str, Any]]:
        """List all registered subscribers (without secrets)."""
        return [
            {
                "id": sub["id"],
                "url": sub["url"],
                "events": [e.value for e in sub["events"]],
                "enabled": sub["enabled"],
            }
            for sub in self._subscribers
        ]

    def publish(self, event: WebhookEvent) -> None:
        """Publish an event to the queue."""
        self._queue.put_nowait(event)

    async def start(self):
        """Start processing events."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Stop processing events."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _process_events(self):
        """Process events from queue and dispatch to subscribers."""
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing webhook event: {e}")

    async def _dispatch(self, event: WebhookEvent):
        """Dispatch event to all matching subscribers."""
        for sub in self._subscribers:
            if not sub["enabled"]:
                continue
            if event.event not in sub["events"]:
                continue

            try:
                await self._deliver(sub, event)
            except Exception as e:
                logger.error(f"Failed to deliver event to {sub['url']}: {e}")

    async def _deliver(self, subscriber: Dict[str, Any], event: WebhookEvent):
        """Deliver a single event to a subscriber."""
        payload = event.to_dict()

        headers = {"Content-Type": "application/json"}
        if subscriber.get("secret"):
            import hmac
            import json

            body = json.dumps(payload)
            signature = hmac.new(
                subscriber["secret"].encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                subscriber["url"],
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            logger.debug(f"Delivered {event.event.value} to {subscriber['url']}")


# Global webhook publisher instance
_publisher: Optional[WebhookPublisher] = None


def get_publisher() -> WebhookPublisher:
    """Get the global webhook publisher instance."""
    global _publisher
    if _publisher is None:
        _publisher = WebhookPublisher()
    return _publisher


async def init_publisher():
    """Initialize and start the global publisher."""
    publisher = get_publisher()
    await publisher.start()


async def shutdown_publisher():
    """Shutdown the global publisher."""
    global _publisher
    if _publisher:
        await _publisher.stop()


def publish_file_event(
    event_type: EventType,
    path: str,
    user: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Publish a file event."""
    event = WebhookEvent(event_type, path, user, metadata)
    publisher = get_publisher()
    publisher.publish(event)
