"""
SyncService - 文件同步业务逻辑

核心职责：
- 计算本地文件与远端文件的差异（delta）
- 检测冲突（同一文件两端都有修改）
- 提供冲突解决接口（人工合并）
- 支持定期同步策略

不含 S3 上传下载，仅核心同步算法和冲突检测。
"""

from __future__ import annotations

import hashlib
import os
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable

import httpx

from ..engine.models import Space

logger = logging.getLogger(__name__)

# 是否在同步后触发 LLM Wiki 处理
SYNC_TRIGGER_WIKI_ENABLED = os.getenv("SYNC_TRIGGER_WIKI", "false").lower() == "true"

# Webhook 配置
DEFAULT_WEBHOOK_URL = os.getenv("SYNC_WEBHOOK_URL", "http://localhost:18424/api/v1/knowledge/webhook/sync")


# =============================================================================
# Domain Types
# =============================================================================

class ChangeType(str, Enum):
    """变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RENAME = "rename"


class ConflictStrategy(str, Enum):
    """冲突策略"""
    LAST_WRITE_WINS = "last_write_wins"
    MANUAL_MERGE = "manual_merge"
    THREE_WAY_MERGE = "three_way_merge"


@dataclass
class FileEntry:
    """文件条目（用于同步计算）"""
    path: str
    name: str
    is_directory: bool
    size: int
    checksum: Optional[str]  # SHA256
    modified_at: float  # Unix timestamp

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "is_directory": self.is_directory,
            "size": self.size,
            "checksum": self.checksum,
            "modified_at": self.modified_at,
        }


@dataclass
class FileChange:
    """单个文件的变更记录"""
    path: str
    change_type: ChangeType
    size: int
    checksum: Optional[str]
    modified_at: float
    old_path: Optional[str] = None  # 用于 rename

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "change_type": self.change_type.value,
            "size": self.size,
            "checksum": self.checksum,
            "modified_at": self.modified_at,
            "old_path": self.old_path,
        }


@dataclass
class SyncDelta:
    """同步 delta - 两端的差异"""
    local_changes: List[FileChange] = field(default_factory=list)
    remote_changes: List[FileChange] = field(default_factory=list)
    conflicts: List[ConflictEntry] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "local_changes": [c.to_dict() for c in self.local_changes],
            "remote_changes": [c.to_dict() for c in self.remote_changes],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "timestamp": self.timestamp,
        }


@dataclass
class ConflictEntry:
    """冲突条目"""
    path: str
    local_version: FileEntry
    remote_version: FileEntry
    base_version: Optional[FileEntry] = None  # 三路合并用

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "local_version": self.local_version.to_dict(),
            "remote_version": self.remote_version.to_dict(),
            "base_version": self.base_version.to_dict() if self.base_version else None,
        }


@dataclass
class SyncSnapshot:
    """同步快照 - 某一时刻的文件状态摘要"""
    space_id: str
    files: Dict[str, FileEntry]  # path -> FileEntry
    root_checksum: str  # 整个目录树的 checksum
    captured_at: float

    def file_count(self) -> int:
        return len(self.files)

    def directory_count(self) -> int:
        return sum(1 for f in self.files.values() if f.is_directory)


@dataclass
class SyncCursor:
    """同步游标 - 记录同步位置，用于增量同步"""
    space_id: str
    user_id: str
    last_sync_at: float
    last_remote_checksum: str
    pending_local_count: int = 0
    pending_remote_count: int = 0


# =============================================================================
# SyncWebhookCaller
# =============================================================================

class SyncWebhookCaller:
    """
    同步后触发 Webhook 调用 LLM Wiki 处理。
    """

    def __init__(self, webhook_url: str = DEFAULT_WEBHOOK_URL):
        self._webhook_url = webhook_url

    def call(self, space_id: str, user_id: str, delta: SyncDelta) -> bool:
        """
        触发 webhook 调用。

        Returns:
            True if webhook was called successfully, False otherwise
        """
        if not SYNC_TRIGGER_WIKI_ENABLED:
            logger.debug("SYNC_TRIGGER_WIKI disabled, skipping webhook")
            return False

        try:
            payload = {
                "space_id": space_id,
                "user_id": user_id,
                "changes_count": len(delta.local_changes) + len(delta.remote_changes),
                "conflicts_count": len(delta.conflicts),
                "timestamp": delta.timestamp,
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self._webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if response.status_code == 200:
                logger.info(f"Sync webhook triggered for space {space_id}")
                return True
            else:
                logger.warning(
                    f"Sync webhook returned {response.status_code}: {response.text}"
                )
                return False

        except httpx.TimeoutException:
            logger.warning(f"Sync webhook timeout for space {space_id}")
            return False
        except Exception as e:
            logger.error(f"Sync webhook error: {e}")
            return False


# =============================================================================
# SyncService
# =============================================================================

class SyncService:
    """
    文件同步业务逻辑。

    支持：
    - 计算本地与远端的 delta
    - 检测冲突（基于修改时间 + checksum）
    - 三种冲突策略
    - 定期同步模式

    不含：
    - S3 上传下载（由上层调用方负责）
    - WebSocket 推送（由上层调用方负责）
    """

    def __init__(
        self,
        db_factory,
        storage_root: str,
        conflict_strategy = "manual_merge",
        sync_interval_seconds: int = 300,  # 5 分钟
    ):
        self._db = db_factory
        self._storage_root = storage_root
        if isinstance(conflict_strategy, str):
            self._conflict_strategy = ConflictStrategy(conflict_strategy)
        else:
            self._conflict_strategy = conflict_strategy
        self._sync_interval = sync_interval_seconds
        self._webhook_caller = SyncWebhookCaller()

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def compute_delta(
        self,
        space_id: str,
        local_snapshot: SyncSnapshot,
        remote_snapshot: SyncSnapshot,
    ) -> SyncDelta:
        """
        计算本地与远端之间的 delta。

        1. 对比本地和远端文件列表
        2. 分类：仅本地修改 / 仅远端修改 / 双方都修改（潜在冲突）
        3. 冲突检测：同一文件两端都有修改
        """
        local_files = local_snapshot.files
        remote_files = remote_snapshot.files
        conflicts: List[ConflictEntry] = []
        local_changes: List[FileChange] = []
        remote_changes: List[FileChange] = []

        # 所有路径
        all_paths = set(local_files.keys()) | set(remote_files.keys())

        for path in all_paths:
            local_entry = local_files.get(path)
            remote_entry = remote_files.get(path)

            if local_entry and not remote_entry:
                # 仅本地存在 → 本地新增
                local_changes.append(FileChange(
                    path=path,
                    change_type=ChangeType.CREATE if path not in remote_files else ChangeType.UPDATE,
                    size=local_entry.size,
                    checksum=local_entry.checksum,
                    modified_at=local_entry.modified_at,
                ))
            elif remote_entry and not local_entry:
                # 仅远端存在 → 远端新增（本地删除或本地从未有过）
                remote_changes.append(FileChange(
                    path=path,
                    change_type=ChangeType.DELETE if path not in local_files else ChangeType.UPDATE,
                    size=remote_entry.size,
                    checksum=remote_entry.checksum,
                    modified_at=remote_entry.modified_at,
                ))
            else:
                # 两端都存在 → 检查是否有冲突
                local_modified = local_entry.modified_at
                remote_modified = remote_entry.modified_at

                # 判断是否有修改（基于 modified_at 或 checksum）
                local_changed = True
                remote_changed = True

                if local_entry.checksum and remote_entry.checksum:
                    if local_entry.checksum == remote_entry.checksum:
                        local_changed = False
                        remote_changed = False

                if local_changed and remote_changed:
                    # 两端都有修改 → 冲突
                    conflict = ConflictEntry(
                        path=path,
                        local_version=local_entry,
                        remote_version=remote_entry,
                    )
                    conflicts.append(conflict)
                elif local_changed and not remote_changed:
                    # 仅本地修改
                    local_changes.append(FileChange(
                        path=path,
                        change_type=ChangeType.UPDATE,
                        size=local_entry.size,
                        checksum=local_entry.checksum,
                        modified_at=local_entry.modified_at,
                    ))
                elif remote_changed and not local_changed:
                    # 仅远端修改
                    remote_changes.append(FileChange(
                        path=path,
                        change_type=ChangeType.UPDATE,
                        size=remote_entry.size,
                        checksum=remote_entry.checksum,
                        modified_at=remote_entry.modified_at,
                    ))

        return SyncDelta(
            local_changes=local_changes,
            remote_changes=remote_changes,
            conflicts=conflicts,
            timestamp=time.time(),
        )

    def resolve_conflict(
        self,
        space_id: str,
        path: str,
        resolution: str,  # "local" | "remote" | "merge"
        merged_content: Optional[bytes] = None,
        user_id: Optional[str] = None,
    ) -> FileEntry:
        """
        解决冲突。

        resolution:
        - "local": 保留本地版本，丢弃远端
        - "remote": 保留远端版本，丢弃本地
        - "merge": 使用合并后的内容（需要 merged_content）
        """
        # 实际实现需要访问文件存储
        # 这里返回占位，实际应由 FileService 处理
        raise NotImplementedError("resolve_conflict 需要 merged_content 参数")

    def should_sync(self, space_id: str, user_id: str) -> bool:
        """
        判断是否应该触发同步。

        定期同步策略：检查距离上次同步是否超过间隔时间。
        """
        # TODO: 从数据库读取 SyncCursor
        # 目前返回 True 表示总是同步
        return True

    def record_sync(
        self,
        space_id: str,
        user_id: str,
        delta: SyncDelta,
    ) -> SyncCursor:
        """
        记录同步结果，更新游标。
        """
        now = time.time()
        cursor = SyncCursor(
            space_id=space_id,
            user_id=user_id,
            last_sync_at=now,
            last_remote_checksum=str(hashlib.md5(str(now).encode()).hexdigest()),
            pending_local_count=len(delta.local_changes),
            pending_remote_count=len(delta.remote_changes),
        )
        # TODO: 存入数据库

        # 触发 webhook 调用 LLM Wiki 处理
        try:
            self._webhook_caller.call(space_id, user_id, delta)
        except Exception as e:
            logger.warning(f"Failed to trigger sync webhook: {e}")

        return cursor

    def build_local_snapshot(
        self,
        space_id: str,
        root_path: Optional[str] = None,
    ) -> SyncSnapshot:
        """
        扫描本地文件，构建快照。

        root_path: 相对于 space 的根路径，默认 /
        """
        from ..engine.storage import StorageEngine
        import os

        if root_path is None:
            root_path = "/"

        # 尝试获取 space 对应的物理路径
        space_path = self._get_space_path(space_id, root_path)
        files: Dict[str, FileEntry] = {}

        try:
            if os.path.isdir(space_path):
                for root, dirs, filenames in os.walk(space_path):
                    for filename in filenames:
                        full_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(full_path, space_path)
                        try:
                            stat = os.stat(full_path)
                            files[rel_path] = FileEntry(
                                path=rel_path,
                                name=filename,
                                is_directory=False,
                                size=stat.st_size,
                                checksum=None,
                                modified_at=stat.st_mtime,
                            )
                        except OSError:
                            pass
                    for dirname in dirs:
                        full_path = os.path.join(root, dirname)
                        rel_path = os.path.relpath(full_path, space_path)
                        try:
                            stat = os.stat(full_path)
                            files[rel_path] = FileEntry(
                                path=rel_path,
                                name=dirname,
                                is_directory=True,
                                size=0,
                                checksum=None,
                                modified_at=stat.st_mtime,
                            )
                        except OSError:
                            pass
        except Exception:
            pass

        # 计算整体 checksum
        root_checksum = self._compute_tree_checksum(files)

        return SyncSnapshot(
            space_id=space_id,
            files=files,
            root_checksum=root_checksum,
            captured_at=time.time(),
        )

    def _get_space_path(self, space_id: str, root_path: str = "/") -> str:
        """获取 space 对应的物理路径"""
        from ..engine.models import Space

        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                return self._storage_root

            # 获取 pool 的 base_path
            pool_path = space.storage_pool.base_path if space.storage_pool else self._storage_root
            # space 的根目录
            space_root = os.path.join(pool_path, "spaces", space_id)
            return os.path.join(space_root, root_path.strip("/"))
        except Exception:
            return self._storage_root
        finally:
            session.close()

    def _compute_tree_checksum(self, files: Dict[str, FileEntry]) -> str:
        """计算整个文件树的 checksum（用于快速判断是否真的变了）"""
        sorted_paths = sorted(files.keys())
        combined = "".join(
            f"{p}{files[p].checksum or ''}{files[p].modified_at}"
            for p in sorted_paths
        )
        return hashlib.sha256(combined.encode()).hexdigest()

    def get_sync_status(self, space_id: str, user_id: str) -> dict:
        """
        获取同步状态摘要。
        """
        # TODO: 从数据库读取 SyncCursor
        return {
            "space_id": space_id,
            "user_id": user_id,
            "last_sync_at": None,
            "pending_local": 0,
            "pending_remote": 0,
            "conflict_count": 0,
            "status": "idle",  # idle | syncing | error
        }
