"""
CapacityAlertService - 容量告警服务

提供容量健康度检查、告警发送、告警历史查询等功能。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import text


class AlertType(str, Enum):
    """告警类型"""
    SOFT_WARNING = "soft_warning"        # 配额使用超过软预警阈值 (80%)
    HARD_WARNING = "hard_warning"        # 配额使用超过硬预警阈值 (95%)
    QUOTA_EXCEEDED = "quota_exceeded"   # 配额已用尽
    OVERCOMMIT_WARNING = "overcommit_warning"  # 承诺总额超过资源池


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警对象"""
    id: str
    type: str
    level: str
    space_id: str
    space_name: str
    pool_id: str
    pool_name: str
    message: str
    current_usage: float
    threshold: float
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    created_at: datetime = None


class CapacityAlertService:
    """容量告警服务"""

    def __init__(self, db_factory=None):
        self._db = db_factory

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def check_capacity_health(self) -> List[Alert]:
        """检查容量健康度"""
        from ..engine.models import StoragePool, Space, SpaceMember
        from sqlalchemy import func

        session = self._get_session()
        alerts = []

        try:
            pools = session.query(StoragePool).filter(
                StoragePool.is_active == True
            ).all()

            for pool in pools:
                actual_used = session.query(
                    func.coalesce(func.sum(SpaceMember.quota_bytes), 0)
                ).join(Space).filter(
                    Space.storage_pool_id == pool.id
                ).scalar() or 0

                usage_ratio = actual_used / pool.total_bytes if pool.total_bytes > 0 else 0

                if usage_ratio >= pool.hard_block_ratio:
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        type=AlertType.QUOTA_EXCEEDED,
                        level=AlertLevel.CRITICAL,
                        space_id=pool.id,
                        space_name=pool.name,
                        pool_id=pool.id,
                        pool_name=pool.name,
                        message=f"存储池 {pool.name} 已用尽 ({usage_ratio:.1%})",
                        current_usage=usage_ratio,
                        threshold=pool.hard_block_ratio,
                        created_at=datetime.utcnow(),
                    )
                    alerts.append(alert)

                elif usage_ratio >= pool.soft_warning_ratio:
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        type=AlertType.SOFT_WARNING,
                        level=AlertLevel.WARNING,
                        space_id=pool.id,
                        space_name=pool.name,
                        pool_id=pool.id,
                        pool_name=pool.name,
                        message=f"存储池 {pool.name} 使用率较高 ({usage_ratio:.1%})",
                        current_usage=usage_ratio,
                        threshold=pool.soft_warning_ratio,
                        created_at=datetime.utcnow(),
                    )
                    alerts.append(alert)

                committed = session.query(
                    func.coalesce(func.sum(Space.committed_bytes), 0)
                ).filter(
                    Space.storage_pool_id == pool.id,
                    Space.quota_type == "committed"
                ).scalar() or 0

                available = pool.total_bytes - pool.reserved_bytes
                if available > 0 and committed > available:
                    overcommit_ratio = committed / available
                    alert = Alert(
                        id=str(uuid.uuid4()),
                        type=AlertType.OVERCOMMIT_WARNING,
                        level=AlertLevel.WARNING,
                        space_id=pool.id,
                        space_name=pool.name,
                        pool_id=pool.id,
                        pool_name=pool.name,
                        message=f"存储池 {pool.name} 承诺配额已超出可用空间 ({overcommit_ratio:.1%})",
                        current_usage=committed,
                        threshold=available,
                        created_at=datetime.utcnow(),
                    )
                    alerts.append(alert)

            spaces = session.query(Space).all()
            for space in spaces:
                if not space.storage_pool_id:
                    continue

                member = session.query(SpaceMember).filter(
                    SpaceMember.space_id == space.id,
                    SpaceMember.role == "admin"
                ).first()

                if not member:
                    continue

                space_used_ratio = space.actual_used_bytes / space.committed_bytes if space.committed_bytes > 0 else 0

                if space.committed_bytes > 0:
                    pool = session.query(StoragePool).filter(
                        StoragePool.id == space.storage_pool_id
                    ).first()
                    pool_name = pool.name if pool else "Unknown"

                    if space_used_ratio >= 1.0:
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            type=AlertType.QUOTA_EXCEEDED,
                            level=AlertLevel.CRITICAL,
                            space_id=space.id,
                            space_name=space.name,
                            pool_id=space.storage_pool_id,
                            pool_name=pool_name,
                            message=f"空间 {space.name} 配额已用尽",
                            current_usage=space_used_ratio,
                            threshold=1.0,
                            created_at=datetime.utcnow(),
                        )
                        alerts.append(alert)
                    elif space_used_ratio >= 0.8:
                        alert = Alert(
                            id=str(uuid.uuid4()),
                            type=AlertType.SOFT_WARNING,
                            level=AlertLevel.WARNING,
                            space_id=space.id,
                            space_name=space.name,
                            pool_id=space.storage_pool_id,
                            pool_name=pool_name,
                            message=f"空间 {space.name} 配额使用率较高 ({space_used_ratio:.1%})",
                            current_usage=space_used_ratio,
                            threshold=0.8,
                            created_at=datetime.utcnow(),
                        )
                        alerts.append(alert)

            return alerts
        finally:
            session.close()

    def send_alert(self, alert: Alert) -> bool:
        """发送告警（保存到数据库）"""
        session = self._get_session()
        try:
            existing = session.execute(
                text("SELECT id FROM hfm_capacity_alerts WHERE space_id = :space_id AND type = :type AND acknowledged = 0 AND created_at > datetime('now', '-1 hour')"),
                {"space_id": alert.space_id, "type": alert.type}
            ).fetchone()

            if existing:
                return False

            session.execute(
                text("""
                    INSERT INTO hfm_capacity_alerts
                    (id, type, level, space_id, space_name, pool_id, pool_name,
                    message, current_usage, threshold, acknowledged, created_at)
                    VALUES (:id, :type, :level, :space_id, :space_name, :pool_id, :pool_name,
                    :message, :current_usage, :threshold, :acknowledged, :created_at)
                """),
                {
                    "id": alert.id,
                    "type": alert.type,
                    "level": alert.level,
                    "space_id": alert.space_id,
                    "space_name": alert.space_name,
                    "pool_id": alert.pool_id,
                    "pool_name": alert.pool_name,
                    "message": alert.message,
                    "current_usage": alert.current_usage,
                    "threshold": alert.threshold,
                    "acknowledged": 0,
                    "created_at": alert.created_at.isoformat() if alert.created_at else datetime.utcnow().isoformat(),
                }
            )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """确认告警"""
        session = self._get_session()
        try:
            session.execute(
                text("""
                    UPDATE hfm_capacity_alerts SET
                    acknowledged = 1, acknowledged_by = :acknowledged_by, acknowledged_at = :acknowledged_at
                    WHERE id = :alert_id
                """),
                {"acknowledged_by": acknowledged_by, "acknowledged_at": datetime.utcnow().isoformat(), "alert_id": alert_id}
            )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_alert_history(
        self,
        space_id: str = None,
        pool_id: str = None,
        acknowledged: bool = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取告警历史"""
        session = self._get_session()
        try:
            query = "SELECT * FROM hfm_capacity_alerts WHERE 1=1"
            params = {}

            if space_id:
                query += " AND space_id = :space_id"
                params["space_id"] = space_id

            if pool_id:
                query += " AND pool_id = :pool_id"
                params["pool_id"] = pool_id

            if acknowledged is not None:
                query += " AND acknowledged = :acknowledged"
                params["acknowledged"] = 1 if acknowledged else 0

            query += " ORDER BY created_at DESC LIMIT :limit"
            params["limit"] = limit

            results = session.execute(text(query), params).fetchall()
            return [dict(r._mapping) for r in results]
        finally:
            session.close()

    def get_unacknowledged_alerts(self) -> List[Dict[str, Any]]:
        """获取未确认告警"""
        session = self._get_session()
        try:
            results = session.execute(
                text("""
                    SELECT * FROM hfm_capacity_alerts
                    WHERE acknowledged = 0
                    ORDER BY level DESC, created_at DESC
                """)
            ).fetchall()

            return [dict(r._mapping) for r in results]
        finally:
            session.close()

    def check_and_alert(self) -> List[Alert]:
        """检查容量并发送告警"""
        alerts = self.check_capacity_health()
        sent_alerts = []

        for alert in alerts:
            if self.send_alert(alert):
                sent_alerts.append(alert)

        return sent_alerts


# Module exports
__all__ = [
    "CapacityAlertService",
    "AlertType",
    "AlertLevel",
    "Alert",
]
