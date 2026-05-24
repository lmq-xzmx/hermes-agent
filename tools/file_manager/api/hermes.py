"""
Hermes API - Hermes 主系统任务调度接口

端点：
- POST /api/v1/hermes/execute     - 触发 Hermes 任务
- GET  /api/v1/hermes/status      - 获取 Hermes 服务状态
- GET  /api/v1/hermes/tasks       - 获取用户的任务列表
- GET  /api/v1/hermes/tasks/{id}  - 获取任务详情
- POST /api/v1/hermes/tasks/{id}/cancel - 取消任务
- POST /api/v1/hermes/callback/{id} - Hermes 回调（内部使用）
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from ..services.hermes_service import (
    HermesService, get_hermes_service, TaskStatus, TaskPriority,
)
from .dto import (
    HermesExecuteRequestDTO,
    HermesTaskResponseDTO,
    HermesTaskListResponseDTO,
    HermesStatusResponseDTO,
    HermesCallbackDTO,
)
from .auth import security, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/hermes", tags=["hermes"])


def _task_to_dto(task) -> HermesTaskResponseDTO:
    """将 HermesTask 转换为 DTO"""
    return HermesTaskResponseDTO(
        id=task.id,
        user_id=task.user_id,
        team_id=task.team_id,
        command=task.command,
        params=task.params,
        status=task.status.value if hasattr(task.status, 'value') else task.status,
        priority=task.priority.value if hasattr(task.priority, 'value') else task.priority,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        started_at=task.started_at,
        completed_at=task.completed_at,
        callback_url=task.callback_url,
    )


# =============================================================================
# 任务触发
# =============================================================================

@router.post("/execute", response_model=HermesTaskResponseDTO)
async def execute_task(
    request: HermesExecuteRequestDTO,
    current_user: dict = Depends(get_current_user),
):
    """
    触发 Hermes 任务执行

    用户通过 File Manager Web 触发 Hermes 操作。
    任务会被放入队列，由后台处理器执行。
    """
    service = get_hermes_service()
    
    # 获取用户默认团队（如果有）
    team_id = request.team_id or current_user.get("default_team_id", "default")
    
    # 解析优先级
    priority = TaskPriority(request.priority.lower())
    
    # 创建任务
    task = service.create_task(
        user_id=current_user["sub"],
        team_id=team_id,
        command=request.command,
        params=request.params,
        priority=priority,
        callback_url=request.callback_url,
    )
    
    # 提交到执行队列
    service.submit_task(task.id)
    
    logger.info(f"User {current_user['sub']} executed Hermes command: {request.command}")
    
    return _task_to_dto(task)


# =============================================================================
# 状态查询
# =============================================================================

@router.get("/status", response_model=HermesStatusResponseDTO)
async def get_status(
    current_user: dict = Depends(get_current_user),
):
    """获取 Hermes 服务状态"""
    service = get_hermes_service()
    return HermesStatusResponseDTO(**service.get_status())


@router.get("/tasks", response_model=HermesTaskListResponseDTO)
async def list_tasks(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    """
    获取当前用户的 Hermes 任务列表

    Args:
        status: 筛选状态（pending/running/completed/failed/cancelled）
        limit: 返回数量限制
    """
    service = get_hermes_service()
    
    task_status = None
    if status:
        try:
            task_status = TaskStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    tasks = service.list_user_tasks(
        user_id=current_user["sub"],
        status=task_status,
        limit=limit,
    )
    
    return HermesTaskListResponseDTO(
        tasks=[_task_to_dto(t) for t in tasks],
        total=len(tasks),
    )


@router.get("/tasks/{task_id}", response_model=HermesTaskResponseDTO)
async def get_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """获取任务详情"""
    service = get_hermes_service()
    task = service.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # 只能查看自己的任务
    if task.user_id != current_user["sub"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return _task_to_dto(task)


# =============================================================================
# 任务控制
# =============================================================================

@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: dict = Depends(get_current_user),
):
    """取消任务（仅能取消 PENDING 状态的任务）"""
    service = get_hermes_service()
    
    success = service.cancel_task(task_id, current_user["sub"])
    
    if not success:
        raise HTTPException(status_code=400, detail="Cannot cancel task")
    
    return {"message": "Task cancelled", "task_id": task_id}


# =============================================================================
# 回调（Hermes 回调 File Manager）
# =============================================================================

@router.post("/callback/{task_id}")
async def task_callback(
    task_id: str,
    callback: HermesCallbackDTO,
    request: Request,
):
    """
    Hermes 任务完成回调

    Hermes 主系统执行完成后，通过此端点通知 File Manager。
    验证 X-Hermes-Signature 头防止恶意回调。
    """
    # TODO: 验证签名
    # signature = request.headers.get("X-Hermes-Signature")
    # if not verify_signature(signature, callback):
    #     raise HTTPException(status_code=403, detail="Invalid signature")
    
    service = get_hermes_service()
    task = service.get_task(task_id)
    
    if not task:
        logger.warning(f"Callback for unknown task: {task_id}")
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    
    # 更新任务状态
    task.result = callback.result
    task.error = callback.error
    if callback.completed_at:
        from datetime import datetime
        task.completed_at = datetime.fromisoformat(callback.completed_at.replace("Z", "+00:00"))
    
    if callback.status == "completed":
        task.status = TaskStatus.COMPLETED
    elif callback.status == "failed":
        task.status = TaskStatus.FAILED
    else:
        task.status = TaskStatus(callback.status)
    
    logger.info(f"Task {task_id} callback received: status={callback.status}")
    
    return {"message": "Callback processed"}


# =============================================================================
# WebSocket 实时通知（可选，后续实现）
# =============================================================================

# from fastapi import WebSocket

# @router.websocket("/ws/{user_id}")
# async def hermes_websocket(ws: WebSocket, user_id: str):
#     """
#     WebSocket 实时通知
    
#     前端可以通过此 WebSocket 接收任务状态变更通知。
#     """
#     await ws.accept()
#     try:
#         while True:
#             # 接收任务状态更新
#             data = await ws.receive_json()
#             await ws.send_json({"event": "task_update", "data": data})
#     except Exception as e:
#         logger.error(f"WebSocket error: {e}")
#     finally:
#         await ws.close()
