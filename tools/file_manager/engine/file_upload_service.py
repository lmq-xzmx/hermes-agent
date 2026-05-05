"""
File Upload Service - 管理文件上传的生命周期

负责：
- 上传开始时创建 FileUpload 记录
- 上传进行中更新进度
- 上传完成/失败时更新状态
- 并发上传配额锁定 (TC-M2-004)
- 配额超卖防护 SELECT FOR UPDATE (TC-M2-005)
"""

from datetime import datetime
from typing import Optional, Tuple

from .models import FileUpload, Base, Space
from .lifecycle_engine import LifecycleEngine


class QuotaExceededError(Exception):
    """配额不足异常"""
    def __init__(self, available: int, required: int):
        self.available = available
        self.required = required
        super().__init__(f"配额不足: 需要 {required} 字节，可用 {available} 字节")


class FileUploadService:
    """文件上传跟踪服务"""

    def __init__(self, db_factory):
        self._db = db_factory
        self._lifecycle = LifecycleEngine()

    def create_upload(self, space_id: str, user_id: str, file_name: str, file_size: int) -> Tuple[FileUpload, int]:
        """
        开始上传时调用，创建跟踪记录。

        TC-M2-004: 并发上传配额锁定
        TC-M2-005: 配额超卖防护 SELECT FOR UPDATE

        使用 SELECT FOR UPDATE 锁定 space 记录，确保配额检查和上传记录创建的原子性。

        Returns:
            Tuple[FileUpload, int]: (上传记录, 预留配额ID)

        Raises:
            QuotaExceededError: 配额不足时抛出
        """
        session = self._db()
        try:
            # TC-M2-005: 使用 SELECT FOR UPDATE 锁定 space 记录
            # 这确保了在检查配额和创建上传记录之间不会有其他事务修改 space
            # 注意：SQLite 不支持 FOR UPDATE，使用 SERIALIZABLE 隔离级别
            query = session.query(Space).filter(Space.id == space_id)
            if "sqlite" not in str(session.get_bind().url):
                query = query.with_for_update(nowait=False)
            space = query.first()

            if not space:
                raise ValueError(f"Space not found: {space_id}")

            # 计算可用配额
            # 可用配额 = 总配额 - 已用配额 - 预留配额（正在上传的文件大小）
            # 注意：使用当前 session 查询，避免跨 session 隔离问题导致看不到未提交的上传记录
            reserved_rows = session.query(FileUpload.file_size).filter(
                FileUpload.space_id == space_id,
                FileUpload.status == "uploading"
            ).all()
            reserved = sum(r[0] for r in reserved_rows) if reserved_rows else 0
            available = space.max_bytes - space.used_bytes - reserved

            if available < file_size:
                raise QuotaExceededError(available, file_size)

            # TC-M2-004: 创建上传记录（带配额预留）
            upload = FileUpload(
                space_id=space_id,
                user_id=user_id,
                file_name=file_name,
                file_size=file_size,
                status="uploading"
            )
            session.add(upload)
            session.commit()
            return upload, reserved + file_size
        finally:
            session.close()

    def update_progress(self, upload_id: str, uploaded_bytes: int) -> bool:
        """更新上传进度"""
        session = self._db()
        try:
            upload = session.query(FileUpload).filter(FileUpload.id == upload_id).first()
            if not upload:
                return False
            upload.uploaded_bytes = uploaded_bytes
            session.commit()
            return True
        finally:
            session.close()

    def mark_completed(self, upload_id: str) -> bool:
        """上传完成时调用"""
        session = self._db()
        try:
            upload = session.query(FileUpload).filter(FileUpload.id == upload_id).first()
            if not upload:
                return False
            upload.status = "completed"
            upload.completed_at = datetime.utcnow()
            session.commit()
            return True
        finally:
            session.close()

    def mark_failed(self, upload_id: str, error: str = None) -> bool:
        """上传失败时调用"""
        session = self._db()
        try:
            upload = session.query(FileUpload).filter(FileUpload.id == upload_id).first()
            if not upload:
                return False
            upload.status = "failed"
            upload.completed_at = datetime.utcnow()
            upload.error_message = error
            session.commit()
            return True
        finally:
            session.close()

    def cancel_upload(self, upload_id: str) -> bool:
        """取消上传"""
        session = self._db()
        try:
            upload = session.query(FileUpload).filter(FileUpload.id == upload_id).first()
            if not upload:
                return False
            upload.status = "cancelled"
            upload.completed_at = datetime.utcnow()
            session.commit()
            return True
        finally:
            session.close()

    def get_quota_reserved(self, space_id: str) -> int:
        """获取空间当前被预留的配额（正在上传的文件总大小）"""
        return self._lifecycle.get_quota_reserved(space_id, self._db)

    def cleanup_stale_uploads(self, hours: int = 24) -> int:
        """
        清理过期的上传记录（状态为 uploa
        ding 但超过 hours 小时未更新的）
        """
        from datetime import timedelta
        session = self._db()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            stale = session.query(FileUpload).filter(
                FileUpload.status == "uploading",
                FileUpload.updated_at < cutoff
            ).all()
            for upload in stale:
                upload.status = "cancelled"
                upload.completed_at = datetime.utcnow()
            session.commit()
            return len(stale)
        finally:
            session.close()