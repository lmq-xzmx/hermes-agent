"""
ApprovalService - 审批业务流程服务

实现审批申请创建、审批处理、审批后触发逻辑。

T5 任务依赖 T4 审批数据模型（ApprovalRequest, ApprovalRecord, ApprovalType, RequestStatus）
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path

from ..engine.models import (
    ApprovalRequest, ApprovalRecord, ApprovalType, RequestStatus,
    User, Space, SpaceMember, Team, Base
)


def _get_default_session_factory() -> Callable[[], Session]:
    """获取默认数据库会话工厂"""
    db_path = Path.home() / ".hermes" / "file_manager" / "hfm.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)


_default_session_factory = None


def _get_default_db():
    """获取默认数据库会话"""
    global _default_session_factory
    if _default_session_factory is None:
        _default_session_factory = _get_default_session_factory()
    return _default_session_factory()


# =============================================================================
# Domain Errors
# =============================================================================

class ApprovalNotFound(Exception):
    """审批申请不存在。"""
    pass


class ApprovalInvalidStatus(Exception):
    """审批状态无效，无法执行操作。"""
    pass


class NotAuthorized(Exception):
    """无权执行此操作。"""
    pass


# =============================================================================
# ApprovalService
# =============================================================================

class ApprovalService:
    """审批业务流程服务"""

    def __init__(self, db_factory=None):
        self._db = db_factory or _get_default_db

    def _get_session(self):
        """获取数据库会话"""
        if callable(self._db):
            return self._db()
        return self._db

    def create_approval_request(
        self,
        approval_type: str,
        applicant_id: str,
        target_id: Optional[str] = None,
        reason: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建审批申请

        Args:
            approval_type: 审批类型 (join_team, private_space, quota_extend, etc.)
            applicant_id: 申请人ID
            target_id: 目标资源ID
            reason: 申请理由
            params: 额外参数

        Returns:
            审批申请信息字典
        """
        session = self._get_session()
        try:
            # 验证申请人存在
            applicant = session.query(User).filter(User.id == applicant_id).first()
            if not applicant:
                raise ValueError(f"申请人 {applicant_id} 不存在")

            # 创建审批申请
            request = ApprovalRequest(
                id=str(uuid.uuid4()),
                type=approval_type,
                applicant_id=applicant_id,
                target_id=target_id,
                reason=reason,
                params=params or {},
                status=RequestStatus.PENDING.value,
                created_at=datetime.utcnow(),
            )

            session.add(request)
            session.commit()
            session.refresh(request)

            return request.to_dict()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_request(self, request_id: str) -> Dict[str, Any]:
        """获取审批申请详情"""
        session = self._get_session()
        try:
            request = session.query(ApprovalRequest).filter(
                ApprovalRequest.id == request_id
            ).first()

            if not request:
                raise ApprovalNotFound(f"审批申请 {request_id} 不存在")

            result = request.to_dict()
            # 添加申请人信息
            if request.applicant:
                result["applicant_name"] = request.applicant.username
            if request.approver:
                result["approver_name"] = request.approver.username

            return result

        finally:
            session.close()

    def get_my_requests(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """获取我的申请列表"""
        session = self._get_session()
        try:
            query = session.query(ApprovalRequest).filter(
                ApprovalRequest.applicant_id == user_id
            )

            if status:
                query = query.filter(ApprovalRequest.status == status)

            requests = query.order_by(ApprovalRequest.created_at.desc()).all()

            result = []
            for req in requests:
                item = req.to_dict()
                item["applicant_name"] = req.applicant.username if req.applicant else None
                result.append(item)

            return result

        finally:
            session.close()

    def get_pending_requests(self, approver_id: str) -> List[Dict[str, Any]]:
        """获取待审批列表（管理员）"""
        session = self._get_session()
        try:
            # 验证审批人是否是管理员
            approver = session.query(User).filter(User.id == approver_id).first()
            if not approver or approver.role_name != "admin":
                raise NotAuthorized("只有管理员可以审批")

            requests = session.query(ApprovalRequest).filter(
                ApprovalRequest.status == RequestStatus.PENDING.value
            ).order_by(ApprovalRequest.created_at.asc()).all()

            result = []
            for req in requests:
                item = req.to_dict()
                item["applicant_name"] = req.applicant.username if req.applicant else None
                result.append(item)

            return result

        finally:
            session.close()

    def process_approval(
        self,
        request_id: str,
        approver_id: str,
        decision: str,  # "approved" or "rejected"
        comment: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理审批

        Args:
            request_id: 审批申请ID
            approver_id: 审批人ID
            decision: 决定 (approved/rejected)
            comment: 审批意见

        Returns:
            更新后的申请信息
        """
        if decision not in ("approved", "rejected"):
            raise ValueError("decision 必须是 approved 或 rejected")

        session = self._get_session()
        try:
            # 获取申请
            request = session.query(ApprovalRequest).filter(
                ApprovalRequest.id == request_id
            ).first()

            if not request:
                raise ApprovalNotFound(f"审批申请 {request_id} 不存在")

            if request.status != RequestStatus.PENDING.value:
                raise ApprovalInvalidStatus(
                    f"申请状态是 {request.status}，无法审批"
                )

            # 验证审批人权限
            approver = session.query(User).filter(User.id == approver_id).first()
            if not approver or approver.role_name != "admin":
                raise NotAuthorized("只有管理员可以审批")

            # 更新申请状态
            old_status = request.status
            request.status = RequestStatus.APPROVED.value if decision == "approved" else RequestStatus.REJECTED.value
            request.approved_by = approver_id
            request.approved_at = datetime.utcnow()
            request.approval_comment = comment
            request.updated_at = datetime.utcnow()

            # 创建审批记录
            record = ApprovalRecord(
                id=str(uuid.uuid4()),
                request_id=request_id,
                approver_id=approver_id,
                decision=decision,
                comment=comment,
                decided_at=datetime.utcnow(),
            )
            session.add(record)

            # 如果批准，执行后续操作
            if decision == "approved":
                self._on_approval_approved(request, session)

            session.commit()
            session.refresh(request)

            return request.to_dict()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def cancel_request(self, request_id: str, user_id: str) -> Dict[str, Any]:
        """取消申请（申请人）"""
        session = self._get_session()
        try:
            request = session.query(ApprovalRequest).filter(
                ApprovalRequest.id == request_id
            ).first()

            if not request:
                raise ApprovalNotFound(f"审批申请 {request_id} 不存在")

            if request.applicant_id != user_id:
                raise NotAuthorized("只能取消自己的申请")

            if request.status != RequestStatus.PENDING.value:
                raise ApprovalInvalidStatus(
                    f"申请状态是 {request.status}，无法取消"
                )

            request.status = RequestStatus.CANCELLED.value
            request.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(request)

            return request.to_dict()

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def _on_approval_approved(self, request: ApprovalRequest, session) -> None:
        """
        审批通过后的触发逻辑

        根据申请类型执行相应的业务操作
        """
        from .space_service import SpaceService
        from .team_service import TeamService

        approval_type = request.type
        target_id = request.target_id
        applicant_id = request.applicant_id
        params = request.params or {}

        if approval_type == ApprovalType.JOIN_TEAM.value:
            # 加入团队申请通过 - 将用户添加到团队
            if target_id:
                self._add_user_to_team(applicant_id, target_id, session)

        elif approval_type == ApprovalType.PRIVATE_SPACE.value:
            # 私人空间申请通过 - 创建私人空间
            space_name = params.get("space_name", f"私人空间_{applicant_id[:8]}")
            self._create_private_space(applicant_id, space_name, params, session)

        elif approval_type == ApprovalType.QUOTA_EXTEND.value:
            # 配额扩展申请通过 - 增加配额
            additional_bytes = params.get("additional_bytes", 0)
            if target_id and additional_bytes:
                self._extend_team_quota(target_id, additional_bytes, session)

        elif approval_type == ApprovalType.TEAM_CREATE.value:
            # 团队创建申请通过 - 创建团队
            team_name = params.get("team_name", f"团队_{applicant_id[:8]}")
            self._create_team(applicant_id, team_name, params, session)

        elif approval_type == ApprovalType.STORAGE_POOL.value:
            # 存储池申请通过
            pass

        elif approval_type == ApprovalType.TEAM_JOIN.value:
            # 加入团队申请通过
            from services.team_service import TeamService
            team_service = TeamService()
            # 将成员添加到团队
            try:
                team_service.add_member(request.target_id, request.applicant_id)
                logger.info(f"Approval approved: user {request.applicant_id} joined team {request.target_id}")
            except Exception as e:
                logger.error(f"Failed to add member to team: {e}")
                raise

        elif approval_type == ApprovalType.TEAM_MEMBER_EXIT.value:
            # 成员退出申请通过
            from services.space_service import SpaceService
            import json
            space_service = SpaceService()
            params = json.loads(request.params or "{}")
            member_id = params.get("member_id", request.applicant_id)

            # 执行成员退出
            try:
                space_service.remove_member_with_notification(
                    team_id=request.target_id,
                    member_id=member_id,
                    operator_id=request.approved_by,
                    action="member_exit_approved"
                )
                logger.info(f"Approval approved: member {member_id} exited team {request.target_id}")
            except Exception as e:
                logger.error(f"Failed to process member exit: {e}")
                raise

    def _add_user_to_team(self, user_id: str, team_id: str, session) -> None:
        """将用户添加到团队（作为成员）"""
        from ..engine.models import TeamMember

        # 检查是否已是成员
        existing = session.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        ).first()

        if existing:
            return  # 已是成员

        # 添加为成员
        member = TeamMember(
            id=str(uuid.uuid4()),
            team_id=team_id,
            user_id=user_id,
            role="member",
            joined_at=datetime.utcnow(),
        )
        session.add(member)

    def _create_private_space(
        self,
        owner_id: str,
        space_name: str,
        params: Dict[str, Any],
        session,
    ) -> None:
        """创建私人空间"""
        # 获取团队ID（如果有）
        team_id = params.get("team_id")

        space = Space(
            id=str(uuid.uuid4()),
            name=space_name,
            type="private",
            owner_id=owner_id,
            team_id=team_id,
            created_at=datetime.utcnow(),
        )
        session.add(space)

        # 自动添加创建者为管理员
        member = SpaceMember(
            id=str(uuid.uuid4()),
            space_id=space.id,
            user_id=owner_id,
            role="admin",
            status="active",
            quota_bytes=params.get("quota_bytes", 10 * 1024 * 1024 * 1024),  # 默认10GB
        )
        session.add(member)

    def _extend_team_quota(self, team_id: str, additional_bytes: int, session) -> None:
        """扩展团队配额"""
        from ..engine.models import StoragePool

        # 获取团队的默认存储池
        pool = session.query(StoragePool).first()
        if not pool:
            return

        # 更新存储池的已分配配额
        # 注意：实际配额管理在 SpaceMember 层面
        pass

    def _create_team(
        self,
        owner_id: str,
        team_name: str,
        params: Dict[str, Any],
        session,
    ) -> None:
        """创建团队"""
        from ..engine.models import Team, TeamMember

        team = Team(
            id=str(uuid.uuid4()),
            name=team_name,
            owner_id=owner_id,
            created_at=datetime.utcnow(),
        )
        session.add(team)
        session.flush()  # 获取 team.id

        # 自动添加创建者为管理员
        member = TeamMember(
            id=str(uuid.uuid4()),
            team_id=team.id,
            user_id=owner_id,
            role="admin",
            joined_at=datetime.utcnow(),
        )
        session.add(member)


# =============================================================================
# Lifecycle Engine Integration
# =============================================================================

def check_requires_approval(approval_type: str, context: Dict[str, Any]) -> bool:
    """
    检查操作是否需要审批

    集成到 lifecycle_engine 的约束检查中
    """
    if approval_type == ApprovalType.JOIN_TEAM.value:
        # 检查团队是否需要审批才能加入
        team_id = context.get("team_id")
        if team_id:
            # TODO: 检查团队配置，看是否需要审批
            # 当前实现: 无 Team 模型，使用 Space 替代团队概念
            # 空间加入审批通过 space_request 机制处理
            return False  # 默认不需要审批
        return False

    elif approval_type == ApprovalType.PRIVATE_SPACE.value:
        # 私人空间创建总是需要审批
        return True

    elif approval_type == ApprovalType.TEAM_CREATE.value:
        # 检查是否达到团队数量上限
        return False

    return False


def raise_if_requires_approval(approval_type: str, context: Dict[str, Any]) -> None:
    """
    如果操作需要审批则抛出异常

    集成到 lifecycle_engine 的约束检查中
    """
    if check_requires_approval(approval_type, context):
        raise ApprovalRequired(
            f"此操作需要管理员审批",
            approval_type=approval_type,
            context=context,
        )


class ApprovalRequired(Exception):
    """操作需要审批异常"""

    def __init__(self, message: str, approval_type: str = None, context: Dict[str, Any] = None):
        super().__init__(message)
        self.approval_type = approval_type
        self.context = context or {}


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "ApprovalService",
    "ApprovalNotFound",
    "ApprovalInvalidStatus",
    "NotAuthorized",
    "ApprovalRequired",
    "check_requires_approval",
    "raise_if_requires_approval",
]
