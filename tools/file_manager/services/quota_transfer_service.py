"""
QuotaTransferService - 配额调配服务

提供配额调配申请、审批、拒绝、过期等功能。
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..engine.models import Space, SpaceMember, User, QuotaTransfer


@dataclass
class QuotaTransferRequest:
    """配额调配请求"""
    from_space_id: str
    to_space_id: str
    transfer_bytes: int
    reason: str
    requested_by: str
    duration_days: int = 7  # 默认7天过期


class QuotaTransferService:
    """配额调配服务"""

    def __init__(self, db_factory=None):
        self._db = db_factory

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def request_transfer(self, request: QuotaTransferRequest) -> Dict[str, Any]:
        """
        申请配额调配
        """
        session = self._get_session()
        try:
            from_space = session.query(Space).filter(
                Space.id == request.from_space_id
            ).first()

            if not from_space:
                raise ValueError(f"源空间 {request.from_space_id} 不存在")

            if from_space.owner_id != request.requested_by:
                raise ValueError("只能调配自己拥有的空间")

            to_space = session.query(Space).filter(
                Space.id == request.to_space_id
            ).first()

            if not to_space:
                raise ValueError(f"目标空间 {request.to_space_id} 不存在")

            if from_space.committed_bytes < request.transfer_bytes:
                raise ValueError(
                    f"源空间配额不足，需要 {request.transfer_bytes} 字节，"
                    f"但只有 {from_space.committed_bytes} 字节"
                )

            expires_at = datetime.utcnow() + timedelta(days=request.duration_days)

            transfer = QuotaTransfer(
                from_space_id=request.from_space_id,
                to_space_id=request.to_space_id,
                transfer_bytes=request.transfer_bytes,
                reason=request.reason,
                requested_by=request.requested_by,
                status="pending",
                expires_at=expires_at,
            )
            session.add(transfer)
            session.commit()
            session.refresh(transfer)

            return transfer.to_dict()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def approve_transfer(self, transfer_id: str, approved_by: str) -> bool:
        """审批配额调配通过"""
        session = self._get_session()
        try:
            transfer = session.query(QuotaTransfer).filter(
                QuotaTransfer.id == transfer_id,
                QuotaTransfer.status == "pending"
            ).first()

            if not transfer:
                raise ValueError(f"调配记录 {transfer_id} 不存在或已处理")

            from_space = session.query(Space).filter(
                Space.id == transfer.from_space_id
            ).first()
            to_space = session.query(Space).filter(
                Space.id == transfer.to_space_id
            ).first()

            if from_space:
                from_space.committed_bytes -= transfer.transfer_bytes
            if to_space:
                to_space.committed_bytes += transfer.transfer_bytes

            transfer.status = "approved"
            transfer.approved_by = approved_by
            transfer.updated_at = datetime.utcnow()

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def reject_transfer(self, transfer_id: str, rejected_by: str, reason: str) -> bool:
        """拒绝配额调配"""
        session = self._get_session()
        try:
            transfer = session.query(QuotaTransfer).filter(
                QuotaTransfer.id == transfer_id,
                QuotaTransfer.status == "pending"
            ).first()

            if not transfer:
                raise ValueError(f"调配记录 {transfer_id} 不存在或已处理")

            transfer.status = "rejected"
            transfer.approved_by = rejected_by
            transfer.rejection_reason = reason
            transfer.updated_at = datetime.utcnow()

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def expire_transfer(self, transfer_id: str) -> bool:
        """过期配额调配"""
        session = self._get_session()
        try:
            transfer = session.query(QuotaTransfer).filter(
                QuotaTransfer.id == transfer_id,
                QuotaTransfer.status == "pending",
                QuotaTransfer.expires_at < datetime.utcnow()
            ).first()

            if not transfer:
                return False

            transfer.status = "expired"
            transfer.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def expire_all_pending(self) -> int:
        """过期所有已到期的调配"""
        session = self._get_session()
        try:
            expired = session.query(QuotaTransfer).filter(
                QuotaTransfer.status == "pending",
                QuotaTransfer.expires_at < datetime.utcnow()
            ).all()

            count = 0
            for transfer in expired:
                transfer.status = "expired"
                transfer.updated_at = datetime.utcnow()
                count += 1

            session.commit()
            return count
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_pending_transfers(self) -> List[Dict[str, Any]]:
        """获取待审批调配列表"""
        session = self._get_session()
        try:
            transfers = session.query(QuotaTransfer).filter(
                QuotaTransfer.status == "pending"
            ).order_by(QuotaTransfer.created_at.asc()).all()
            return [t.to_dict() for t in transfers]
        finally:
            session.close()

    def get_transfer_history(
        self,
        space_id: str = None,
        user_id: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """获取调配历史"""
        session = self._get_session()
        try:
            query = session.query(QuotaTransfer)
            if space_id:
                query = query.filter(
                    or_(
                        QuotaTransfer.from_space_id == space_id,
                        QuotaTransfer.to_space_id == space_id
                    )
                )
            if user_id:
                query = query.filter(QuotaTransfer.requested_by == user_id)

            transfers = query.order_by(
                QuotaTransfer.created_at.desc()
            ).limit(limit).all()
            return [t.to_dict() for t in transfers]
        finally:
            session.close()

    def cancel_transfer(self, transfer_id: str, user_id: str) -> bool:
        """取消调配申请"""
        session = self._get_session()
        try:
            transfer = session.query(QuotaTransfer).filter(
                QuotaTransfer.id == transfer_id,
                QuotaTransfer.requested_by == user_id,
                QuotaTransfer.status == "pending"
            ).first()

            if not transfer:
                return False

            transfer.status = "cancelled"
            transfer.updated_at = datetime.utcnow()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


# Module exports
__all__ = [
    "QuotaTransferService",
    "QuotaTransferRequest",
]
