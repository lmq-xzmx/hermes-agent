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
        # File operations are routed by user_ctx.active_team_id
        self._pool_storages: Dict[str, StorageEngine] = {}
        # Default pool id
        self._default_pool_id: Optional[str] = None

    def register_pool(self, pool_id: str, storage_engine: StorageEngine) -> None:
        """Register a named storage pool."""
        self._pool_storages[pool_id] = storage_engine

    def unregister_pool(self, pool_id: str) -> None:
        """Unregister a storage pool."""
        self._pool_storages.pop(pool_id, None)

    def _get_storage_for_team(self, team_id: Optional[str]) -> StorageEngine:
        """Return the appropriate storage engine for a team."""
        if team_id and team_id in self._pool_storages:
            return self._pool_storages[team_id]
        return self.storage  # Fall back to primary storage

    def _make_team_path(self, user_path: str, user_ctx: PermissionContext) -> str:
        """
        Prefix user_path with the team directory structure.

        Layout: teams/{team_id}/{user_id}/...
        If no active_team_id, returns user_path unchanged (backwards-compatible).
        """
        if not user_ctx.active_team_id:
            return user_path
        return f"teams/{user_ctx.active_team_id}/{user_ctx.user_id}/{user_path.lstrip('/')}"

    def _update_team_used_bytes(self, delta_bytes: int, user_ctx: PermissionContext) -> None:
        """Increment team's used_bytes after a successful write."""
        if not self._db_factory or not user_ctx.active_team_id:
            return
        from .team_service import TeamService
        svc = TeamService(db_factory=self._db_factory)
        svc.increment_team_usage(team_id=user_ctx.active_team_id, delta_bytes=delta_bytes)

    def _check_quota(self, file_size: int, user_ctx: PermissionContext) -> None:
        """Check if user has quota to write file_size bytes. Raises TeamQuotaExceeded."""
        if not self._db_factory:
            return  # No quota enforcement if no DB

        from .team_service import TeamService
        svc = TeamService(db_factory=self._db_factory)
        contexts = svc.get_user_storage_context(user_id=str(user_ctx.user_id))
        if not contexts:
            return
        ctx0 = contexts[0]
        quota = ctx0.get("max_bytes", 0)
        used = ctx0.get("used_bytes", 0)
        remaining = quota - used
        if quota > 0 and file_size > remaining:
            from .team_service import TeamQuotaExceeded
            team_name = ctx0.get("team_name", ctx0.get("team_id", ""))
            raise TeamQuotaExceeded(
                team_name=team_name,
                max_bytes=quota,
                used_bytes=used,
                required=file_size,
            )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def _resolve_storage_and_path(self, user_path: str, user_ctx: PermissionContext) -> tuple:
        """Return (storage_engine, effective_path) for a user request."""
        storage = self._get_storage_for_team(user_ctx.active_team_id)
        effective_path = self._make_team_path(user_path, user_ctx)
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
                {"path": effective_path, "item_count": len(items), "ip_address": ip_address},
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
                {"path": effective_path, "size": len(content), "ip_address": ip_address},
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
        """Write/create file. Raises FileAccessDenied / FileAlreadyExists."""
        self._check_quota(len(request.content), user_ctx)
        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.WRITE, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.write", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            result = storage.write_file(
                effective_path,
                request.content,
                overwrite=request.overwrite,
            )
            # Update team used_bytes after successful write
            self._update_team_used_bytes(len(request.content), user_ctx)
            self._event_bus.publish(Event.create(
                EventType.FILE_WRITE,
                {"path": effective_path, "size": len(request.content), "overwrite": request.overwrite, "ip_address": ip_address},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return result
        except FileExistsError:
            raise FileAlreadyExists(f"File exists: {request.path}")

    def delete_file(
        self,
        request: FileDeleteRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete file/directory. Raises FileAccessDenied / FileNotFound / DirectoryNotEmpty."""
        storage, effective_path = self._resolve_storage_and_path(request.path, user_ctx)
        decision = self._checker.check(Operation.DELETE, effective_path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.delete", effective_path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        # Get file size before deletion to update quota
        file_size = 0
        try:
            stat = storage.get_stat(effective_path)
            if stat.get("type") != "directory":
                file_size = stat.get("size", 0)
        except FileNotFoundError:
            pass  # Non-existent file, nothing to charge

        try:
            storage.delete_path(effective_path, recursive=request.recursive)
            # Decrement team used_bytes
            if file_size > 0:
                self._update_team_used_bytes(-file_size, user_ctx)
            self._event_bus.publish(Event.create(
                EventType.FILE_DELETE,
                {"path": effective_path, "recursive": request.recursive, "ip_address": ip_address},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))
            return {"message": f"Deleted: {request.path}"}
        except FileNotFoundError:
            raise FileNotFound(f"Not found: {request.path}")
        except DirectoryNotEmptyError:
            raise DirectoryNotEmpty(f"Directory not empty: {request.path}")

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
                {"path": effective_path, "ip_address": ip_address},
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
                {"from": eff_from, "to": eff_to, "ip_address": ip_address},
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
                {"from": eff_from, "to": eff_to, "ip_address": ip_address},
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
            {"operation": operation, "path": path, "reason": "denied", "ip_address": ip_address},
            user_id=ctx.user_id, username=ctx.username,
        ))
