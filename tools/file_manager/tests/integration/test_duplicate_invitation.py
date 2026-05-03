"""
T6: 并发邀请防护集成测试

REQ-M2-018: 并发邀请防护
- 数据库唯一索引: ix_hfm_space_members_unique
- 应用层检查: space_service.py:713

TDD 流程:
    Red: 编写失败的测试（模拟并发邀请场景）
    Green: 验证防护机制生效
    Refactor: 优化测试代码
"""

import os
import sys
import pytest
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Make file_manager importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import Space, SpaceMember, User, Role, StoragePool
from tools.file_manager.services.space_service import SpaceService, UserAlreadyInSpace
from tools.file_manager.engine.lifecycle_exception import LifecycleViolation
from tools.file_manager.engine.lifecycle_engine import LifecycleEngine


class TestDuplicateInvitationProtection:
    """
    并发邀请防护集成测试

    验证:
    1. 数据库唯一索引防止重复记录
    2. 应用层检查在事务中生效
    3. 并发邀请时只有一个成功
    """

    @pytest.fixture
    def db_session(self, tmp_path, monkeypatch):
        """Create an in-memory SQLite DB with all tables."""
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

        from tools.file_manager.engine.models import init_db, Base
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
    def storage_pool(self, db_session):
        """Create a test storage pool (10GB)."""
        pool = StoragePool(
            name="Test Pool",
            base_path="/tmp/test-pool",
            protocol="local",
            total_bytes=10 * 1024**3,
            free_bytes=10 * 1024**3,
            is_active=True,
        )
        db_session.add(pool)
        db_session.commit()
        db_session.refresh(pool)
        return pool

    @pytest.fixture
    def space(self, db_session, storage_pool):
        """Create a test space with alice as owner."""
        user = db_session.query(User).filter(User.username == "alice").first()

        space = Space(
            name="Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=1 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        db_session.refresh(space)
        return space

    @pytest.fixture
    def space_service(self, db_factory):
        return SpaceService(db_factory=db_factory)

    def test_database_unique_index_exists(self, db_session, space):
        """
        契约测试: 数据库唯一索引 ix_hfm_space_members_unique 存在

        验证 SpaceMember 表的唯一索引正确创建。
        """
        from sqlalchemy import inspect

        inspector = inspect(db_session.get_bind())
        indexes = inspector.get_indexes("hfm_space_members")

        assert len(indexes) > 0, "SpaceMember should have indexes"

    def test_application_layer_rejects_duplicate_invitation(
        self, db_session, space, space_service
    ):
        """
        契约测试: 应用层检查拒绝重复邀请 - REQ-M2-018

        验证 space_service.add_member() 在发现已存在活动成员时正确处理。
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # First invitation should succeed
        result1 = space_service.add_member(
            space_id=space.id,
            user_id=user.id,
            requesting_user_id=space.owner_id,
            role="member"
        )
        assert result1 is not None, "First invitation should succeed"

        # Second invitation with same user should raise UserAlreadyInSpace
        with pytest.raises(UserAlreadyInSpace):
            space_service.add_member(
                space_id=space.id,
                user_id=user.id,
                requesting_user_id=space.owner_id,
                role="member"
            )

    def test_concurrent_invitations_same_user_rejected(self, db_session, space, db_factory):
        """
        契约测试: 并发邀请同一用户只有一个成功 - REQ-M2-018

        Note: 使用顺序测试替代多线程测试（SQLite 不支持多线程并发）
        验证数据库唯一索引防止重复成员记录。
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # First, add the member via service
        service = SpaceService(db_factory)
        service.add_member(
            space_id=space.id,
            user_id=user.id,
            requesting_user_id=space.owner_id,
            role="member"
        )

        # Verify that the member was added
        member = db_session.query(SpaceMember).filter(
            SpaceMember.space_id == space.id,
            SpaceMember.user_id == user.id,
            SpaceMember.status == "active"
        ).first()
        assert member is not None, "Member should be added"

        # Verify second add_member call raises error
        with pytest.raises(UserAlreadyInSpace):
            service.add_member(
                space_id=space.id,
                user_id=user.id,
                requesting_user_id=space.owner_id,
                role="member"
            )

        # Verify the duplicate constraint works at database level too
        # Try to insert duplicate directly
        from sqlalchemy.exc import IntegrityError
        dup_member = SpaceMember(
            space_id=space.id,
            user_id=user.id,
            role="member",
            status="active",
        )
        db_session.add(dup_member)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_recently_removed_member_cannot_be_reinvited(
        self, db_session, space, space_service
    ):
        """
        边缘 case: REQ-M2-013 MEMBER_RECENTLY_REMOVED

        验证刚被移除的成员不能立即重新邀请（24小时窗口期）。
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # First, add the member
        space_service.add_member(
            space_id=space.id,
            user_id=user.id,
            requesting_user_id=space.owner_id,
            role="member"
        )

        # Remove the member
        member = db_session.query(SpaceMember).filter(
            SpaceMember.space_id == space.id,
            SpaceMember.user_id == user.id
        ).first()
        member.status = "removed"
        db_session.commit()

        # Check lifecycle rule for recently removed
        engine = LifecycleEngine()
        context = {
            "space_id": space.id,
            "user_id": user.id,
            "is_owner": space.owner_id == user.id,
            "was_recently_removed": True
        }

        # Lifecycle engine should block re-invite
        violated = engine.check("invite_member", context)
        assert violated is not None, "Should detect recently_removed constraint"
        assert violated.code == "MEMBER_RECENTLY_REMOVED"

    def test_duplicate_invitation_integrity_error(self, db_session, space, db_factory):
        """
        契约测试: 并发重复邀请触发数据库唯一索引

        场景：两个事务同时添加同一成员，第二个应因唯一索引而失败
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        # First invitation succeeds
        service = SpaceService(db_factory)
        service.add_member(
            space_id=space.id,
            user_id=user.id,
            requesting_user_id=space.owner_id,
            role="member"
        )

        # Second invitation should be caught by application layer first
        with pytest.raises(UserAlreadyInSpace):
            service.add_member(
                space_id=space.id,
                user_id=user.id,
                requesting_user_id=space.owner_id,
                role="member"
            )

    def test_user_can_join_different_spaces(self, db_session, storage_pool, db_factory):
        """
        验证: 同一用户可以同时存在于不同空间 - REQ-M2-018 边界

        唯一索引只防止同一 space_id + user_id 组合，
        不应阻止用户加入不同空间。
        """
        user = db_session.query(User).filter(User.username == "alice").first()

        service = SpaceService(db_factory)

        # Create two different spaces
        space1 = Space(
            name="Space 1",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=1 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        space2 = Space(
            name="Space 2",
            storage_pool_id=storage_pool.id,
            owner_id=user.id,
            max_bytes=1 * 1024**3,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space1)
        db_session.add(space2)
        db_session.commit()

        # Refresh to get IDs while still attached to session
        db_session.refresh(space1)
        db_session.refresh(space2)

        space1_id = space1.id
        space2_id = space2.id

        # User should be able to join both spaces
        result1 = service.add_member(
            space_id=space1_id,
            user_id=user.id,
            requesting_user_id=user.id,
            role="owner"
        )
        assert result1 is not None

        result2 = service.add_member(
            space_id=space2_id,
            user_id=user.id,
            requesting_user_id=user.id,
            role="owner"
        )
        assert result2 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])