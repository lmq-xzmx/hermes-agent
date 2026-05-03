"""
ResourcePlanService - 资源套餐服务

提供套餐查询、订阅、升级、超用费用计算等功能。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from ..engine.models import User, Space, SpaceMember


@dataclass
class UsageFee:
    """超用费用"""
    user_id: str
    plan_id: str
    base_fee: Decimal
    overage_fee: Decimal
    total_fee: Decimal
    usage_bytes: int
    included_bytes: int
    overage_bytes: int


class ResourcePlanService:
    """资源套餐服务"""

    # 内置套餐定义
    BUILTIN_PLANS = [
        {
            "id": "free",
            "name": "免费版",
            "plan_type": "free",
            "quota_bytes": 10 * 1024 * 1024 * 1024,  # 10GB
            "price_monthly": Decimal("0"),
            "price_yearly": Decimal("0"),
            "overage_allowed": False,
            "max_overage_bytes": 0,
            "features": ["基础存储", "有限协作"],
            "is_active": True,
            "sort_order": 1,
        },
        {
            "id": "starter",
            "name": "入门版",
            "plan_type": "starter",
            "quota_bytes": 100 * 1024 * 1024 * 1024,  # 100GB
            "price_monthly": Decimal("29"),
            "price_yearly": Decimal("290"),
            "overage_allowed": True,
            "max_overage_bytes": 50 * 1024 * 1024 * 1024,  # 50GB
            "features": ["更大存储", "团队协作", "技术支持"],
            "is_active": True,
            "sort_order": 2,
        },
        {
            "id": "professional",
            "name": "专业版",
            "plan_type": "professional",
            "quota_bytes": 1024 * 1024 * 1024 * 1024,  # 1TB
            "price_monthly": Decimal("99"),
            "price_yearly": Decimal("990"),
            "overage_allowed": True,
            "max_overage_bytes": 500 * 1024 * 1024 * 1024,  # 500GB
            "features": ["海量存储", "高级协作", "优先支持", "数据分析"],
            "is_active": True,
            "sort_order": 3,
        },
        {
            "id": "enterprise",
            "name": "企业版",
            "plan_type": "enterprise",
            "quota_bytes": 10 * 1024 * 1024 * 1024 * 1024,  # 10TB
            "price_monthly": Decimal("299"),
            "price_yearly": Decimal("2990"),
            "overage_allowed": True,
            "max_overage_bytes": 0,  # 无限制
            "features": ["无限扩展", "企业级安全", "专属支持", "高级分析", "定制化"],
            "is_active": True,
            "sort_order": 4,
        },
    ]

    def __init__(self, db_factory=None):
        self._db = db_factory

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def get_available_plans(self) -> List[Dict[str, Any]]:
        """
        获取可用套餐列表

        Returns:
            套餐列表
        """
        # 返回内置套餐
        return self.BUILTIN_PLANS

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        获取套餐详情

        Args:
            plan_id: 套餐ID

        Returns:
            套餐详情
        """
        for plan in self.BUILTIN_PLANS:
            if plan["id"] == plan_id:
                return plan
        return None

    def subscribe_plan(self, user_id: str, plan_id: str) -> bool:
        """
        订阅套餐

        Args:
            user_id: 用户ID
            plan_id: 套餐ID

        Returns:
            是否成功
        """
        session = self._get_session()
        try:
            # 验证用户存在
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"用户 {user_id} 不存在")

            # 获取套餐
            plan = self.get_plan(plan_id)
            if not plan:
                raise ValueError(f"套餐 {plan_id} 不存在")

            # 创建或更新用户订阅记录
            from ..engine.models import Subscription

            existing = session.query(Subscription).filter(
                Subscription.user_id == user_id
            ).first()

            now = datetime.utcnow()
            expires_at = now + timedelta(days=30)  # 默认30天

            if existing:
                existing.plan_id = plan_id
                existing.status = "active"
                existing.started_at = now
                existing.expires_at = expires_at
            else:
                subscription = Subscription(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    plan_id=plan_id,
                    status="active",
                    started_at=now,
                    expires_at=expires_at,
                    billing_cycle="monthly",
                    auto_renew=True,
                )
                session.add(subscription)

            # 为用户创建个人空间（如果没有）
            personal_space = session.query(Space).filter(
                Space.owner_id == user_id,
                Space.team_id == None
            ).first()

            if personal_space:
                # 更新配额
                personal_space.committed_bytes = plan["quota_bytes"]
                personal_space.quota_type = "committed"
                personal_space.quota_source = "personal"
                personal_space.source_id = user_id
            else:
                # 创建个人空间
                space = Space(
                    id=str(uuid.uuid4()),
                    name=f"{user.username} 的空间",
                    type="private",
                    owner_id=user_id,
                    team_id=None,
                    quota_type="committed",
                    committed_bytes=plan["quota_bytes"],
                    actual_used_bytes=0,
                    quota_source="personal",
                    source_id=user_id,
                    created_at=now,
                    updated_at=now,
                )
                session.add(space)

                # 创建 SpaceMember
                member = SpaceMember(
                    id=str(uuid.uuid4()),
                    space_id=space.id,
                    user_id=user_id,
                    role="admin",
                    status="active",
                    quota_bytes=plan["quota_bytes"],
                    joined_at=now,
                )
                session.add(member)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def upgrade_plan(self, user_id: str, new_plan_id: str) -> bool:
        """
        升级套餐

        Args:
            user_id: 用户ID
            new_plan_id: 新套餐ID

        Returns:
            是否成功
        """
        return self.subscribe_plan(user_id, new_plan_id)

    def get_user_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取用户订阅信息

        Args:
            user_id: 用户ID

        Returns:
            订阅信息
        """
        session = self._get_session()
        try:
            from ..engine.models import Subscription

            sub = session.query(Subscription).filter(
                Subscription.user_id == user_id,
                Subscription.status == "active"
            ).first()

            if not sub:
                return None

            plan = self.get_plan(sub.plan_id)

            return {
                "id": sub.id,
                "user_id": sub.user_id,
                "plan_id": sub.plan_id,
                "plan_name": plan["name"] if plan else "Unknown",
                "status": sub.status,
                "started_at": sub.started_at.isoformat() if sub.started_at else None,
                "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
                "billing_cycle": sub.billing_cycle,
                "auto_renew": sub.auto_renew,
            }
        finally:
            session.close()

    def get_user_usage(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户使用量

        Args:
            user_id: 用户ID

        Returns:
            使用量信息
        """
        session = self._get_session()
        try:
            # 获取用户订阅
            sub = self.get_user_subscription(user_id)
            plan_quota = sub["plan"]["quota_bytes"] if sub else 0

            # 计算用户实际使用量
            # 1. 个人空间使用量 (space_type == "private")
            personal_space = session.query(Space).filter(
                Space.owner_id == user_id,
                Space.space_type == "private"
            ).first()

            personal_used = personal_space.actual_used_bytes if personal_space else 0

            # 2. 团队空间使用量（作为成员）
            memberships = session.query(SpaceMember).filter(
                SpaceMember.user_id == user_id,
                SpaceMember.status == "active"
            ).all()

            team_spaces = []
            total_team_used = 0
            for m in memberships:
                space = session.query(Space).filter(Space.id == m.space_id).first()
                if space and space.space_type == "team":
                    team_spaces.append({
                        "space_id": space.id,
                        "space_name": space.name,
                        "quota_bytes": m.quota_bytes,
                        "used_bytes": space.actual_used_bytes,
                    })
                    total_team_used += space.actual_used_bytes

            total_used = personal_used + total_team_used
            available = plan_quota - total_used if plan_quota > 0 else 0

            return {
                "user_id": user_id,
                "plan_quota_bytes": plan_quota,
                "personal_used_bytes": personal_used,
                "team_used_bytes": total_team_used,
                "total_used_bytes": total_used,
                "available_bytes": available,
                "usage_ratio": total_used / plan_quota if plan_quota > 0 else 0,
                "team_spaces": team_spaces,
            }
        finally:
            session.close()

    def calculate_usage_fee(self, user_id: str) -> UsageFee:
        """
        计算超用费用

        Args:
            user_id: 用户ID

        Returns:
            超用费用信息
        """
        usage = self.get_user_usage(user_id)
        sub = self.get_user_subscription(user_id)

        if not sub:
            return UsageFee(
                user_id=user_id,
                plan_id="",
                base_fee=Decimal("0"),
                overage_fee=Decimal("0"),
                total_fee=Decimal("0"),
                usage_bytes=0,
                included_bytes=0,
                overage_bytes=0,
            )

        plan = sub["plan"]
        included_bytes = plan["quota_bytes"]
        usage_bytes = usage["total_used_bytes"]
        overage_bytes = max(0, usage_bytes - included_bytes)

        # 计算基础费用（简化处理）
        base_fee = plan["price_monthly"]

        # 计算超用费用（如果允许超用）
        overage_fee = Decimal("0")
        if plan["overage_allowed"] and overage_bytes > 0:
            max_overage = plan.get("max_overage_bytes", 0)
            if max_overage > 0:
                overage_bytes = min(overage_bytes, max_overage)

            # 按 GB 计算，每 GB 0.1 元
            overage_gb = overage_bytes / (1024 * 1024 * 1024)
            overage_fee = Decimal(str(overage_gb * 0.1))

        return UsageFee(
            user_id=user_id,
            plan_id=sub["plan_id"],
            base_fee=base_fee,
            overage_fee=overage_fee,
            total_fee=base_fee + overage_fee,
            usage_bytes=usage_bytes,
            included_bytes=included_bytes,
            overage_bytes=overage_bytes,
        )


# Module exports
__all__ = [
    "ResourcePlanService",
    "UsageFee",
]
