"""
SubscriptionService - 商业化订阅管理服务

提供：
- 订阅检查逻辑
- 配额自动分配（基于订阅）
- 订阅管理 API

T10: 商业化配额预留
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal

from ..engine.models import Subscription, ResourcePlan, User, Space, SpaceMember


class SubscriptionService:
    """商业化订阅管理服务"""

    def __init__(self, db_factory):
        self._db_factory = db_factory

    def _db(self):
        return self._db_factory()

    # =========================================================================
    # 订阅计划管理
    # =========================================================================

    def create_plan(
        self,
        name: str,
        storage_bytes: int,
        team_count: int,
        member_count: int,
        price_monthly: float,
        price_yearly: float,
        description: Optional[str] = None,
    ) -> ResourcePlan:
        """创建资源计划（管理员）"""
        session = self._db()
        try:
            plan = ResourcePlan(
                name=name,
                description=description,
                storage_bytes=storage_bytes,
                team_count=team_count,
                member_count=member_count,
                price_monthly=Decimal(str(price_monthly)),
                price_yearly=Decimal(str(price_yearly)),
                is_active=True,
            )
            session.add(plan)
            session.commit()
            session.refresh(plan)
            return plan
        finally:
            session.close()

    def get_plan(self, plan_id: str) -> Optional[ResourcePlan]:
        """获取资源计划详情"""
        session = self._db()
        try:
            return session.query(ResourcePlan).filter(ResourcePlan.id == plan_id).first()
        finally:
            session.close()

    def list_active_plans(self) -> List[ResourcePlan]:
        """列出所有活跃的资源计划"""
        session = self._db()
        try:
            return session.query(ResourcePlan).filter(ResourcePlan.is_active == True).all()
        finally:
            session.close()

    def deactivate_plan(self, plan_id: str) -> bool:
        """停用一个资源计划（不影响现有订阅）"""
        session = self._db()
        try:
            plan = session.query(ResourcePlan).filter(ResourcePlan.id == plan_id).first()
            if not plan:
                return False
            plan.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    # =========================================================================
    # 订阅管理
    # =========================================================================

    def subscribe(
        self,
        user_id: str,
        plan_id: str,
        billing_cycle: str = "monthly",
        auto_renew: bool = True,
    ) -> Subscription:
        """
        创建用户订阅

        Args:
            user_id: 用户ID
            plan_id: 计划ID
            billing_cycle: 计费周期 ("monthly" 或 "yearly")
            auto_renew: 是否自动续费

        Returns:
            订阅记录
        """
        session = self._db()
        try:
            plan = session.query(ResourcePlan).filter(ResourcePlan.id == plan_id).first()
            if not plan:
                raise ValueError(f"Plan {plan_id} not found or inactive")

            # 计算过期时间
            if billing_cycle == "yearly":
                expires_at = datetime.utcnow() + timedelta(days=365)
            else:
                expires_at = datetime.utcnow() + timedelta(days=30)

            subscription = Subscription(
                user_id=user_id,
                plan_id=plan_id,
                status="active",
                started_at=datetime.utcnow(),
                expires_at=expires_at,
                billing_cycle=billing_cycle,
                auto_renew=auto_renew,
            )
            session.add(subscription)
            session.commit()
            session.refresh(subscription)
            return subscription
        finally:
            session.close()

    def get_user_subscription(self, user_id: str) -> Optional[Subscription]:
        """获取用户当前活跃订阅"""
        session = self._db()
        try:
            return (
                session.query(Subscription)
                .filter(
                    Subscription.user_id == user_id,
                    Subscription.status == "active",
                )
                .first()
            )
        finally:
            session.close()

    def cancel_subscription(self, subscription_id: str, user_id: str) -> bool:
        """取消订阅"""
        session = self._db()
        try:
            sub = session.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id,
            ).first()
            if not sub:
                return False
            sub.status = "cancelled"
            session.commit()
            return True
        finally:
            session.close()

    def renew_subscription(self, subscription_id: str) -> Subscription:
        """续费订阅"""
        session = self._db()
        try:
            sub = session.query(Subscription).filter(Subscription.id == subscription_id).first()
            if not sub or sub.status != "active":
                raise ValueError("Invalid subscription")

            # 延长过期时间
            if sub.billing_cycle == "yearly":
                sub.expires_at = sub.expires_at + timedelta(days=365)
            else:
                sub.expires_at = sub.expires_at + timedelta(days=30)

            session.commit()
            session.refresh(sub)
            return sub
        finally:
            session.close()

    def list_user_subscriptions(self, user_id: str) -> List[Subscription]:
        """列出用户所有订阅（包括历史）"""
        session = self._db()
        try:
            return (
                session.query(Subscription)
                .filter(Subscription.user_id == user_id)
                .order_by(Subscription.created_at.desc())
                .all()
            )
        finally:
            session.close()

    # =========================================================================
    # 订阅检查逻辑
    # =========================================================================

    def check_subscription_active(self, user_id: str) -> bool:
        """检查用户是否有活跃订阅"""
        sub = self.get_user_subscription(user_id)
        return sub is not None and sub.is_active()

    def get_subscription_quotas(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户订阅配额信息

        Returns:
            dict: {has_subscription, plan_name, storage_bytes, teams_remaining, members_remaining}
        """
        sub = self.get_user_subscription(user_id)
        if not sub or not sub.is_active():
            return {
                "has_subscription": False,
                "plan_name": None,
                "storage_bytes": 0,
                "teams_remaining": 0,
                "members_remaining": 0,
            }

        plan = sub.plan
        return {
            "has_subscription": True,
            "plan_name": plan.name,
            "storage_bytes": plan.storage_bytes,
            "teams_remaining": plan.team_count,
            "members_remaining": plan.member_count,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        }

    def can_create_team(self, user_id: str) -> bool:
        """检查用户是否可以创建新团队"""
        quotas = self.get_subscription_quotas(user_id)
        if not quotas["has_subscription"]:
            return False

        from ..engine.models import Team
        session = self._db()
        try:
            user_team_count = session.query(Team).filter(Team.owner_id == user_id).count()
            return user_team_count < quotas["teams_remaining"]
        finally:
            session.close()

    def can_add_member(self, user_id: str) -> bool:
        """检查用户是否可以添加新成员"""
        quotas = self.get_subscription_quotas(user_id)
        if not quotas["has_subscription"]:
            return False

        from ..engine.models import SpaceMember
        session = self._db()
        try:
            member_count = session.query(SpaceMember).join(Space).filter(
                Space.owner_id == user_id
            ).count()
            return member_count < quotas["members_remaining"]
        finally:
            session.close()

    # =========================================================================
    # 配额自动分配（基于订阅）
    # =========================================================================

    def allocate_quota_from_subscription(
        self,
        user_id: str,
        space_id: str,
        default_quota_bytes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        根据用户订阅自动分配空间配额

        Args:
            user_id: 用户ID
            space_id: 空间ID
            default_quota_bytes: 默认配额（未订阅时使用）

        Returns:
            dict: {allocated, quota_bytes, source}
        """
        session = self._db()
        try:
            sub = self.get_user_subscription(user_id)
            space = session.query(Space).filter(Space.id == space_id).first()

            if not space:
                return {"allocated": False, "quota_bytes": 0, "source": "none"}

            if sub and sub.is_active():
                # 基于订阅分配
                plan = sub.plan
                # 平均分配给团队成员
                quota_bytes = plan.storage_bytes // max(plan.member_count, 1)
                space.max_bytes = quota_bytes
                session.commit()
                return {
                    "allocated": True,
                    "quota_bytes": quota_bytes,
                    "source": f"subscription:{plan.name}",
                }
            elif default_quota_bytes:
                # 使用默认配额
                space.max_bytes = default_quota_bytes
                session.commit()
                return {
                    "allocated": True,
                    "quota_bytes": default_quota_bytes,
                    "source": "default",
                }
            else:
                return {"allocated": False, "quota_bytes": 0, "source": "none"}
        finally:
            session.close()

    # =========================================================================
    # 订阅统计
    # =========================================================================

    def get_subscription_stats(self) -> Dict[str, Any]:
        """获取订阅统计信息（管理员）"""
        session = self._db()
        try:
            total_subs = session.query(Subscription).count()
            active_subs = session.query(Subscription).filter(
                Subscription.status == "active"
            ).count()
            expired_subs = session.query(Subscription).filter(
                Subscription.status == "active",
                Subscription.expires_at < datetime.utcnow(),
            ).count()

            # 收入统计
            active_list = session.query(Subscription).filter(
                Subscription.status == "active"
            ).all()

            monthly_revenue = 0.0
            yearly_revenue = 0.0
            for sub in active_list:
                plan = sub.plan
                if sub.billing_cycle == "monthly":
                    monthly_revenue += float(plan.price_monthly)
                else:
                    yearly_revenue += float(plan.price_yearly)

            return {
                "total_subscriptions": total_subs,
                "active_subscriptions": active_subs,
                "expired_subscriptions": expired_subs,
                "monthly_recurring_revenue": monthly_revenue,
                "yearly_recurring_revenue": yearly_revenue,
            }
        finally:
            session.close()