"""
QuotaService - 四层配额计算辅助函数

提供：
- calculate_pool_available(pool_id) - 存储池可用配额
- calculate_team_quota_used(team_id) - 团队已用配额
- calculate_space_available(space_id) - 空间可用配额
- calculate_user_available(user_id) - 用户可用配额
"""

from __future__ import annotations

from typing import Optional
from sqlalchemy import func
from ..engine.models import Space, SpaceMember, StoragePool, Team, User, FileUpload


class QuotaService:
    """四层配额计算服务"""

    def __init__(self, db_factory):
        """
        Args:
            db_factory: 数据库会话工厂
        """
        self._db_factory = db_factory

    def _db(self):
        return self._db_factory()

    # =========================================================================
    # 第一层：存储池配额
    # =========================================================================

    def calculate_pool_available(self, pool_id: str) -> int:
        """
        存储池可用配额 = 总容量 - 已分配给团队的配额

        Args:
            pool_id: 存储池 ID

        Returns:
            可用字节数
        """
        session = self._db()

        pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
        if not pool:
            return 0

        # 已分配给团队的配额 = 所有团队的 max_bytes 之和
        allocated_bytes = (
            session.query(func.sum(Team.max_bytes))
            .filter(Team.storage_pool_id == pool_id)
            .scalar() or 0
        )

        return pool.total_bytes - allocated_bytes

    def calculate_pool_usage(self, pool_id: str) -> dict:
        """
        获取存储池配额使用详情

        Returns:
            dict: {total, allocated, used, available}
        """
        session = self._db()

        pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
        if not pool:
            return {"total": 0, "allocated": 0, "used": 0, "available": 0}

        allocated_bytes = (
            session.query(func.sum(Team.max_bytes))
            .filter(Team.storage_pool_id == pool_id)
            .scalar() or 0
        )

        used_bytes = (
            session.query(func.sum(Space.used_bytes))
            .join(Team, Space.team_id == Team.id)
            .filter(Team.storage_pool_id == pool_id)
            .scalar() or 0
        )

        return {
            "total": pool.total_bytes,
            "allocated": allocated_bytes,
            "used": used_bytes,
            "available": pool.total_bytes - allocated_bytes,
        }

    # =========================================================================
    # 第二层：团队配额
    # =========================================================================

    def calculate_team_quota_used(self, team_id: str) -> int:
        """
        团队已用配额 = 所有 SpaceMember quota_bytes 之和

        Args:
            team_id: 团队 ID

        Returns:
            已用字节数
        """
        session = self._db()

        # 团队已用 = 所有 space 的 used_bytes 之和
        used_bytes = (
            session.query(func.sum(Space.used_bytes))
            .filter(Space.team_id == team_id)
            .scalar() or 0
        )

        return used_bytes

    def calculate_team_allocated(self, team_id: str) -> int:
        """
        团队已分配配额 = 所有 SpaceMember quota_bytes 之和

        Args:
            team_id: 团队 ID

        Returns:
            已分配字节数
        """
        session = self._db()

        allocated_bytes = (
            session.query(func.sum(SpaceMember.quota_bytes))
            .join(Space, SpaceMember.space_id == Space.id)
            .filter(Space.team_id == team_id)
            .scalar() or 0
        )

        return allocated_bytes

    def calculate_team_available(self, team_id: str) -> int:
        """
        团队可用配额 = 团队 max_bytes - 已用配额

        Args:
            team_id: 团队 ID

        Returns:
            可用字节数
        """
        session = self._db()

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            return 0

        used = self.calculate_team_quota_used(team_id)
        return max(0, team.max_bytes - used)

    # =========================================================================
    # 第三层：空间配额
    # =========================================================================

    def calculate_space_available(self, space_id: str, user_id: str = None) -> int:
        """
        空间可用配额 = SpaceMember.quota_bytes - 已使用

        Args:
            space_id: 空间 ID
            user_id: 可选，用户 ID 用于个人空间

        Returns:
            可用字节数
        """
        session = self._db()

        space = session.query(Space).filter(Space.id == space_id).first()
        if not space:
            return 0

        if space.max_bytes > 0:
            # 团队空间：使用 Space.max_bytes
            available = space.max_bytes - space.used_bytes
            return max(0, available)
        else:
            # 个人空间：查找 SpaceMember 的 quota_bytes
            query = session.query(SpaceMember).filter(SpaceMember.space_id == space_id)
            if user_id:
                query = query.filter(SpaceMember.user_id == user_id)
            member = query.first()
            if member and member.quota_bytes:
                return max(0, member.quota_bytes - space.used_bytes)
            return 0

    def calculate_space_usage(self, space_id: str, user_id: str = None) -> dict:
        """
        获取空间配额使用详情

        Returns:
            dict: {max_bytes, used_bytes, reserved_bytes, available}
        """
        session = self._db()

        space = session.query(Space).filter(Space.id == space_id).first()
        if not space:
            return {"max_bytes": 0, "used_bytes": 0, "reserved_bytes": 0, "available": 0}

        # 预留配额（正在上传的文件）
        reserved_bytes = (
            session.query(func.sum(FileUpload.file_size))
            .filter(
                FileUpload.space_id == space_id,
                FileUpload.status.in_(["pending", "uploading"])
            )
            .scalar() or 0
        )

        # 可用配额计算
        if space.max_bytes > 0:
            max_bytes = space.max_bytes
        else:
            query = session.query(SpaceMember).filter(SpaceMember.space_id == space_id)
            if user_id:
                query = query.filter(SpaceMember.user_id == user_id)
            member = query.first()
            max_bytes = member.quota_bytes if member and member.quota_bytes else 0

        available = max(0, max_bytes - space.used_bytes - reserved_bytes)

        return {
            "max_bytes": max_bytes,
            "used_bytes": space.used_bytes,
            "reserved_bytes": reserved_bytes,
            "available": available,
        }

    # =========================================================================
    # 第四层：用户配额
    # =========================================================================

    def calculate_user_available(self, user_id: str) -> int:
        """
        用户可用配额 = 个人空间配额 - 已使用

        Args:
            user_id: 用户 ID

        Returns:
            可用字节数
        """
        session = self._db()

        # 查找用户的个人空间（space_type = 'personal'，owner_id = user_id）
        personal_spaces = (
            session.query(Space)
            .filter(
                Space.owner_id == user_id,
                Space.space_type == "personal"
            )
            .all()
        )

        total_available = 0
        for space in personal_spaces:
            available = self.calculate_space_available(space.id, user_id)
            total_available += available

        return total_available

    def calculate_user_usage(self, user_id: str) -> dict:
        """
        获取用户配额使用详情

        Returns:
            dict: {space_count, total_quota, total_used, total_available}
        """
        session = self._db()

        personal_spaces = (
            session.query(Space)
            .filter(
                Space.owner_id == user_id,
                Space.space_type == "personal"
            )
            .all()
        )

        total_quota = 0
        total_used = 0
        total_available = 0

        for space in personal_spaces:
            usage = self.calculate_space_usage(space.id, user_id)
            total_quota += usage["max_bytes"]
            total_used += usage["used_bytes"]
            total_available += usage["available"]

        return {
            "space_count": len(personal_spaces),
            "total_quota": total_quota,
            "total_used": total_used,
            "total_available": total_available,
        }

    # =========================================================================
    # 配额预警检查
    # =========================================================================

    def check_quota_warning(self, space_id: str) -> Optional[dict]:
        """
        检查配额是否触发预警阈值

        Returns:
            dict: {level, ratio, message} 或 None（无预警）
            level: "warning" (80-90%), "critical" (90-100%), "exceeded" (>100%)
        """
        session = self._db()

        space = session.query(Space).filter(Space.id == space_id).first()
        if not space or space.max_bytes == 0:
            return None

        ratio = space.used_bytes / space.max_bytes

        if ratio >= 1.0:
            return {
                "level": "exceeded",
                "ratio": ratio,
                "message": f"空间「{space.name}」配额已用尽",
            }
        elif ratio >= 0.9:
            return {
                "level": "critical",
                "ratio": ratio,
                "message": f"空间「{space.name}」配额使用率 {ratio*100:.1f}%",
            }
        elif ratio >= 0.8:
            return {
                "level": "warning",
                "ratio": ratio,
                "message": f"空间「{space.name}」配额使用率 {ratio*100:.1f}%",
            }
        return None

    # =========================================================================
    # 批量配额查询
    # =========================================================================

    def get_all_spaces_quota(self, team_id: str = None) -> list:
        """
        获取所有空间的配额信息

        Args:
            team_id: 可选，按团队筛选

        Returns:
            list: 空间配额信息列表
        """
        session = self._db()

        query = session.query(Space)
        if team_id:
            query = query.filter(Space.team_id == team_id)

        spaces = query.all()
        result = []

        for space in spaces:
            usage = self.calculate_space_usage(space.id)
            result.append({
                "space_id": space.id,
                "space_name": space.name,
                "team_id": space.team_id,
                **usage,
            })

        return result


# =============================================================================
# 独立函数接口（兼容现有代码）
# =============================================================================

def calculate_pool_available(pool_id: str, db_factory) -> int:
    """存储池可用配额"""
    service = QuotaService(db_factory)
    return service.calculate_pool_available(pool_id)


def calculate_team_quota_used(team_id: str, db_factory) -> int:
    """团队已用配额"""
    service = QuotaService(db_factory)
    return service.calculate_team_quota_used(team_id)


def calculate_space_available(space_id: str, db_factory, user_id: str = None) -> int:
    """空间可用配额"""
    service = QuotaService(db_factory)
    return service.calculate_space_available(space_id, user_id)


def calculate_user_available(user_id: str, db_factory) -> int:
    """用户可用配额"""
    service = QuotaService(db_factory)
    return service.calculate_user_available(user_id)