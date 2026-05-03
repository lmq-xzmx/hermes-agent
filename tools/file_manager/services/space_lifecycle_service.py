"""
SpaceLifecycleService - 空间生命周期服务

提供创建空间、更新配额、归档空间、转移所有权等功能。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session

from ..engine.models import Space, SpaceMember, User, StoragePool


@dataclass
class CreateSpaceRequest:
    """创建空间请求"""
    name: str
    owner_id: str
    space_type: str = "private"  # private | team
    team_id: Optional[str] = None
    quota_bytes: int = 0
    quota_type: str = "committed"  # committed | reserved | unlimited


class SpaceLifecycleService:
    """空间生命周期服务"""

    def __init__(self, db_factory=None):
        self._db = db_factory

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def create_space_with_quota(self, request: CreateSpaceRequest) -> Dict[str, Any]:
        """
        创建空间并分配配额

        Args:
            request: 创建空间请求

        Returns:
            空间信息
        """
        session = self._get_session()
        try:
            # 验证所有者存在
            owner = session.query(User).filter(User.id == request.owner_id).first()
            if not owner:
                raise ValueError(f"用户 {request.owner_id} 不存在")

            # 如果是团队空间，验证团队存在
            if request.team_id:
                pool = session.query(StoragePool).filter(
                    StoragePool.id == request.team_id
                ).first()
                if not pool:
                    raise ValueError(f"存储池 {request.team_id} 不存在")

            # 创建空间
            space = Space(
                id=str(uuid.uuid4()),
                name=request.name,
                space_type=request.space_type,
                owner_id=request.owner_id,
                storage_pool_id=request.team_id or "",  # team_id used as pool_id for team spaces
                quota_type=request.quota_type or "committed",
                committed_bytes=request.quota_bytes,
                actual_used_bytes=0,
                quota_source="team" if request.team_id else "personal",
                source_id=request.team_id or request.owner_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            session.add(space)
            session.flush()

            # 为所有者创建 SpaceMember 记录
            member = SpaceMember(
                id=str(uuid.uuid4()),
                space_id=space.id,
                user_id=request.owner_id,
                role="admin",
                status="active",
                quota_bytes=request.quota_bytes,
                joined_at=datetime.utcnow(),
            )

            session.add(member)
            session.commit()
            session.refresh(space)

            return space.to_dict() if hasattr(space, 'to_dict') else {
                "id": space.id,
                "name": space.name,
                "space_type": space.space_type,
                "owner_id": space.owner_id,
                "source_id": space.source_id,
                "quota_type": space.quota_type,
                "committed_bytes": space.committed_bytes,
                "actual_used_bytes": space.actual_used_bytes,
                "created_at": space.created_at.isoformat() if space.created_at else None,
            }
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_space_quota(
        self,
        space_id: str,
        new_quota: int,
        updated_by: str = None,
    ) -> bool:
        """
        更新空间配额

        Args:
            space_id: 空间ID
            new_quota: 新配额大小
            updated_by: 更新人ID

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise ValueError(f"空间 {space_id} 不存在")

            old_quota = space.committed_bytes
            space.committed_bytes = new_quota
            space.updated_at = datetime.utcnow()

            # 同时更新 SpaceMember 的配额
            admin_member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.role == "admin"
            ).first()

            if admin_member:
                admin_member.quota_bytes = new_quota

            session.commit()

            # 记录配额变更日志（可选）
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def archive_space(self, space_id: str) -> bool:
        """
        归档空间（回收配额）

        Args:
            space_id: 空间ID

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise ValueError(f"空间 {space_id} 不存在")

            # 回收配额
            space.committed_bytes = 0
            space.quota_type = "unlimited"
            space.updated_at = datetime.utcnow()

            # 更新 SpaceMember 配额
            session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id
            ).update({"quota_bytes": 0})

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def transfer_space_ownership(
        self,
        space_id: str,
        new_owner_id: str,
    ) -> bool:
        """
        转移空间所有权

        Args:
            space_id: 空间ID
            new_owner_id: 新所有者ID

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            # 验证新所有者存在
            new_owner = session.query(User).filter(User.id == new_owner_id).first()
            if not new_owner:
                raise ValueError(f"用户 {new_owner_id} 不存在")

            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise ValueError(f"空间 {space_id} 不存在")

            old_owner_id = space.owner_id

            # 更新空间所有者
            space.owner_id = new_owner_id
            space.source_id = new_owner_id
            space.updated_at = datetime.utcnow()

            # 更新或创建新所有者的 SpaceMember
            existing_member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == new_owner_id
            ).first()

            if existing_member:
                existing_member.role = "admin"
            else:
                new_member = SpaceMember(
                    id=str(uuid.uuid4()),
                    space_id=space_id,
                    user_id=new_owner_id,
                    role="admin",
                    status="active",
                    quota_bytes=space.committed_bytes,
                    joined_at=datetime.utcnow(),
                )
                session.add(new_member)

            # 将旧所有者降级为 member
            old_member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == old_owner_id
            ).first()

            if old_member:
                old_member.role = "member"

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_space_with_quota(self, space_id: str) -> Optional[Dict[str, Any]]:
        """
        获取空间详情（含配额信息）

        Args:
            space_id: 空间ID

        Returns:
            空间详情
        """
        session = self._get_session()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                return None

            # 获取成员列表
            members = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.status == "active"
            ).all()

            return {
                "id": space.id,
                "name": space.name,
                "space_type": space.space_type,
                "owner_id": space.owner_id,
                "source_id": space.source_id,
                "quota_type": space.quota_type,
                "committed_bytes": space.committed_bytes,
                "actual_used_bytes": space.actual_used_bytes,
                "quota_source": space.quota_source,
                "status": space.status,
                "members": [
                    {
                        "user_id": m.user_id,
                        "role": m.role,
                        "quota_bytes": m.quota_bytes,
                    }
                    for m in members
                ],
                "created_at": space.created_at.isoformat() if space.created_at else None,
                "updated_at": space.updated_at.isoformat() if space.updated_at else None,
            }
        finally:
            session.close()

    def list_user_spaces(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的空间列表

        Args:
            user_id: 用户ID

        Returns:
            空间列表
        """
        session = self._get_session()
        try:
            # 获取用户作为成员的空间
            memberships = session.query(SpaceMember).filter(
                SpaceMember.user_id == user_id,
                SpaceMember.status == "active"
            ).all()

            spaces = []
            for m in memberships:
                space = session.query(Space).filter(Space.id == m.space_id).first()
                if space:
                    spaces.append({
                        "id": space.id,
                        "name": space.name,
                        "type": space.type,
                        "role": m.role,
                        "quota_bytes": m.quota_bytes,
                        "actual_used_bytes": space.actual_used_bytes,
                        "created_at": space.created_at.isoformat() if space.created_at else None,
                    })

            return spaces
        finally:
            session.close()


# Module exports
__all__ = [
    "SpaceLifecycleService",
    "CreateSpaceRequest",
]
