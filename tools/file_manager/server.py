"""
Hermes File Manager - FastAPI Server

Entry point for running HFM as a standalone REST API server.
"""

import os
import sys
from pathlib import Path

# Add tools directory to path
_tools_dir = Path(__file__).parent.parent  # tools/
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from file_manager.api.auth import (
    AuthAPI, JWTManager, LoginRequest, RegisterRequest,
    RefreshRequest, get_current_user, get_client_info, jwt_required
)
from file_manager.api.files import FilesAPI, FileReadRequest, FileWriteRequest
from file_manager.api.admin import AdminAPI
from file_manager.api.share import ShareAPI, CreateShareRequest
from file_manager.api.middleware import RateLimiter, LoginRateLimiter, setup_middleware
from file_manager.engine.models import init_db, create_builtin_roles, User, Role
from file_manager.engine.permission import PermissionEngine
from file_manager.engine.storage import StorageEngine


# ============================================================================
# Configuration
# ============================================================================

def get_config():
    # Try to load from Hermes config.yaml first
    config = {}
    try:
        import yaml
        config_path = Path.home() / ".hermes" / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                hermes_cfg = yaml.safe_load(f) or {}
            fm_cfg = hermes_cfg.get("file_manager", {})
            config["database_url"] = fm_cfg.get("database_url", "")
            config["storage_root"] = fm_cfg.get("storage_root", "")
            config["jwt_secret"] = fm_cfg.get("jwt_secret", "")
            config["default_admin"] = fm_cfg.get("default_admin", {})
    except Exception:
        pass

    return {
        "database_url": os.environ.get("HFM_DATABASE_URL", config.get("database_url", "sqlite:///~/.hermes/file_manager/hfm.db")),
        "storage_root": os.environ.get("HFM_STORAGE_ROOT", config.get("storage_root", "~/.hermes/file_manager/storage")),
        "jwt_secret": os.environ.get("HFM_JWT_SECRET", config.get("jwt_secret", "change-me-in-production")),
        "port": int(os.environ.get("HFM_PORT", "8080")),
        "host": os.environ.get("HFM_HOST", "0.0.0.0"),
        "default_admin": config.get("default_admin") or {
            "username": os.environ.get("HFM_ADMIN_USER", "admin"),
            "password": os.environ.get("HFM_ADMIN_PASS", "admin123"),
        },
    }


# ============================================================================
# Lifespan
# ============================================================================

_api_instances = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    config = get_config()
    
    # Expand storage path
    storage_root = os.path.expanduser(config["storage_root"])
    
    # Initialize database
    db_url = config["database_url"]
    if db_url.startswith("sqlite:///"):
        db_path = os.path.expanduser(db_url.replace("sqlite:///", ""))
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_url = f"sqlite:///{db_path}"
    
    db_factory = init_db(db_url)
    
    # Create builtin roles
    session = db_factory()
    try:
        create_builtin_roles(session)

        # Create default admin user if none exists
        admin_config = config.get("default_admin")
        if admin_config:
            existing_admin = session.query(User).filter(User.username == admin_config["username"]).first()
            if not existing_admin:
                admin_role = session.query(Role).filter(Role.name == "admin").first()
                if admin_role:
                    user = User(
                        username=admin_config["username"],
                        role_id=admin_role.id,
                    )
                    user.set_password(admin_config["password"])
                    session.add(user)
                    session.commit()
    finally:
        session.close()
    
    # Initialize permission engine
    permission_engine = PermissionEngine(storage_root)
    
    # Initialize storage engine
    storage = StorageEngine(storage_root, permission_engine)
    
    # Initialize JWT manager
    jwt_manager = JWTManager(config["jwt_secret"], db_factory)
    
    # Initialize API handlers
    auth_api = AuthAPI(jwt_manager, db_factory)
    files_api = FilesAPI(storage, db_factory)
    admin_api = AdminAPI(db_factory)
    share_api = ShareAPI(db_factory, storage)
    
    # Store in app state
    _api_instances["config"] = config
    _api_instances["db_factory"] = db_factory
    _api_instances["jwt_manager"] = jwt_manager
    _api_instances["storage"] = storage
    _api_instances["auth"] = auth_api
    _api_instances["files"] = files_api
    _api_instances["admin"] = admin_api
    _api_instances["share"] = share_api
    
    # Mount static files from web/ directory (relative to server.py location)
    _web_dir = str(Path(__file__).parent / "web")
    app.mount('/static', StaticFiles(directory=_web_dir), name='static')
    
    yield
    
    # Cleanup
    _api_instances.clear()


# ============================================================================
# FastAPI App
# ============================================================================

app = FastAPI(
    title="Hermes File Manager API",
    description="Team collaboration file management with RBAC permissions",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hermes-file-manager"}


@app.get("/")
async def root():
    return {
        "service": "Hermes File Manager",
        "version": "1.0.0",
        "docs": "/docs",
    }


# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/api/v1/auth/login")
async def login(request: LoginRequest, req: Request):
    """Authenticate and get tokens"""
    limiter = LoginRateLimiter()
    limiter.check_login_attempt(req)
    
    client_info = get_client_info(req)
    
    try:
        auth = _api_instances["auth"]
        result = auth.login(
            request,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )
        limiter.record_success(req)
        return result
    except HTTPException:
        limiter.record_failed_attempt(req)
        raise


@app.post("/api/v1/auth/register")
async def register(request: RegisterRequest, req: Request):
    """Register new user (admin only in production)"""
    auth = _api_instances["auth"]
    client_info = get_client_info(req)
    
    # In production, require admin auth
    return auth.register(
        request,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
    )


@app.post("/api/v1/auth/refresh")
async def refresh(request: RefreshRequest):
    """Refresh access token"""
    auth = _api_instances["auth"]
    return auth.refresh(request)


@app.post("/api/v1/auth/logout")
async def logout(user: User = Depends(get_current_user)):
    """Logout (requires auth)"""
    return {"message": "Logged out"}


@app.get("/api/v1/auth/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info"""
    # user.role lazy-loads from a detached session; re-fetch role safely
    db_factory = _api_instances.get("db_factory")
    role_name = None
    if db_factory and user.role_id:
        session = db_factory()
        try:
            role = session.query(Role).filter(Role.id == user.role_id).first()
            role_name = role.name if role else None
        finally:
            session.close()
    data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role_id": user.role_id,
        "role_name": role_name,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }
    return data


# ============================================================================
# File Operation Endpoints
# ============================================================================

@app.get("/api/v1/files/list")
async def list_files(
    path: str = "",
    include_hidden: bool = False,
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """List directory contents"""
    files = _api_instances["files"]
    client_info = get_client_info(req)
    
    return files.list_directory(
        path=path,
        user=user,
        include_hidden=include_hidden,
        ip_address=client_info["ip_address"],
    )


@app.post("/api/v1/files/read")
async def read_file(
    request: FileReadRequest,
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """Read file contents"""
    files = _api_instances["files"]
    client_info = get_client_info(req)
    
    return files.read_file(
        request,
        user=user,
        ip_address=client_info["ip_address"],
    )


@app.post("/api/v1/files/write")
async def write_file(
    request: FileWriteRequest,
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """Write file"""
    files = _api_instances["files"]
    client_info = get_client_info(req)
    
    return files.write_file(
        request,
        user=user,
        ip_address=client_info["ip_address"],
    )


@app.post("/api/v1/files/delete")
async def delete_file(
    request_body: Request,  # FileDeleteRequest
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """Delete file or directory"""
    from pydantic import BaseModel
    
    class FileDeleteRequest(BaseModel):
        path: str
        recursive: bool = False
    
    body = await request_body.json()
    delete_request = FileDeleteRequest(**body)
    
    files = _api_instances["files"]
    client_info = get_client_info(req)
    
    return files.delete_file(
        delete_request,
        user=user,
        ip_address=client_info["ip_address"],
    )


@app.post("/api/v1/files/mkdir")
async def create_directory(
    request_body: Request,
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """Create directory"""
    from pydantic import BaseModel
    
    class MkDirRequest(BaseModel):
        path: str
    
    body = await request_body.json()
    mkdir_request = MkDirRequest(**body)
    
    files = _api_instances["files"]
    client_info = get_client_info(req)
    
    return files.create_directory(
        mkdir_request,
        user=user,
        ip_address=client_info["ip_address"],
    )


@app.get("/api/v1/files/stat")
async def get_stat(
    path: str,
    user: User = Depends(get_current_user),
):
    """Get file/directory metadata"""
    files = _api_instances["files"]
    return files.get_stat(path=path, user=user)


# ============================================================================
# Share Endpoints
# ============================================================================

@app.post("/api/v1/share")
async def create_share(
    request: CreateShareRequest,
    user: User = Depends(get_current_user),
    req: Request = None,
):
    """Create share link"""
    share = _api_instances["share"]
    client_info = get_client_info(req)
    
    return share.create_share_link(
        request,
        user=user,
        ip_address=client_info["ip_address"],
    )


@app.get("/api/v1/share/{token}")
async def get_share(token: str):
    """Get share link info"""
    share = _api_instances["share"]
    return share.get_share_link(token)


@app.get("/api/v1/share/{token}/content")
async def access_share_content(
    token: str,
    password: str = None,
    req: Request = None,
):
    """Access share link content"""
    share = _api_instances["share"]
    client_info = get_client_info(req) if req else {}
    
    return share.access_share_content(
        token=token,
        password=password,
        ip_address=client_info.get("ip_address"),
    )


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/api/v1/admin/users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_user),
):
    """List all users (admin only)"""
    admin = _api_instances["admin"]
    return admin.list_users(user, limit=limit, offset=offset)


@app.post("/api/v1/admin/users")
async def create_user(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Create user (admin only)"""
    from pydantic import BaseModel
    
    class CreateUserRequest(BaseModel):
        username: str
        password: str
        email: str = None
        role_id: str = None
    
    body = await req.json()
    create_request = CreateUserRequest(**body)
    
    admin = _api_instances["admin"]
    return admin.create_user(create_request, user)


@app.get("/api/v1/admin/roles")
async def list_roles(user: User = Depends(get_current_user)):
    """List all roles"""
    admin = _api_instances["admin"]
    return admin.list_roles(user)


@app.get("/api/v1/admin/audit")
async def query_audit(
    request: Request,
    user: User = Depends(get_current_user),
):
    """Query audit logs"""
    from pydantic import BaseModel
    from datetime import datetime
    
    class AuditQueryRequest(BaseModel):
        user_id: str = None
        action: str = None
        path: str = None
        result: str = None
        start_date: str = None
        end_date: str = None
        limit: int = 100
        offset: int = 0
    
    body = await req.json()
    query = AuditQueryRequest(**body)
    
    admin = _api_instances["admin"]
    return admin.query_audit_logs(query, user)


# ============================================================================
# Main
# ============================================================================

def main():
    import uvicorn
    
    config = get_config()
    
    print(f"Starting Hermes File Manager on {config['host']}:{config['port']}")
    print(f"Storage root: {config['storage_root']}")
    print(f"Database: {config['database_url']}")
    
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
    )


if __name__ == "__main__":
    main()
