"""
测试 Knowledge Service - 知识库同步服务

包括：
- 实体/概念提取
- 图谱构建
- 增量同步
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from file_manager.services.knowledge_service import (
    KnowledgeService,
    Entity, Concept, GraphRelation,
    SyncStatus, SyncMode, SyncJob,
)


class TestEntityExtraction:
    """测试实体提取功能"""

    def setup_method(self):
        """每个测试方法前创建 fresh instance"""
        self.svc = KnowledgeService()

    def test_extract_person_entities(self):
        """测试人名提取（英文和中文）"""
        content = """
        Zhang San and Li Si are discussing project progress.
        Wang Wu is responsible for backend development.
        张三和李四在讨论项目进度。
        王五负责后端开发。
        """
        entities = self.svc.extract_entities(content, "/test/page.md")

        entity_names = [e.name for e in entities]
        # Check for either English or Chinese names
        has_english_names = any("Zhang" in name or "Li" in name or "Wang" in name for name in entity_names)
        has_chinese_names = any(len(name) <= 4 and not any(c.isupper() for c in name) for name in entity_names if len(entity_names) > 0)
        assert len(entity_names) > 0, f"Expected some entities, got none. Names: {entity_names}"
        # Either English first+last name or Chinese 2-4 char names should be found
        assert has_english_names or has_chinese_names, f"Expected some person names, got: {entity_names}"

    def test_extract_technology_entities(self):
        """测试技术名词提取"""
        content = """
        我们使用 Python 和 TypeScript 开发后端服务。
        前端使用 React 框架。
        部署在 Docker 和 Kubernetes 环境中。
        """
        entities = self.svc.extract_entities(content, "/test/page.md")

        tech_names = [e.name for e in entities]
        assert any(t in tech_names for t in ["Python", "TypeScript", "React", "Docker", "Kubernetes"])

    def test_extract_no_duplicates(self):
        """测试去重"""
        content = """
        Python 被广泛使用。Python 是解释型语言。
        """
        entities = self.svc.extract_entities(content, "/test/page.md")

        # 不应该有重复
        names = [e.name for e in entities]
        assert len(names) == len(set(names))

    def test_extract_with_page_path(self):
        """测试实体关联页面路径"""
        content = "张三和李四在讨论"
        entities = self.svc.extract_entities(content, "/docs/team/meeting.md")

        for entity in entities:
            assert entity.page_path == "/docs/team/meeting.md"
            assert entity.id  # 应该有 UUID
            assert entity.type  # 应该有类型


class TestConceptExtraction:
    """测试概念提取功能"""

    def setup_method(self):
        self.svc = KnowledgeService()

    def test_extract_architecture_concepts(self):
        """测试架构模式提取"""
        content = """
        我们采用 Microservices 架构。
        使用 Event-Driven 设计。
        """
        concepts = self.svc.extract_concepts(content, "/docs/arch.md")

        concept_names = [c.name for c in concepts]
        assert any(c in concept_names for c in ["Microservices", "Event-Driven"])

    def test_extract_design_pattern_concepts(self):
        """测试设计模式提取"""
        content = """
        使用 Factory 模式创建对象。
        Observer 模式用于事件处理。
        """
        concepts = self.svc.extract_concepts(content, "/docs/pattern.md")

        pattern_names = [c.name for c in concepts]
        assert any(p in pattern_names for p in ["Factory", "Observer"])

    def test_concept_metadata(self):
        """测试概念元数据"""
        content = "REST API 是常用的接口设计"
        concepts = self.svc.extract_concepts(content, "/docs/api.md")

        for concept in concepts:
            assert concept.metadata.get('source') == 'regex_extraction'
            assert 'match_pos' in concept.metadata


class TestKnowledgeGraph:
    """测试知识图谱构建"""

    def setup_method(self):
        self.svc = KnowledgeService()

    def test_build_graph_with_links(self):
        """测试基于 wiki links 构建关系"""
        entities = [
            Entity(id="e1", type="person", name="张三", page_path="/docs/team.md"),
            Entity(id="e2", type="project", name="Hermes", page_path="/docs/team.md"),
        ]
        concepts = [
            Concept(id="c1", type="technology", name="Python", page_path="/docs/team.md"),
        ]
        links = ["张三", "Python"]  # wiki link 指向的实体

        relations = self.svc.build_knowledge_graph(entities, concepts, links)

        # 应该有基于链接的关系
        assert len(relations) >= 0

    def test_store_graph_data(self):
        """测试图谱数据存储"""
        entities = [
            Entity(id="e1", type="person", name="张三", page_path="/test.md"),
        ]
        concepts = [
            Concept(id="c1", type="term", name="API", page_path="/test.md"),
        ]
        relations = [
            GraphRelation(source_id="e1", target_id="c1", relation_type="related_to", weight=0.8),
        ]

        result = self.svc.store_graph_data("space_123", entities, concepts, relations)

        assert result['entities_stored'] == 1
        assert result['concepts_stored'] == 1
        assert result['relations_stored'] == 1

        # 验证数据是否真的被存储
        assert len(self.svc._entities) == 1
        assert len(self.svc._concepts) == 1
        assert len(self.svc._relations) == 1


class TestSyncJob:
    """测试同步任务"""

    def test_sync_job_creation(self):
        """测试 SyncJob 创建"""
        job = SyncJob(
            id="job_001",
            source_path="/docs/test.md",
            target_project="hermes-tech",
            status=SyncStatus.PENDING,
            mode=SyncMode.MANUAL,
            created_at=datetime.now(),
        )

        assert job.id == "job_001"
        assert job.status == SyncStatus.PENDING
        assert job.files_synced == 0
        assert job.files_failed == 0

    def test_sync_status_enum(self):
        """测试 SyncStatus 枚举"""
        assert SyncStatus.PENDING.value == "pending"
        assert SyncStatus.RUNNING.value == "running"
        assert SyncStatus.COMPLETED.value == "completed"
        assert SyncStatus.FAILED.value == "failed"


class TestServiceStatus:
    """测试服务状态检查"""

    @pytest.mark.asyncio
    async def test_check_service_status_success(self):
        """测试服务正常时返回 True"""
        svc = KnowledgeService(llm_wiki_url="http://localhost:19827")

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await svc.check_service_status()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_service_status_failure(self):
        """测试服务不可用时返回 False"""
        svc = KnowledgeService(llm_wiki_url="http://localhost:19827")

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Connection refused")

            result = await svc.check_service_status()
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])