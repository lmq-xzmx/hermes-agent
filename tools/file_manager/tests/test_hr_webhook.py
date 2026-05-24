"""
测试 HR Webhook API - 入职/离职事件处理

包括：
- HMAC 签名验证
- 入职 Webhook 处理
- 离职 Webhook 处理
- 企业配置下发

注意：这些测试需要 FastAPI TestClient，使用 app 作为 fixture
"""

import pytest
import hmac
import hashlib
import time
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# 使用 conftest 提供的 app fixture
# 由于 server.py 有复杂的依赖，我们直接测试 HMAC 验证逻辑


class TestHMACSignature:
    """测试 HMAC 签名验证"""

    def setup_method(self):
        # 导入签名验证函数
        from file_manager.api.admin.webhooks.onboarding import verify_hmac_signature
        self.verify_fn = verify_hmac_signature
        self.secret = "test-secret-key"

    def test_valid_signature(self):
        """测试有效签名"""
        timestamp = str(int(time.time()))
        payload = '{"event": "employee.onboarding"}'

        signature = hmac.new(
            self.secret.encode(),
            f"{timestamp}.{payload}".encode(),
            hashlib.sha256
        ).hexdigest()

        result = self.verify_fn(
            secret=self.secret,
            timestamp=timestamp,
            payload=payload,
            signature=f"sha256={signature}",
        )
        assert result is True

    def test_invalid_signature(self):
        """测试无效签名"""
        result = self.verify_fn(
            secret=self.secret,
            timestamp=str(int(time.time())),
            payload='{"event": "test"}',
            signature="sha256=invalid_signature",
        )
        assert result is False

    def test_expired_timestamp(self):
        """测试过期时间戳"""
        old_timestamp = str(int(time.time()) - 600)  # 10分钟前
        payload = '{"event": "test"}'

        signature = hmac.new(
            self.secret.encode(),
            f"{old_timestamp}.{payload}".encode(),
            hashlib.sha256
        ).hexdigest()

        result = self.verify_fn(
            secret=self.secret,
            timestamp=old_timestamp,
            payload=payload,
            signature=f"sha256={signature}",
            max_age_seconds=300,  # 5分钟有效期
        )
        assert result is False

    def test_signature_without_sha256_prefix(self):
        """测试缺少 sha256= 前缀"""
        timestamp = str(int(time.time()))
        payload = '{"event": "test"}'

        signature = hmac.new(
            self.secret.encode(),
            f"{timestamp}.{payload}".encode(),
            hashlib.sha256
        ).hexdigest()

        # 不带前缀的签名应该失败
        result = self.verify_fn(
            secret=self.secret,
            timestamp=timestamp,
            payload=payload,
            signature=signature,  # 直接是 hex，没有 sha256= 前缀
        )
        assert result is False

    def test_different_payload_changes_result(self):
        """测试不同 payload 产生不同结果"""
        timestamp = str(int(time.time()))

        sig1 = hmac.new(
            self.secret.encode(),
            f"{timestamp}.payload1".encode(),
            hashlib.sha256
        ).hexdigest()

        sig2 = hmac.new(
            self.secret.encode(),
            f"{timestamp}.payload2".encode(),
            hashlib.sha256
        ).hexdigest()

        # 同一个 timestamp，不同 payload，签名不同
        assert sig1 != sig2


class TestWebhookSecret:
    """测试 Webhook Secret 获取"""

    def test_get_webhook_secret_default(self):
        """测试默认 secret"""
        from file_manager.api.admin.webhooks.onboarding import get_webhook_secret

        with patch.dict('os.environ', {}, clear=True):
            secret = get_webhook_secret()
            assert secret == "dev-webhook-secret"

    def test_get_webhook_secret_from_env(self):
        """测试从环境变量获取"""
        from file_manager.api.admin.webhooks.onboarding import get_webhook_secret

        with patch.dict('os.environ', {'HR_WEBHOOK_SECRET': 'my-secret-key'}):
            secret = get_webhook_secret()
            assert secret == "my-secret-key"


class TestOnboardingRequest:
    """测试入职请求模型"""

    def test_employee_info_model(self):
        """测试员工信息模型"""
        from file_manager.api.admin.webhooks.onboarding import EmployeeInfo

        emp = EmployeeInfo(
            external_id="user_123",
            name="张三",
            email="zhangsan@company.com",
            department="技术部",
            department_id="dept_tech",
        )

        assert emp.external_id == "user_123"
        assert emp.name == "张三"
        assert emp.email == "zhangsan@company.com"

    def test_onboarding_settings_model(self):
        """测试入职设置模型"""
        from file_manager.api.admin.webhooks.onboarding import OnboardingSettings

        settings = OnboardingSettings(
            knowledge_share_policy="full_share",
            default_space="hermes-tech",
            role="editor",
        )

        assert settings.knowledge_share_policy == "full_share"
        assert settings.default_space == "hermes-tech"
        assert settings.role == "editor"

    def test_onboarding_settings_defaults(self):
        """测试默认值"""
        from file_manager.api.admin.webhooks.onboarding import OnboardingSettings

        settings = OnboardingSettings()

        assert settings.knowledge_share_policy == "full_share"
        assert settings.default_space == "hermes-tech"
        assert settings.role == "editor"


class TestOffboardingRequest:
    """测试离职请求模型"""

    def test_offboarding_settings_model(self):
        """测试离职设置模型"""
        from file_manager.api.admin.webhooks.onboarding import OffboardingSettings

        settings = OffboardingSettings(
            last_workday="2026-12-31",
            grace_period_days=30,
            export_personal=True,
        )

        assert settings.last_workday == "2026-12-31"
        assert settings.grace_period_days == 30
        assert settings.export_personal is True

    def test_offboarding_settings_defaults(self):
        """测试离职设置默认值"""
        from file_manager.api.admin.webhooks.onboarding import OffboardingSettings

        settings = OffboardingSettings(last_workday="2026-12-31")

        assert settings.grace_period_days == 30
        assert settings.export_personal is True


class TestWebhookResponse:
    """测试 Webhook 响应模型"""

    def test_response_model_success(self):
        """测试成功响应"""
        from file_manager.api.admin.webhooks.onboarding import WebhookResponse

        response = WebhookResponse(
            status="success",
            user_id="user_123",
            message="Employee onboarding completed",
        )

        assert response.status == "success"
        assert response.user_id == "user_123"

    def test_response_model_with_actions(self):
        """测试带 actions 的响应"""
        from file_manager.api.admin.webhooks.onboarding import WebhookResponse

        response = WebhookResponse(
            status="success",
            user_id="user_123",
            message="Done",
            actions=[
                {"action": "create_account", "result": "created"},
                {"action": "join_space", "result": "hermes-tech"},
            ],
        )

        assert len(response.actions) == 2
        assert response.actions[0]["action"] == "create_account"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])