"""
Storage Adapters - Protocol support for StorageEngine multi-pool architecture.

Each adapter implements the same interface as StorageEngine but handles
a specific protocol (local, smb, nfs, s3, minio).
"""

from __future__ import annotations

import os
import io
import shutil
import hashlib
import tempfile
import subprocess
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, BinaryIO


class StorageAdapter(ABC):
    """Base class for all storage adapters."""

    @abstractmethod
    def exists(self, path: str) -> bool: ...

    @abstractmethod
    def is_dir(self, path: str) -> bool: ...

    @abstractmethod
    def is_file(self, path: str) -> bool: ...

    @abstractmethod
    def list_dir(self, path: str) -> List[str]: ...

    @abstractmethod
    def read_file(self, path: str) -> bytes: ...

    @abstractmethod
    def write_file(self, path: str, content: bytes) -> None: ...

    @abstractmethod
    def delete(self, path: str, recursive: bool = False) -> None: ...

    @abstractmethod
    def mkdir(self, path: str) -> None: ...

    @abstractmethod
    def stat(self, path: str) -> Dict[str, Any]: ...

    @abstractmethod
    def get_free_space(self) -> int: ...

    @abstractmethod
    def get_total_space(self) -> int: ...

    @abstractmethod
    def get_used_space(self) -> int: ...

    def close(self) -> None:
        """Cleanup resources. Override in subclasses that hold connections."""
        pass


# ---------------------------------------------------------------------------
# Local Storage Adapter
# ---------------------------------------------------------------------------

class LocalStorageAdapter(StorageAdapter):
    """
    Adapter for local filesystem storage.
    Wraps the existing StorageEngine for backward compatibility.
    """

    def __init__(self, root_path: str, **kwargs):
        self.root = Path(root_path).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, path: str) -> Path:
        p = (self.root / path.lstrip("/")).resolve()
        if not str(p).startswith(str(self.root)):
            raise ValueError(f"Path escape attempt: {path}")
        return p

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()

    def is_dir(self, path: str) -> bool:
        p = self._resolve(path)
        return p.is_dir()

    def is_file(self, path: str) -> bool:
        p = self._resolve(path)
        return p.is_file()

    def list_dir(self, path: str = "") -> List[str]:
        p = self._resolve(path)
        if not p.is_dir():
            return []
        return sorted([item.name for item in p.iterdir()])

    def read_file(self, path: str) -> bytes:
        return self._resolve(path).read_bytes()

    def write_file(self, path: str, content: bytes) -> None:
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)

    def delete(self, path: str, recursive: bool = False) -> None:
        p = self._resolve(path)
        if not p.exists():
            return
        if p.is_dir():
            shutil.rmtree(p) if recursive else p.rmdir()
        else:
            p.unlink()

    def mkdir(self, path: str) -> None:
        p = self._resolve(path)
        p.mkdir(parents=True, exist_ok=True)

    def stat(self, path: str) -> Dict[str, Any]:
        import mimetypes
        p = self._resolve(path)
        st = p.stat()
        return {
            "size": st.st_size,
            "modified": st.st_mtime,
            "type": "directory" if p.is_dir() else "file",
            "mime": mimetypes.guess_type(str(p))[0],
        }

    def get_free_space(self) -> int:
        stat = os.statvfs(str(self.root))
        return stat.f_bavail * stat.f_frsize

    def get_total_space(self) -> int:
        stat = os.statvfs(str(self.root))
        return stat.f_blocks * stat.f_frsize

    def get_used_space(self) -> int:
        total = self.get_total_space()
        free = self.get_free_space()
        return total - free


# ---------------------------------------------------------------------------
# SMB Storage Adapter
# ---------------------------------------------------------------------------

class SMBStorageAdapter(StorageAdapter):
    """
    Adapter for SMB/CIFS shares using smbclient (smbclient CLI wrapper).

    Requires: pip install smbprotocol && smbclient binary on PATH.
    Alternative: use pysmb (smbprotocol) for pure-Python.
    """

    def __init__(
        self,
        host: str,
        share: str,
        username: str,
        password: str,
        domain: str = "",
        port: int = 445,
        **kwargs,
    ):
        self.host = host
        self.share = share
        self.username = username
        self.password = password
        self.domain = domain
        self.port = port
        self._connected = False

    def _run_smb(self, *args) -> subprocess.CompletedProcess:
        cmd = [
            "smbclient",
            self.share,
            "--user", f"{self.domain}/{self.username}%{self.password}"
            if self.domain else f"{self.username}%{self.password}",
            "--port", str(self.port),
            "--connect-timeout", "10",
            "-c", ";".join(args),
        ]
        try:
            return subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError:
            raise RuntimeError(
                "smbclient binary not found. Install smbclient or use "
                "SMBStorageAdapterViaPython for pure-Python SMB."
            )

    def _smb_path(self, path: str) -> str:
        normalized = path.lstrip("/")
        return normalized.replace("/", "\\")

    def exists(self, path: str) -> bool:
        sp = self._smb_path(path)
        r = self._run_smb(f"stat \"{sp}\"")
        return r.returncode == 0

    def is_dir(self, path: str) -> bool:
        sp = self._smb_path(path)
        r = self._run_smb(f"stat \"{sp}\"", "quit")
        return "directory" in r.stdout.lower()

    def is_file(self, path: str) -> bool:
        return self.exists(path) and not self.is_dir(path)

    def list_dir(self, path: str = "") -> List[str]:
        sp = self._smb_path(path) if path else ""
        r = self._run_smb(f"cd \"{sp}\"", "ls", "quit")
        lines = r.stdout.strip().split("\n")
        names = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 2 and not line.startswith("\t"):
                name = parts[0].strip()
                if name and name not in (".", ".."):
                    names.append(name)
        return names

    def read_file(self, path: str) -> bytes:
        sp = self._smb_path(path)
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        try:
            r = self._run_smb(f"get \"{sp}\" \"{tmp_path.replace('\\', '/')}\"", "quit")
            if r.returncode != 0:
                raise FileNotFoundError(f"SMB read failed: {r.stderr}")
            with open(tmp_path, "rb") as f:
                return f.read()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def write_file(self, path: str, content: bytes) -> None:
        sp = self._smb_path(path)
        dir_part = str(Path(sp).parent).replace("\\", "/")
        file_part = Path(sp).name
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            r = self._run_smb(
                f"cd \"{dir_part}\"", f"put \"{tmp_path.replace('\\', '/')}\" \"{file_part}\"", "quit"
            )
            if r.returncode != 0:
                raise IOError(f"SMB write failed: {r.stderr}")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def delete(self, path: str, recursive: bool = False) -> bool:
        sp = self._smb_path(path)
        cmd = f"del \"{sp}\"" if not recursive else f"rmdir \"{sp}\""
        r = self._run_smb(cmd, "quit")
        return r.returncode == 0

    def mkdir(self, path: str) -> None:
        sp = self._smb_path(path)
        r = self._run_smb(f"mkdir \"{sp}\"", "quit")
        if r.returncode != 0 and "already exists" not in r.stderr.lower():
            raise IOError(f"SMB mkdir failed: {r.stderr}")

    def stat(self, path: str) -> Dict[str, Any]:
        sp = self._smb_path(path)
        r = self._run_smb(f"stat \"{sp}\"", "quit")
        # Parse output: blocks=1234 ... etc
        result: Dict[str, Any] = {"size": 0, "modified": 0, "type": "unknown"}
        for line in r.stdout.split("\n"):
            if "size" in line.lower():
                try:
                    result["size"] = int([p for p in line.split() if p.isdigit()][-1])
                except (IndexError, ValueError):
                    pass
            if "directory" in line.lower():
                result["type"] = "directory"
            elif "file" in line.lower():
                result["type"] = "file"
        return result

    def get_free_space(self) -> int:
        r = self._run_smb("quit")
        # smbclient doesn't expose dfs directly; probe with a large file trick
        return 0

    def get_total_space(self) -> int:
        return 0

    def get_used_space(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# NFS Storage Adapter
# ---------------------------------------------------------------------------

class NFSStorageAdapter(StorageAdapter):
    """
    Adapter for NFS mounts.
    Treats an already-mounted NFS path as local storage.
    For unmounted NFS, use nfs autodiscovery via /sbin/mount.nfs.
    """

    def __init__(self, mount_path: str, **kwargs):
        self.mount_path = Path(mount_path)
        if not self.mount_path.exists():
            raise ValueError(f"NFS mount path does not exist: {mount_path}")
        self._local = LocalStorageAdapter(str(self.mount_path))

    def exists(self, path: str) -> bool:
        return self._local.exists(path)

    def is_dir(self, path: str) -> bool:
        return self._local.is_dir(path)

    def is_file(self, path: str) -> bool:
        return self._local.is_file(path)

    def list_dir(self, path: str = "") -> List[str]:
        return self._local.list_dir(path)

    def read_file(self, path: str) -> bytes:
        return self._local.read_file(path)

    def write_file(self, path: str, content: bytes) -> None:
        self._local.write_file(path, content)

    def delete(self, path: str, recursive: bool = False) -> None:
        self._local.delete(path, recursive)

    def mkdir(self, path: str) -> None:
        self._local.mkdir(path)

    def stat(self, path: str) -> Dict[str, Any]:
        return self._local.stat(path)

    def get_free_space(self) -> int:
        return self._local.get_free_space()

    def get_total_space(self) -> int:
        return self._local.get_total_space()

    def get_used_space(self) -> int:
        return self._local.get_used_space()


# ---------------------------------------------------------------------------
# S3 Storage Adapter (MinIO / AWS S3 compatible)
# ---------------------------------------------------------------------------

class S3StorageAdapter(StorageAdapter):
    """
    Adapter for S3-compatible object storage (MinIO, AWS S3, etc.).

    Requires: pip install boto3
    """

    def __init__(
        self,
        endpoint: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
        secure: bool = True,
        prefix: str = "",
        **kwargs,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.bucket = bucket
        self.prefix = prefix.lstrip("/")
        self._secure = secure

        try:
            import boto3
        except ImportError:
            raise RuntimeError(
                "boto3 is required for S3/MinIO support. "
                "Install with: pip install boto3"
            )

        self._client = boto3.client(
            "s3",
            endpoint_url=f"{'https' if secure else 'http'}://{endpoint}",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )

    def _key(self, path: str) -> str:
        normalized = path.lstrip("/")
        if self.prefix:
            return f"{self.prefix}/{normalized}"
        return normalized

    def exists(self, path: str) -> bool:
        try:
            self._client.head_object(Bucket=self.bucket, Key=self._key(path))
            return True
        except Exception:
            return False

    def is_dir(self, path: str) -> bool:
        key = self._key(path)
        if not key.endswith("/"):
            key += "/"
        try:
            resp = self._client.list_objects_v2(Bucket=self.bucket, Prefix=key, MaxEntries=1)
            return bool(resp.get("Contents"))
        except Exception:
            return False

    def is_file(self, path: str) -> bool:
        return self.exists(path) and not self.is_dir(path)

    def list_dir(self, path: str = "") -> List[str]:
        prefix = self._key(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"
        try:
            resp = self._client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter="/")
            names = []
            for obj in resp.get("Contents", []):
                name = obj["Key"][len(prefix):]
                if name and "/" not in name:
                    names.append(name)
            for obj in resp.get("CommonPrefixes", []):
                name = obj["Prefix"][len(prefix):].rstrip("/")
                if name:
                    names.append(name)
            return sorted(names)
        except Exception:
            return []

    def read_file(self, path: str) -> bytes:
        try:
            resp = self._client.get_object(Bucket=self.bucket, Key=self._key(path))
            return resp["Body"].read()
        except Exception as e:
            raise FileNotFoundError(f"S3 read failed: {e}")

    def write_file(self, path: str, content: bytes) -> None:
        self._client.put_object(Bucket=self.bucket, Key=self._key(path), Body=content)

    def delete(self, path: str, recursive: bool = False) -> None:
        key = self._key(path)
        if recursive:
            resp = self._client.list_objects_v2(Bucket=self.bucket, Prefix=key)
            keys = [obj["Key"] for obj in resp.get("Contents", [])]
            if keys:
                self._client.delete_objects(
                    Bucket=self.bucket,
                    Delete={"Objects": [{"Key": k} for k in keys]}
                )
        else:
            self._client.delete_object(Bucket=self.bucket, Key=key)

    def mkdir(self, path: str) -> None:
        # S3 doesn't have directories, but we create a 0-byte marker
        key = self._key(path)
        if not key.endswith("/"):
            key += "/"
        self._client.put_object(Bucket=self.bucket, Key=key, Body=b"")

    def stat(self, path: str) -> Dict[str, Any]:
        try:
            resp = self._client.head_object(Bucket=self.bucket, Key=self._key(path))
            return {
                "size": resp.get("ContentLength", 0),
                "modified": resp["LastModified"].timestamp() if "LastModified" in resp else 0,
                "type": "directory" if self.is_dir(path) else "file",
                "mime": resp.get("ContentType"),
            }
        except Exception:
            return {"size": 0, "modified": 0, "type": "unknown"}

    def get_free_space(self) -> int:
        try:
            resp = self._client.list_objects_v2(Bucket=self.bucket, MaxEntries=1)
            # S3 doesn't report capacity; estimate from bucket size if available
            return 0
        except Exception:
            return 0

    def get_total_space(self) -> int:
        return 0

    def get_used_space(self) -> int:
        return 0


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_storage_adapter(
    protocol: str,
    base_path: str,
    **kwargs,
) -> StorageAdapter:
    """
    Factory to create a StorageAdapter by protocol.

    Parameters
    ----------
    protocol : str
        One of: local, smb, nfs, s3, minio
    base_path : str
        Protocol-specific connection string or path:
        - local: filesystem path
        - smb:  //host/share  (parsed from base_path)
        - nfs:  mount point path
        - s3:   bucket name (endpoint/credentials in kwargs)
        - minio: bucket name (same as s3, different defaults)

    Additional kwargs per protocol:
    - smb: host, share, username, password, domain, port
    - s3/minio: endpoint, bucket, access_key, secret_key, region, secure
    """
    protocol = protocol.lower()

    if protocol == "local":
        return LocalStorageAdapter(base_path, **kwargs)

    elif protocol == "smb":
        # base_path format: //HOST/share or host/share
        # Extract host/share from base_path if not in kwargs
        host = kwargs.get("host")
        share = kwargs.get("share")
        if not host or not share:
            # Try parsing from base_path: //host/share
            import re
            m = re.match(r"(?://)?([^/]+)/([^/]+)", base_path)
            if m:
                host, share = m.group(1), m.group(2)
            else:
                raise ValueError(
                    f"smb protocol requires host/share in base_path or kwargs. "
                    f"Got: base_path={base_path}"
                )
        return SMBStorageAdapter(
            host=host,
            share=f"//{host}/{share}",
            username=kwargs.get("username", "guest"),
            password=kwargs.get("password", ""),
            domain=kwargs.get("domain", ""),
            port=kwargs.get("port", 445),
        )

    elif protocol == "nfs":
        return NFSStorageAdapter(base_path, **kwargs)

    elif protocol in ("s3", "minio"):
        secure = kwargs.get("secure", protocol == "s3")
        return S3StorageAdapter(
            endpoint=kwargs.get("endpoint", "s3.amazonaws.com" if protocol == "s3" else base_path),
            bucket=base_path,  # bucket name IS the base_path for s3/minio
            access_key=kwargs.get("access_key", os.getenv("AWS_ACCESS_KEY_ID", "")),
            secret_key=kwargs.get("secret_key", os.getenv("AWS_SECRET_ACCESS_KEY", "")),
            region=kwargs.get("region", "us-east-1"),
            secure=secure,
            prefix=kwargs.get("prefix", ""),
        )

    else:
        raise ValueError(f"Unknown storage protocol: {protocol}")
