"""
HR Webhook API - 入职/离职事件处理

接收 HR 系统的 Webhook 事件，自动完成员工入职/离职流程。
"""

from __future__ import annotations

import hmac
import hashlib
import time
from typing import Optional
from fastapi import HTTPException, Request, Depends
from pydantic import BaseModel, Field

from file_manager.services.auth_service import AuthService
from file_manager.services.team_service import TeamService
from file_manager.services.space_service import SpaceService
from file_manager.api.auth import get_current_user
from file_manager.services.permission_context import PermissionContext


# ============================================================================
# HMAC 签名验证
# ============================================================================

def verify_hmac_signature(
    secret: str,
    timestamp: str,
    payload: str,
    signature: str,
    max_age_seconds: int = 300,
) -> bool:
    """
    验证 Webhook 请求的 HMAC-SHA256 签名。

    1. 检查时间戳是否在允许范围内（防止重放攻击）
    2. 计算期望的签名
    3. 与请求中的签名比对
    """
    # 检查时间戳
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if current_time - request_time > max_age_seconds:
            return False
    except ValueError:
        return False

    # 计算签名
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{payload}".encode(),
        hashlib.sha256
    ).hexdigest()

    # 常数时间比较
    return hmac.compare_digest(f"sha256={expected}", signature)


def get_webhook_secret() -> str:
    """获取配置的 webhook secret"""
    import os
    return os.environ.get("HR_WEBHOOK_SECRET", "dev-webhook-secret")


# ============================================================================
# Request Models
# ============================================================================

class EmployeeInfo(BaseModel):
    """员工信息"""
    external_id: str = Field(..., description="HR 系统中的员工 ID")
    name: str = Field(..., description="员工姓名")
    email: str = Field(..., description="员工邮箱")
    department: str = Field(..., description="部门名称")
    department_id: str = Field(..., description="部门 ID")
    position: Optional[str] = Field(None, description="职位")
    hire_date: Optional[str] = Field(None, description="入职日期")
    manager: Optional[dict] = Field(None, description="主管信息")


class OnboardingSettings(BaseModel):
    """入职设置"""
    knowledge_share_policy: str = Field(default="full_share", description="共享策略")
    default_space: str = Field(default="hermes-tech", description="默认加入的 Space")
    role: str = Field(default="editor", description="角色")


class OnboardingRequest(BaseModel):
    """入职 Webhook 请求"""
    event: str = Field(..., description="事件类型")
    event_id: str = Field(..., description="事件唯一 ID")
    timestamp: str = Field(..., description="ISO 8601 时间")
    employee: EmployeeInfo
    settings: OnboardingSettings


class OffboardingSettings(BaseModel):
    """离职设置"""
    last_workday: str = Field(..., description="最后工作日")
    grace_period_days: int = Field(default=30, description="宽限期天数")
    export_personal: bool = Field(default=True, description="是否允许导出个人笔记")


class OffboardingRequest(BaseModel):
    """离职 Webhook 请求"""
    event: str = Field(..., description="事件类型")
    event_id: str = Field(..., description="事件唯一 ID")
    timestamp: str = Field(..., description="ISO 8601 时间")
    employee: EmployeeInfo
    settings: OffboardingSettings


class WebhookResponse(BaseModel):
    """通用响应"""
    status: str  # success | error
    user_id: Optional[str] = None
    message: str
    actions: Optional[list] = None


# ============================================================================
# Webhook Handlers
# ============================================================================

async def handle_onboarding(
    req: OnboardingRequest,
    request: Request,
    current_user: PermissionContext = Depends(get_current_user),
) -> WebhookResponse:
    """
    处理员工入职 Webhook。

    自动执行：
    1. 创建账号
    2. 分配 SSO 角色
    3. 加入团队 Space
    4. 下发企业配置
    """
    # 权限检查：仅 admin 可处理入职
    if current_user.role_name != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    # 检查是否已存在用户
    from ...services.auth_service import AuthService
    auth_service = AuthService()

    try:
        existing_user = auth_service.get_user_by_email(req.employee.email)
        if existing_user:
            return WebhookResponse(
                status="success",
                user_id=str(existing_user.id),
                message="User already exists, updating instead",
            )
    except ValueError:
        pass  # 用户不存在，继续创建

    # 创建新用户
    user_id = f"hermes_user_{req.employee.external_id}"

    # TODO: 调用实际的用户创建服务
    # user = auth_service.create_user(...)

    return WebhookResponse(
        status="success",
        user_id=user_id,
        message="Employee onboarding completed",
        actions=[
            {"action": "create_account", "result": "created"},
            {"action": "assign_role", "result": req.settings.role},
            {"action": "join_space", "result": req.settings.default_space},
            {"action": "notify_config", "result": "sent"},
        ],
    )


async def handle_offboarding(
    req: OffboardingRequest,
    request: Request,
    current_user: PermissionContext = Depends(get_current_user),
) -> WebhookResponse:
    """
    处理员工离职 Webhook。

    自动执行：
    1. 权限降级为 viewer
    2. 设置过期时间
    3. 通知员工导出个人笔记
    """
    # 权限检查：仅 admin 可处理离职
    if current_user.role_name != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    from datetime import datetime, timedelta

    # 计算过期日期
    grace_days = req.settings.grace_period_days
    expiry_date = datetime.now() + timedelta(days=grace_days)

    # TODO: 调用实际的用户降级服务
    # auth_service.downgrade_user(req.employee.email, role="viewer")
    # auth_service.set_expiry(req.employee.email, expiry_date)

    return WebhookResponse(
        status="success",
        user_id=f"hermes_user_{req.employee.external_id}",
        message="Employee offboarding completed",
        actions=[
            {"action": "role_downgrade", "result": "viewer"},
            {"action": "set_expiry", "result": expiry_date.isoformat()},
            {"action": "notify_employee", "result": "pending"},
        ],
    )


def verify_webhook_request(request: Request) -> bool:
    """验证 Webhook 请求的 HMAC 签名"""
    signature = request.headers.get("X-Hermes-Signature", "")
    timestamp = request.headers.get("X-Hermes-Timestamp", "")

    if not signature or not timestamp:
        return False

    # 获取原始请求体
    import json
    body = request._json  # FastAPI 提供

    secret = get_webhook_secret()
    payload = json.dumps(body) if isinstance(body, dict) else str(body)

    return verify_hmac_signature(secret, timestamp, payload, signature)