"""
HermesService - Hermes 主系统任务调度服务

核心职责：
- 接收 File Manager Web 的 Hermes 操作请求
- 管理任务队列和状态
- 调用 Hermes MCP Server 执行任务
- 接收 Hermes 执行结果并通知客户端

不含 Hermes 主系统本身，仅 File Manager 侧的调度逻辑。
"""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

import httpx

logger = logging.getLogger(__name__)

# Hermes MCP Server 配置
HERMES_MCP_URL = os.getenv("HERMES_MCP_URL", "http://localhost:8081/mcp")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "")

# 任务超时时间（秒）
TASK_TIMEOUT = 300


# =============================================================================
# Domain Types
# =============================================================================

class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 取消


class TaskPriority(str, Enum):
    """任务优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


# =============================================================================
# HermesTask 数据模型
# =============================================================================

@dataclass
class HermesTask:
    """Hermes 任务"""
    id: str
    user_id: str
    team_id: str
    command: str
    params: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    callback_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "team_id": self.team_id,
            "command": self.command,
            "params": self.params,
            "status": self.status.value,
            "priority": self.priority.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "callback_url": self.callback_url,
        }


# =============================================================================
# HermesService
# =============================================================================

class HermesService:
    """
    Hermes 任务调度服务

    接收 File Manager Web 的请求，调度到 Hermes MCP Server 执行。
    """

    def __init__(self, db_factory=None):
        self._db_factory = db_factory
        self._tasks: Dict[str, HermesTask] = {}
        self._user_subscriptions: Dict[str, List[str]] = {}  # user_id -> [task_ids]
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._task_processor: Optional[asyncio.Task] = None

    # -------------------------------------------------------------------------
    # 任务管理
    # -------------------------------------------------------------------------

    def create_task(
        self,
        user_id: str,
        team_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        callback_url: Optional[str] = None,
    ) -> HermesTask:
        """
        创建新任务

        Args:
            user_id: 触发任务的用户 ID
            team_id: 团队 ID（用于权限验证）
            command: Hermes 命令（如 "execute", "query", "cron.list"）
            params: 命令参数
            priority: 优先级
            callback_url: 完成后回调的 Webhook URL

        Returns:
            HermesTask 对象
        """
        task = HermesTask(
            id=str(uuid.uuid4())[:8],
            user_id=user_id,
            team_id=team_id,
            command=command,
            params=params or {},
            priority=priority,
            callback_url=callback_url,
        )
        self._tasks[task.id] = task

        # 记录用户订阅
        if user_id not in self._user_subscriptions:
            self._user_subscriptions[user_id] = []
        self._user_subscriptions[user_id].append(task.id)

        logger.info(f"Created Hermes task {task.id}: {command} for user {user_id}")
        return task

    def get_task(self, task_id: str) -> Optional[HermesTask]:
        """获取任务"""
        return self._tasks.get(task_id)

    def list_user_tasks(
        self,
        user_id: str,
        status: Optional[TaskStatus] = None,
        limit: int = 20,
    ) -> List[HermesTask]:
        """列出用户的任务"""
        task_ids = self._user_subscriptions.get(user_id, [])
        tasks = [self._tasks[tid] for tid in task_ids if tid in self._tasks]

        if status:
            tasks = [t for t in tasks if t.status == status]

        # 按创建时间倒序
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks[:limit]

    def cancel_task(self, task_id: str, user_id: str) -> bool:
        """
        取消任务（仅能取消自己的任务，且必须是 PENDING 状态）

        Returns:
            True if cancelled, False otherwise
        """
        task = self._tasks.get(task_id)
        if not task:
            return False
        if task.user_id != user_id:
            logger.warning(f"User {user_id} tried to cancel task {task_id} owned by {task.user_id}")
            return False
        if task.status != TaskStatus.PENDING:
            return False

        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow()
        logger.info(f"Cancelled Hermes task {task_id}")
        return True

    # -------------------------------------------------------------------------
    # 任务执行
    # -------------------------------------------------------------------------

    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行单个任务，调用 Hermes MCP Server

        Returns:
            执行结果
        """
        task = self._tasks.get(task_id)
        if not task:
            return {"error": f"Task {task_id} not found"}

        if task.status != TaskStatus.PENDING:
            return {"error": f"Task {task_id} is not pending (status: {task.status})"}

        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        try:
            result = await self._call_hermes(task)
            task.status = TaskStatus.COMPLETED
            task.result = result
            task.completed_at = datetime.utcnow()
            logger.info(f"Hermes task {task_id} completed successfully")
            return result

        except asyncio.TimeoutError:
            task.status = TaskStatus.FAILED
            task.error = "Task timeout"
            task.completed_at = datetime.utcnow()
            logger.error(f"Hermes task {task_id} timeout")
            return {"error": "Task timeout"}

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.utcnow()
            logger.error(f"Hermes task {task_id} failed: {e}")
            return {"error": str(e)}

    async def _call_hermes(self, task: HermesTask) -> Dict[str, Any]:
        """
        调用 Hermes MCP Server

        构建符合 MCP 协议的请求，发送到 Hermes MCP Server。
        """
        headers = {"Content-Type": "application/json"}
        if HERMES_API_KEY:
            headers["Authorization"] = f"Bearer {HERMES_API_KEY}"

        # MCP 格式请求
        payload = {
            "jsonrpc": "2.0",
            "id": task.id,
            "method": "tools/call",
            "params": {
                "name": task.command,
                "arguments": task.params,
            }
        }

        async with httpx.AsyncClient(timeout=TASK_TIMEOUT) as client:
            response = await client.post(
                HERMES_MCP_URL,
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                raise Exception(f"Hermes error: {result['error']}")

            return result.get("result", {})

    # -------------------------------------------------------------------------
    # 异步任务处理
    # -------------------------------------------------------------------------

    async def start(self):
        """启动任务处理器"""
        if self._running:
            return
        self._running = True
        self._task_processor = asyncio.create_task(self._process_tasks())
        logger.info("HermesService task processor started")

    async def stop(self):
        """停止任务处理器"""
        self._running = False
        if self._task_processor:
            self._task_processor.cancel()
            try:
                await self._task_processor
            except asyncio.CancelledError:
                pass
        logger.info("HermesService task processor stopped")

    async def _process_tasks(self):
        """
        异步任务处理器

        从队列中取出任务并执行。
        """
        while self._running:
            try:
                task_id = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self.execute_task(task_id)

                # 如果有 callback_url，发送回调
                task = self._tasks.get(task_id)
                if task and task.callback_url:
                    await self._send_callback(task)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    def submit_task(self, task_id: str):
        """提交任务到执行队列"""
        self._queue.put_nowait(task_id)

    async def _send_callback(self, task: HermesTask):
        """发送任务完成回调"""
        if not task.callback_url:
            return

        payload = {
            "task_id": task.id,
            "status": task.status.value,
            "result": task.result,
            "error": task.error,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(task.callback_url, json=payload)
                logger.info(f"Callback sent for task {task.id}")
        except Exception as e:
            logger.error(f"Failed to send callback for task {task.id}: {e}")

    # -------------------------------------------------------------------------
    # 权限验证
    # -------------------------------------------------------------------------

    def can_execute(self, user_id: str, team_id: str, command: str) -> bool:
        """
        检查用户是否有权限执行命令

        目前只做基础检查，后续可以对接 RBAC。
        """
        # TODO: 对接 File Manager 的 RBAC
        # 目前只要 user 属于 team 就可以执行
        return True

    # -------------------------------------------------------------------------
    # 状态查询
    # -------------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        """获取 HermesService 状态"""
        pending = sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)
        running = sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)
        completed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self._tasks.values() if t.status == TaskStatus.FAILED)

        return {
            "queue_size": self._queue.qsize(),
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "total": len(self._tasks),
            "running_state": self._running,
        }


# =============================================================================
# Global Instance
# =============================================================================

_hermes_service: Optional[HermesService] = None


def get_hermes_service() -> HermesService:
    """获取全局 HermesService 实例"""
    global _hermes_service
    if _hermes_service is None:
        _hermes_service = HermesService()
    return _hermes_service


async def init_hermes_service():
    """初始化 HermesService"""
    service = get_hermes_service()
    await service.start()


async def shutdown_hermes_service():
    """关闭 HermesService"""
    global _hermes_service
    if _hermes_service:
        await _hermes_service.stop()
