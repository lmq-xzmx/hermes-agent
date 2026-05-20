"""
TrashService - Business logic for soft-delete / trash / recovery mechanism.

Handles:
- Moving files to trash instead of physical deletion
- Listing trash contents for a space
- Restoring files from trash
- Permanently deleting files from trash
- Emptying trash (purging expired items)

=== Lifecycle Rules ===
| 操作 | 系统角色 | 空间角色 | 权限说明 |
|------|---------|---------|---------|
| 查看回收站 | admin/editor/viewer/guest | owner/member/viewer | 必须为space成员 |
| 恢复文件 | admin/editor | owner/member | 必须为space成员，admin可恢复任意文件 |
| 永久删除 | admin | owner | admin可永久删除任意文件 |
| 清空回收站 | admin | owner | admin可清空任意空间回收站 |

=== Trash Permissions ===
- space:read    - 查看回收站列表
- space:write   - 恢复文件（需要原始路径写权限）
- space:delete  - 永久删除文件
- space:manage  - 清空回收站
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..engine.models import DeletedFile, Space, SpaceMember, User, Base, AuditAction
from ..engine.storage import StorageEngine
from ..engine.audit import AuditLogger
from .space_service import SpaceNotFound

logger = logging.getLogger(__name__)

# =============================================================================
# Domain Errors
# =============================================================================

class TrashItemNotFound(Exception):
    """Trash item does not exist."""
    pass


class TrashAccessDenied(Exception):
    """User does not have access to this trash item."""
    pass


class TrashExpired(Exception):
    """Trash item has expired and cannot be restored."""
    pass


class TrashPermissionDenied(Exception):
    """User does not have permission for this trash operation."""
    pass


# =============================================================================
# Permission Constants
# =============================================================================

class TrashPermission:
    """Trash operation permissions."""
    READ = "trash:read"      # View trash list
    RESTORE = "trash:restore"  # Restore files from trash
    DELETE = "trash:delete"    # Permanent delete
    PURGE = "trash:purge"      # Empty trash (admin only)


# =============================================================================
# TrashService
# =============================================================================

class TrashService:
    """Business logic for trash/recovery operations."""

    # Default retention period in days
    DEFAULT_RETENTION_DAYS = 30

    def __init__(
        self,
        db_factory: Any,
        storage: StorageEngine,
        default_pool_storage_path: str,
        default_pool_id: Optional[str] = None,
    ):
        self._db_factory = db_factory
        self._storage = storage
        self._default_pool_storage_path = default_pool_storage_path
        self._default_pool_id = default_pool_id or "default"

    def _get_session(self):
        return self._db_factory()

    def _resolve_storage_for_space(self, space_id: str) -> StorageEngine:
        """Return storage engine for the given space."""
        return self._storage

    def _check_space_access(self, session: Any, space_id: str, user_id: str) -> tuple[bool, str, Optional[str]]:
        """
        Check if user has access to the space and return their role.

        Returns: (has_access, space_role, error_message)
        - has_access: Whether user is a member of the space
        - space_role: owner's member | viewer | None
        - error_message: Error description if access denied
        """
        # Check if user is admin (system-level)
        user = session.query(User).filter(User.id == user_id).first()
        if user and user.role and user.role.name == "admin":
            return True, "admin", None

        # Check space membership
        membership = session.query(SpaceMember).filter(
            SpaceMember.space_id == space_id,
            SpaceMember.user_id == user_id,
            SpaceMember.status == "active"
        ).first()

        if not membership:
            return False, None, "您不是该空间的成员"

        return True, membership.role, None

    def _require_trash_permission(
        self,
        session: Any,
        space_id: str,
        user_id: str,
        permission: str,
        deleted_file: Optional[DeletedFile] = None,
    ) -> None:
        """
        Check if user has the required trash permission.

        Permission rules:
        - admin: Full access to all operations
        - owner: Can restore, delete, purge
        - member: Can restore their own files, cannot purge
        - viewer: Cannot perform any write operations on trash

        Raises:
            TrashPermissionDenied: If user lacks permission
        """
        has_access, space_role, error = self._check_space_access(session, space_id, user_id)
        if not has_access:
            raise TrashPermissionDenied(error)

        # System admin has full access
        if space_role == "admin":
            return

        # Check permission based on operation
        if permission == TrashPermission.READ:
            # All space members can view trash
            if space_role in ("owner", "member", "viewer"):
                return
            raise TrashPermissionDenied("您没有查看回收站的权限")

        elif permission == TrashPermission.RESTORE:
            # Owner can restore any file
            # Member can only restore their own files
            if space_role == "owner":
                return
            if space_role == "member" and deleted_file and deleted_file.deleted_by == user_id:
                return
            if space_role == "member" and deleted_file:
                raise TrashPermissionDenied("您只能恢复自己删除的文件")
            raise TrashPermissionDenied("您没有恢复文件的权限")

        elif permission in (TrashPermission.DELETE, TrashPermission.PURGE):
            # Only owner can permanent delete or empty trash
            if space_role == "owner":
                return
            if space_role == "member":
                raise TrashPermissionDenied("成员没有永久删除权限，需要空间所有者操作")
            raise TrashPermissionDenied("您没有永久删除的权限")

        raise TrashPermissionDenied(f"未知权限: {permission}")

    # -------------------------------------------------------------------------
    # Trash Operations
    # -------------------------------------------------------------------------

    def move_to_trash(
        self,
        space_id: str,
        user_path: str,
        user_id: str,
        is_directory: bool,
        file_size: int,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ) -> DeletedFile:
        """
        Move a file/directory to trash instead of physically deleting it.
        Creates a DeletedFile record and returns it.
        """
        session = self._get_session()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"Space {space_id} not found")

            # Build effective path
            effective_path = f"spaces/{space_id}/shared/{user_path.lstrip('/')}"
            # Extract just the filename for trash path
            file_name = user_path.lstrip('/').split('/')[-1]
            trash_path = f"spaces/{space_id}/_trash/{file_name}"

            # Ensure _trash directory exists
            trash_dir = f"spaces/{space_id}/_trash/shared"
            try:
                self._storage.create_directory(trash_dir)
            except Exception:
                pass  # Directory may already exist

            # Move file to trash location - try move_file first, then fallback to copy+delete
            move_succeeded = False
            try:
                self._storage.move_file(effective_path, trash_path, overwrite=True)
                move_succeeded = True
            except Exception:
                # Fallback: copy file to trash, then delete original
                try:
                    import shutil
                    src = self._storage._resolve_user_path(effective_path)
                    dst = self._storage._resolve_user_path(trash_path)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    if src.is_file():
                        shutil.copy2(str(src), str(dst))
                    else:
                        shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
                    # Now delete original
                    self._storage.delete_path(effective_path, recursive=is_directory)
                    move_succeeded = True
                except Exception as e:
                    import logging
                    logging.warning(f"Failed to move to trash: {e}")
                    move_succeeded = False

            # Only create DeletedFile record if move actually succeeded
            if not move_succeeded:
                raise FileNotFoundError(f"无法移动到回收站: {user_path}")

            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(days=retention_days)

            # Create deleted file record
            deleted_file = DeletedFile(
                space_id=space_id,
                original_path=user_path,
                name=user_path.split("/")[-1] if "/" in user_path else user_path,
                is_directory=is_directory,
                file_size=file_size,
                deleted_by=user_id,
                deleted_at=datetime.utcnow(),
                expires_at=expires_at,
            )
            session.add(deleted_file)
            session.commit()

            # Check and trigger quota-based cleanup if needed
            try:
                cleanup_result = self.check_and_cleanup_quota(space_id)
                if cleanup_result and cleanup_result.get("cleaned", 0) > 0:
                    logger.info(f"Auto cleanup triggered after move_to_trash: {cleanup_result}")
            except Exception as e:
                logger.warning(f"Quota cleanup check failed: {e}")

            return deleted_file
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def list_trash(
        self,
        space_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List items in trash for a space."""
        session = self._get_session()
        try:
            # Check permission
            self._require_trash_permission(
                session, space_id, user_id, TrashPermission.READ
            )

            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"Space {space_id} not found")

            # Query deleted files
            query = session.query(DeletedFile).filter(
                DeletedFile.space_id == space_id
            ).order_by(DeletedFile.deleted_at.desc())

            total = query.count()
            items = query.offset(offset).limit(limit).all()

            return {
                "space_id": space_id,
                "space_name": space.name,
                "total": total,
                "items": [item.to_dict() for item in items],
            }
        finally:
            session.close()

    def restore_from_trash(
        self,
        space_id: str,
        deleted_file_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Restore a file from trash to its original location.

        Permission rules:
        - admin: Can restore any file
        - owner: Can restore any file in their space
        - member: Can only restore files they deleted themselves
        - viewer: Cannot restore files
        """
        session = self._get_session()
        try:
            # Check if item exists
            deleted_file = session.query(DeletedFile).filter(
                DeletedFile.id == deleted_file_id,
                DeletedFile.space_id == space_id,
            ).first()

            if not deleted_file:
                raise TrashItemNotFound(f"Trash item {deleted_file_id} not found")

            if datetime.utcnow() > deleted_file.expires_at:
                raise TrashExpired("This trash item has expired and cannot be restored")

            # Check permission
            self._require_trash_permission(
                session, space_id, user_id, TrashPermission.RESTORE, deleted_file
            )

            logger.info(
                f"Trash restore: user={user_id} file={deleted_file.original_path} "
                f"deleted_by={deleted_file.deleted_by}"
            )

            # Build paths
            effective_path = f"spaces/{space_id}/shared/{deleted_file.original_path.lstrip('/')}"
            trash_path = f"spaces/{space_id}/_trash/shared/{deleted_file.original_path.lstrip('/')}"

            # Restore file from trash
            try:
                self._storage.move_file(trash_path, effective_path, overwrite=True)
            except Exception as e:
                logger.warning(f"Failed to move file during restore: {e}")
                pass  # File may not be in trash location

            # Remove deleted file record
            session.delete(deleted_file)
            session.commit()

            # Audit log
            self._log_audit(
                session=session,
                action=AuditAction.TRASH_RESTORE,
                user_id=user_id,
                space_id=space_id,
                result="success",
                details={
                    "file_name": deleted_file.name,
                    "original_path": deleted_file.original_path,
                    "file_size": deleted_file.file_size,
                }
            )

            return {
                "message": f"Restored: {deleted_file.original_path}",
                "original_path": deleted_file.original_path,
            }
        except (TrashItemNotFound, TrashExpired, TrashPermissionDenied) as exc:
            self._log_audit(
                session=self._get_session(),
                action=AuditAction.TRASH_RESTORE,
                user_id=user_id,
                space_id=space_id,
                result="denied",
                details={"error": str(exc)}
            )
            raise
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def permanent_delete(
        self,
        space_id: str,
        deleted_file_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Permanently delete a file from trash (cannot be restored).

        Permission rules:
        - admin: Can permanently delete any file
        - owner: Can permanently delete any file in their space
        - member: Cannot permanent delete
        - viewer: Cannot permanent delete
        """
        session = self._get_session()
        try:
            # Check if item exists
            deleted_file = session.query(DeletedFile).filter(
                DeletedFile.id == deleted_file_id,
                DeletedFile.space_id == space_id,
            ).first()

            if not deleted_file:
                raise TrashItemNotFound(f"Trash item {deleted_file_id} not found")

            # Check permission
            self._require_trash_permission(
                session, space_id, user_id, TrashPermission.DELETE, deleted_file
            )

            logger.info(
                f"Trash permanent delete: user={user_id} file={deleted_file.original_path}"
            )

            # Build trash path and physically delete
            trash_path = f"spaces/{space_id}/_trash/shared/{deleted_file.original_path.lstrip('/')}"
            try:
                self._storage.delete_path(trash_path, recursive=True)
            except Exception:
                pass  # File may already be gone

            # Remove deleted file record
            file_name = deleted_file.name
            file_size = deleted_file.file_size
            original_path = deleted_file.original_path
            session.delete(deleted_file)
            session.commit()

            # Audit log
            self._log_audit(
                session=session,
                action=AuditAction.TRASH_DELETE,
                user_id=user_id,
                space_id=space_id,
                result="success",
                details={
                    "file_name": file_name,
                    "original_path": original_path,
                    "file_size": file_size,
                }
            )

            return {
                "message": f"Permanently deleted: {original_path}",
            }
        except (TrashItemNotFound, TrashPermissionDenied) as exc:
            self._log_audit(
                session=self._get_session(),
                action=AuditAction.TRASH_DELETE,
                user_id=user_id,
                space_id=space_id,
                result="denied",
                details={"error": str(exc)}
            )
            raise
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def empty_trash(
        self,
        space_id: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """Empty all items in trash for a space.

        Permission rules:
        - admin: Can empty any space's trash
        - owner: Can empty their own space's trash
        - member: Cannot empty trash
        - viewer: Cannot empty trash
        """
        session = self._get_session()
        try:
            # Check permission
            self._require_trash_permission(
                session, space_id, user_id, TrashPermission.PURGE
            )

            # Query all deleted files for this space
            deleted_files = session.query(DeletedFile).filter(
                DeletedFile.space_id == space_id
            ).all()

            count = len(deleted_files)

            logger.info(f"Trash empty: user={user_id} space={space_id} count={count}")

            # Physically delete each file from trash
            for df in deleted_files:
                trash_path = f"spaces/{space_id}/_trash/shared/{df.original_path.lstrip('/')}"
                try:
                    self._storage.delete_path(trash_path, recursive=True)
                except Exception:
                    pass

            # Remove all deleted file records
            session.query(DeletedFile).filter(
                DeletedFile.space_id == space_id
            ).delete()

            session.commit()

            # Audit log
            self._log_audit(
                session=session,
                action=AuditAction.TRASH_EMPTY,
                user_id=user_id,
                space_id=space_id,
                result="success",
                details={"count": count}
            )

            return {
                "message": f"Emptied trash: {count} items permanently deleted",
                "count": count,
            }
        except TrashPermissionDenied as exc:
            self._log_audit(
                session=self._get_session(),
                action=AuditAction.TRASH_EMPTY,
                user_id=user_id,
                space_id=space_id,
                result="denied",
                details={"error": str(exc)}
            )
            raise
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    def purge_expired(self, space_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Purge all expired trash items.
        If space_id is provided, only purge that space, otherwise purge all spaces.
        """
        session = self._get_session()
        try:
            now = datetime.utcnow()

            # Build query for expired items
            query = session.query(DeletedFile).filter(
                DeletedFile.expires_at < now
            )
            if space_id:
                query = query.filter(DeletedFile.space_id == space_id)

            expired_items = query.all()
            count = len(expired_items)

            # Physically delete each expired file
            for df in expired_items:
                trash_path = f"spaces/{df.space_id}/_trash/shared/{df.original_path.lstrip('/')}"
                try:
                    self._storage.delete_path(trash_path, recursive=True)
                except Exception:
                    pass

            # Remove expired records
            query.delete()
            session.commit()

            return {
                "message": f"Purged {count} expired trash items",
                "count": count,
            }
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Quota-based Auto Cleanup
    # -------------------------------------------------------------------------

    # Threshold for trash size as percentage of space quota (50%)
    TRASH_QUOTA_THRESHOLD = 0.5

    def _get_space_quota(self, session: Any, space_id: str) -> tuple[int, int]:
        """
        Get space quota info.

        Returns: (quota_bytes, used_bytes)
        - quota_bytes: Total quota for the space
        - used_bytes: Current usage in bytes
        """
        space = session.query(Space).filter(Space.id == space_id).first()
        if not space:
            return 0, 0

        # Get space's quota limit (from space or pool default)
        quota_bytes = space.quota_bytes or (1024 * 1024 * 1024)  # Default 1GB

        # Calculate trash size
        trash_size = session.query(DeletedFile).filter(
            DeletedFile.space_id == space_id
        ).with_entities(
            session.query(DeletedFile.file_size).label('size')
        ).all()
        used_bytes = sum(t.file_size or 0 for t in trash_size)

        return quota_bytes, used_bytes

    def _auto_cleanup_for_space(self, space_id: str, reason: str) -> Dict[str, Any]:
        """
        Auto cleanup oldest expired items in trash when quota threshold exceeded.

        This is called when trash size exceeds TRASH_QUOTA_THRESHOLD of space quota.
        It deletes the oldest expired items until trash is below threshold.
        """
        session = self._get_session()
        try:
            quota_bytes, trash_size = self._get_space_quota(session, space_id)
            target_size = int(quota_bytes * self.TRASH_QUOTA_THRESHOLD)

            if trash_size <= target_size:
                return {"message": "Trash size below threshold", "cleaned": 0}

            # Get oldest expired items first
            expired_items = session.query(DeletedFile).filter(
                DeletedFile.space_id == space_id,
                DeletedFile.expires_at < datetime.utcnow()
            ).order_by(DeletedFile.deleted_at.asc()).all()

            cleaned_count = 0
            freed_bytes = 0

            for item in expired_items:
                if trash_size - freed_bytes <= target_size:
                    break

                # Physically delete
                trash_path = f"spaces/{space_id}/_trash/shared/{item.original_path.lstrip('/')}"
                try:
                    self._storage.delete_path(trash_path, recursive=True)
                except Exception:
                    pass

                freed_bytes += item.file_size or 0
                cleaned_count += 1

                # Remove record
                session.delete(item)

            session.commit()

            logger.info(
                f"Auto cleanup for space {space_id}: reason={reason}, "
                f"cleaned={cleaned_count} items, freed={freed_bytes} bytes"
            )

            return {
                "message": f"Auto cleanup: {cleaned_count} items deleted",
                "cleaned": cleaned_count,
                "freed_bytes": freed_bytes,
                "reason": reason,
            }
        except Exception as e:
            session.rollback()
            logger.error(f"Auto cleanup failed: {e}")
            return {"message": f"Auto cleanup failed: {e}", "cleaned": 0}
        finally:
            session.close()

    def check_and_cleanup_quota(self, space_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if trash quota is exceeded and trigger cleanup if needed.

        Call this after move_to_trash() to enforce quota limits.
        """
        session = self._get_session()
        try:
            quota_bytes, used_bytes = self._get_space_quota(session, space_id)
            threshold = int(quota_bytes * self.TRASH_QUOTA_THRESHOLD)

            if used_bytes > threshold:
                logger.warning(
                    f"Trash quota exceeded for space {space_id}: "
                    f"used={used_bytes}, threshold={threshold}"
                )
                return self._auto_cleanup_for_space(space_id, "quota_exceeded")
            return None
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Audit Logging
    # -------------------------------------------------------------------------

    def _log_audit(
        self,
        session: Any,
        action: AuditAction,
        user_id: str,
        space_id: str,
        result: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log an audit entry for trash operations."""
        try:
            audit_logger = AuditLogger(session)
            # Get user object for audit log
            user = session.query(User).filter(User.id == user_id).first()
            audit_logger.log(
                action=action,
                result=result,
                user=user,
                path=f"/spaces/{space_id}/trash",
                extra=details,
            )
        except Exception as e:
            logger.warning(f"Failed to write audit log: {e}")

    # -------------------------------------------------------------------------
    # Scheduled Tasks
    # -------------------------------------------------------------------------

    _scheduler_thread: Optional[threading.Thread] = None
    _shutdown_event: Optional[threading.Event] = None

    @classmethod
    def start_scheduler(cls, db_factory: Any, storage: StorageEngine,
                        interval_hours: int = 24) -> None:
        """
        Start background scheduler for purge_expired.

        Runs purge_expired every `interval_hours` hours.
        """
        if cls._scheduler_thread and cls._scheduler_thread.is_alive():
            logger.warning("Scheduler already running")
            return

        cls._shutdown_event = threading.Event()
        cls._scheduler_thread = threading.Thread(
            target=cls._scheduler_loop,
            args=(db_factory, storage, interval_hours),
            daemon=True,
            name="TrashPurgeScheduler"
        )
        cls._scheduler_thread.start()
        logger.info(f"Trash purge scheduler started (interval={interval_hours}h)")

    @classmethod
    def stop_scheduler(cls) -> None:
        """Stop the background scheduler."""
        if cls._shutdown_event:
            cls._shutdown_event.set()
        if cls._scheduler_thread:
            cls._scheduler_thread.join(timeout=5)
            cls._scheduler_thread = None
        logger.info("Trash purge scheduler stopped")

    @classmethod
    def _scheduler_loop(cls, db_factory: Any, storage: StorageEngine,
                        interval_hours: int) -> None:
        """Background loop that periodically purges expired items."""
        import time
        interval_seconds = interval_hours * 3600

        while not cls._shutdown_event.wait(interval_seconds):
            try:
                logger.info("Running scheduled purge_expired...")
                svc = cls(db_factory, storage, "/tmp")
                result = svc.purge_expired()
                logger.info(f"Scheduled purge completed: {result}")
            except Exception as e:
                logger.error(f"Scheduled purge failed: {e}")
