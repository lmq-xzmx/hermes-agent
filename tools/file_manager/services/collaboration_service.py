"""
CollaborationService - 协作会话业务逻辑

跨 Space 临时授权，支持创建、撤销会话和权限检查。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ..engine.models import CollaborationSession, Space, SpaceMember, User


class CollaborationError(Exception):
    """协作会话相关错误"""
    pass


class SessionNotFound(CollaborationError):
    """会话不存在"""
    pass


class SessionExpired(CollaborationError):
    """会话已过期"""
    pass


class PermissionDenied(CollaborationError):
    """权限不足"""
    pass


class CollaborationService:
    """
    协作会话业务逻辑。

    用于在 Space 之间临时共享权限，比如：
    - 项目经理临时需要访问某个团队的文件
    - 跨团队协作时授予特定用户读写权限
    """

    def __init__(self, db_factory):
        self._db = db_factory

    def create_session(
        self,
        space_id: str,
        creator_id: str,
        target_user_id: str,
        permissions: List[str],
        expires_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        创建协作会话。只有 space owner 可以创建。

        permissions: ["read", "write"] 等
        """
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise CollaborationError("Space 不存在")

            if space.owner_id != creator_id:
                raise PermissionDenied("只有 space owner 可以创建协作会话")

            # 检查目标用户是否是 space 成员（可选，允许跨 space 授权）
            # 如果允许跨 space 协作，注释下面这段
            # member = session.query(SpaceMember).filter(
            #     SpaceMember.space_id == space_id,
            #     SpaceMember.user_id == target_user_id,
            #     SpaceMember.status == "active"
            # ).first()
            # if not member:
            #     raise CollaborationError("目标用户不是 space 成员")

            expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

            collab = CollaborationSession(
                space_id=space_id,
                created_by=creator_id,
                target_user_id=target_user_id,
                permissions=permissions,
                expires_at=expires_at,
                is_active=True,
            )
            session.add(collab)
            session.commit()
            return collab.to_dict()
        finally:
            session.close()

    def revoke_session(self, session_id: str, requesting_user_id: str) -> bool:
        """
        撤销协作会话。只有创建者或 space owner 可以撤销。
        """
        session = self._db()
        try:
            collab = session.query(CollaborationSession).filter(
                CollaborationSession.id == session_id
            ).first()
            if not collab:
                raise SessionNotFound()

            space = session.query(Space).filter(Space.id == collab.space_id).first()
            is_creator = collab.created_by == requesting_user_id
            is_space_owner = space and space.owner_id == requesting_user_id

            if not is_creator and not is_space_owner:
                raise PermissionDenied("无权撤销此会话")

            collab.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    def get_active_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话详情。"""
        session = self._db()
        try:
            collab = session.query(CollaborationSession).filter(
                CollaborationSession.id == session_id
            ).first()
            if not collab:
                return None
            if collab.is_expired():
                collab.is_active = False
                session.commit()
                return None
            return collab.to_dict() if collab.is_active else None
        finally:
            session.close()

    def get_user_collaborations(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户作为目标的所有有效协作会话。"""
        session = self._db()
        try:
            collabs = (
                session.query(CollaborationSession)
                .filter(
                    CollaborationSession.target_user_id == user_id,
                    CollaborationSession.is_active == True,
                )
                .all()
            )
            return [c.to_dict() for c in collabs if not c.is_expired()]
        finally:
            session.close()

    def get_space_collaborations(self, space_id: str) -> List[Dict[str, Any]]:
        """获取空间的所有有效协作会话。"""
        session = self._db()
        try:
            collabs = (
                session.query(CollaborationSession)
                .filter(
                    CollaborationSession.space_id == space_id,
                    CollaborationSession.is_active == True,
                )
                .all()
            )
            return [c.to_dict() for c in collabs if not c.is_expired()]
        finally:
            session.close()

    def check_user_has_collaborative_access(
        self,
        user_id: str,
        space_id: str,
        required_permission: str = "read",
    ) -> bool:
        """
        检查用户是否有协作会话授予的空间权限。
        用于在 SpaceMember 检查之外额外检查协作授权。
        """
        session = self._db()
        try:
            collab = (
                session.query(CollaborationSession)
                .filter(
                    CollaborationSession.target_user_id == user_id,
                    CollaborationSession.space_id == space_id,
                    CollaborationSession.is_active == True,
                )
                .first()
            )
            if not collab or collab.is_expired():
                return False

            # 检查是否有所需权限
            if required_permission == "write":
                return "write" in (collab.permissions or [])
            elif required_permission == "read":
                # read 权限包含在 write 中
                return "read" in (collab.permissions or []) or "write" in (collab.permissions or [])
            return False
        finally:
            session.close()

    def cleanup_expired_sessions(self) -> int:
        """清理所有过期会话。返回清理数量。"""
        session = self._db()
        try:
            now = datetime.utcnow()
            expired = (
                session.query(CollaborationSession)
                .filter(
                    CollaborationSession.is_active == True,
                    CollaborationSession.expires_at < now,
                )
                .all()
            )
            count = len(expired)
            for collab in expired:
                collab.is_active = False
            session.commit()
            return count
        finally:
            session.close()