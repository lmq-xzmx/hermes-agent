"""
WebSocket endpoint for real-time admin analytics updates.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for admin analytics."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


class AnalyticsBroadcaster:
    """
    Broadcasts analytics updates to connected WebSocket clients.

    Updates are triggered by:
    - Periodic timer (configurable interval)
    - EventBus events (quota warnings, alerts)
    """

    def __init__(self, manager: ConnectionManager, db_factory, event_bus):
        self._manager = manager
        self._db_factory = db_factory
        self._event_bus = event_bus
        self._broadcast_interval = 30  # seconds
        self._running = False
        self._task = None

    async def start(self):
        """Start the broadcaster."""
        self._running = True
        self._task = asyncio.create_task(self._broadcast_loop())

        # Subscribe to EventBus events
        from file_manager.services.event_bus import EventType, Event
        self._event_bus.subscribe(EventType.QUOTA_WARNING, self._on_quota_warning)
        self._event_bus.subscribe(EventType.LIFECYCLE_VIOLATION, self._on_lifecycle_violation)

        logger.info("Analytics broadcaster started")

    async def stop(self):
        """Stop the broadcaster."""
        self._running = False
        if self._task:
            self._task.cancel()
        logger.info("Analytics broadcaster stopped")

    async def _broadcast_loop(self):
        """Periodic broadcast loop."""
        while self._running:
            try:
                await asyncio.sleep(self._broadcast_interval)
                await self._broadcast_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in broadcast loop: {e}")

    async def _broadcast_update(self):
        """Fetch and broadcast current analytics state."""
        if not self._manager.active_connections:
            return

        try:
            overview = await self._fetch_overview()
            alerts = await self._fetch_alerts()

            message = {
                "type": "analytics_update",
                "data": {
                    "overview": overview,
                    "alerts": alerts
                },
                "timestamp": self._get_timestamp()
            }

            await self._manager.broadcast(message)
            logger.debug("Broadcasted analytics update")

        except Exception as e:
            logger.exception(f"Error broadcasting update: {e}")

    async def _fetch_overview(self):
        """Fetch overview data for broadcast."""
        from datetime import datetime, timedelta
        from ..engine.models import User, Space, StoragePool, AuditLog

        session = self._db_factory()
        try:
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)

            total_users = session.query(User).count()
            active_users_7d = session.query(AuditLog.user_id).filter(
                AuditLog.created_at >= seven_days_ago,
                AuditLog.user_id.isnot(None)
            ).distinct().count()
            new_users_7d = session.query(User).filter(
                User.created_at >= seven_days_ago
            ).count()

            total_teams = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active"
            ).count()
            total_spaces = session.query(Space).filter(
                Space.status == "active"
            ).count()

            pools = session.query(StoragePool).filter(StoragePool.is_active == True).all()
            total_bytes = sum(p.total_bytes for p in pools)
            used_bytes = sum(p.total_bytes - p.free_bytes for p in pools)

            return {
                "total_users": total_users,
                "active_users_7d": active_users_7d,
                "new_users_7d": new_users_7d,
                "total_teams": total_teams,
                "total_spaces": total_spaces,
                "total_pools": len(pools),
                "storage": {
                    "total_bytes": total_bytes,
                    "used_bytes": used_bytes,
                    "free_bytes": sum(p.free_bytes for p in pools),
                    "usage_rate": round(used_bytes / total_bytes, 4) if total_bytes > 0 else 0
                }
            }
        finally:
            session.close()

    async def _fetch_alerts(self):
        """Fetch current alerts for broadcast."""
        from datetime import datetime
        from ..engine.models import Space

        session = self._db_factory()
        try:
            spaces = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active",
                Space.max_bytes > 0
            ).all()

            alerts = []
            for space in spaces:
                usage_rate = space.used_bytes / space.max_bytes
                if usage_rate > 0.8:
                    alerts.append({
                        "id": f"alert_{space.id}",
                        "type": "quota_warning",
                        "level": "critical" if usage_rate > 0.9 else "warning",
                        "resource": "Space",
                        "resource_id": space.id,
                        "resource_name": space.name,
                        "usage_rate": round(usage_rate, 4),
                        "message": f"空间配额使用率超过{int(usage_rate * 100)}%",
                        "created_at": datetime.utcnow().isoformat()
                    })

            alerts.sort(key=lambda x: x["usage_rate"], reverse=True)
            return alerts[:10]
        finally:
            session.close()

    def _get_timestamp(self):
        from datetime import datetime
        return datetime.utcnow().isoformat()

    async def _on_quota_warning(self, event):
        """Handle QUOTA_WARNING event from EventBus."""
        try:
            data = event.data
            alert = {
                "type": "quota_warning",
                "data": {
                    "space_id": data.get("space_id"),
                    "space_name": data.get("space_name"),
                    "usage_rate": data.get("usage_rate"),
                    "message": f"空间配额使用率超过{int(data.get('usage_rate', 0) * 100)}%"
                },
                "timestamp": self._get_timestamp()
            }
            await self._manager.broadcast(alert)
        except Exception as e:
            logger.exception(f"Error broadcasting quota warning: {e}")

    async def _on_lifecycle_violation(self, event):
        """Handle LIFECYCLE_VIOLATION event from EventBus."""
        try:
            data = event.data
            message = {
                "type": "lifecycle_violation",
                "data": {
                    "code": data.get("code"),
                    "message": data.get("message")
                },
                "timestamp": self._get_timestamp()
            }
            await self._manager.broadcast(message)
        except Exception as e:
            logger.exception(f"Error broadcasting lifecycle violation: {e}")

    async def broadcast_alert(self, alert: Dict):
        """Broadcast a single alert immediately."""
        message = {
            "type": "alert",
            "data": alert,
            "timestamp": self._get_timestamp()
        }
        await self._manager.broadcast(message)


# WebSocket endpoint handler
async def websocket_admin_analytics(websocket: WebSocket, token: str):
    """
    WebSocket endpoint for admin analytics real-time updates.

    Query params:
        token: Authentication token

    Message types sent to client:
    - analytics_update: Periodic analytics state update
    - alert: Real-time alert notification
    - quota_update: Quota usage change notification
    """
    # Import auth_service from server's global instances
    from ..server import _api_instances

    try:
        # Verify token using AuthService
        auth_service = _api_instances.get("auth_service")
        if not auth_service:
            logger.error("AuthService not initialized")
            await websocket.close(code=4001, reason="Server error")
            return

        user_ctx = auth_service.get_user_from_token(token)
        if not user_ctx or user_ctx.role_name != 'admin':
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except ValueError as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=4001, reason="Invalid token")
        return
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        await websocket.close(code=4001, reason="Server error")
        return

    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        while True:
            # Keep connection alive, handle client messages
            data = await websocket.receive_text()

            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.exception(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Global connection manager
_connection_manager: ConnectionManager = None


def get_connection_manager() -> ConnectionManager:
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager