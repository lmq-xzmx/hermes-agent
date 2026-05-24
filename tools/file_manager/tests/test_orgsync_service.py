"""
Unit Tests for OrgSync Service
"""

import pytest
from services.orgsync_service import (
    OrgSyncService,
    WeChatWorkAdapter,
    FeishuAdapter,
    OrgProvider,
    OrgUser,
    OrgDepartment,
    SyncResult,
)


class TestWeChatWorkAdapter:
    """Test WeChat Work adapter"""

    def test_adapter_initialization(self):
        """Should initialize with corp credentials"""
        adapter = WeChatWorkAdapter(
            corp_id="test-corp-id",
            agent_id="test-agent-id",
            secret="test-secret",
        )
        assert adapter._corp_id == "test-corp-id"
        assert adapter._agent_id == "test-agent-id"
        assert adapter._secret == "test-secret"
        assert adapter.provider == OrgProvider.WECHAT_WORK


class TestFeishuAdapter:
    """Test Feishu adapter"""

    def test_adapter_initialization(self):
        """Should initialize with app credentials"""
        adapter = FeishuAdapter(
            app_id="test-app-id",
            app_secret="test-secret",
        )
        assert adapter._corp_id == "test-app-id"
        assert adapter._secret == "test-secret"
        assert adapter.provider == OrgProvider.FEISHU


class TestOrgUser:
    """Test OrgUser dataclass"""

    def test_org_user_creation(self):
        """Should create OrgUser with required fields"""
        user = OrgUser(
            provider=OrgProvider.WECHAT_WORK,
            provider_user_id="user-123",
            name="Test User",
        )
        assert user.provider == OrgProvider.WECHAT_WORK
        assert user.provider_user_id == "user-123"
        assert user.name == "Test User"
        assert user.email is None
        assert user.is_leader is False

    def test_org_user_with_all_fields(self):
        """Should create OrgUser with all fields"""
        user = OrgUser(
            provider=OrgProvider.FEISHU,
            provider_user_id="user-456",
            name="Alice",
            email="alice@example.com",
            department_id="dept-1",
            department_name="Engineering",
            is_leader=True,
        )
        assert user.email == "alice@example.com"
        assert user.department_id == "dept-1"
        assert user.department_name == "Engineering"
        assert user.is_leader is True


class TestOrgDepartment:
    """Test OrgDepartment dataclass"""

    def test_org_department_creation(self):
        """Should create OrgDepartment"""
        dept = OrgDepartment(
            provider=OrgProvider.WECHAT_WORK,
            department_id="dept-001",
            parent_id="0",
            name="Headquarters",
        )
        assert dept.department_id == "dept-001"
        assert dept.parent_id == "0"
        assert dept.name == "Headquarters"

    def test_org_department_order(self):
        """Should support order field"""
        dept = OrgDepartment(
            provider=OrgProvider.FEISHU,
            department_id="dept-002",
            parent_id="0",
            name="Sales",
            order=100,
        )
        assert dept.order == 100


class TestSyncResult:
    """Test SyncResult dataclass"""

    def test_sync_result_success(self):
        """Should track successful sync"""
        result = SyncResult(
            provider=OrgProvider.WECHAT_WORK,
            started_at=1000.0,
            completed_at=1010.0,
            users_added=5,
            users_updated=2,
            departments_added=3,
        )
        assert result.success is True
        assert result.total_changes == 10  # 5+2+3
        assert len(result.errors) == 0

    def test_sync_result_with_errors(self):
        """Should track errors"""
        result = SyncResult(
            provider=OrgProvider.WECHAT_WORK,
            started_at=1000.0,
            completed_at=1010.0,
            errors=["API timeout", "Invalid data"],
        )
        assert result.success is False
        assert len(result.errors) == 2


class TestOrgSyncServiceInitialization:
    """Test OrgSyncService initialization"""

    def test_service_initialization(self):
        """Should initialize with db_factory"""
        # Mock db_factory
        def mock_db():
            return None

        svc = OrgSyncService(
            db_factory=mock_db,
            default_role="editor",
            sync_interval_seconds=1800,
        )
        assert svc._default_role == "editor"
        assert svc._sync_interval == 1800

    def test_register_provider(self):
        """Should register organization provider"""
        def mock_db():
            return None

        svc = OrgSyncService(db_factory=mock_db)
        adapter = WeChatWorkAdapter(
            corp_id="test",
            agent_id="test",
            secret="test",
        )
        svc.register_provider("wechat-work-main", adapter)
        assert "wechat-work-main" in svc._providers
        assert svc._providers["wechat-work-main"].provider == OrgProvider.WECHAT_WORK


class TestOrgSyncServiceSync:
    """Test OrgSyncService sync operations"""

    def test_sync_from_unknown_provider(self):
        """Should return error for unknown provider"""
        def mock_db():
            return None

        svc = OrgSyncService(db_factory=mock_db)
        result = svc.sync_from_provider("unknown-provider")
        assert result.success is False
        assert len(result.errors) > 0

    def test_get_last_sync_time_not_set(self):
        """Should return None when no sync has been done"""
        def mock_db():
            return None

        svc = OrgSyncService(db_factory=mock_db)
        assert svc.get_last_sync_time("any-provider") is None


class TestOrgProviderEnum:
    """Test OrgProvider enum"""

    def test_provider_values(self):
        """Should have correct provider values"""
        assert OrgProvider.WECHAT_WORK.value == "wechat_work"
        assert OrgProvider.FEISHU.value == "feishu"
        assert OrgProvider.DINGTALK.value == "dingtalk"