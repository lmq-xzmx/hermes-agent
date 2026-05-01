"""
FileLockService - 文件锁业务逻辑

防止并发编辑冲突，支持锁获取、释放、延期和自动清理。
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from ..engine.models import FileLock, Space, User
from ..engine.storage import StorageEngine


class FileLockError(Exception):
    """文件锁相关错误"""
    pass


class LockNotFound(FileLockError):
    """锁不存在"""
    pass


class LockExpired(FileLockError):
    """锁已过期"""
    pass


class LockHeldByOther(FileLockError):
    """锁被他人持有"""
    def __init__(self, lock: FileLock):
        self.lock = lock
        super().__init__(f"文件已被 {lock.user.username if lock.user else '其他人'} 锁定")


class FileLockService:
    """
    文件锁业务逻辑。

    锁机制：
    - 用户获取编辑锁后，其他用户无法在同一文件上获取编辑锁
    - 锁默认 30 分钟超时，可手动延期
    - 后台线程定期清理过期锁
    - 文件所有者可以强制释放他人的锁
    """

    def __init__(self, db_factory):
        self._db = db_factory
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()

    # -------------------------------------------------------------------------
    # Lock Operations
    # -------------------------------------------------------------------------

    def acquire_lock(
        self,
        space_id: str,
        path: str,
        user_id: str,
        lock_type: str = "edit",
        timeout_minutes: int = 30,
    ) -> Dict[str, Any]:
        """
        获取文件编辑锁。

        如果文件已有有效锁且属于当前用户，自动续期。
        如果文件被他人锁定，抛出 LockHeldByOther。
        """
        session = self._db()
        try:
            # 检查是否有现有锁
            existing = (
                session.query(FileLock)
                .filter(
                    FileLock.space_id == space_id,
                    FileLock.path == path,
                    FileLock.is_active == True,
                )
                .first()
            )

            if existing:
                if existing.is_expired():
                    # 过期锁，删除后创建新的
                    session.delete(existing)
                    session.commit()
                elif existing.locked_by == user_id:
                    # 自己的锁，续期
                    existing.expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
                    session.commit()
                    return existing.to_dict()
                else:
                    # 被他人锁定
                    raise LockHeldByOther(existing)

            # 创建新锁
            expires_at = datetime.utcnow() + timedelta(minutes=timeout_minutes)
            lock = FileLock(
                space_id=space_id,
                path=path,
                locked_by=user_id,
                expires_at=expires_at,
                lock_type=lock_type,
                is_active=True,
            )
            session.add(lock)
            session.commit()
            return lock.to_dict()
        finally:
            session.close()

    def release_lock(self, lock_id: str, user_id: str) -> bool:
        """
        释放文件锁。只有锁持有者或 space owner 可以释放。
        """
        session = self._db()
        try:
            lock = session.query(FileLock).filter(FileLock.id == lock_id).first()
            if not lock:
                raise LockNotFound()

            # 检查权限：持有者或 space owner
            space = session.query(Space).filter(Space.id == lock.space_id).first()
            is_owner = space and space.owner_id == user_id

            if lock.locked_by != user_id and not is_owner:
                raise FileLockError("无权释放他人的锁")

            lock.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    def check_lock(self, space_id: str, path: str) -> Optional[Dict[str, Any]]:
        """
        检查文件是否有有效锁。返回锁信息或 None。
        """
        session = self._db()
        try:
            lock = (
                session.query(FileLock)
                .filter(
                    FileLock.space_id == space_id,
                    FileLock.path == path,
                    FileLock.is_active == True,
                )
                .first()
            )
            if lock and not lock.is_expired():
                return lock.to_dict()
            elif lock and lock.is_expired():
                # 清理过期锁
                lock.is_active = False
                session.commit()
            return None
        finally:
            session.close()

    def extend_lock(self, lock_id: str, user_id: str, minutes: int = 30) -> bool:
        """延长锁的过期时间。只有锁持有者可以延期。"""
        session = self._db()
        try:
            lock = session.query(FileLock).filter(FileLock.id == lock_id).first()
            if not lock:
                raise LockNotFound()
            if lock.locked_by != user_id:
                raise FileLockError("只能延期自己的锁")
            if not lock.is_active or lock.is_expired():
                raise LockExpired()

            lock.expires_at = datetime.utcnow() + timedelta(minutes=minutes)
            session.commit()
            return True
        finally:
            session.close()

    def get_user_locks(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户持有的所有有效锁。"""
        session = self._db()
        try:
            locks = (
                session.query(FileLock)
                .filter(
                    FileLock.locked_by == user_id,
                    FileLock.is_active == True,
                )
                .all()
            )
            return [l.to_dict() for l in locks if not l.is_expired()]
        finally:
            session.close()

    def get_space_locks(self, space_id: str) -> List[Dict[str, Any]]:
        """获取空间内所有有效锁。"""
        session = self._db()
        try:
            locks = (
                session.query(FileLock)
                .filter(
                    FileLock.space_id == space_id,
                    FileLock.is_active == True,
                )
                .all()
            )
            return [l.to_dict() for l in locks if not l.is_expired()]
        finally:
            session.close()

    def cleanup_expired_locks(self) -> int:
        """清理所有过期锁。返回清理数量。"""
        session = self._db()
        try:
            now = datetime.utcnow()
            expired = (
                session.query(FileLock)
                .filter(
                    FileLock.is_active == True,
                    FileLock.expires_at < now,
                )
                .all()
            )
            count = len(expired)
            for lock in expired:
                lock.is_active = False
            session.commit()
            return count
        finally:
            session.close()

    def force_release_lock(self, lock_id: str, requesting_user_id: str) -> bool:
        """强制释放锁（space owner 或管理员）。"""
        session = self._db()
        try:
            lock = session.query(FileLock).filter(FileLock.id == lock_id).first()
            if not lock:
                raise LockNotFound()

            space = session.query(Space).filter(Space.id == lock.space_id).first()
            if not space:
                raise FileLockError("Space 不存在")

            # 检查是否是 owner 或 admin
            is_admin = self._is_admin(requesting_user_id, session)
            is_space_owner = space.owner_id == requesting_user_id

            if not is_admin and not is_space_owner:
                raise FileLockError("只有 space owner 或 admin 可以强制解锁")

            lock.is_active = False
            session.commit()
            return True
        finally:
            session.close()

    def _is_admin(self, user_id: str, session) -> bool:
        """检查用户是否为管理员。"""
        user = session.query(User).filter(User.id == user_id).first()
        return user and user.role and user.role.name == "admin"

    # -------------------------------------------------------------------------
    # Cleanup Background Thread
    # -------------------------------------------------------------------------

    def start_cleanup_thread(self, interval_seconds: int = 300) -> None:
        """启动后台清理线程（每 5 分钟检查一次）。"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return

        self._stop_cleanup.clear()

        def cleanup_loop():
            while not self._stop_cleanup.wait(interval_seconds):
                try:
                    count = self.cleanup_expired_locks()
                    if count > 0:
                        print(f"[FileLockService] Cleaned up {count} expired locks")
                except Exception as e:
                    print(f"[FileLockService] Cleanup error: {e}")

        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def stop_cleanup_thread(self) -> None:
        """停止后台清理线程。"""
        self._stop_cleanup.set()
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)