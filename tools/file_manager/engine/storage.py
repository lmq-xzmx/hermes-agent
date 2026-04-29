"""
File Storage Engine - Secure file operations with permission integration
"""

from __future__ import annotations

import io
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, BinaryIO
import mimetypes

from .permission import PermissionEngine, Operation


class FileOperationError(Exception):
    """Base exception for file operations"""
    pass


class FileNotFoundError(FileOperationError):
    """File does not exist"""
    pass


class FileExistsError(FileOperationError):
    """File already exists"""
    pass


class DirectoryNotEmptyError(FileOperationError):
    """Directory is not empty"""
    pass


class StorageEngine:
    """
    Secure file storage engine
    
    All operations go through the permission engine to ensure
    users can only access files within their allowed paths.
    """
    
    def __init__(
        self,
        storage_root: str,
        permission_engine: PermissionEngine,
    ):
        self.storage_root = Path(storage_root).resolve()
        self.permission_engine = permission_engine
        
        # Ensure storage root exists
        self.storage_root.mkdir(parents=True, exist_ok=True)
        
        # Guess common types
        mimetypes.init()
    
    # -------------------------------------------------------------------------
    # Directory Operations
    # -------------------------------------------------------------------------
    
    def list_directory(
        self,
        path: str,
        include_hidden: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List directory contents
        
        Returns:
            List of file/directory info dicts with keys:
            - name, path, type (file/directory), size, modified, permissions
        """
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not full_path.is_dir():
            raise FileOperationError(f"Not a directory: {path}")
        
        items = []
        for entry in full_path.iterdir():
            name = entry.name
            
            # Skip hidden files unless requested
            if not include_hidden and name.startswith("."):
                continue
            
            stat = entry.stat()
            items.append({
                "name": name,
                "path": str(entry.relative_to(self.storage_root)),
                "type": "directory" if entry.is_dir() else "file",
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "permissions": self._format_permissions(stat.st_mode),
            })
        
        # Sort: directories first, then by name
        items.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))
        
        return items
    
    def create_directory(self, path: str) -> Dict[str, Any]:
        """Create a directory"""
        full_path = self._resolve_user_path(path)
        
        if full_path.exists():
            raise FileExistsError(f"Already exists: {path}")
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        full_path.mkdir(parents=False, exist_ok=False)
        
        stat = full_path.stat()
        return {
            "name": full_path.name,
            "path": str(full_path.relative_to(self.storage_root)),
            "type": "directory",
            "size": 0,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
        }
    
    def remove_directory(self, path: str, recursive: bool = False) -> None:
        """Remove a directory"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not full_path.is_dir():
            raise FileOperationError(f"Not a directory: {path}")
        
        if not recursive and any(full_path.iterdir()):
            raise DirectoryNotEmptyError(f"Directory not empty: {path}")
        
        shutil.rmtree(full_path)
    
    # -------------------------------------------------------------------------
    # File Operations
    # -------------------------------------------------------------------------
    
    def read_file(
        self,
        path: str,
        offset: int = 0,
        size: Optional[int] = None,
        encoding: str = "utf-8",
    ) -> str:
        """
        Read file contents as text
        
        Args:
            path: File path relative to storage root
            offset: Byte offset to start reading from
            size: Maximum bytes to read (None = rest of file)
            encoding: Text encoding (default utf-8)
        
        Returns:
            File contents as string
        """
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not full_path.is_file():
            raise FileOperationError(f"Not a file: {path}")
        
        with open(full_path, "r", encoding=encoding, errors="replace") as f:
            if offset > 0:
                f.seek(offset)
            if size is not None:
                return f.read(size)
            return f.read()
    
    def read_file_bytes(
        self,
        path: str,
        offset: int = 0,
        size: Optional[int] = None,
    ) -> bytes:
        """Read file contents as binary"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not full_path.is_file():
            raise FileOperationError(f"Not a file: {path}")
        
        with open(full_path, "rb") as f:
            if offset > 0:
                f.seek(offset)
            if size is not None:
                return f.read(size)
            return f.read()
    
    def write_file(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """
        Write content to file
        
        Args:
            path: File path relative to storage root
            content: Text content to write
            encoding: Text encoding
            overwrite: If False, fail if file exists
        """
        full_path = self._resolve_user_path(path)
        
        if not overwrite and full_path.exists():
            raise FileExistsError(f"File already exists: {path}")
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "w", encoding=encoding) as f:
            f.write(content)
        
        stat = full_path.stat()
        return {
            "name": full_path.name,
            "path": str(full_path.relative_to(self.storage_root)),
            "type": "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
        }
    
    def write_file_bytes(
        self,
        path: str,
        content: bytes,
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """Write binary content to file"""
        full_path = self._resolve_user_path(path)
        
        if not overwrite and full_path.exists():
            raise FileExistsError(f"File already exists: {path}")
        
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(full_path, "wb") as f:
            f.write(content)
        
        stat = full_path.stat()
        return {
            "name": full_path.name,
            "path": str(full_path.relative_to(self.storage_root)),
            "type": "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
        }
    
    def copy_file(
        self,
        from_path: str,
        to_path: str,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Copy a file to a new location"""
        src = self._resolve_user_path(from_path)
        dst = self._resolve_user_path(to_path)
        
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {from_path}")
        
        if not src.is_file():
            raise FileOperationError(f"Source is not a file: {from_path}")
        
        if dst.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {to_path}")
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        
        stat = dst.stat()
        return {
            "name": dst.name,
            "path": str(dst.relative_to(self.storage_root)),
            "type": "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
        }
    
    def move_file(
        self,
        from_path: str,
        to_path: str,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Move/rename a file or directory"""
        src = self._resolve_user_path(from_path)
        dst = self._resolve_user_path(to_path)
        
        if not src.exists():
            raise FileNotFoundError(f"Source not found: {from_path}")
        
        if dst.exists() and not overwrite:
            raise FileExistsError(f"Destination exists: {to_path}")
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        
        stat = dst.stat()
        return {
            "name": dst.name,
            "path": str(dst.relative_to(self.storage_root)),
            "type": "directory" if dst.is_dir() else "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
        }
    
    def delete_file(self, path: str) -> None:
        """Delete a file"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if full_path.is_dir():
            raise FileOperationError(f"Is a directory, use remove_directory: {path}")
        
        full_path.unlink()
    
    def delete_path(self, path: str, recursive: bool = False) -> None:
        """Delete a file or directory"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Not found: {path}")
        
        if full_path.is_dir():
            self.remove_directory(path, recursive=recursive)
        else:
            self.delete_file(path)
    
    # -------------------------------------------------------------------------
    # Metadata Operations
    # -------------------------------------------------------------------------
    
    def get_stat(self, path: str) -> Dict[str, Any]:
        """Get file/directory metadata"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Not found: {path}")
        
        stat = full_path.stat()
        
        return {
            "name": full_path.name,
            "path": str(full_path.relative_to(self.storage_root)),
            "type": "directory" if full_path.is_dir() else "file",
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "permissions": self._format_permissions(stat.st_mode),
            "mime_type": mimetypes.guess_type(str(full_path))[0],
            "is_symlink": full_path.is_symlink(),
        }
    
    def get_checksum(self, path: str, algorithm: str = "sha256") -> str:
        """Calculate file checksum"""
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        
        if not full_path.is_file():
            raise FileOperationError(f"Not a file: {path}")
        
        h = hashlib.new(algorithm)
        with open(full_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    
    def search(
        self,
        path: str,
        pattern: str,
        recursive: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern
        
        Args:
            path: Directory to search in
            pattern: Glob pattern (e.g., "*.txt", "**/*.py")
            recursive: Search subdirectories
        """
        full_path = self._resolve_user_path(path)
        
        if not full_path.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        
        results = []
        
        if recursive:
            glob_pattern = f"**/{pattern}"
        else:
            glob_pattern = pattern
        
        for match in full_path.glob(glob_pattern):
            if match.is_file():
                stat = match.stat()
                results.append({
                    "name": match.name,
                    "path": str(match.relative_to(self.storage_root)),
                    "type": "file",
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
        
        return results
    
    # -------------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------------
    
    def _resolve_user_path(self, user_path: str) -> Path:
        """
        Resolve a user-provided path against storage root
        
        This is the critical security boundary - it ensures users
        cannot escape the storage root via path traversal attacks.
        """
        if not user_path:
            return self.storage_root
        
        # Use permission engine to safely resolve
        try:
            return self.permission_engine.resolve_path(user_path, str(self.storage_root))
        except (ValueError, PermissionError):
            # Path traversal attempt
            raise PermissionError(f"Path traversal detected: {user_path}")
    
    @staticmethod
    def _format_permissions(mode: int) -> str:
        """Convert stat mode to rwx string (Unix format like rw-r--r--)"""
        import stat
        # S_IRUSR = 0o400, S_IWUSR = 0o200, S_IXUSR = 0o100
        # S_IRGRP = 0o040, S_IWGRP = 0o020, S_IXGRP = 0o010
        # S_IROTH = 0o004, S_IWOTH = 0o002, S_IXOTH = 0o001
        chars = []
        for label, mask in [("r", stat.S_IRUSR), ("w", stat.S_IWUSR), ("x", stat.S_IXUSR)]:
            chars.append(label if mode & mask else "-")
        for label, mask in [("r", stat.S_IRGRP), ("w", stat.S_IWGRP), ("x", stat.S_IXGRP)]:
            chars.append(label if mode & mask else "-")
        for label, mask in [("r", stat.S_IROTH), ("w", stat.S_IWOTH), ("x", stat.S_IXOTH)]:
            chars.append(label if mode & mask else "-")
        return "".join(chars)
