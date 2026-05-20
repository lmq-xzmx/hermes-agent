"""
Knowledge Service - 知识库同步服务

提供文档同步到 llm_wiki 知识库的功能
支持权限检查和多种同步模式
"""

from __future__ import annotations

import httpx
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class SyncMode(str, Enum):
    MANUAL = "manual"
    INTERVAL = "interval"
    WEBHOOK = "webhook"


@dataclass
class SyncJob:
    id: str
    source_path: str
    target_project: str
    status: SyncStatus
    mode: SyncMode
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    files_synced: int = 0
    files_failed: int = 0


@dataclass
class SearchResult:
    id: str
    title: str
    snippet: str
    score: float
    path: str


@dataclass
class KnowledgeBase:
    id: str
    name: str
    project: str
    description: str
    synced_at: Optional[datetime]
    created_by: str


class KnowledgeService:
    """知识库同步服务"""

    def __init__(self, llm_wiki_url: str = "http://localhost:19827"):
        self.llm_wiki_url = llm_wiki_url
        self._sync_jobs: List[SyncJob] = []
        self._user_settings: dict = {}  # 用户设置存储

    async def check_service_status(self) -> bool:
        """检查 llm_wiki 服务是否运行"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.llm_wiki_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    async def sync_to_knowledge(
        self,
        source_path: str,
        target_project: str,
        user_id: str,
        is_space_member: bool = False,
        is_space_owner: bool = False,
        is_admin: bool = False
    ) -> SyncJob:
        """
        同步文档到知识库

        权限检查:
        - 空间成员: 可以同步
        - 空间所有者: 可以同步和管理同步设置
        - 管理员: 可以同步和管理
        - 非成员: 不能同步
        """
        # 权限检查
        if not is_space_member and not is_admin:
            raise PermissionError("只有空间成员才能同步文档到知识库")

        job = SyncJob(
            id=str(uuid.uuid4()),
            source_path=source_path,
            target_project=target_project,
            status=SyncStatus.PENDING,
            mode=SyncMode.MANUAL,
            created_at=datetime.now()
        )

        self._sync_jobs.append(job)

        # 调用 llm_wiki API 执行同步
        try:
            job.status = SyncStatus.RUNNING
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{self.llm_wiki_url}/sync",
                    json={
                        "source_path": source_path,
                        "project": target_project,
                        "user_id": user_id
                    }
                )
                if resp.status_code == 200:
                    data = resp.json() if resp.text else {}
                    job.files_synced = data.get("files_synced", 1)
                    job.files_failed = data.get("files_failed", 0)
                    job.status = SyncStatus.COMPLETED
                    job.completed_at = datetime.now()
                else:
                    job.status = SyncStatus.FAILED
                    job.error_message = resp.text
        except Exception as e:
            job.status = SyncStatus.FAILED
            job.error_message = str(e)

        return job

    async def search_knowledge(
        self,
        query: str,
        project: str,
        is_space_member: bool = False,
        is_admin: bool = False
    ) -> List[SearchResult]:
        """
        搜索知识库

        权限检查:
        - 空间成员: 可以搜索
        - 管理员: 可以全局搜索
        - 非成员: 不能搜索
        """
        if not is_space_member and not is_admin:
            raise PermissionError("只有空间成员才能搜索知识库")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.llm_wiki_url}/search",
                    params={"q": query, "project": project}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return [
                        SearchResult(
                            id=str(uuid.uuid4()),
                            title=item.get("title", ""),
                            snippet=item.get("snippet", ""),
                            score=item.get("score", 0.0),
                            path=item.get("path", "")
                        )
                        for item in data.get("results", [])
                    ]
                return []
        except Exception:
            return []

    async def get_search_suggestions(self, query: str, project: str) -> List[str]:
        """获取搜索建议（自动补全）"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.llm_wiki_url}/suggestions",
                    params={"q": query, "project": project}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("suggestions", [])
                return []
        except Exception:
            return []

    def get_sync_history(self, project: Optional[str] = None) -> List[SyncJob]:
        """获取同步历史"""
        if project:
            return [j for j in self._sync_jobs if j.target_project == project]
        return self._sync_jobs

    def get_sync_mode(self, user_id: str) -> str:
        """获取用户的同步模式设置"""
        settings = self._user_settings.get(user_id, {})
        return settings.get("sync_mode", "manual")

    def get_sync_interval(self, user_id: str) -> int:
        """获取用户的同步间隔（分钟）"""
        settings = self._user_settings.get(user_id, {})
        return settings.get("sync_interval", 30)

    def get_user_settings(self, user_id: str) -> dict:
        """获取用户设置"""
        return self._user_settings.get(user_id, {
            "sync_mode": "manual",
            "sync_interval": 30,
            "auto_sync": False
        })

    def update_user_settings(self, user_id: str, settings: dict) -> None:
        """更新用户设置"""
        if user_id not in self._user_settings:
            self._user_settings[user_id] = {
                "sync_mode": "manual",
                "sync_interval": 30,
                "auto_sync": False
            }
        self._user_settings[user_id].update(settings)


# Singleton instance
_knowledge_service: Optional[KnowledgeService] = None
_interval_sync_jobs: dict = {}  # user_id -> list of cron job ids


def get_knowledge_service() -> KnowledgeService:
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service
