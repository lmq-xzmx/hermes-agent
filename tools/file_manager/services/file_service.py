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
    ):
        self.storage = storage
        self._checker = permission_checker
        self._event_bus = event_bus or get_event_bus()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def list_directory(
        self,
        path: str,
        user_ctx: PermissionContext,
        include_hidden: bool = False,
        ip_address: Optional[str] = None,
    ) -> FileListResponseDTO:
        """List directory contents. Raises FileAccessDenied / FileNotFound."""
        decision = self._checker.check(Operation.LIST, path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.list", path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            raw_items = self.storage.list_directory(path, include_hidden=include_hidden)
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
                {"path": path, "item_count": len(items), "ip_address": ip_address},
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
        decision = self._checker.check(Operation.READ, request.path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.read", request.path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            content = self.storage.read_file(
                request.path,
                offset=request.offset,
                size=request.size,
                encoding=request.encoding,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_READ,
                {"path": request.path, "size": len(content), "ip_address": ip_address},
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
        decision = self._checker.check(Operation.WRITE, request.path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.write", request.path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            result = self.storage.write_file(
                request.path,
                request.content,
                overwrite=request.overwrite,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_WRITE,
                {"path": request.path, "size": len(request.content), "overwrite": request.overwrite, "ip_address": ip_address},
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
        decision = self._checker.check(Operation.DELETE, request.path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.delete", request.path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            self.storage.delete_path(request.path, recursive=request.recursive)
            self._event_bus.publish(Event.create(
                EventType.FILE_DELETE,
                {"path": request.path, "recursive": request.recursive, "ip_address": ip_address},
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
        decision = self._checker.check(Operation.WRITE, request.path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.create_dir", request.path, user_ctx, ip_address)
            raise FileAccessDenied(decision.reason, decision)

        try:
            result = self.storage.create_directory(request.path)
            self._event_bus.publish(Event.create(
                EventType.FILE_CREATE_DIR,
                {"path": request.path, "ip_address": ip_address},
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
        # Check read on source
        read_decision = self._checker.check(Operation.READ, request.from_path, user_ctx)
        if not read_decision.allowed:
            self._publish_denied("file.copy.read", request.from_path, user_ctx, ip_address)
            raise FileAccessDenied(read_decision.reason, read_decision)

        # Check write on destination
        write_decision = self._checker.check(Operation.WRITE, request.to_path, user_ctx)
        if not write_decision.allowed:
            self._publish_denied("file.copy.write", request.to_path, user_ctx, ip_address)
            raise FileAccessDenied(write_decision.reason, write_decision)

        try:
            result = self.storage.copy_file(
                request.from_path,
                request.to_path,
                overwrite=request.overwrite,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_COPY,
                {"from": request.from_path, "to": request.to_path, "ip_address": ip_address},
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
        # Check delete on source
        delete_decision = self._checker.check(Operation.DELETE, request.from_path, user_ctx)
        if not delete_decision.allowed:
            self._publish_denied("file.move.delete", request.from_path, user_ctx, ip_address)
            raise FileAccessDenied(delete_decision.reason, delete_decision)

        # Check write on destination
        write_decision = self._checker.check(Operation.WRITE, request.to_path, user_ctx)
        if not write_decision.allowed:
            self._publish_denied("file.move.write", request.to_path, user_ctx, ip_address)
            raise FileAccessDenied(write_decision.reason, write_decision)

        try:
            result = self.storage.move_file(
                request.from_path,
                request.to_path,
                overwrite=request.overwrite,
            )
            self._event_bus.publish(Event.create(
                EventType.FILE_MOVE,
                {"from": request.from_path, "to": request.to_path, "ip_address": ip_address},
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
        decision = self._checker.check(Operation.READ, path, user_ctx)
        if not decision.allowed:
            self._publish_denied("file.stat", path, user_ctx)
            raise FileAccessDenied(decision.reason, decision)

        try:
            stat = self.storage.get_stat(path)
            return FileStatResponseDTO(
                name=stat["name"],
                path=stat["path"],
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
