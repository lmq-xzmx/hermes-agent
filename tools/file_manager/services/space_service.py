"""
SpaceService - Business logic for hierarchical Spaces, sub-spaces, and requests.

Handles:
- Space CRUD operations
- Space hierarchy (root -> team -> private)
- Private sub-space requests and approval workflow
- Space membership management
- Invite credentials
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..engine.models import (
    StoragePool, Space, SpaceMember, SpaceCredential, SpaceRequest, SpaceLink, User, Base
)
from ..engine.storage import StorageEngine

logger = logging.getLogger(__name__)

# =============================================================================
# Domain Errors
# =============================================================================

class StoragePoolNotFound(Exception):
    """Storage pool does not exist."""
    pass


class SpaceNotFound(Exception):
    """Space does not exist."""
    pass


class SpaceQuotaExceeded(Exception):
    """Space quota exceeded."""
    def __init__(self, space_name: str, max_bytes: int, used_bytes: int, required: int):
        self.space_name = space_name
        self.max_bytes = max_bytes
        self.used_bytes = used_bytes
        self.required = required
        super().__init__(
            f"空间「{space_name}」配额已满（{used_bytes}/{max_bytes} 字节），"
            f"还需 {required} 字节"
        )


class SpaceRequestNotFound(Exception):
    """Space request does not exist."""
    pass


class SpaceRequestInvalid(Exception):
    """Space request is invalid or cannot be approved."""
    pass


class NotSpaceOwner(Exception):
    """Only the space owner can perform this action."""
    pass


class UserAlreadyInSpace(Exception):
    """User is already a member of this space."""
    pass


class CredentialNotFound(Exception):
    """Credential token not found or invalid."""
    pass


class CredentialExpired(Exception):
    """Credential token has expired or is fully used."""
    pass


class QuotaExceeded(Exception):
    """Space quota exceeded for write operation."""
    def __init__(self, space_name: str, max_bytes: int, used_bytes: int, required: int):
        self.space_name = space_name
        self.max_bytes = max_bytes
        self.used_bytes = used_bytes
        self.required = required
        super().__init__(
            f"空间「{space_name}」配额不足（已用 {used_bytes}/{max_bytes} 字节）"
            f"，本次写入需 {required} 字节"
        )


def _generate_space_code(session, pool_prefix: str = "SP") -> str:
    """Generate a human-readable space code like SP-2026-001."""
    year = datetime.now().year
    pattern = f"{pool_prefix}-{year}-%"
    existing = session.query(Space.code).filter(Space.code.like(pattern)).all()
    max_seq = 0
    for row in existing:
        code = row[0]
        if code:
            try:
                parts = code.split("-")
                if len(parts) >= 3:
                    seq = int(parts[-1])
                    if seq > max_seq:
                        max_seq = seq
            except (ValueError, IndexError):
                pass
    new_seq = max_seq + 1
    return f"{pool_prefix}-{year}-{new_seq:03d}"


# =============================================================================
# Quota Warning Event (published via EventBus)
# =============================================================================

QUOTA_WARNING_80 = "quota_warning_80"
QUOTA_WARNING_90 = "quota_warning_90"
QUOTA_WARNING_100 = "quota_warning_100"


# =============================================================================
# SpaceService
# =============================================================================

class SpaceService:
    """
    Stateless business-logic service for spaces, sub-spaces, and requests.

    Space Hierarchy:
      Root Space (binds to StoragePool, created by admin)
        └── Team Space (shared by team members)
              └── Private Space (personal, created when request approved)

    Storage layout per space:
      {pool_base_path}/spaces/{space_id}/
        shared/                 ← team shared files
        members/
          {user_id}/           ← member personal files (if private space)
    """

    def __init__(self, db_factory, storage_root: Optional[str] = None):
        self._db = db_factory
        self._storage_root = storage_root

    def _get_storage_root(self) -> str:
        """Get storage root path."""
        if self._storage_root:
            return self._storage_root
        import os
        from pathlib import Path
        hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
        return str(Path(hermes_home) / "file_manager" / "storage")

    def _get_space(self, space_id: str) -> Space:
        """Helper: get space or raise SpaceNotFound."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"空间 {space_id} 不存在")
            return space
        finally:
            session.close()

    def check_quota_for_write(self, space_id: str, additional_bytes: int, user_id: str = None) -> None:
        """
        检查 Space 配额是否足够接受本次写入。
        写入前调用。如果配额不足，抛出 QuotaExceeded。
        如果达到阈值，发送警告事件。
        """
        space = self._get_space(space_id)

        if space.max_bytes == 0:
            return  # 无限制

        used = space.used_bytes
        max_bytes = space.max_bytes

        # 计算预留配额（正在上传的文件）
        from sqlalchemy import func
        from file_manager.engine.models import FileUpload
        session = self._db()
        try:
            reserved_bytes = (
                session.query(func.sum(FileUpload.file_size))
                .filter(
                    FileUpload.space_id == space_id,
                    FileUpload.status == "uploading"
                )
                .scalar()
            ) or 0
        finally:
            session.close()

        available = max_bytes - used - reserved_bytes

        # 检查是否有足够空间
        if additional_bytes > available:
            # 集成生命周期约束检查
            from file_manager.engine import get_lifecycle_engine
            engine = get_lifecycle_engine()
            context = {
                "space_id": space_id,
                "space_name": space.name,
                "user_id": user_id,
                "sufficient_quota": False,
                "current_usage": used,
                "max_bytes": max_bytes,
                "additional_bytes": additional_bytes,
            }
            engine.raise_if_violated("check_quota", context)

            # 如果约束检查通过（不太可能），抛出原异常
            raise QuotaExceeded(
                space_name=space.name,
                max_bytes=max_bytes,
                used_bytes=used,
                required=additional_bytes,
            )

        # 检查是否触发警告阈值
        usage_ratio = used / max_bytes if max_bytes > 0 else 0

        if usage_ratio >= 1.0:
            event_type = QUOTA_WARNING_100
        elif usage_ratio >= 0.9:
            event_type = QUOTA_WARNING_90
        elif usage_ratio >= 0.8:
            event_type = QUOTA_WARNING_80
        else:
            return  # 无需警告

        self._publish_quota_warning(space, usage_ratio, event_type)

    def check_quota_for_write_with_lock(
        self, space_id: str, additional_bytes: int, user_id: str = None
    ) -> None:
        """
        检查 Space 配额是否足够接受本次写入（使用 SELECT FOR UPDATE 悲观锁）。

        在事务中使用 SELECT ... FOR UPDATE 锁定 Space 记录，防止并发超卖。
        同时考虑 FileUpload 表中正在上传的文件预留配额。

        T5: REQ-M2-017 配额超卖防护核心实现

        Args:
            space_id: 空间 ID
            additional_bytes: 本次写入需要的字节数
            user_id: 用户 ID（用于生命周期约束检查）

        Raises:
            QuotaExceeded: 配额不足时抛出
        """
        session = self._db()
        try:
            # Step 1: 使用 SELECT FOR UPDATE 锁定 Space 记录（PostgreSQL/MySQL支持）
            # SQLite 使用 SERIALIZABLE 隔离级别，无需 FOR UPDATE
            query = session.query(Space).filter(Space.id == space_id)
            if "sqlite" not in str(session.get_bind().url):
                query = query.with_for_update(nowait=False)
            space = query.first()

            if not space:
                raise SpaceNotFound(f"空间 {space_id} 不存在")

            if space.max_bytes == 0:
                return  # 无限制

            # Step 2: 计算预留配额（正在上传的文件总大小）
            from tools.file_manager.engine.models import FileUpload
            from sqlalchemy import func
            reserved_bytes = (
                session.query(func.sum(FileUpload.file_size))
                .filter(
                    FileUpload.space_id == space_id,
                    FileUpload.status == "uploading"
                )
                .scalar() or 0
            )

            # Step 3: 计算可用配额
            used = space.used_bytes
            max_bytes = space.max_bytes
            available = max_bytes - used - reserved_bytes

            # Step 4: 检查配额是否足够
            if additional_bytes > available:
                # 集成生命周期约束检查
                from file_manager.engine import get_lifecycle_engine
                engine = get_lifecycle_engine()
                context = {
                    "space_id": space_id,
                    "space_name": space.name,
                    "user_id": user_id,
                    "sufficient_quota": False,
                    "current_usage": used,
                    "reserved_bytes": reserved_bytes,
                    "max_bytes": max_bytes,
                    "additional_bytes": additional_bytes,
                    "quota_reserved": reserved_bytes,
                }
                engine.raise_if_violated("check_quota", context)

                # 如果约束检查通过（不太可能），抛出原异常
                raise QuotaExceeded(
                    space_name=space.name,
                    max_bytes=max_bytes,
                    used_bytes=used + reserved_bytes,
                    required=additional_bytes,
                )

            # Step 5: 检查是否触发警告阈值（基于实际使用量，不含预留）
            usage_ratio = used / max_bytes if max_bytes > 0 else 0

            if usage_ratio >= 1.0:
                event_type = QUOTA_WARNING_100
            elif usage_ratio >= 0.9:
                event_type = QUOTA_WARNING_90
            elif usage_ratio >= 0.8:
                event_type = QUOTA_WARNING_80
            else:
                return  # 无需警告

            self._publish_quota_warning(space, usage_ratio, event_type)

        finally:
            session.close()

    def _publish_quota_warning(
        self, space: Space, usage_ratio: float, event_type: str
    ) -> None:
        """Publish quota warning via EventBus and create in-app notification."""
        try:
            from .event_bus import get_event_bus
            bus = get_event_bus()
            bus.publish(
                topic=event_type,
                data={
                    "space_id": space.id,
                    "space_name": space.name,
                    "used_bytes": space.used_bytes,
                    "max_bytes": space.max_bytes,
                    "usage_ratio": round(usage_ratio * 100, 2),
                    "owner_id": space.owner_id,
                },
            )
            # Also create in-app notification
            self._create_quota_notification(space, usage_ratio)
        except Exception:
            pass  # Non-critical: quota warnings should not break writes

    def _create_quota_notification(
        self, space: Space, usage_ratio: float
    ) -> None:
        """Create an in-app notification for quota warning."""
        try:
            from .notification_service import NotificationService
            if not hasattr(self, "_notification_svc"):
                self._notification_svc = NotificationService(db_factory=self._db_factory)
            self._notification_svc.create_quota_warning(
                space_id=space.id,
                space_name=space.name,
                used_bytes=space.used_bytes,
                max_bytes=space.max_bytes,
                usage_percent=usage_ratio,
            )
        except Exception:
            pass  # Non-critical: notifications should not break writes

    def update_used_bytes(self, space_id: str, delta: int) -> None:
        """
        更新 Space 的 used_bytes（原子操作）。
        delta: 正数表示增加使用量，负数表示释放空间。
        """
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"空间 {space_id} 不存在")
            space.used_bytes = max(0, space.used_bytes + delta)
            session.commit()
        finally:
            session.close()

    def get_quota_status(self, space_id: str) -> Dict[str, Any]:
        """获取 Space 配额状态（含使用率、剩余空间）。"""
        space = self._get_space(space_id)
        max_bytes = space.max_bytes
        used_bytes = space.used_bytes

        result = {
            "space_id": space_id,
            "space_name": space.name,
            "max_bytes": max_bytes,
            "used_bytes": used_bytes,
            "used_ratio": 0.0,
            "remaining_bytes": 0,
            "is_unlimited": max_bytes == 0,
        }

        if max_bytes > 0:
            result["used_ratio"] = round(used_bytes / max_bytes * 100, 2)
            result["remaining_bytes"] = max(0, max_bytes - used_bytes)
            # 警告等级
            if result["used_ratio"] >= 100:
                result["quota_status"] = "exceeded"
            elif result["used_ratio"] >= 90:
                result["quota_status"] = "critical"
            elif result["used_ratio"] >= 80:
                result["quota_status"] = "warning"
            else:
                result["quota_status"] = "normal"
        else:
            result["quota_status"] = "unlimited"
            result["remaining_bytes"] = -1  # 表示无限制

        return result

    # -------------------------------------------------------------------------
    # Storage Pool Management
    # -------------------------------------------------------------------------

    def list_pools(self) -> List[Dict[str, Any]]:
        """List all storage pools."""
        session = self._db()
        try:
            pools = session.query(StoragePool).all()
            return [p.to_dict() for p in pools]
        finally:
            session.close()

    def create_pool(
        self,
        name: str,
        base_path: str,
        protocol: str = "local",
        total_bytes: int = 0,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new storage pool.

        - base_path: absolute path on disk
        - protocol: "local" | "smb" | "nfs" | "s3"
        - total_bytes: 0 = auto-detect from disk
        """
        session = self._db()
        try:
            resolved = str(Path(os.path.expanduser(base_path)).resolve())
            os.makedirs(resolved, exist_ok=True)

            if total_bytes == 0 and protocol == "local":
                stat = shutil.disk_usage(resolved)
                free = stat.free
                total = stat.total
            else:
                total = total_bytes
                free = total_bytes

            pool = StoragePool(
                name=name,
                base_path=resolved,
                protocol=protocol,
                total_bytes=total,
                free_bytes=free,
                description=description,
                is_active=True,
            )
            session.add(pool)
            session.commit()
            return pool.to_dict()
        finally:
            session.close()

    def refresh_pool_space(self, pool_id: str) -> Dict[str, Any]:
        """Re-probe free space on a local pool."""
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                raise StoragePoolNotFound(f"存储池 {pool_id} 不存在")
            if pool.protocol == "local":
                try:
                    stat = shutil.disk_usage(pool.base_path)
                    pool.free_bytes = stat.free
                    if pool.total_bytes == 0:
                        pool.total_bytes = stat.total
                except OSError:
                    pass
            session.commit()
            return pool.to_dict()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Space Management
    # -------------------------------------------------------------------------

    def list_spaces(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List spaces. If user_id given, returns only spaces the user is a member of.
        """
        session = self._db()
        try:
            query = session.query(Space)
            if user_id:
                space_ids = (
                    session.query(SpaceMember.space_id)
                    .filter(SpaceMember.user_id == user_id)
                    .all()
                )
                space_ids = [s[0] for s in space_ids]
                if not space_ids:
                    return []
                query = query.filter(Space.id.in_(space_ids))
            return [s.to_dict() for s in query.all()]
        finally:
            session.close()

    def get_space(self, space_id: str) -> Dict[str, Any]:
        """Get space details with members."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"空间 {space_id} 不存在")
            return space.to_dict(include_members=True)
        finally:
            session.close()

    def create_space(
        self,
        name: str,
        owner_id: str,
        storage_pool_id: str,
        parent_id: Optional[str] = None,
        max_bytes: int = 0,
        space_type: str = "team",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a new space.

        - space_type: "root" | "team" | "private"
        - parent_id: parent space for team/private spaces
        """
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == storage_pool_id).first()
            if not pool:
                raise StoragePoolNotFound(f"存储池 {storage_pool_id} 不存在")
            if not pool.is_active:
                raise SpaceRequestInvalid("该存储池已停用")

            # Verify parent space if provided
            if parent_id:
                parent = session.query(Space).filter(Space.id == parent_id).first()
                if not parent:
                    raise SpaceNotFound(f"父空间 {parent_id} 不存在")
                if parent.storage_pool_id != storage_pool_id:
                    raise SpaceRequestInvalid("父空间不在同一个存储池中")

            space = Space(
                name=name,
                parent_id=parent_id,
                storage_pool_id=storage_pool_id,
                owner_id=owner_id,
                max_bytes=max_bytes,
                used_bytes=0,
                space_type=space_type,
                status="active",
                description=description,
                code=_generate_space_code(session),
            )
            session.add(space)
            session.flush()

            # Create owner as first member
            member = SpaceMember(
                space_id=space.id,
                user_id=owner_id,
                role="owner",
            )
            session.add(member)

            # Create physical directory structure
            self._create_space_directories(pool.base_path, space.id, space_type)

            session.commit()
            return space.to_dict(include_members=True)
        finally:
            session.close()

    def _create_space_directories(self, pool_base: str, space_id: str, space_type: str) -> None:
        """Create physical directory structure for a space."""
        space_path = os.path.join(pool_base, "spaces", space_id)
        os.makedirs(space_path, exist_ok=True)
        os.makedirs(os.path.join(space_path, "shared"), exist_ok=True)
        if space_type == "private":
            os.makedirs(os.path.join(space_path, "members"), exist_ok=True)

    def update_space(
        self,
        space_id: str,
        requesting_user_id: str,
        name: Optional[str] = None,
        max_bytes: Optional[int] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update space settings. Only owner can do this."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()
            if space.owner_id != requesting_user_id:
                raise NotSpaceOwner("只有空间所有者可以修改空间设置")

            # 如果修改配额，检查 update_quota 约束
            if max_bytes is not None and max_bytes != space.max_bytes:
                from file_manager.engine import get_lifecycle_engine
                engine = get_lifecycle_engine()
                context = {
                    "space_id": space_id,
                    "user_id": requesting_user_id,
                    "is_owner": space.owner_id == requesting_user_id,
                    "old_quota": space.max_bytes,
                    "new_quota": max_bytes,
                }
                engine.raise_if_violated("update_quota", context)

            if name is not None:
                space.name = name
            if max_bytes is not None:
                space.max_bytes = max_bytes
            if status is not None:
                space.status = status
            space.updated_at = datetime.utcnow()
            session.commit()
            return space.to_dict()
        finally:
            session.close()

    def delete_space(self, space_id: str, requesting_user_id: str) -> None:
        """Delete a space and all its files. Only owner can do this."""
        from file_manager.engine import get_lifecycle_engine

        engine = get_lifecycle_engine()
        member_count = engine.get_member_count_for_space(space_id, self._db)
        pending_request_count = engine.get_pending_request_count(space_id, self._db)

        # Check constraint: space must have no members and no pending requests
        context = {
            "space_id": space_id,
            "member_count": member_count,
            "pending_request_count": pending_request_count
        }
        engine.raise_if_violated("delete_space", context)

        # If constraint passes, proceed with deletion
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()
            if space.owner_id != requesting_user_id:
                raise NotSpaceOwner()

            # Delete physical files
            pool = space.storage_pool
            if pool and pool.protocol == "local":
                space_path = os.path.join(pool.base_path, "spaces", space.id)
                if os.path.exists(space_path):
                    shutil.rmtree(space_path)

            session.delete(space)
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Space Members
    # -------------------------------------------------------------------------

    def list_members(self, space_id: str) -> List[Dict[str, Any]]:
        """List all members of a space."""
        session = self._db()
        try:
            members = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.status == "active"
            ).all()
            return [m.to_dict() for m in members]
        finally:
            session.close()

    def add_member(
        self,
        space_id: str,
        user_id: str,
        requesting_user_id: str,
        role: str = "member",
    ) -> Dict[str, Any]:
        """Add a user to a space. Only owner can do this."""
        from file_manager.engine import get_lifecycle_engine

        engine = get_lifecycle_engine()
        is_owner = engine.check_owner(requesting_user_id, space_id, self._db)
        was_recently_removed = engine.check_recently_removed_member(user_id, space_id, self._db)

        # Check constraint: only owner can invite
        context = {
            "space_id": space_id,
            "is_owner": is_owner,
            "was_recently_removed": was_recently_removed
        }
        engine.raise_if_violated("invite_member", context)

        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()

            # Check if already a member
            existing = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == user_id
            ).first()
            if existing:
                if existing.status == "active":
                    raise UserAlreadyInSpace("该用户已是空间成员")
                # Reactivate rejected member
                existing.status = "active"
                existing.role = role
                session.commit()
                return existing.to_dict()

            member = SpaceMember(
                space_id=space_id,
                user_id=user_id,
                role=role,
                status="active",
            )
            session.add(member)

            # Create member's personal directory if private space
            if space.space_type == "private":
                pool = space.storage_pool
                member_dir = os.path.join(pool.base_path, "spaces", space_id, "members", user_id)
                os.makedirs(member_dir, exist_ok=True)

            session.commit()
            return member.to_dict()
        finally:
            session.close()

    def remove_member(
        self,
        space_id: str,
        target_user_id: str,
        requesting_user_id: str,
    ) -> None:
        """Remove a user from a space."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()

            member = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == target_user_id
            ).first()
            if not member:
                raise SpaceRequestInvalid("该用户不是空间成员")

            is_owner = requesting_user_id == space.owner_id
            is_self = requesting_user_id == target_user_id

            if not is_owner and not is_self:
                raise NotSpaceOwner()

            if member.role == "owner":
                owner_count = session.query(SpaceMember).filter(
                    SpaceMember.space_id == space_id,
                    SpaceMember.role == "owner"
                ).count()
                if owner_count <= 1:
                    raise SpaceRequestInvalid("无法移除唯一的所有者")

            member.status = "removed"
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Credentials (Invite Tokens)
    # -------------------------------------------------------------------------

    def create_credential(
        self,
        space_id: str,
        created_by: str,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate an invite token for a space."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()
            if space.owner_id != created_by:
                raise NotSpaceOwner()

            token = secrets.token_urlsafe(16)
            cred = SpaceCredential(
                space_id=space_id,
                token=token,
                max_uses=max_uses,
                expires_at=expires_at,
                created_by=created_by,
                is_active=True,
            )
            session.add(cred)
            session.commit()
            return cred.to_dict(include_token=True)
        finally:
            session.close()

    def list_credentials(
        self,
        space_id: str,
        requesting_user_id: str,
    ) -> List[Dict[str, Any]]:
        """List all credentials for a space. Only owner can view."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound()
            if space.owner_id != requesting_user_id:
                raise NotSpaceOwner()
            creds = session.query(SpaceCredential).filter(
                SpaceCredential.space_id == space_id
            ).all()
            return [c.to_dict() for c in creds]
        finally:
            session.close()

    def revoke_credential(self, credential_id: str, requesting_user_id: str) -> None:
        """Revoke a credential token."""
        session = self._db()
        try:
            cred = session.query(SpaceCredential).filter(
                SpaceCredential.id == credential_id
            ).first()
            if not cred:
                raise CredentialNotFound()
            space = cred.space
            if space.owner_id != requesting_user_id:
                raise NotSpaceOwner()
            cred.is_active = False
            session.commit()
        finally:
            session.close()

    def join_via_credential(self, token: str, user_id: str) -> Dict[str, Any]:
        """Use an invite token to join a space."""
        from file_manager.engine import get_lifecycle_engine

        engine = get_lifecycle_engine()

        session = self._db()
        try:
            cred = session.query(SpaceCredential).filter(
                SpaceCredential.token == token
            ).first()
            if not cred:
                raise CredentialNotFound("凭证不存在")
            if not cred.is_valid():
                # Use lifecycle engine for consistent error handling
                context = {"is_valid": False}
                engine.raise_if_violated("join_team", context)

            space = cred.space
            if not space.is_active:
                raise SpaceRequestInvalid("该空间已停用")

            # Check if already a member
            existing = session.query(SpaceMember).filter(
                SpaceMember.space_id == space.id,
                SpaceMember.user_id == user_id
            ).first()
            if existing and existing.status == "active":
                raise UserAlreadyInSpace(f"你已经是空间「{space.name}」的成员了")

            if existing:
                existing.status = "active"
            else:
                member = SpaceMember(
                    space_id=space.id,
                    user_id=user_id,
                    role="member",
                    status="active",
                )
                session.add(member)

            # Increment usage
            cred.used_count += 1
            session.commit()

            return space.to_dict(include_members=True)
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Space Requests (Private Sub-Space)
    # -------------------------------------------------------------------------

    def create_request(
        self,
        space_id: str,
        requester_id: str,
        requested_name: str,
        requested_bytes: int = 0,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a request for a private sub-space.
        Team members use this to request their own private space.
        """
        session = self._db()
        try:
            parent = session.query(Space).filter(Space.id == space_id).first()
            if not parent:
                raise SpaceNotFound(f"空间 {space_id} 不存在")
            if parent.space_type == "private":
                raise SpaceRequestInvalid("私有空间不能创建子空间")

            # Check if user is a member
            membership = session.query(SpaceMember).filter(
                SpaceMember.space_id == space_id,
                SpaceMember.user_id == requester_id,
                SpaceMember.status == "active"
            ).first()

            # 集成生命周期约束检查 (create_private_space)
            from file_manager.engine import get_lifecycle_engine
            engine = get_lifecycle_engine()
            context = {
                "space_id": space_id,
                "user_id": requester_id,
                "is_team_member": membership is not None,
                "parent_space_name": parent.name,
            }
            engine.raise_if_violated("create_private_space", context)

            # Check if user already has a pending request
            existing = session.query(SpaceRequest).filter(
                SpaceRequest.space_id == space_id,
                SpaceRequest.requester_id == requester_id,
                SpaceRequest.status == "pending"
            ).first()
            if existing:
                raise SpaceRequestInvalid("你已有一个待处理的申请")

            request = SpaceRequest(
                space_id=space_id,
                requester_id=requester_id,
                requested_name=requested_name,
                requested_bytes=requested_bytes,
                reason=reason,
                status="pending",
            )
            session.add(request)
            session.commit()
            return request.to_dict()
        finally:
            session.close()

    def create_member_exit_request(
        self,
        team_id: str,
        member_id: str,
        reason: Optional[str] = None
    ) -> SpaceRequest:
        """
        创建成员退出申请（生成待办任务给管理员）

        Args:
            team_id: 团队ID
            member_id: 成员ID
            reason: 退出原因

        Returns:
            SpaceRequest 对象
        """
        from engine.models import SpaceRequest, User, Space

        session = self._db()
        try:
            # 验证成员存在
            member = session.query(User).filter(User.id == member_id).first()
            if not member:
                raise ValueError(f"Member {member_id} not found")

            # 验证团队存在
            team = session.query(Space).filter(Space.id == team_id, Space.space_type == "team").first()
            if not team:
                raise ValueError(f"Team {team_id} not found")

            # 创建申请
            request = SpaceRequest(
                id=str(uuid.uuid4()),
                space_id=team_id,
                requester_id=member_id,
                requested_name=f"成员退出: {member.username}",
                status="pending",
                reason=reason or "成员主动申请退出",
                params_json=json.dumps({"type": "team_member_exit", "member_id": member_id})
            )
            session.add(request)
            session.commit()

            return request
        finally:
            session.close()

    def remove_member_with_notification(
        self,
        team_id: str,
        member_id: str,
        operator_id: str,
        action: str = "remove_by_admin"
    ) -> Dict[str, Any]:
        """
        管理员移除成员并发送通知

        Args:
            team_id: 团队ID
            member_id: 被移除成员ID
            operator_id: 操作人ID
            action: 操作类型 ("remove_by_admin", "quota_recovery", "data_clear", "data_transfer")

        Returns:
            操作结果
        """
        from engine.models import SpaceMember, User, Space
        from services.notification_service import NotificationService

        session = self._db()
        try:
            # 移除成员
            member_record = session.query(SpaceMember).filter(
                SpaceMember.space_id == team_id,
                SpaceMember.user_id == member_id
            ).first()

            if not member_record:
                raise ValueError(f"Member {member_id} not found in team {team_id}")

            # 获取成员信息用于通知
            member_user = session.query(User).filter(User.id == member_id).first()
            member_name = member_user.username if member_user else "未知成员"

            # 删除成员记录
            session.delete(member_record)
            session.commit()

            # 发送通知（如果 NotificationService 存在）
            try:
                notification_service = NotificationService()
                notification_service.create_notification(
                    user_id=member_id,
                    title="您已被移出团队",
                    content=f"您已被移出团队，请联系管理员了解详情",
                    notification_type="team_remove"
                )
            except Exception as e:
                logger.warning(f"Failed to send notification: {e}")

            return {
                "success": True,
                "member_id": member_id,
                "member_name": member_name,
                "action": action
            }
        finally:
            session.close()

    def list_requests(
        self,
        space_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List space requests. If space_id is None, list all pending requests (admin)."""
        session = self._db()
        try:
            query = session.query(SpaceRequest)
            if space_id:
                query = query.filter(SpaceRequest.space_id == space_id)
            if status:
                query = query.filter(SpaceRequest.status == status)
            requests = query.order_by(SpaceRequest.created_at.desc()).all()
            return [r.to_dict() for r in requests]
        finally:
            session.close()

    def approve_request(
        self,
        request_id: str,
        reviewer_id: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Approve a private sub-space request.
        Creates the private space and adds the user as owner.
        """
        session = self._db()
        try:
            req = session.query(SpaceRequest).filter(SpaceRequest.id == request_id).first()
            if not req:
                raise SpaceRequestNotFound(f"申请 {request_id} 不存在")
            if req.status != "pending":
                raise SpaceRequestInvalid(f"申请已被处理（状态：{req.status}）")

            parent = session.query(Space).filter(Space.id == req.space_id).first()
            if not parent:
                raise SpaceNotFound("父空间不存在")

            # Verify reviewer is owner of parent space
            if parent.owner_id != reviewer_id:
                raise NotSpaceOwner("只有父空间所有者可以审批申请")

            # Calculate quota (use requested or default 1GB)
            quota = req.requested_bytes if req.requested_bytes > 0 else 1024 * 1024 * 1024

            # Create the private space
            private_space = Space(
                name=req.requested_name,
                parent_id=parent.id,
                storage_pool_id=parent.storage_pool_id,
                owner_id=req.requester_id,
                max_bytes=quota,
                used_bytes=0,
                space_type="private",
                status="active",
                description=f"私有空间 - 由 {parent.name} 成员申请",
            )
            session.add(private_space)
            session.flush()

            # Add requester as owner of private space
            member = SpaceMember(
                space_id=private_space.id,
                user_id=req.requester_id,
                role="owner",
                quota_bytes=quota,
                status="active",
            )
            session.add(member)

            # Create physical directories
            pool = parent.storage_pool
            self._create_space_directories(pool.base_path, private_space.id, "private")

            # Update request status
            req.status = "approved"
            req.reviewed_by = reviewer_id
            req.reviewed_at = datetime.utcnow()
            req.review_note = note

            session.commit()

            return {
                "request": req.to_dict(),
                "space": private_space.to_dict(include_members=True),
            }
        except SpaceRequestNotFound:
            raise
        except SpaceRequestInvalid:
            raise
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def reject_request(
        self,
        request_id: str,
        reviewer_id: str,
        note: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reject a private sub-space request."""
        session = self._db()
        try:
            req = session.query(SpaceRequest).filter(SpaceRequest.id == request_id).first()
            if not req:
                raise SpaceRequestNotFound(f"申请 {request_id} 不存在")
            if req.status != "pending":
                raise SpaceRequestInvalid(f"申请已被处理（状态：{req.status}）")

            parent = session.query(Space).filter(Space.id == req.space_id).first()
            if parent.owner_id != reviewer_id:
                raise NotSpaceOwner("只有空间所有者可以审批申请")

            req.status = "rejected"
            req.reviewed_by = reviewer_id
            req.reviewed_at = datetime.utcnow()
            req.review_note = note
            session.commit()

            return req.to_dict()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Space Links (Cross-team Collaboration)
    # -------------------------------------------------------------------------

    def list_space_links(self, space_id: str) -> List[Dict[str, Any]]:
        """List all cross-space links for a space (both incoming and outgoing)."""
        session = self._db()
        try:
            links = session.query(SpaceLink).filter(
                (SpaceLink.source_space_id == space_id) | (SpaceLink.target_space_id == space_id),
                SpaceLink.status == "active"
            ).all()
            return [link.to_dict() for link in links]
        finally:
            session.close()

    def create_space_link(
        self,
        source_space_id: str,
        target_space_id: str,
        created_by: str,
        permission: str = "read",
    ) -> Dict[str, Any]:
        """Create a cross-space collaboration link. Source space owner only."""
        from file_manager.engine import get_lifecycle_engine
        engine = get_lifecycle_engine()

        if source_space_id == target_space_id:
            raise ValueError("不能链接到自身")

        session = self._db()
        try:
            # Check ownership
            is_owner = engine.check_owner(created_by, source_space_id, session)
            if not is_owner:
                raise NotSpaceOwner("只有源空间所有者可以创建链接")

            # Check if link already exists
            existing = session.query(SpaceLink).filter(
                SpaceLink.source_space_id == source_space_id,
                SpaceLink.target_space_id == target_space_id,
                SpaceLink.status == "active"
            ).first()
            if existing:
                raise ValueError("链接已存在")

            link = SpaceLink(
                source_space_id=source_space_id,
                target_space_id=target_space_id,
                created_by=created_by,
                permission=permission,
            )
            session.add(link)
            session.commit()
            return link.to_dict()
        finally:
            session.close()

    def revoke_space_link(self, link_id: str, requesting_user_id: str) -> None:
        """Revoke a cross-space link."""
        from file_manager.engine import get_lifecycle_engine
        engine = get_lifecycle_engine()

        session = self._db()
        try:
            link = session.query(SpaceLink).filter(SpaceLink.id == link_id).first()
            if not link:
                raise ValueError("链接不存在")

            # Check ownership
            is_owner = engine.check_owner(requesting_user_id, link.source_space_id, session)
            if not is_owner:
                raise NotSpaceOwner("只有源空间所有者可以撤销链接")

            link.status = "revoked"
            session.commit()
        finally:
            session.close()

    def get_cross_team_spaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all spaces accessible through cross-team collaboration links."""
        session = self._db()
        try:
            # Find spaces where user is a member
            member_space_ids = [m.space_id for m in session.query(SpaceMember).filter(
                SpaceMember.user_id == user_id,
                SpaceMember.status == "active"
            ).all()]

            # Find cross-team links from those spaces
            links = session.query(SpaceLink).filter(
                SpaceLink.source_space_id.in_(member_space_ids),
                SpaceLink.status == "active"
            ).all()

            cross_team_spaces = []
            for link in links:
                target_space = session.query(Space).filter(Space.id == link.target_space_id).first()
                if target_space and target_space.status == "active":
                    cross_team_spaces.append({
                        "link": link.to_dict(),
                        "space": target_space.to_dict(),
                        "permission": link.permission,
                    })

            return cross_team_spaces
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # User Storage Context
    # -------------------------------------------------------------------------

    def get_user_spaces(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all spaces a user has access to."""
        session = self._db()
        try:
            memberships = session.query(SpaceMember).filter(
                SpaceMember.user_id == user_id,
                SpaceMember.status == "active"
            ).all()

            spaces = []
            for m in memberships:
                space = m.space
                if space and space.status == "active":
                    spaces.append({
                        "space": space.to_dict(),
                        "role": m.role,
                        "quota_bytes": m.quota_bytes or space.max_bytes,
                    })
            return spaces
        finally:
            session.close()

    def get_user_storage_context(self, user_id: str) -> List[Dict[str, Any]]:
        """Get storage context for all spaces a user belongs to."""
        user_spaces = self.get_user_spaces(user_id)
        contexts = []
        for item in user_spaces:
            space = item["space"]
            contexts.append({
                "space_id": space["id"],
                "space_name": space["name"],
                "space_type": space["space_type"],
                "max_bytes": item["quota_bytes"],
                "used_bytes": space["used_bytes"],
                "pool_id": space["storage_pool_id"],
            })
        return contexts

    # -------------------------------------------------------------------------
    # Activity Log
    # -------------------------------------------------------------------------

    def get_activity(
        self,
        space_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get recent activity for a space.
        Returns audit logs where extra->space_id matches this space.
        """
        session = self._db()
        try:
            # Verify space exists
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"空间 {space_id} 不存在")

            from ..engine.models import AuditLog

            # Query audit logs with space context in extra (stored as metadata column)
            from sqlalchemy import text
            if session.bind.dialect == "sqlite":
                query = session.query(AuditLog).filter(
                    text("json_extract(metadata, '$.space_id') = :space_id")
                ).params(space_id=space_id).order_by(AuditLog.created_at.desc())
            else:
                query = session.query(AuditLog).filter(
                    text("metadata->>'space_id' = :space_id")
                ).params(space_id=space_id).order_by(AuditLog.created_at.desc())

            total = query.count()
            activities = query.offset(offset).limit(limit).all()

            return {
                "space_id": space_id,
                "space_name": space.name,
                "total": total,
                "activities": [a.to_dict() for a in activities],
            }
        finally:
            session.close()
