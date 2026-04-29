"""
Files API - File operations with permission checking
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from pathlib import Path

from fastapi import Request, HTTPException, Depends

from ..engine.models import Operation
from pydantic import BaseModel

from ..engine.models import User, AuditAction
from ..engine.storage import StorageEngine, FileNotFoundError, FileExistsError, DirectoryNotEmptyError
from ..engine.audit import AuditLogger
from .auth import get_current_user, get_client_info


# ============================================================================
# Pydantic Models
# ============================================================================

class FileReadRequest(BaseModel):
    path: str
    offset: int = 0
    size: Optional[int] = None
    encoding: str = "utf-8"


class FileWriteRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = True


class FileCopyRequest(BaseModel):
    from_path: str
    to_path: str
    overwrite: bool = False


class FileMoveRequest(BaseModel):
    from_path: str
    to_path: str
    overwrite: bool = False


class MkDirRequest(BaseModel):
    path: str


class FileDeleteRequest(BaseModel):
    path: str
    recursive: bool = False


class FileSearchRequest(BaseModel):
    path: str
    pattern: str
    recursive: bool = True


class ShareRequest(BaseModel):
    path: str
    password: Optional[str] = None
    permissions: str = "read"  # read or read_write
    expires_in_days: Optional[int] = None
    max_access_count: Optional[int] = None


# ============================================================================
# Files API
# ============================================================================

class FilesAPI:
    """File operations API handlers"""
    
    def __init__(
        self,
        storage: StorageEngine,
        db_session_factory,
    ):
        self.storage = storage
        self.db_factory = db_session_factory
    
    def list_directory(
        self,
        path: str,
        user: User,
        include_hidden: bool = False,
        ip_address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List directory contents"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            # Check permission
            decision = self.storage.permission_engine.check_permission(
                user, Operation.LIST, path, list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, Operation.LIST, path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                items = self.storage.list_directory(path, include_hidden=include_hidden)
                audit.log_file_operation(
                    AuditAction.FILE_LIST, user, path, "success", ip_address
                )
                return items
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
        finally:
            session.close()
    
    def read_file(
        self,
        request: FileReadRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Read file contents"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            decision = self.storage.permission_engine.check_permission(
                user, Operation.READ, request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, Operation.READ, request.path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                content = self.storage.read_file(
                    request.path,
                    offset=request.offset,
                    size=request.size,
                    encoding=request.encoding,
                )
                audit.log_file_operation(
                    AuditAction.FILE_READ, user, request.path, "success", ip_address
                )
                return {
                    "content": content,
                    "path": request.path,
                    "offset": request.offset,
                    "size": len(content),
                }
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"File not found: {request.path}")
        finally:
            session.close()
    
    def write_file(
        self,
        request: FileWriteRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write/create file"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            decision = self.storage.permission_engine.check_permission(
                user, Operation.WRITE, request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, Operation.WRITE, request.path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                result = self.storage.write_file(
                    request.path,
                    request.content,
                    overwrite=request.overwrite,
                )
                audit.log_file_operation(
                    AuditAction.FILE_WRITE, user, request.path, "success", ip_address
                )
                return result
            except FileExistsError:
                raise HTTPException(status_code=409, detail=f"File exists: {request.path}")
        finally:
            session.close()
    
    def delete_file(
        self,
        request: FileDeleteRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete file or directory"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            decision = self.storage.permission_engine.check_permission(
                user, Operation.DELETE, request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, Operation.DELETE, request.path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                self.storage.delete_path(request.path, recursive=request.recursive)
                audit.log_file_operation(
                    AuditAction.FILE_DELETE, user, request.path, "success", ip_address
                )
                return {"message": f"Deleted: {request.path}"}
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Not found: {request.path}")
            except DirectoryNotEmptyError:
                raise HTTPException(
                    status_code=409,
                    detail=f"Directory not empty: {request.path}. Use recursive=true"
                )
        finally:
            session.close()
    
    def create_directory(
        self,
        request: MkDirRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create directory"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            decision = self.storage.permission_engine.check_permission(
                user, Operation.WRITE, request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, "mkdir", request.path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                result = self.storage.create_directory(request.path)
                audit.log_file_operation(
                    AuditAction.FILE_CREATE, user, request.path, "success", ip_address
                )
                return result
            except FileExistsError:
                raise HTTPException(status_code=409, detail=f"Already exists: {request.path}")
        finally:
            session.close()
    
    def copy_file(
        self,
        request: FileCopyRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Copy file"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            # Check read permission on source
            read_decision = self.storage.permission_engine.check_permission(
                user, Operation.READ, request.from_path,
                list(user.role.permission_rules) if user.role else []
            )
            if not read_decision.allowed:
                audit.log_permission_denied(user, "copy", request.from_path, ip_address)
                raise HTTPException(status_code=403, detail=read_decision.reason)
            
            # Check write permission on destination
            write_decision = self.storage.permission_engine.check_permission(
                user, Operation.WRITE, request.to_path,
                list(user.role.permission_rules) if user.role else []
            )
            if not write_decision.allowed:
                audit.log_permission_denied(user, "copy", request.to_path, ip_address)
                raise HTTPException(status_code=403, detail=write_decision.reason)
            
            try:
                result = self.storage.copy_file(
                    request.from_path,
                    request.to_path,
                    overwrite=request.overwrite,
                )
                audit.log_file_operation(
                    AuditAction.FILE_COPY, user, f"{request.from_path} -> {request.to_path}",
                    "success", ip_address
                )
                return result
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except FileExistsError:
                raise HTTPException(status_code=409, detail=f"Destination exists: {request.to_path}")
        finally:
            session.close()
    
    def move_file(
        self,
        request: FileMoveRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Move/rename file or directory"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            # Check delete permission on source
            delete_decision = self.storage.permission_engine.check_permission(
                user, Operation.DELETE, request.from_path,
                list(user.role.permission_rules) if user.role else []
            )
            if not delete_decision.allowed:
                audit.log_permission_denied(user, "move", request.from_path, ip_address)
                raise HTTPException(status_code=403, detail=delete_decision.reason)
            
            # Check write permission on destination
            write_decision = self.storage.permission_engine.check_permission(
                user, Operation.WRITE, request.to_path,
                list(user.role.permission_rules) if user.role else []
            )
            if not write_decision.allowed:
                audit.log_permission_denied(user, "move", request.to_path, ip_address)
                raise HTTPException(status_code=403, detail=write_decision.reason)
            
            try:
                result = self.storage.move_file(
                    request.from_path,
                    request.to_path,
                    overwrite=request.overwrite,
                )
                audit.log_file_operation(
                    AuditAction.FILE_MOVE, user, f"{request.from_path} -> {request.to_path}",
                    "success", ip_address
                )
                return result
            except FileNotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e))
            except FileExistsError:
                raise HTTPException(status_code=409, detail=f"Destination exists: {request.to_path}")
        finally:
            session.close()
    
    def get_stat(
        self,
        path: str,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get file/directory metadata"""
        session = self.db_factory()
        try:
            decision = self.storage.permission_engine.check_permission(
                user, Operation.READ, path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                return self.storage.get_stat(path)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Not found: {path}")
        finally:
            session.close()
    
    def search_files(
        self,
        request: FileSearchRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search for files"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            decision = self.storage.permission_engine.check_permission(
                user, Operation.LIST, request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                audit.log_permission_denied(user, "search", request.path, ip_address)
                raise HTTPException(status_code=403, detail=decision.reason)
            
            try:
                results = self.storage.search(
                    request.path,
                    request.pattern,
                    recursive=request.recursive,
                )
                return results
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail=f"Directory not found: {request.path}")
        finally:
            session.close()
