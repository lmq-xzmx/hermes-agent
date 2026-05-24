"""
Knowledge Service - 知识库同步服务

提供文档同步到 llm_wiki 知识库的功能
支持权限检查和多种同步模式
"""

from __future__ import annotations

import httpx
import uuid
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


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
class Entity:
    """实体：人名、项目、技术名词等"""
    id: str
    type: str  # person/project/technology/concept
    name: str
    page_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Concept:
    """概念：架构模式、设计原则等"""
    id: str
    type: str  # architecture/design_pattern/term/process
    name: str
    page_path: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class GraphRelation:
    """图谱关系"""
    source_id: str
    target_id: str
    relation_type: str  # "depends_on", "related_to", "implements", "uses"
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


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

    # 实体提取正则模式
    ENTITY_PATTERNS = {
        'person': re.compile(r'\b([A-Z][a-z]+ [A-Z][a-z]+|[一-龥]{2,4})\b'),
        'project': re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:Project)\b', re.IGNORECASE),
        'technology': re.compile(r'\b(Python|JavaScript|TypeScript|React|Vue|Node\.js|Docker|Kubernetes|AWS|Azure|GCP)\b'),
    }

    # 概念提取正则模式
    CONCEPT_PATTERNS = {
        'architecture': re.compile(r'\b(Microservices|Monolith|Serverless|Event-Driven|CQRS|DDD)\b', re.IGNORECASE),
        'design_pattern': re.compile(r'\b(Factory|Observer|Strategy|Adapter|Decorator)\b', re.IGNORECASE),
        'term': re.compile(r'\b(API|REST|GraphQL|gRPC|OAuth|JWT|SSO)\b', re.IGNORECASE),
    }

    def __init__(self, llm_wiki_url: str = "http://localhost:19827"):
        self.llm_wiki_url = llm_wiki_url
        self._sync_jobs: List[SyncJob] = []
        self._user_settings: dict = {}  # 用户设置存储
        self._entities: List[Entity] = []
        self._concepts: List[Concept] = []
        self._relations: List[GraphRelation] = []

    async def check_service_status(self) -> bool:
        """检查 llm_wiki 服务是否运行"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{self.llm_wiki_url}/health")
                return resp.status_code == 200
        except Exception:
            return False

    def extract_entities(self, content: str, page_path: str) -> List[Entity]:
        """从内容中提取实体"""
        entities = []
        seen_names = set()

        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1).strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    entities.append(Entity(
                        id=str(uuid.uuid4()),
                        type=entity_type,
                        name=name,
                        page_path=page_path,
                        metadata={'source': 'regex_extraction', 'match_pos': match.start()}
                    ))

        return entities

    def extract_concepts(self, content: str, page_path: str) -> List[Concept]:
        """从内容中提取概念"""
        concepts = []
        seen_names = set()

        for concept_type, pattern in self.CONCEPT_PATTERNS.items():
            for match in pattern.finditer(content):
                name = match.group(1).strip()
                if name and name not in seen_names:
                    seen_names.add(name)
                    concepts.append(Concept(
                        id=str(uuid.uuid4()),
                        type=concept_type,
                        name=name,
                        page_path=page_path,
                        metadata={'source': 'regex_extraction', 'match_pos': match.start()}
                    ))

        return concepts

    def build_knowledge_graph(
        self,
        entities: List[Entity],
        concepts: List[Concept],
        links: List[str]
    ) -> List[GraphRelation]:
        """根据提取的实体/概念和链接关系构建图谱"""
        relations = []

        # 实体间关系（基于同页面）
        entity_map = {e.name: e for e in entities}
        concept_map = {c.name: c for c in concepts}

        # 基于 [[wiki links]] 建立关系
        for linked_name in links:
            if linked_name in entity_map and linked_name in concept_map:
                relations.append(GraphRelation(
                    source_id=entity_map[linked_name].id,
                    target_id=concept_map[linked_name].id,
                    relation_type='related_to',
                    weight=0.8
                ))

        return relations

    def store_graph_data(
        self,
        space_id: str,
        entities: List[Entity],
        concepts: List[Concept],
        relations: List[GraphRelation]
    ) -> Dict[str, int]:
        """存储图谱数据到 PostgreSQL jsonb（MVP）或内存（测试）"""
        # 过滤属于此 space 的数据
        self._entities.extend([e for e in entities])
        self._concepts.extend([c for c in concepts])
        self._relations.extend(relations)

        return {
            'entities_stored': len(entities),
            'concepts_stored': len(concepts),
            'relations_stored': len(relations),
        }

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
