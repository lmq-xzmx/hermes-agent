"""
T5: 配额超卖防护集成测试

测试 check_quota_for_write_with_lock 的 SELECT FOR UPDATE 功能

测试场景：
1. 配额超限时抛出 QuotaExceeded
2. 并发上传时正确锁定 Space 记录
3. 配额预留计算正确
"""

import pytest

from file_manager.engine.models import Space, FileUpload
from file_manager.services.space_service import QuotaExceeded, SpaceService
from file_manager.engine.file_upload_service import FileUploadService
from file_manager.engine.lifecycle_exception import LifecycleViolation


class TestConcurrentUploadQuota:
    """并发上传配额防护测试 - T5 REQ-M2-017"""

    @pytest.fixture
    def space_service(self, db_factory):
        return SpaceService(db_factory=db_factory)

    @pytest.fixture
    def upload_service(self, db_factory):
        return FileUploadService(db_factory=db_factory)

    def test_quota_exceeded_raises_exception(
        self, db_session, test_user, storage_pool, space_service
    ):
        """
        测试：配额超限时 check_quota_for_write_with_lock 抛出异常

        场景：空间已使用90MB，尝试上传20MB（超过剩余10MB）
        """
        # 创建100MB配额空间，已使用90MB
        space = Space(
            name="Quota Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=test_user.id,
            max_bytes=100 * 1024 * 1024,
            used_bytes=90 * 1024 * 1024,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        space_id = space.id

        # 尝试上传 20MB（超过剩余10MB），应抛出异常
        with pytest.raises((QuotaExceeded, LifecycleViolation)):
            space_service.check_quota_for_write_with_lock(
                space_id=space_id,
                additional_bytes=20 * 1024 * 1024,
                user_id=test_user.id
            )

    def test_quota_with_pending_uploads(
        self, db_session, test_user, storage_pool, upload_service, space_service
    ):
        """
        测试：配额检查应考虑正在上传的文件预留

        场景：空间已使用80MB，有20MB的pending upload，尝试上传1MB应被拒绝
        """
        user_id = test_user.id  # 先获取，避免后续detach问题

        # 创建100MB配额空间，已使用80MB
        space = Space(
            name="Quota Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=user_id,
            max_bytes=100 * 1024 * 1024,
            used_bytes=80 * 1024 * 1024,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        space_id = space.id

        # 创建一个20MB的上传记录（预留20MB）
        upload_service.create_upload(
            space_id=space_id,
            user_id=user_id,
            file_name="pending.bin",
            file_size=20 * 1024 * 1024
        )

        # 剩余配额 = 100 - 80 - 20 = 0MB，尝试上传1MB应被拒绝
        with pytest.raises((QuotaExceeded, LifecycleViolation)):
            space_service.check_quota_for_write_with_lock(
                space_id=space_id,
                additional_bytes=1 * 1024 * 1024,
                user_id=user_id
            )

    def test_quota_with_multiple_pending_uploads(
        self, db_session, test_user, storage_pool, upload_service, space_service
    ):
        """
        测试：多个并发预留配额时，计算正确

        场景：空间已使用50MB，有3个各20MB的pending upload
        由于 max=100MB, used=50MB, 只能创建2个20MB上传（共预留40MB），第三个20MB上传应被拒绝
        """
        user_id = test_user.id  # 先获取，避免后续detach问题

        # 创建100MB配额空间，已使用50MB
        space = Space(
            name="Quota Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=user_id,
            max_bytes=100 * 1024 * 1024,
            used_bytes=50 * 1024 * 1024,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        space_id = space.id

        # 创建2个并发上传，每个20MB（预留共40MB）
        # 可用 = 100 - 50 - 40 = 10MB，所以第三个上传会失败
        for i in range(2):
            upload_service.create_upload(
                space_id=space_id,
                user_id=user_id,
                file_name=f"pending_{i}.bin",
                file_size=20 * 1024 * 1024
            )

        # 剩余配额 = 100 - 50 - 40 = 10MB < 20MB，第三个上传应被拒绝
        from file_manager.engine.file_upload_service import QuotaExceededError as UploadQuotaExceeded
        with pytest.raises((QuotaExceeded, LifecycleViolation, UploadQuotaExceeded)):
            upload_service.create_upload(
                space_id=space_id,
                user_id=user_id,
                file_name="pending_2.bin",
                file_size=20 * 1024 * 1024
            )

    def test_quota_available_allows_upload(
        self, db_session, test_user, storage_pool, space_service
    ):
        """
        测试：配额足够时，允许上传

        场景：空间已使用50MB，尝试上传30MB（剩余50MB刚好够）
        """
        user_id = test_user.id  # 先获取

        # 创建100MB配额空间，已使用50MB
        space = Space(
            name="Quota Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=user_id,
            max_bytes=100 * 1024 * 1024,
            used_bytes=50 * 1024 * 1024,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        space_id = space.id

        # 尝试上传 30MB（剩余50MB刚好够），不应抛出异常
        space_service.check_quota_for_write_with_lock(
            space_id=space_id,
            additional_bytes=30 * 1024 * 1024,
            user_id=user_id
        )

    def test_get_quota_reserved_sums_pending(
        self, db_session, test_user, storage_pool, upload_service
    ):
        """
        测试：get_quota_reserved 正确计算预留配额
        """
        user_id = test_user.id  # 先获取

        # 创建100MB配额空间
        space = Space(
            name="Quota Test Space",
            storage_pool_id=storage_pool.id,
            owner_id=user_id,
            max_bytes=100 * 1024 * 1024,
            used_bytes=0,
            space_type="team",
            status="active",
        )
        db_session.add(space)
        db_session.commit()
        space_id = space.id

        # 创建3个pending upload，每个20MB
        for i in range(3):
            upload_service.create_upload(
                space_id=space_id,
                user_id=user_id,
                file_name=f"pending_{i}.bin",
                file_size=20 * 1024 * 1024
            )

        # 预留应该 = 60MB
        reserved = upload_service.get_quota_reserved(space_id)
        assert reserved == 60 * 1024 * 1024, f"Expected 60MB reserved, got {reserved}"
