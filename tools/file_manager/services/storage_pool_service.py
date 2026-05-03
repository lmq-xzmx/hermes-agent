"""
StoragePoolService - 存储池管理服务

提供存储池统计、配额检查、配额分配回收等功能。
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..engine.models import StoragePool, Space, SpaceMember


@dataclass
class PoolStats:
    """存储池统计信息"""
    pool_id: str
    total_bytes: int
    reserved_bytes: int
    committed_bytes: int  # 已承诺配额总和
    actual_used_bytes: int
    available_for_commit: int
    usage_ratio: float
    overcommit_ratio: float
    status: str  # normal | warning | critical


@dataclass
class WriteResult:
    """写入检查结果"""
    allowed: bool
    reason: Optional[str] = None
    available_bytes: int = 0
    warning_level: Optional[str] = None  # soft | hard | none


class StoragePoolService:
    """存储池管理服务"""

    def __init__(self, db_factory=None):
        self._db = db_factory

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def get_pool_stats(self, pool_id: str = None) -> PoolStats:
        """
        获取存储池统计信息

        Args:
            pool_id: 存储池ID，如果为None则返回默认池

        Returns:
            PoolStats 对象
        """
        session = self._get_session()
        try:
            query = session.query(StoragePool)
            if pool_id:
                query = query.filter(StoragePool.id == pool_id)

            pool = query.first()
            if not pool:
                raise ValueError(f"存储池 {pool_id} 不存在")

            # 计算已承诺配额总和 (所有 Space 的 committed_bytes 之和)
            committed = session.query(
                func.coalesce(func.sum(Space.committed_bytes), 0)
            ).filter(
                Space.storage_pool_id == pool_id,
                Space.quota_type == "committed"
            ).scalar() or 0

            # 计算实际使用量
            actual_used = session.query(
                func.coalesce(func.sum(SpaceMember.quota_bytes), 0)
            ).join(Space).filter(
                Space.storage_pool_id == pool_id
            ).scalar() or 0

            # 可用配额 = 总容量 - 预留 - 已承诺
            available = pool.total_bytes - pool.reserved_bytes - committed

            # 使用率
            usage_ratio = actual_used / pool.total_bytes if pool.total_bytes > 0 else 0

            # 透支率 = 已承诺 / (总容量 - 预留)
            total_available = pool.total_bytes - pool.reserved_bytes
            overcommit_ratio = committed / total_available if total_available > 0 else 0

            # 状态判断
            if usage_ratio >= pool.hard_block_ratio:
                status = "critical"
            elif usage_ratio >= pool.soft_warning_ratio:
                status = "warning"
            else:
                status = "normal"

            return PoolStats(
                pool_id=pool.id,
                total_bytes=pool.total_bytes,
                reserved_bytes=pool.reserved_bytes,
                committed_bytes=committed,
                actual_used_bytes=actual_used,
                available_for_commit=available,
                usage_ratio=round(usage_ratio, 4),
                overcommit_ratio=round(overcommit_ratio, 4),
                status=status
            )
        finally:
            session.close()

    def get_all_pools_stats(self) -> List[PoolStats]:
        """获取所有存储池的统计信息"""
        session = self._get_session()
        try:
            pools = session.query(StoragePool).all()
            return [self.get_pool_stats(pool.id) for pool in pools]
        finally:
            session.close()

    def check_write_allowed(
        self,
        space_id: str,
        file_size: int,
    ) -> WriteResult:
        """
        检查写入是否允许

        Args:
            space_id: 空间ID
            file_size: 拟写入的文件大小

        Returns:
            WriteResult 对象
        """
        session = self._get_session()
        try:
            # 获取 Space 和关联的 Pool
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                return WriteResult(allowed=False, reason="空间不存在")

            if not space.storage_pool_id:
                return WriteResult(allowed=True)  # 个人空间不受存储池限制

            pool = session.query(StoragePool).filter(
                StoragePool.id == space.storage_pool_id
            ).first()

            if not pool:
                return WriteResult(allowed=True)

            # 计算当前已使用量
            current_used = session.query(
                func.coalesce(func.sum(SpaceMember.quota_bytes), 0)
            ).join(Space).filter(
                Space.storage_pool_id == space.storage_pool_id
            ).scalar() or 0

            available = pool.total_bytes - current_used

            # 检查是否有空间写入
            if file_size > available:
                if not pool.allow_overcommit:
                    return WriteResult(
                        allowed=False,
                        reason=f"存储空间不足，需要 {file_size} 字节，但只有 {available} 字节可用",
                        available_bytes=available,
                        warning_level="hard"
                    )
                elif available < 0:
                    return WriteResult(
                        allowed=False,
                        reason="存储池已透支，无法继续写入",
                        available_bytes=0,
                        warning_level="hard"
                    )

            # 计算预警级别
            new_usage = (current_used + file_size) / pool.total_bytes
            warning_level = "none"
            if new_usage >= pool.hard_block_ratio:
                warning_level = "hard"
            elif new_usage >= pool.soft_warning_ratio:
                warning_level = "soft"

            return WriteResult(
                allowed=True,
                available_bytes=available - file_size,
                warning_level=warning_level
            )
        finally:
            session.close()

    def allocate_quota(self, space_id: str, committed_bytes: int) -> bool:
        """
        分配配额给空间

        Args:
            space_id: 空间ID
            committed_bytes: 承诺配额大小

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise ValueError(f"空间 {space_id} 不存在")

            # 检查存储池是否有足够配额
            pool_stats = self.get_pool_stats(space.storage_pool_id)
            if committed_bytes > pool_stats.available_for_commit:
                raise ValueError(
                    f"存储池配额不足，需要 {committed_bytes} 字节，但只有 "
                    f"{pool_stats.available_for_commit} 字节可用"
                )

            space.committed_bytes = committed_bytes
            space.quota_type = "committed"
            space.updated_at = datetime.utcnow()

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def reclaim_quota(self, space_id: str) -> bool:
        """
        回收空间的配额

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

            space.committed_bytes = 0
            space.quota_type = "unlimited"
            space.source_id = None
            space.updated_at = datetime.utcnow()

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_pool_config(
        self,
        pool_id: str,
        reserved_bytes: int = None,
        allow_overcommit: bool = None,
        soft_warning_ratio: float = None,
        hard_block_ratio: float = None,
        buffer_ratio: float = None,
    ) -> bool:
        """
        更新存储池配置

        Args:
            pool_id: 存储池ID
            reserved_bytes: 预留空间
            allow_overcommit: 是否允许透支
            soft_warning_ratio: 软预警阈值
            hard_block_ratio: 硬阻塞阈值
            buffer_ratio: 缓冲比例

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                raise ValueError(f"存储池 {pool_id} 不存在")

            if reserved_bytes is not None:
                pool.reserved_bytes = reserved_bytes
            if allow_overcommit is not None:
                pool.allow_overcommit = allow_overcommit
            if soft_warning_ratio is not None:
                pool.soft_warning_ratio = soft_warning_ratio
            if hard_block_ratio is not None:
                pool.hard_block_ratio = hard_block_ratio
            if buffer_ratio is not None:
                pool.buffer_ratio = buffer_ratio

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_pool(self, pool_id: str) -> Optional[Dict[str, Any]]:
        """获取存储池详情"""
        session = self._get_session()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                return None

            return {
                "id": pool.id,
                "name": pool.name,
                "protocol": pool.protocol,
                "base_path": pool.base_path,
                "total_bytes": pool.total_bytes,
                "reserved_bytes": pool.reserved_bytes,
                "allow_overcommit": pool.allow_overcommit,
                "soft_warning_ratio": pool.soft_warning_ratio,
                "hard_block_ratio": pool.hard_block_ratio,
                "buffer_ratio": pool.buffer_ratio,
                "status": pool.status,
                "is_active": pool.is_active,
                "created_at": pool.created_at.isoformat() if pool.created_at else None,
            }
        finally:
            session.close()


# Module exports
__all__ = [
    "StoragePoolService",
    "PoolStats",
    "WriteResult",
]
