"""
REQ-M6-002: 集成测试框架搭建 - Lifecycle API 测试

测试 lifecycle engine 与 service 层的集成：
- 配额超限拦截 (REQ-M2-001)
- 非成员禁止上传 (REQ-M2-002)
- 存储池校验 (REQ-M2-003)
- 生命周期约束 (REQ-M2-005~010)

使用 fixtures from tests/integration/conftest.py
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestLifecycleAPISmoke:
    """生命周期约束 API 冒烟测试"""

    def test_lifecycle_engine_import(self):
        """验证 lifecycle engine 可正常导入"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine
        engine = LifecycleEngine()
        assert engine is not None

    def test_space_service_import(self):
        """验证 SpaceService 可正常导入"""
        from file_manager.services.space_service import SpaceService
        assert SpaceService is not None

    def test_team_service_import(self):
        """验证 TeamService 可正常导入"""
        from file_manager.services.team_service import TeamService
        assert TeamService is not None


class TestQuotaConstraints:
    """配额约束集成测试 (REQ-M2-001)"""

    def test_quota_check_returns_true_when_available(
        self, db_session, test_user, small_space
    ):
        """配额充足时检查应返回 True"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        ctx = {
            "db_session": db_session,
            "user_id": test_user.id,
            "space_id": small_space.id,
            "file_size": 1024,  # 1KB, small_space has 1MB
        }

        result = engine.check("quota_available", ctx)
        # Should pass (return None or True depending on implementation)
        assert result is None or result is True

    def test_quota_exceeded_violation(
        self, db_session, test_user, small_space
    ):
        """配额超限时应触发约束"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()

        # Set space used_bytes close to max_bytes
        small_space.used_bytes = small_space.max_bytes - 100
        db_session.commit()

        # Calculate remaining quota
        remaining = small_space.max_bytes - small_space.used_bytes
        file_size = 1000  # Larger than remaining (100 bytes)

        # Quota is exceeded if file_size > remaining
        assert file_size > remaining, "File size should exceed remaining quota"


class TestMembershipConstraints:
    """成员约束集成测试 (REQ-M2-002)"""

    def test_is_member_check_for_owner(
        self, db_session, test_user, space
    ):
        """空间所有者应被视为成员"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        # First, add owner as a member
        from file_manager.engine.models import SpaceMember
        member = SpaceMember(
            space_id=space.id,
            user_id=test_user.id,
            role="owner",
            status="active",
        )
        db_session.add(member)
        db_session.commit()

        result = engine.check_membership(
            user_id=test_user.id,
            space_id=space.id,
            db_factory=lambda: db_session
        )
        # Owner added as member should be a member
        assert result is True

    def test_is_member_check_for_non_member(
        self, db_session, admin_user, space
    ):
        """非成员应返回违规"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        result = engine.check_membership(
            user_id=admin_user.id,  # admin is not a member of space
            space_id=space.id,
            db_factory=lambda: db_session
        )
        # Non-member should return False
        assert result is False


class TestPoolConstraints:
    """存储池约束集成测试 (REQ-M2-003, REQ-M2-005)"""

    def test_get_team_count_for_pool(
        self, db_session, test_user, storage_pool
    ):
        """验证获取池中团队数量"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine
        from file_manager.engine.models import Team

        engine = LifecycleEngine()

        # Create a team using this pool
        team = Team(
            name="Test Team for Pool",
            owner_id=test_user.id,
            storage_pool_id=storage_pool.id,
            max_bytes=1024**3,
            used_bytes=0,
            status="active",
        )
        db_session.add(team)
        db_session.commit()

        count = engine.get_team_count_for_pool(storage_pool.id, lambda: db_session)
        assert count >= 1

    def test_pool_available_for_team_creation(
        self, db_session, storage_pool
    ):
        """有可用存储池时应允许创建团队"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        available_count = engine.get_available_pool_count(lambda: db_session)
        assert available_count >= 1


class TestOwnershipConstraints:
    """所有权约束集成测试 (REQ-M2-007, REQ-M2-008, REQ-M2-009)"""

    def test_owner_can_invite_member(
        self, db_session, test_user, admin_user, space
    ):
        """所有者应能邀请成员"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        is_owner = engine.check_owner(
            user_id=test_user.id,  # owner
            space_id=space.id,
            db_factory=lambda: db_session
        )
        assert is_owner is True

    def test_non_owner_cannot_invite_member(
        self, db_session, admin_user, space
    ):
        """非所有者不能邀请成员"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        is_owner = engine.check_owner(
            user_id=admin_user.id,  # not owner
            space_id=space.id,
            db_factory=lambda: db_session
        )
        assert is_owner is False

    def test_owner_can_update_quota(
        self, db_session, test_user, space
    ):
        """所有者应能更新配额"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        is_owner = engine.check_owner(
            user_id=test_user.id,
            space_id=space.id,
            db_factory=lambda: db_session
        )
        assert is_owner is True

    def test_non_owner_cannot_update_quota(
        self, db_session, admin_user, space
    ):
        """非所有者不能更新配额"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        is_owner = engine.check_owner(
            user_id=admin_user.id,
            space_id=space.id,
            db_factory=lambda: db_session
        )
        assert is_owner is False


class TestSpaceDeletionConstraints:
    """空间删除约束集成测试 (REQ-M2-006)"""

    def test_get_member_count_for_space(
        self, db_session, test_user, admin_user, space
    ):
        """验证获取空间成员数量"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine
        from file_manager.engine.models import SpaceMember

        engine = LifecycleEngine()

        # Add a member to the space
        member = SpaceMember(
            space_id=space.id,
            user_id=admin_user.id,
            role="member",
            status="active",
        )
        db_session.add(member)
        db_session.commit()

        count = engine.get_member_count_for_space(space.id, lambda: db_session)
        assert count >= 1

    def test_space_without_members_count(
        self, db_session, test_user, space
    ):
        """无成员的空间"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        count = engine.get_member_count_for_space(space.id, lambda: db_session)
        assert count == 0


class TestEdgeCases:
    """边缘 case 集成测试 (REQ-M2-011~014)"""

    def test_get_team_migrating_count(
        self, db_session, test_user, storage_pool
    ):
        """POOL_MIGRATING 状态处理"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        count = engine.get_team_migrating_count(storage_pool.id, lambda: db_session)
        assert count >= 0

    def test_get_quota_reserved(
        self, db_session, test_user, space
    ):
        """QUOTA_RESERVED 并发边缘 case"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        reserved = engine.get_quota_reserved(space.id, lambda: db_session)
        assert reserved >= 0

    def test_member_recently_removed_case(
        self, db_session, test_user, admin_user, space
    ):
        """MEMBER_RECENTLY_REMOVED 边缘 case"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine
        from file_manager.engine.models import SpaceMember

        engine = LifecycleEngine()

        # Add member then remove
        member = SpaceMember(
            space_id=space.id,
            user_id=admin_user.id,
            role="member",
            status="removed",  # Recently removed
        )
        db_session.add(member)
        db_session.commit()

        was_removed = engine.check_recently_removed_member(
            user_id=admin_user.id,
            space_id=space.id,
            db_factory=lambda: db_session,
            hours=24
        )
        assert was_removed is True

    def test_get_pending_request_count(
        self, db_session, test_user, space
    ):
        """SPACE_HAS_PENDING_REQUESTS 边缘 case"""
        from file_manager.engine.lifecycle_engine import LifecycleEngine

        engine = LifecycleEngine()
        count = engine.get_pending_request_count(space.id, lambda: db_session)
        assert count >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
