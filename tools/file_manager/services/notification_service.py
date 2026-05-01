"""
NotificationService - In-app notification management for quota warnings, invites, etc.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from ..engine.models import Notification, Space


# =============================================================================
# Domain Errors
# =============================================================================

class NotificationNotFound(Exception):
    """Notification not found."""
    pass


# =============================================================================
# NotificationService
# =============================================================================

class NotificationService:
    """Business logic for user notifications."""

    def __init__(self, db_factory):
        self._db_factory = db_factory

    def create_notification(
        self,
        user_id: str,
        type: str,
        title: str,
        message: str,
        link: Optional[str] = None,
    ) -> Notification:
        """Create a new notification for a user."""
        session = self._db_factory()
        try:
            notification = Notification(
                user_id=user_id,
                type=type,
                title=title,
                message=message,
                link=link,
                is_read=False,
            )
            session.add(notification)
            session.commit()
            return notification
        finally:
            session.close()

    def create_quota_warning(
        self,
        space_id: str,
        space_name: str,
        used_bytes: int,
        max_bytes: int,
        usage_percent: float,
    ) -> Notification:
        """Create a quota warning notification for the space owner."""
        session = self._db_factory()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                return None

            owner_id = space.owner_id
            usage_str = f"{used_bytes / (1024**3):.2f} GB" if used_bytes > 1024**3 else f"{used_bytes / 1024**2:.2f} MB"
            max_str = f"{max_bytes / (1024**3):.2f} GB" if max_bytes > 1024**3 else f"{max_bytes / 1024**2:.2f} MB"

            if usage_percent >= 1.0:
                title = "空间配额已满"
                message = f"空间「{space_name}」配额已满（{usage_str}/{max_str}），无法继续写入文件。"
            elif usage_percent >= 0.9:
                title = "空间配额即将用尽"
                message = f"空间「{space_name}」配额使用率达 {usage_percent*100:.0f}%（{usage_str}/{max_str}），请及时清理。"
            else:
                title = "空间配额警告"
                message = f"空间「{space_name}」配额使用率达 {usage_percent*100:.0f}%（{usage_str}/{max_str}），请注意管理。"

            notification = Notification(
                user_id=owner_id,
                type="quota_warning",
                title=title,
                message=message,
                link=f"/spaces/{space_id}",
                is_read=False,
            )
            session.add(notification)
            session.commit()
            return notification
        finally:
            session.close()

    def list_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List notifications for a user."""
        session = self._db_factory()
        try:
            query = session.query(Notification).filter(
                Notification.user_id == user_id
            )
            if unread_only:
                query = query.filter(Notification.is_read == False)

            total = query.count()
            unread_count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            ).count()

            notifications = query.order_by(
                Notification.created_at.desc()
            ).offset(offset).limit(limit).all()

            return {
                "total": total,
                "unread_count": unread_count,
                "notifications": [n.to_dict() for n in notifications],
            }
        finally:
            session.close()

    def mark_as_read(
        self,
        notification_id: str,
        user_id: str,
    ) -> Notification:
        """Mark a notification as read."""
        session = self._db_factory()
        try:
            notification = session.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            ).first()

            if not notification:
                raise NotificationNotFound(f"Notification {notification_id} not found")

            notification.is_read = True
            session.commit()
            return notification
        finally:
            session.close()

    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user. Returns count."""
        session = self._db_factory()
        try:
            count = session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            ).update({"is_read": True})
            session.commit()
            return count
        finally:
            session.close()

    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification."""
        session = self._db_factory()
        try:
            notification = session.query(Notification).filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            ).first()

            if not notification:
                return False

            session.delete(notification)
            session.commit()
            return True
        finally:
            session.close()

    def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications."""
        session = self._db_factory()
        try:
            return session.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
            ).count()
        finally:
            session.close()
