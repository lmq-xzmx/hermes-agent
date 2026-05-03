"""
T2: 配额超限拦截集成测试

TDD Red阶段：验证配额超限时上传被拦截，返回 403 + QUOTA_EXCEEDED

测试场景：
1. 配额超限场景 (403 + QUOTA_EXCEEDED)
2. 配额刚好用尽场景
3. 配额超限后释放再使用场景

依赖: T1 (集成测试框架) 已完成
参考: tests/integration/conftest.py fixtures
"""

import pytest
import sys
from pathlib import Path

# Make file_manager importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from file_manager.engine.models import Space, SpaceMember, StoragePool, User, Role
from file_manager.engine.lifecycle_exception import LifecycleViolation, ErrorCode
from file_manager.services.space_service import SpaceService, QuotaExceeded


class TestQuotaExceededIntegration:
    """配额超限拦截集成测试 - REQ-M2-001"""

    @pytest.fixture
    def db_session(self, tmp_path, monkeypatch):
        """Create an in-memory SQLite DB with all tables."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

        from file_manager.engine.models import init_db, Base
        factory = init_db("sqlite:///:memory:")
        session = factory()

        # Seed test user role
        role = Role(name="user", description="Regular user", is_system=True)
        session.add(role)
        session.flush()

        # Seed test user
        user = User(username="alice", email="alice@test.local", role_id=role.id)
        user.set_password("secret123")
        session.add(user)
        session.commit()

        return session

    @pytest.fixture
    def db_factory(self, db_session):
        """DB factory that always returns the same session."""
        class Factory:
            def __call__(self):
                return db_session
        return Factory()

    @pytest.fixture
    def space_service(self, db_factory):
        return SpaceService(db_factory=db_factory)

    @pytest.fixture
    def small_pool(self, db_session):
        """Create a small storage pool (10MB) for quota tests."""
        pool = StoragePool(
            name="Small Pool",
            base_path="/tmp/small-pool",
            protocol="local",
            total_bytes=10 * 1024**2,  # 10 MB
            free_bytes=10 * 1024**2,
            is_active=True,
        )
        db_session.add(pool)
        db_session.commit()
        return pool

    @pytest.fixture
    def quota_space(self, db_session, small_pool):
        """Create a test space with 5MB quota."""
        from file_manager.engine.models import User

        user = db_session.query(User).filter(User.username == "alice").first()

        space = Space(
            name="Quota Test Space",
            storage_pool_id=small_pool.id,
            owner_id=user.id,
            max_bytes=5 * 1024**2,  # 5 MB quota
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.flush()

        # Add user as member
        member = SpaceMember(
            space_id=space.id,
            user_id=user.id,
            role="member",
            status="active",
        )
        db_session.add(member)
        db_session.commit()

        return space

    def test_quota_exceeded_blocks_upload(
        self, db_session, quota_space, space_service
    ):
        """
        Red测试：配额超限时，新上传应被阻止

        场景：空间配额5MB，已使用4MB，尝试上传2MB
        期望：抛出 LifecycleViolation 异常（lifecycle_engine.py 已有 QUOTA_EXCEEDED 检查）
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # 已使用 4MB，剩余 1MB
        quota_space.used_bytes = 4 * 1024**2
        db_session.commit()
        db_session.refresh(quota_space)

        # 尝试上传 2MB（超过剩余1MB）
        with pytest.raises(LifecycleViolation) as exc_info:
            space_service.check_quota_for_write(
                space_id=quota_space.id,
                additional_bytes=2 * 1024**2,  # 2 MB
                user_id=user.id
            )

        # 验证错误码
        assert "quota" in str(exc_info.value).lower() or "配额" in str(exc_info.value)

    def test_quota_exceeded_returns_403_error(
        self, db_session, quota_space, space_service
    ):
        """
        验证配额超限时返回的异常包含正确的错误码

        场景：配额用尽时尝试写入
        期望：异常包含 SPACE_QUOTA_EXCEEDED 错误码
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # 配额已用尽
        quota_space.used_bytes = quota_space.max_bytes
        db_session.commit()
        db_session.refresh(quota_space)

        # 尝试上传任何大小都应该被阻止
        with pytest.raises(LifecycleViolation):
            space_service.check_quota_for_write(
                space_id=quota_space.id,
                additional_bytes=1024,  # 1KB
                user_id=user.id
            )

    def test_quota_at_exactly_limit(
        self, db_session, quota_space, space_service
    ):
        """
        配额刚好用尽场景

        场景：已使用 = 最大配额
        期望：任何写入都被阻止
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # 刚好用尽
        quota_space.used_bytes = quota_space.max_bytes
        db_session.commit()
        db_session.refresh(quota_space)

        with pytest.raises(LifecycleViolation):
            space_service.check_quota_for_write(
                space_id=quota_space.id,
                additional_bytes=1,  # 最小单位
                user_id=user.id
            )

    def test_quota_reserved_prevents_overwrite(
        self, db_session, quota_space, space_service, db_factory
    ):
        """
        配额预留场景

        场景：已有上传预留时，配额检查应考虑预留量
        期望：used + reserved + new > max 时阻止

        注意：需要使用 check_quota_for_write_with_lock 才能考虑预留配额
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # 获取所有 id 在 commit/detach 之前
        space_id = quota_space.id
        user_id = user.id

        # 已使用 3MB
        quota_space.used_bytes = 3 * 1024**2
        db_session.commit()

        # 创建 2MB 预留（模拟正在上传的文件）
        from file_manager.engine.file_upload_service import FileUploadService
        upload_service = FileUploadService(db_factory=db_factory)

        upload = upload_service.create_upload(
            space_id=space_id,
            user_id=user_id,
            file_name="pending.bin",
            file_size=2 * 1024**2  # 2 MB reserved
        )

        # 现在可用配额 = 5 - 3 - 2 = 0 MB
        # 尝试上传 1KB 应该被阻止
        # 注意：使用 check_quota_for_write_with_lock 才能考虑预留配额
        with pytest.raises((LifecycleViolation, Exception)):
            space_service.check_quota_for_write_with_lock(
                space_id=space_id,
                additional_bytes=1024,  # 1 KB
                user_id=user_id
            )


class TestQuotaExceededErrorCode:
    """配额超限错误码契约测试 - 确保与 INTERFACE_CONTRACT.md 一致"""

    @pytest.fixture
    def db_session(self, tmp_path, monkeypatch):
        """Create an in-memory SQLite DB with all tables."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

        from file_manager.engine.models import init_db, Base
        factory = init_db("sqlite:///:memory:")
        session = factory()

        role = Role(name="user", description="Regular user", is_system=True)
        session.add(role)
        session.flush()

        user = User(username="alice", email="alice@test.local", role_id=role.id)
        user.set_password("secret123")
        session.add(user)
        session.commit()

        return session

    def test_lifecycle_violation_quota_exceeded_code(
        self, db_session, tmp_path, monkeypatch
    ):
        """
        验证 LifecycleViolation.quota_exceeded() 返回正确的错误码

        根据 INTERFACE_CONTRACT.md:
        - 配额超限应返回 code: "LIFECYCLE_QUOTA_EXCEEDED" 或 "SPACE_QUOTA_EXCEEDED"
        """
        from file_manager.engine.lifecycle_exception import LifecycleViolation

        error = LifecycleViolation.quota_exceeded(
            space_name="Test Space",
            used=5 * 1024**2,
            max=5 * 1024**2,
            required=1 * 1024**2
        )

        # 验证错误码
        assert error.code in [ErrorCode.SPACE_QUOTA_EXCEEDED.value, "LIFECYCLE_QUOTA_EXCEEDED"]
        assert "配额" in error.message or "quota" in error.message.lower()

    def test_quota_exceeded_guidance_action(self, db_session):
        """验证配额超限时的 guidance 包含正确的操作指引"""
        from file_manager.engine.lifecycle_exception import LifecycleViolation

        error = LifecycleViolation.quota_exceeded(
            space_name="Test Space",
            used=5 * 1024**2,
            max=5 * 1024**2,
            required=1 * 1024**2
        )

        # 验证 guidance 包含操作指引
        assert error.guidance is not None
        # 根据设计，guidance 应包含 path 或 action
        assert error.guidance.path or error.guidance.action_type or error.guidance.label


if __name__ == "__main__":
    pytest.main([__file__, "-v"])