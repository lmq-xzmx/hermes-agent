"""
Sync API - 文件同步端点

提供同步相关的 HTTP API：
- GET  /spaces/{space_id}/sync/status - 获取同步状态
- POST /spaces/{space_id}/sync/delta - 计算 delta
- POST /spaces/{space_id}/sync/resolve - 解决冲突
- GET  /spaces/{space_id}/sync/snapshot - 获取当前快照
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any
from fastapi import Request, HTTPException, Depends
from pydantic import BaseModel

from .auth import get_current_user
from ..services.auth_service import AuthenticatedUser


# ============================================================================
# Pydantic Models
# ============================================================================

class FileEntryDTO(BaseModel):
    path: str
    name: str
    is_directory: bool
    size: int
    checksum: Optional[str] = None
    modified_at: float


class SyncSnapshotRequest(BaseModel):
    """客户端提交自己的快照"""
    files: List[FileEntryDTO]
    root_checksum: str


class SyncSnapshotResponse(BaseModel):
    space_id: str
    files: List[FileEntryDTO]
    root_checksum: str
    file_count: int
    captured_at: float


class SyncDeltaRequest(BaseModel):
    """请求 delta 计算"""
    local_snapshot: SyncSnapshotRequest
    remote_checksum: Optional[str] = None


class ConflictDTO(BaseModel):
    path: str
    local_version: FileEntryDTO
    remote_version: FileEntryDTO
    base_version: Optional[FileEntryDTO] = None


class SyncDeltaResponse(BaseModel):
    local_changes: List[Dict[str, Any]]
    remote_changes: List[Dict[str, Any]]
    conflicts: List[ConflictDTO]
    timestamp: float


class ResolveConflictRequest(BaseModel):
    path: str
    resolution: str  # "local" | "remote" | "merge"


class SyncStatusResponse(BaseModel):
    space_id: str
    user_id: str
    last_sync_at: Optional[float]
    pending_local: int
    pending_remote: int
    conflict_count: int
    status: str  # idle | syncing | error


# ============================================================================
# Route Handlers
# ============================================================================

def get_sync_service(request: Request):
    """获取 SyncService"""
    from ..server import _api_instances
    return _api_instances.get("sync_service")


def get_space_service(request: Request):
    """获取 SpaceService"""
    from ..server import _api_instances
    return _api_instances.get("space_service")


async def get_sync_status(
    space_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncStatusResponse:
    """获取同步状态"""
    sync_service = get_sync_service(request)
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")

    status = sync_service.get_sync_status(space_id, current_user.id)
    return SyncStatusResponse(**status)


async def get_sync_snapshot(
    space_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncSnapshotResponse:
    """获取当前本地快照（供客户端对比）"""
    sync_service = get_sync_service(request)
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")

    # 获取 space 信息
    space_service = get_space_service(request)
    if not space_service:
        raise HTTPException(status_code=503, detail="Space service not available")

    try:
        space = space_service.get_space(space_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Space not found")

    # 构建快照
    snapshot = sync_service.build_local_snapshot(space_id)

    return SyncSnapshotResponse(
        space_id=space_id,
        files=[FileEntryDTO(**f.to_dict()) for f in snapshot.files.values()],
        root_checksum=snapshot.root_checksum,
        file_count=snapshot.file_count(),
        captured_at=snapshot.captured_at,
    )


async def compute_sync_delta(
    space_id: str,
    req: SyncDeltaRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> SyncDeltaResponse:
    """计算本地与远端之间的 delta"""
    sync_service = get_sync_service(request)
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")

    # 构建本地快照
    local_files = {f.path: f for f in req.local_snapshot.files}

    from ..services.sync_service import SyncSnapshot, FileEntry
    local_snapshot = SyncSnapshot(
        space_id=space_id,
        files={
            path: FileEntry(
                path=f.path,
                name=f.name,
                is_directory=f.is_directory,
                size=f.size,
                checksum=f.checksum,
                modified_at=f.modified_at,
            )
            for path, f in local_files.items()
        },
        root_checksum=req.local_snapshot.root_checksum,
        captured_at=0,
    )

    # 构建远端快照（从数据库/存储获取）
    remote_snapshot = sync_service.build_local_snapshot(space_id)

    # 计算 delta
    delta = sync_service.compute_delta(space_id, local_snapshot, remote_snapshot)

    return SyncDeltaResponse(
        local_changes=[c.to_dict() for c in delta.local_changes],
        remote_changes=[c.to_dict() for c in delta.remote_changes],
        conflicts=[
            ConflictDTO(
                path=c.path,
                local_version=FileEntryDTO(**c.local_version.to_dict()),
                remote_version=FileEntryDTO(**c.remote_version.to_dict()),
                base_version=FileEntryDTO(**c.base_version.to_dict()) if c.base_version else None,
            )
            for c in delta.conflicts
        ],
        timestamp=delta.timestamp,
    )


async def resolve_conflict(
    space_id: str,
    req: ResolveConflictRequest,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """解决冲突"""
    sync_service = get_sync_service(request)
    if not sync_service:
        raise HTTPException(status_code=503, detail="Sync service not available")

    if req.resolution not in ("local", "remote", "merge"):
        raise HTTPException(status_code=400, detail="Invalid resolution")

    try:
        result = sync_service.resolve_conflict(
            space_id=space_id,
            path=req.path,
            resolution=req.resolution,
            user_id=current_user.id,
        )
        return {"status": "resolved", "path": req.path, "resolution": req.resolution}
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="Conflict resolution not fully implemented")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
