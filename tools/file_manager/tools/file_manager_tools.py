"""
Hermes File Manager Tools - Integration with hermes-agent

Provides file management capabilities through the hermes-agent tool system.
Each tool operation is permission-checked via the HFM backend.
"""

import json
import os
from typing import Optional, Dict, Any, List

# Import HFM components
import sys
from pathlib import Path

# Add parent directory to path for imports
_tools_dir = Path(__file__).parent.parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from file_manager.engine.models import User, Role, PermissionRule, AuditAction
from file_manager.engine.permission import PermissionEngine, Operation
from file_manager.engine.storage import StorageEngine, FileNotFoundError, FileExistsError
from file_manager.engine.audit import AuditLogger


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_API_URL = os.environ.get("HFM_API_URL", "http://localhost:8080")
DEFAULT_API_KEY = os.environ.get("HFM_API_KEY", "")
DEFAULT_STORAGE_ROOT = os.environ.get(
    "HFM_STORAGE_ROOT",
    str(Path.home() / ".hermes" / "file_manager" / "storage")
)


# ============================================================================
# Tool Schemas
# ============================================================================

FILE_MANAGER_LIST_SCHEMA = {
    "name": "file_manager_list",
    "description": "List directory contents from the Hermes File Manager. Requires authentication.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to list (relative to storage root). Empty lists root.",
                "default": ""
            },
            "include_hidden": {
                "type": "boolean",
                "description": "Include hidden files (starting with .)",
                "default": False
            }
        }
    }
}

FILE_MANAGER_READ_SCHEMA = {
    "name": "file_manager_read",
    "description": "Read file contents from Hermes File Manager.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to read"
            },
            "offset": {
                "type": "integer",
                "description": "Byte offset to start reading from",
                "default": 0
            },
            "size": {
                "type": "integer",
                "description": "Maximum bytes to read",
                "default": None
            }
        },
        "required": ["path"]
    }
}

FILE_MANAGER_WRITE_SCHEMA = {
    "name": "file_manager_write",
    "description": "Write content to a file in Hermes File Manager.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "File path to write"
            },
            "content": {
                "type": "string",
                "description": "Content to write"
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite if file exists",
                "default": True
            }
        },
        "required": ["path", "content"]
    }
}

FILE_MANAGER_DELETE_SCHEMA = {
    "name": "file_manager_delete",
    "description": "Delete a file or directory from Hermes File Manager.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to delete"
            },
            "recursive": {
                "type": "boolean",
                "description": "Delete directories recursively",
                "default": False
            }
        },
        "required": ["path"]
    }
}

FILE_MANAGER_MKDIR_SCHEMA = {
    "name": "file_manager_mkdir",
    "description": "Create a directory in Hermes File Manager.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Directory path to create"
            }
        },
        "required": ["path"]
    }
}

FILE_MANAGER_MV_SCHEMA = {
    "name": "file_manager_mv",
    "description": "Move or rename a file or directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "from_path": {
                "type": "string",
                "description": "Source path"
            },
            "to_path": {
                "type": "string",
                "description": "Destination path"
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite destination if exists",
                "default": False
            }
        },
        "required": ["from_path", "to_path"]
    }
}

FILE_MANAGER_CP_SCHEMA = {
    "name": "file_manager_cp",
    "description": "Copy a file or directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "from_path": {
                "type": "string",
                "description": "Source path"
            },
            "to_path": {
                "type": "string",
                "description": "Destination path"
            },
            "overwrite": {
                "type": "boolean",
                "description": "Overwrite destination if exists",
                "default": False
            }
        },
        "required": ["from_path", "to_path"]
    }
}

FILE_MANAGER_STAT_SCHEMA = {
    "name": "file_manager_stat",
    "description": "Get file or directory metadata.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to get metadata for"
            }
        },
        "required": ["path"]
    }
}

FILE_MANAGER_SHARE_SCHEMA = {
    "name": "file_manager_share",
    "description": "Create a share link for a file or directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to share"
            },
            "password": {
                "type": "string",
                "description": "Optional password protection",
                "default": None
            },
            "permissions": {
                "type": "string",
                "description": "read or read_write",
                "default": "read"
            },
            "expires_in_days": {
                "type": "integer",
                "description": "Days until link expires",
                "default": 7
            }
        },
        "required": ["path"]
    }
}

FILE_MANAGER_LOGIN_SCHEMA = {
    "name": "file_manager_login",
    "description": "Login to Hermes File Manager and store credentials for subsequent operations.",
    "parameters": {
        "type": "object",
        "properties": {
            "username": {
                "type": "string",
                "description": "Username"
            },
            "password": {
                "type": "string",
                "description": "Password"
            }
        },
        "required": ["username", "password"]
    }
}

FILE_MANAGER_LOGOUT_SCHEMA = {
    "name": "file_manager_logout",
    "description": "Logout from Hermes File Manager and clear stored credentials.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}


# ============================================================================
# Session State
# ============================================================================

# Global session state (in-memory for tool context)
# In production, this would be persisted or managed by the agent
_session_store: Dict[str, Any] = {}


def _get_session() -> Dict[str, Any]:
    """Get or create the HFM session state"""
    return _session_store


def _clear_session():
    """Clear HFM session state"""
    _session_store.clear()


def _tool_error(message: str) -> str:
    """Format tool error response"""
    return json.dumps({"error": message})


def _tool_success(data: Any) -> str:
    """Format tool success response"""
    return json.dumps(data, indent=2)


# ============================================================================
# Direct Engine Mode (bypasses HTTP API for local operations)
# ============================================================================

class DirectEngine:
    """
    Direct access to HFM engine without HTTP
    
    Used when HFM server is not running or for local operations.
    Credentials are stored in the session.
    """
    
    def __init__(self, storage_root: str, db_session_factory):
        self.storage_root = storage_root
        self.db_factory = db_session_factory
        self.permission_engine = PermissionEngine(storage_root)
        self.storage = StorageEngine(storage_root, self.permission_engine)
        self._current_user: Optional[User] = None
    
    def set_user(self, user: User):
        self._current_user = user
    
    def _check_permission(self, operation: Operation, path: str) -> bool:
        """Check if current user has permission for operation on path"""
        if not self._current_user or not self._current_user.role:
            return False
        
        decision = self.permission_engine.check_permission(
            self._current_user,
            operation,
            path,
            list(self._current_user.role.permission_rules)
        )
        return decision.allowed
    
    def list(self, path: str = "", include_hidden: bool = False) -> List[Dict[str, Any]]:
        """List directory"""
        if not self._check_permission(Operation.LIST, path):
            return [{"error": "Permission denied"}]
        
        try:
            return self.storage.list_directory(path, include_hidden=include_hidden)
        except FileNotFoundError as e:
            return [{"error": str(e)}]
    
    def read(self, path: str, offset: int = 0, size: Optional[int] = None) -> Dict[str, Any]:
        """Read file"""
        if not self._check_permission(Operation.READ, path):
            return {"error": "Permission denied"}
        
        try:
            content = self.storage.read_file(path, offset=offset, size=size)
            return {"path": path, "content": content, "size": len(content)}
        except FileNotFoundError as e:
            return {"error": str(e)}
    
    def write(self, path: str, content: str, overwrite: bool = True) -> Dict[str, Any]:
        """Write file"""
        if not self._check_permission(Operation.WRITE, path):
            return {"error": "Permission denied"}
        
        try:
            result = self.storage.write_file(path, content, overwrite=overwrite)
            return result
        except FileExistsError as e:
            return {"error": str(e)}
    
    def delete(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """Delete file/directory"""
        if not self._check_permission(Operation.DELETE, path):
            return {"error": "Permission denied"}
        
        try:
            self.storage.delete_path(path, recursive=recursive)
            return {"message": f"Deleted: {path}"}
        except FileNotFoundError as e:
            return {"error": str(e)}
    
    def mkdir(self, path: str) -> Dict[str, Any]:
        """Create directory"""
        if not self._check_permission(Operation.WRITE, path):
            return {"error": "Permission denied"}
        
        try:
            return self.storage.create_directory(path)
        except FileExistsError as e:
            return {"error": str(e)}
    
    def mv(self, from_path: str, to_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """Move file/directory"""
        if not self._check_permission(Operation.DELETE, from_path):
            return {"error": "Permission denied"}
        if not self._check_permission(Operation.WRITE, to_path):
            return {"error": "Permission denied"}
        
        try:
            return self.storage.move_file(from_path, to_path, overwrite=overwrite)
        except (FileNotFoundError, FileExistsError) as e:
            return {"error": str(e)}
    
    def cp(self, from_path: str, to_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """Copy file/directory"""
        if not self._check_permission(Operation.READ, from_path):
            return {"error": "Permission denied"}
        if not self._check_permission(Operation.WRITE, to_path):
            return {"error": "Permission denied"}
        
        try:
            return self.storage.copy_file(from_path, to_path, overwrite=overwrite)
        except (FileNotFoundError, FileExistsError) as e:
            return {"error": str(e)}
    
    def stat(self, path: str) -> Dict[str, Any]:
        """Get metadata"""
        if not self._check_permission(Operation.READ, path):
            return {"error": "Permission denied"}
        
        try:
            return self.storage.get_stat(path)
        except FileNotFoundError as e:
            return {"error": str(e)}


# ============================================================================
# HTTP API Mode
# ============================================================================

import httpx


class HTTPEngine:
    """
    HTTP client for remote HFM server
    
    Used when HFM server is running and accessible via HTTP.
    """
    
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self._token: Optional[str] = None
    
    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
    ) -> Dict:
        """Make HTTP request to HFM server"""
        url = f"{self.api_url}{endpoint}"
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=self._headers())
            elif method == "POST":
                response = await client.post(url, json=data, headers=self._headers())
            elif method == "PUT":
                response = await client.put(url, json=data, headers=self._headers())
            elif method == "DELETE":
                response = await client.delete(url, headers=self._headers())
            else:
                return {"error": f"Unknown method: {method}"}
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                return {"error": error_data.get("detail", str(response.status_code))}
            except:
                return {"error": str(response.status_code)}
        
        return response.json()
    
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and store token"""
        result = await self._request("POST", "/api/v1/auth/login", {
            "username": username,
            "password": password
        })
        
        if "access_token" in result:
            self._token = result["access_token"]
        
        return result
    
    async def logout(self) -> Dict[str, Any]:
        """Logout and clear token"""
        result = await self._request("POST", "/api/v1/auth/logout")
        self._token = None
        return result
    
    async def list(self, path: str = "", include_hidden: bool = False) -> List[Dict]:
        """List directory"""
        params = f"?path={path}&include_hidden={include_hidden}"
        result = await self._request("GET", f"/api/v1/files/list{params}")
        
        if isinstance(result, list):
            return result
        return [result]
    
    async def read(self, path: str, offset: int = 0, size: Optional[int] = None) -> Dict:
        """Read file"""
        return await self._request("POST", "/api/v1/files/read", {
            "path": path,
            "offset": offset,
            "size": size
        })
    
    async def write(self, path: str, content: str, overwrite: bool = True) -> Dict:
        """Write file"""
        return await self._request("POST", "/api/v1/files/write", {
            "path": path,
            "content": content,
            "overwrite": overwrite
        })
    
    async def delete(self, path: str, recursive: bool = False) -> Dict:
        """Delete file/directory"""
        return await self._request("POST", "/api/v1/files/delete", {
            "path": path,
            "recursive": recursive
        })
    
    async def mkdir(self, path: str) -> Dict:
        """Create directory"""
        return await self._request("POST", "/api/v1/files/mkdir", {
            "path": path
        })
    
    async def mv(self, from_path: str, to_path: str, overwrite: bool = False) -> Dict:
        """Move file/directory"""
        return await self._request("POST", "/api/v1/files/move", {
            "from": from_path,
            "to": to_path,
            "overwrite": overwrite
        })
    
    async def cp(self, from_path: str, to_path: str, overwrite: bool = False) -> Dict:
        """Copy file/directory"""
        return await self._request("POST", "/api/v1/files/copy", {
            "from": from_path,
            "to": to_path,
            "overwrite": overwrite
        })
    
    async def stat(self, path: str) -> Dict:
        """Get metadata"""
        params = f"?path={path}"
        return await self._request("GET", f"/api/v1/files/stat{params}")
    
    async def share(self, path: str, password: Optional[str] = None,
                   permissions: str = "read", expires_in_days: int = 7) -> Dict:
        """Create share link"""
        return await self._request("POST", "/api/v1/share", {
            "path": path,
            "password": password,
            "permissions": permissions,
            "expires_in_days": expires_in_days
        })


# ============================================================================
# Tool Functions
# ============================================================================

def file_manager_list(path: str = "", include_hidden: bool = False, **kwargs) -> str:
    """List directory contents"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.list(path, include_hidden))
        else:
            result = engine.list(path, include_hidden)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"List failed: {e}")


def file_manager_read(path: str, offset: int = 0, size: Optional[int] = None, **kwargs) -> str:
    """Read file contents"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.read(path, offset, size))
        else:
            result = engine.read(path, offset, size)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Read failed: {e}")


def file_manager_write(path: str, content: str, overwrite: bool = True, **kwargs) -> str:
    """Write file"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.write(path, content, overwrite))
        else:
            result = engine.write(path, content, overwrite)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Write failed: {e}")


def file_manager_delete(path: str, recursive: bool = False, **kwargs) -> str:
    """Delete file or directory"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.delete(path, recursive))
        else:
            result = engine.delete(path, recursive)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Delete failed: {e}")


def file_manager_mkdir(path: str, **kwargs) -> str:
    """Create directory"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.mkdir(path))
        else:
            result = engine.mkdir(path)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Mkdir failed: {e}")


def file_manager_mv(from_path: str, to_path: str, overwrite: bool = False, **kwargs) -> str:
    """Move/rename file or directory"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.mv(from_path, to_path, overwrite))
        else:
            result = engine.mv(from_path, to_path, overwrite)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Move failed: {e}")


def file_manager_cp(from_path: str, to_path: str, overwrite: bool = False, **kwargs) -> str:
    """Copy file or directory"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.cp(from_path, to_path, overwrite))
        else:
            result = engine.cp(from_path, to_path, overwrite)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Copy failed: {e}")


def file_manager_stat(path: str, **kwargs) -> str:
    """Get file/directory metadata"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            result = asyncio.run(engine.stat(path))
        else:
            result = engine.stat(path)
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Stat failed: {e}")


def file_manager_share(
    path: str,
    password: Optional[str] = None,
    permissions: str = "read",
    expires_in_days: int = 7,
    **kwargs
) -> str:
    """Create share link for a file/directory"""
    session = _get_session()
    
    engine = session.get("engine")
    if not engine:
        return _tool_error("Not logged in. Use file_manager_login first.")
    
    if not isinstance(engine, HTTPEngine):
        return _tool_error("Share links require HTTP API mode")
    
    try:
        import asyncio
        result = asyncio.run(engine.share(path, password, permissions, expires_in_days))
        
        if "token" in result:
            share_url = f"{engine.api_url}/s/{result['token']}"
            result["share_url"] = share_url
        
        return _tool_success(result)
    except Exception as e:
        return _tool_error(f"Share failed: {e}")


def file_manager_login(username: str, password: str, **kwargs) -> str:
    """Login to Hermes File Manager"""
    session = _get_session()
    
    api_url = os.environ.get("HFM_API_URL", DEFAULT_API_URL)
    use_http = os.environ.get("HFM_USE_HTTP", "true").lower() == "true"
    
    try:
        if use_http:
            engine = HTTPEngine(api_url, os.environ.get("HFM_API_KEY", ""))
            import asyncio
            result = asyncio.run(engine.login(username, password))
            
            if "access_token" in result:
                session["engine"] = engine
                session["user"] = result.get("user", {})
                return _tool_success({
                    "message": "Logged in successfully",
                    "user": result.get("user", {}).get("username"),
                    "mode": "http"
                })
            else:
                return _tool_error(f"Login failed: {result.get('error', 'Unknown error')}")
        else:
            # Direct mode - need db_session_factory
            from file_manager.engine.models import init_db, create_builtin_roles
            from sqlalchemy.orm import Session
            
            db_factory = init_db(os.environ.get("HFM_DATABASE_URL", "sqlite:///~/.hermes/file_manager/hfm.db"))
            session_db = db_factory()
            
            try:
                from file_manager.engine.models import User
                user = session_db.query(User).filter(User.username == username).first()
                
                if not user or not user.check_password(password):
                    return _tool_error("Invalid username or password")
                
                if not user.is_active:
                    return _tool_error("Account is disabled")
                
                engine = DirectEngine(
                    os.environ.get("HFM_STORAGE_ROOT", DEFAULT_STORAGE_ROOT),
                    db_factory
                )
                engine.set_user(user)
                
                session["engine"] = engine
                session["user"] = user.to_dict()
                
                return _tool_success({
                    "message": "Logged in successfully",
                    "user": user.username,
                    "role": user.role.name if user.role else None,
                    "mode": "direct"
                })
            finally:
                session_db.close()
    except Exception as e:
        return _tool_error(f"Login failed: {e}")


def file_manager_logout(**kwargs) -> str:
    """Logout from Hermes File Manager"""
    session = _get_session()
    
    engine = session.get("engine")
    
    try:
        if isinstance(engine, HTTPEngine):
            import asyncio
            asyncio.run(engine.logout())
    except:
        pass
    
    _clear_session()
    
    return _tool_success({"message": "Logged out successfully"})


# ============================================================================
# Registry Registration
# ============================================================================

def check_file_manager_requirements() -> bool:
    """Check if file_manager tool dependencies are available"""
    try:
        import httpx
        return True
    except ImportError:
        return False


from tools.registry import registry

# Register all tools
registry.register(
    name="file_manager_login",
    toolset="file-manager",
    schema=FILE_MANAGER_LOGIN_SCHEMA,
    handler=lambda args, **kw: file_manager_login(
        username=args.get("username", ""),
        password=args.get("password", ""),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="🔐",
)

registry.register(
    name="file_manager_logout",
    toolset="file-manager",
    schema=FILE_MANAGER_LOGOUT_SCHEMA,
    handler=lambda args, **kw: file_manager_logout(**kw),
    check_fn=check_file_manager_requirements,
    emoji="🔒",
)

registry.register(
    name="file_manager_list",
    toolset="file-manager",
    schema=FILE_MANAGER_LIST_SCHEMA,
    handler=lambda args, **kw: file_manager_list(
        path=args.get("path", ""),
        include_hidden=args.get("include_hidden", False),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="📁",
)

registry.register(
    name="file_manager_read",
    toolset="file-manager",
    schema=FILE_MANAGER_READ_SCHEMA,
    handler=lambda args, **kw: file_manager_read(
        path=args.get("path", ""),
        offset=args.get("offset", 0),
        size=args.get("size"),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="📄",
)

registry.register(
    name="file_manager_write",
    toolset="file-manager",
    schema=FILE_MANAGER_WRITE_SCHEMA,
    handler=lambda args, **kw: file_manager_write(
        path=args.get("path", ""),
        content=args.get("content", ""),
        overwrite=args.get("overwrite", True),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="✏️",
)

registry.register(
    name="file_manager_delete",
    toolset="file-manager",
    schema=FILE_MANAGER_DELETE_SCHEMA,
    handler=lambda args, **kw: file_manager_delete(
        path=args.get("path", ""),
        recursive=args.get("recursive", False),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="🗑️",
)

registry.register(
    name="file_manager_mkdir",
    toolset="file-manager",
    schema=FILE_MANAGER_MKDIR_SCHEMA,
    handler=lambda args, **kw: file_manager_mkdir(
        path=args.get("path", ""),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="📂",
)

registry.register(
    name="file_manager_mv",
    toolset="file-manager",
    schema=FILE_MANAGER_MV_SCHEMA,
    handler=lambda args, **kw: file_manager_mv(
        from_path=args.get("from_path", ""),
        to_path=args.get("to_path", ""),
        overwrite=args.get("overwrite", False),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="➡️",
)

registry.register(
    name="file_manager_cp",
    toolset="file-manager",
    schema=FILE_MANAGER_CP_SCHEMA,
    handler=lambda args, **kw: file_manager_cp(
        from_path=args.get("from_path", ""),
        to_path=args.get("to_path", ""),
        overwrite=args.get("overwrite", False),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="📋",
)

registry.register(
    name="file_manager_stat",
    toolset="file-manager",
    schema=FILE_MANAGER_STAT_SCHEMA,
    handler=lambda args, **kw: file_manager_stat(
        path=args.get("path", ""),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="📊",
)

registry.register(
    name="file_manager_share",
    toolset="file-manager",
    schema=FILE_MANAGER_SHARE_SCHEMA,
    handler=lambda args, **kw: file_manager_share(
        path=args.get("path", ""),
        password=args.get("password"),
        permissions=args.get("permissions", "read"),
        expires_in_days=args.get("expires_in_days", 7),
        **kw
    ),
    check_fn=check_file_manager_requirements,
    emoji="🔗",
)
