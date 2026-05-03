"""
File Upload Service - 管理文件上传的生命周期

负责：
- 上传开始时创建 FileUpload 记录
- 上传进行中更新进度
- 上传完成/失败时更新状态
"""

from datetime import datetime
from typing import Optional

from .models import FileUpload, Base
from .lifecycle_engine import LifecycleEngine


class FileUploadService:
    """文件上传跟踪服务"""

    def __init__(self, db_factory):
        self._db = db_factory
        self._lifecycle = LifecycleEngine()

    def create_upload(self, space_id: str, user_id: str, file_name: str, file_size: int) -> FileUpload:
        """开始上传时调用，创建跟踪记录"""
        session = self._db()
        try:
            upload = FileUpload(
                space_id=space_id,
                user_id=user_id,
                file_name=file_name,
                file_size=file_size,
                status="uploading"
            )
            session.add(upload)
            session.commit()
            return upload
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