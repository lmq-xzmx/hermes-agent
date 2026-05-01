"""
FileService - Pure business logic for file operations.

No FastAPI, no ORM. Uses PermissionChecker (primitives) and StorageEngine.
Emits events to EventBus for audit logging.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

from .permission_checker import PermissionChecker, PermissionContext, Operation, PermissionDecision
from .event_bus import EventBus, EventType, Event, get_event_bus
from ..api.webhook import get_publisher, EventType as WebhookEventType, publish_file_event
from ..api.dto import (
    FileItemDTO, FileListResponseDTO, FileContentResponseDTO,
    FileStatResponseDTO, FileWriteRequestDTO, FileReadRequestDTO,
    FileDeleteRequestDTO, MkDirRequestDTO, FileCopyRequestDTO, FileMoveRequestDTO,
)
from ..engine.storage import StorageEngine, FileNotFoundError, FileExistsError, DirectoryNotEmptyError


# =============================================================================
# Service Errors (pure domain errors, not HTTP)
# =============================================================================

class FileAccessDenied(Exception):
    """Permission denied."""
    def __init__(self, reason: str, decision: Optional[PermissionDecision] = None):
        self.reason = reason
        self.decision = decision
        super().__init__(reason)


class FileNotFound(Exception):
    """File or directory not found."""
    pass


class FileAlreadyExists(Exception):
    """File or directory already exists."""
    pass


class DirectoryNotEmpty(Exception):
    """Directory not empty (requires recursive)."""
    pass


class FileLocked(Exception):
    """File is locked by another user."""
    def __init__(self, path: str, locked_by: str, expires_at: str):
        self.path = path
        self.locked_by = locked_by
        self.expires_at = expires_at
        super().__init__(f"文件已被 {locked_by} 锁定，请在 {expires_at} 后重试")


# =============================================================================
# FileService
# =============================================================================

class FileService:
    """
    File operation business logic. Stateless.

    Flow:
      API route (thin HTTP) → FileService (pure logic) → StorageEngine (I/O)

    FileService:
      - Converts AuthenticatedUser → PermissionContext (primitives)
      - Calls PermissionChecker (pure logic) for auth decisions
      - Calls StorageEngine for actual filesystem operations
      - Emits events to EventBus for audit/analytics
    """

    def __init__(
        self,
        storage: StorageEngine,
        permission_checker: PermissionChecker,
        event_bus: Optional[EventBus] = None,
        db_factory: Optional[Any] = None,
    ):
        self.storage = storage  # Primary (default pool) storage engine
        self._checker = permission_checker
        self._event_bus = event_bus or get_event_bus()
        self._db_factory = db_factory
        # Multi-pool registry: pool_id → StorageEngine
        # File operations are routed by user_ctx.active_space_id (spaces/{space_id}/shared/)
        self._pool_storages: Dict[str, StorageEngine] = {}
        # Default pool id
        self._default_pool_id: Optional[str] = None

    def register_pool(self, pool_id: str, storage_engine: StorageEngine) -> None:
        """Register a named storage pool."""
        self._pool_storages[pool_id] = storage_engine

    def unregister_pool(self, pool_id: str) -> None:
        """Unregister a storage pool."""
        self._pool_storages.pop(pool_id, None)

    def _get_storage_for_space(self, space_id: Optional[str]) -> StorageEngine:
        """Return the appropriate storage engine for a space."""
        if space_id and space_id in self._pool_storages:
            return self._pool_storages[space_id]
        return self.storage  # Fall back to primary storage

    def _make_space_path(self, user_path: str, user_ctx: PermissionContext) -> str:
        """
        Build effective path under spaces/{space_id}/shared/.
        ALL file operations go through Space. No teams/ path.

        Layout: spaces/{space_id}/shared/{path}
        If no active_space_id, raises PermissionError (must select a space first).

        If user_path already starts with 'spaces/', it's an effective path returned
        by list — use it directly to avoid double-prefixing.
        """
        if not user_ctx.active_space_id:
            raise FileAccessDenied(
                "请先选择一个工作空间再进行文件操作",
                decision=None
            )
        # Already an effective path (from list response) — use as-is
        if user_path.startswith('spaces/'):
            return user_path
        # Clean relative path
        clean = user_path.lstrip('/')
        return f"spaces/{user_ctx.active_space_id}/shared/{clean}"

    def _update_space_used_bytes(self, delta_bytes: int, user_ctx: PermissionContext) -> None:
        """Update space used_bytes after a successful write/delete."""
        if not self._db_factory or not user_ctx.active_space_id:
            return
        from .space_service import SpaceService
        svc = SpaceService(db_factory=self._db_factory)
        svc.update_used_bytes(space_id=user_ctx.active_space_id, delta=delta_bytes)

    def _check_quota(self, file_size: int, user_ctx: PermissionContext) -> None:
        """Check if space has quota for writing file_size bytes. Raises QuotaExceeded."""
        if not self._db_factory or not user_ctx.active_space_id:
            return  # No quota enforcement if no DB

        from .space_service import SpaceService, QuotaExceeded
        svc = SpaceService(db_factory=self._db_factory)
        svc.check_quota_for_write(space_id=user_ctx.active_space_id, additional_bytes=file_size)

    def _check_file_lock(self, space_id: Optional[str], user_path: str, user_id: str) -> None:
        """Check if file is locked by another user. Raises FileLocked."""
        if not self._db_factory or not space_id:
            return  # No lock enforcement if no DB

        from .file_lock_service import FileLockService, LockHeldByOther
        try:
            svc = FileLockService(db_factory=self._db_factory)
            # Use user_path directly (relative path or effective path)
            lock_info = svc.check_lock(space_id, user_path)
            if lock_info and lock_info.get("locked_by") != user_id:
                raise FileLocked(
                    path=user_path,
                    locked_by=lock_info.get("locked_by_name", "其他人"),
                    expires_at=lock_info.get("expires_at", "未知"),
                )
        except LockHeldByOther as e:
            raise FileLocked(
                path=user_path,
                locked_by=e.lock.user.username if e.lock and e.lock.user else "其他人",
                expires_at=e.lock.expires_at.isoformat() if e.lock else "未知",
            )
        except FileLocked:
            raise  # Re-raise FileLocked exceptions
        except Exception:
            pass  # Lock check is non-critical, allow operation if lock service fails

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def _resolve_storage_and_path(self, user_path: str, user_ctx: PermissionContext) -> tuple:
        """Return (storage_engine, effective_path) for a user request."""
        storage = self._get_storage_for_space(user_ctx.active_space_id)
        effective_path = self._make_space_path(user_path, user_ctx)
        return storage, effective_path

    def list_directory(
        self,
        path: str,
        user_ctx: PermissionContext,
        include_hidden: bool = False,
        ip_address: Optional[str] = None,
    ) -> FileListResponseDTO:
        """List directory contents. Raises FileAccessDenied / FileNotFound."""
        storage, effective_path = self._resolve_storage_and_path(path, user_ctx)
        decision = self._checker.check(Operation.LIST, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.list", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            raw_items = storage.list_directory(effective_path, include_hidden=include_hidden)
            items = [
                FileItemDTO(
                    name=item["name"],
                    path=item["path"],
                    is_directory=item.get("type") == "directory",
                    size=item.get("size", 0),
                    modified=item.get("modified"),
                    created=item.get("created"),
                    permissions=item.get("permissions", ""),
                )
                for item in raw_items
            ]
            response = FileListResponseDTO(path=path, items=items, total=len(items), readable=True)

            self._event_bus.publish(Event.create(
                EventType.FILE_LIST,
                {"path": effective_path, "item_count": len(items), "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return response
        except FileNotFoundError:
            raise FileNotFound(f"Directory not found: {path}")

    def read_file(
        self,
        request: FileReadRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> FileContentResponseDTO:
        """Read file contents. Raises FileAccessDenied / FileNotFound."""
        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.READ, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.read", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            content = storage.read_file(
                effective_path,
                offset=request.offset,
                size=request.size,
                encoding=request.encoding,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_READ,
                {"path": effective_path, "size": len(content), "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return FileContentResponseDTO(
                path=request.path,
                content=content,
                size=len(content),
                encoding=request.encoding,
            )
        except FileNotFoundError:
            raise FileNotFound(f"File not found: {request.path}")

    def write_file(
        self,
        request: FileWriteRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write/create file. Raises FileAccessDenied / FileAlreadyExists / FileLocked."""
        self._check_quota(len(request.content), user_ctx)
        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.WRITE, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.write", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        # Check file lock
        self._check_file_lock(user_ctx.active_space_id, request.path, user_ctx.user_id)

        try:
            result = storage.write_file(
                effective_path,
                request.content,
                overwrite=request.overwrite,
            )
            # Update space used_bytes after successful write
            self._update_space_used_bytes(len(request.content), user_ctx)
            self._event_bus.publish(Event.create(
                EventType.FILE_WRITE,
                {"path": effective_path, "size": len(request.content), "overwrite": request.overwrite, "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            # Create version record
            self._create_version(
                user_ctx=user_ctx,
                path=request.path,
                name=request.path.split("/")[-1],
                is_directory=False,
                size=len(request.content),
                action="update" if request.overwrite else "create",
            )

            # Publish webhook event
            publish_file_event(
                WebhookEventType.FILE_UPDATED if request.overwrite else WebhookEventType.FILE_CREATED,
                path=request.path,
                user=user_ctx.username,
                metadata={"size": len(request.content), "space_id": user_ctx.active_space_id},
            )

            return result
        except FileExistsError:
            raise FileAlreadyExists(f"File exists: {request.path}")

    def delete_file(
        self,
        request: FileDeleteRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete file/directory. Raises FileAccessDenied / FileNotFound / DirectoryNotEmpty / FileLocked."""
        # Validate active space before any operation
        if not user_ctx.active_space_id:
            raise FileAccessDenied(
                "请先选择一个工作空间再进行删除操作",
                decision=None
            )

        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.DELETE, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.delete", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        # Check file lock
        self._check_file_lock(user_ctx.active_space_id, request.path, user_ctx.user_id)

        # Get file size before deletion to update quota
        file_size = 0
        is_directory = False
        try:
            stat = storage.get_stat(effective_path)
            if stat.get("type") != "directory":
                file_size = stat.get("size", 0)
            else:
                is_directory = True
        except FileNotFoundError:
            raise FileNotFound(f"文件不存在: {request.path}")

        soft_deleted = False
        try:
            # Try soft-delete via TrashService first (if db available)
            if self._db_factory and user_ctx.active_space_id:
                try:
                    from .trash_service import TrashService
                    trash_svc = TrashService(
                        db_factory=self._db_factory,
                        storage=storage,
                        default_pool_storage_path="",
                    )
                    trash_svc.move_to_trash(
                        space_id=user_ctx.active_space_id,
                        user_path=request.path,
                        user_id=user_ctx.user_id,
                        is_directory=is_directory,
                        file_size=file_size,
                    )
                    # Decrement space used_bytes for files (not directories)
                    if file_size > 0:
                        self._update_space_used_bytes(-file_size, user_ctx)
                    self._event_bus.publish(Event.create(
                        EventType.FILE_DELETE,
                        {"path": effective_path, "recursive": request.recursive, "ip_address": ip_address, "space_id": user_ctx.active_space_id, "soft_delete": True},
                        user_id=user_ctx.user_id, username=user_ctx.username,
                    ))
                    soft_deleted = True
                    # Publish webhook event
                    publish_file_event(
                        WebhookEventType.FILE_DELETED,
                        path=request.path,
                        user=user_ctx.username,
                        metadata={"space_id": user_ctx.active_space_id, "soft_delete": True},
                    )
                    return {"message": f"已移到回收站: {request.path}"}
                except ImportError:
                    pass  # Fall back to hard delete if TrashService unavailable
                except Exception as e:
                    # Log the error instead of silent pass
                    import logging
                    logging.warning(f"Soft delete failed, falling back to hard delete: {e}")
                    pass  # Fall through to hard delete

            # Hard delete (fallback or when no db)
            storage.delete_path(effective_path, recursive=request.recursive)
            # Decrement space used_bytes
            if file_size > 0:
                self._update_space_used_bytes(-file_size, user_ctx)
            self._event_bus.publish(Event.create(
                EventType.FILE_DELETE,
                {"path": effective_path, "recursive": request.recursive, "ip_address": ip_address, "space_id": user_ctx.active_space_id, "soft_delete": False},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            # Publish webhook event
            publish_file_event(
                WebhookEventType.FILE_DELETED,
                path=request.path,
                user=user_ctx.username,
                metadata={"space_id": user_ctx.active_space_id, "soft_delete": False},
            )
            return {"message": f"已删除: {request.path}"}
        except FileNotFoundError:
            raise FileNotFound(f"文件不存在: {request.path}")
        except DirectoryNotEmptyError:
            raise DirectoryNotEmpty(f"目录不为空，请先删除子文件: {request.path}")

    def create_directory(
        self,
        request: MkDirRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create directory. Raises FileAccessDenied / FileAlreadyExists."""
        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.WRITE, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.create_dir", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            result = storage.create_directory(effective_path)
            self._event_bus.publish(Event.create(
                EventType.FILE_CREATE_DIR,
                {"path": effective_path, "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return result
        except FileExistsError:
            raise FileAlreadyExists(f"Already exists: {request.path}")

    def copy_file(
        self,
        request: FileCopyRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Copy file. Raises FileAccessDenied / FileNotFound / FileAlreadyExists."""
        storage, eff_from = self._resolve_storage_and_path(request.from_path, user_ctx)
        _, eff_to = self._resolve_storage_and_path(request.to_path, user_ctx)
        # Check read on source
        read_decision = self._checker.check(Operation.READ, eff_from, user_ctx)
        if not read_decision.allowed:
            self._publish_denied("file.copy.read", eff_from, user_ctx, ip_address)
            raise FileAccessDenied(read_decision.reason, read_decision)

        # Check write on destination
        write_decision = self._checker.check(Operation.WRITE, eff_to, user_ctx)
        if not write_decision.allowed:
            self._publish_denied("file.copy.write", eff_to, user_ctx, ip_address)
            raise FileAccessDenied(write_decision.reason, write_decision)

        try:
            result = storage.copy_file(
                eff_from,
                eff_to,
                overwrite=request.overwrite,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_COPY,
                {"from": eff_from, "to": eff_to, "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return result
        except FileNotFoundError as e:
            raise FileNotFound(str(e))
        except FileExistsError:
            raise FileAlreadyExists(f"Destination exists: {request.to_path}")

    def move_file(
        self,
        request: FileMoveRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move/rename file or directory. Raises FileAccessDenied / FileNotFound / FileAlreadyExists."""
        storage, eff_from = self._resolve_storage_and_path(request.from_path, user_ctx)
        _, eff_to = self._resolve_storage_and_path(request.to_path, user_ctx)
        # Check delete on source
        delete_decision = self._checker.check(Operation.DELETE, eff_from, user_ctx)
        if not delete_decision.allowed:
            self._publish_denied("file.move.delete", eff_from, user_ctx, ip_address)
            raise FileAccessDenied(delete_decision.reason, delete_decision)

        # Check write on destination
        write_decision = self._checker.check(Operation.WRITE, eff_to, user_ctx)
        if not write_decision.allowed:
            self._publish_denied("file.move.write", eff_to, user_ctx, ip_address)
            raise FileAccessDenied(write_decision.reason, write_decision)

        try:
            result = storage.move_file(
                eff_from,
                eff_to,
                overwrite=request.overwrite,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_MOVE,
                {"from": eff_from, "to": eff_to, "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return result
        except FileNotFoundError as e:
            raise FileNotFound(str(e))
        except FileExistsError:
            raise FileAlreadyExists(f"Destination exists: {request.to_path}")

    def get_stat(
        self,
        path: str,
        user_ctx: PermissionContext,
    ) -> FileStatResponseDTO:
        """Get file/directory metadata. Raises FileAccessDenied / FileNotFound."""
        storage, effective_path = self._resolve_storage_and_path(path, user_ctx)
        decision = self._checker.check(Operation.READ, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.stat", effective_path, user_ctx)
            raise FileAccessDenied(decision.reason, decision)

        try:
            stat = storage.get_stat(effective_path)
            return FileStatResponseDTO(
                name=stat["name"],
                path=path,
                is_directory=stat.get("type") == "directory",
                size=stat["size"],
                modified=stat.get("modified"),
                created=stat.get("created"),
                permissions=stat.get("permissions", ""),
            )
        except FileNotFoundError:
            raise FileNotFound(f"Not found: {path}")

    # -------------------------------------------------------------------------
    # Version Control
    # -------------------------------------------------------------------------

    def _create_version(
        self,
        user_ctx: PermissionContext,
        path: str,
        name: str,
        is_directory: bool,
        size: int,
        action: str,
        checksum: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Create a file version record. Returns the version record or None if no DB."""
        if not self._db_factory or not user_ctx.active_space_id:
            return None

        session = self._db_factory()
        try:
            from ..engine.models import FileVersion

            # Get next version number for this path
            latest = session.query(FileVersion).filter(
                FileVersion.space_id == user_ctx.active_space_id,
                FileVersion.path == path,
            ).order_by(FileVersion.version.desc()).first()

            next_version = (latest.version + 1) if latest else 1

            version = FileVersion(
                space_id=user_ctx.active_space_id,
                path=path,
                name=name,
                is_directory=is_directory,
                size=size,
                checksum=checksum,
                version=next_version,
                action=action,
                created_by=user_ctx.user_id,
            )
            session.add(version)
            session.commit()

            return version.to_dict()
        except Exception:
            session.rollback()
            return None
        finally:
            session.close()

    def list_versions(
        self,
        path: str,
        user_ctx: PermissionContext,
    ) -> List[Dict[str, Any]]:
        """List all versions for a file path."""
        if not self._db_factory or not user_ctx.active_space_id:
            return []

        session = self._db_factory()
        try:
            from ..engine.models import FileVersion

            versions = session.query(FileVersion).filter(
                FileVersion.space_id == user_ctx.active_space_id,
                FileVersion.path == path,
            ).order_by(FileVersion.version.desc()).all()

            return [v.to_dict() for v in versions]
        finally:
            session.close()

    def restore_version(
        self,
        path: str,
        version: int,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Restore a file to a previous version. Creates new version with restored content."""
        if not self._db_factory or not user_ctx.active_space_id:
            raise FileNotFound("Version history not available")

        session = self._db_factory()
        try:
            from ..engine.models import FileVersion

            # Find the version to restore
            old_version = session.query(FileVersion).filter(
                FileVersion.space_id == user_ctx.active_space_id,
                FileVersion.path == path,
                FileVersion.version == version,
            ).first()

            if not old_version:
                raise FileNotFound(f"Version {version} not found for {path}")

            # Get storage
            storage = self._get_storage_for_space(user_ctx.active_space_id)
            effective_path = self._make_space_path(path, user_ctx)

            # Read current content if it exists
            current_content = None
            if not old_version.is_directory:
                try:
                    current_content = storage.read_file(effective_path)
                except FileNotFoundError:
                    pass

            # Create new version with "restore" action
            next_version = old_version.version + 1
            new_ver = FileVersion(
                space_id=user_ctx.active_space_id,
                path=path,
                name=old_version.name,
                is_directory=old_version.is_directory,
                size=old_version.size,
                checksum=old_version.checksum,
                version=next_version,
                action="restore",
                created_by=user_ctx.user_id,
                metadata={"restored_from_version": version},
            )
            session.add(new_ver)

            # If it's a file, write the old content back
            if current_content is not None and not old_version.is_directory:
                storage.write_file(effective_path, current_content)

            session.commit()

            self._event_bus.publish(Event.create(
                EventType.FILE_RESTORE,
                {"path": path, "restored_version": version, "new_version": next_version, "ip_address": ip_address, "space_id": user_ctx.active_space_id},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return {
                "message": f"Restored {path} to version {version}",
                "new_version": next_version,
            }
        except FileNotFoundError:
            raise
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _publish_denied(
        self,
        operation: str,
        path: str,
        ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> None:
        self._event_bus.publish(Event.create(
            EventType.FILE_LIST if operation == "file.list" else EventType.FILE_READ,
            {"operation": operation, "path": path, "reason": "denied", "ip_address": ip_address, "space_id": ctx.active_space_id},
            user_id=ctx.user_id, username=ctx.username,
        ))
