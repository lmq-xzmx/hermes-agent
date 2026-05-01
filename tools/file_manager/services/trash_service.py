"""
TrashService - Business logic for soft-delete / trash / recovery mechanism.

Handles:
- Moving files to trash instead of physical deletion
- Listing trash contents for a space
- Restoring files from trash
- Permanently deleting files from trash
- Emptying trash (purging expired items)
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from ..engine.models import DeletedFile, Space, User, Base
from ..engine.storage import StorageEngine
from .space_service import SpaceNotFound


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
        """Restore a file from trash to its original location."""
        session = self._get_session()
        try:
            deleted_file = session.query(DeletedFile).filter(
                DeletedFile.id == deleted_file_id,
                DeletedFile.space_id == space_id,
            ).first()

            if not deleted_file:
                raise TrashItemNotFound(f"Trash item {deleted_file_id} not found")

            if datetime.utcnow() > deleted_file.expires_at:
                raise TrashExpired("This trash item has expired and cannot be restored")

            # Build paths
            effective_path = f"spaces/{space_id}/shared/{deleted_file.original_path.lstrip('/')}"
            trash_path = f"spaces/{space_id}/_trash/shared/{deleted_file.original_path.lstrip('/')}"

            # Restore file from trash
            try:
                self._storage.move_file(trash_path, effective_path, overwrite=True)
            except Exception:
                pass  # File may not be in trash location

            # Remove deleted file record
            session.delete(deleted_file)
            session.commit()

            return {
                "message": f"Restored: {deleted_file.original_path}",
                "original_path": deleted_file.original_path,
            }
        except TrashItemNotFound:
            raise
        except TrashExpired:
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
        """Permanently delete a file from trash (cannot be restored)."""
        session = self._get_session()
        try:
            deleted_file = session.query(DeletedFile).filter(
                DeletedFile.id == deleted_file_id,
                DeletedFile.space_id == space_id,
            ).first()

            if not deleted_file:
                raise TrashItemNotFound(f"Trash item {deleted_file_id} not found")

            # Build trash path and physically delete
            trash_path = f"spaces/{space_id}/_trash/shared/{deleted_file.original_path.lstrip('/')}"
            try:
                self._storage.delete_path(trash_path, recursive=True)
            except Exception:
                pass  # File may already be gone

            # Remove deleted file record
            session.delete(deleted_file)
            session.commit()

            return {
                "message": f"Permanently deleted: {deleted_file.original_path}",
            }
        except TrashItemNotFound:
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
        """Empty all items in trash for a space."""
        session = self._get_session()
        try:
            # Query all deleted files for this space
            deleted_files = session.query(DeletedFile).filter(
                DeletedFile.space_id == space_id
            ).all()

            count = len(deleted_files)

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

            return {
                "message": f"Emptied trash: {count} items permanently deleted",
                "count": count,
            }
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
