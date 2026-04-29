"""
Hermes File Manager - FastAPI Server (refactored)

Architecture:
  This file      → FastAPI app + thin HTTP route handlers
  services/      → Pure business logic (no FastAPI, no ORM coupling)
  api/dto.py    → Pydantic request/response models
  engine/       → StorageEngine, PermissionEngine, SQLAlchemy models

Route handlers are intentionally thin: they parse HTTP, call a service,
and return HTTP responses. All business logic lives in services/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add tools directory to path
_tools_dir = Path(__file__).parent.parent
if str(_tools_dir) not in sys.path:
    sys.path.insert(0, str(_tools_dir))

from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from file_manager.engine.models import init_db, create_builtin_roles, User, Role
from file_manager.engine.storage import StorageEngine
from file_manager.services import (
    AuthService, FileService, PermissionChecker, PermissionContext,
    EventBus, get_event_bus, AuditEventSubscriber,
)
from file_manager.api.dto import (
    LoginRequestDTO, RegisterRequestDTO, RefreshRequestDTO,
    LoginResponseDTO, UserResponseDTO,
    FileReadRequestDTO, FileWriteRequestDTO, FileDeleteRequestDTO,
    MkDirRequestDTO, FileCopyRequestDTO, FileMoveRequestDTO,
    CreateShareRequestDTO, CreateUserRequestDTO, AuditQueryRequestDTO,
    FileListResponseDTO, FileContentResponseDTO, FileStatResponseDTO,
    AuditLogEntryDTO, AuditQueryResponseDTO, UserListItemDTO,
    RoleDTO, UserListResponseDTO, MessageResponseDTO,
)
from file_manager.services.share_service import ShareService
from file_manager.services.admin_service import AdminService
from file_manager.api.auth import security, get_client_info


# ============================================================================
# App State / Global Store
# ============================================================================

_api_instances: dict = {}


# ============================================================================
# Configuration
# ============================================================================

def get_config() -> dict:
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
        "database_url": os.environ.get(
            "HFM_DATABASE_URL",
            config.get("database_url", "sqlite:///~/.hermes/file_manager/hfm.db"),
        ),
        "storage_root": os.environ.get(
            "HFM_STORAGE_ROOT",
            config.get("storage_root", "~/.hermes/file_manager/storage"),
        ),
        "jwt_secret": os.environ.get(
            "HFM_JWT_SECRET",
            config.get("jwt_secret", "change-me-in-production"),
        ),
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

@asynccontextmanager
async def lifespan(app: FastAPI):
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

    # Seed builtin roles + default admin
    session = db_factory()
    try:
        create_builtin_roles(session)
        admin_config = config.get("default_admin")
        if admin_config:
            existing = session.query(User).filter(User.username == admin_config["username"]).first()
            if not existing:
                admin_role = session.query(Role).filter(Role.name == "admin").first()
                if admin_role:
                    user = User(username=admin_config["username"], role_id=admin_role.id)
                    user.set_password(admin_config["password"])
                    session.add(user)
                    session.commit()
    finally:
        session.close()

    # Storage engine
    storage = StorageEngine(storage_root, permission_engine=None)  # Permission checks live in FileService layer

    # Event bus
    event_bus = get_event_bus()

    # Permission checker (pure logic)
    permission_checker = PermissionChecker(storage_root)

    # Services
    auth_service = AuthService(
        db_factory=db_factory,
        jwt_secret=config["jwt_secret"],
        event_bus=event_bus,
    )
    file_service = FileService(
        storage=storage,
        permission_checker=permission_checker,
        event_bus=event_bus,
    )
    share_service = ShareService(
        db_factory=db_factory,
        storage=storage,
        permission_checker=permission_checker,
        event_bus=event_bus,
    )
    admin_service = AdminService(
        db_factory=db_factory,
        event_bus=event_bus,
    )

    # Audit subscriber (consumes events → DB writes)
    audit_subscriber = AuditEventSubscriber(db_factory=db_factory, event_bus=event_bus)
    audit_subscriber.register()

    # Store in app state
    _api_instances["config"] = config
    _api_instances["db_factory"] = db_factory
    _api_instances["storage"] = storage
    _api_instances["auth_service"] = auth_service
    _api_instances["file_service"] = file_service
    _api_instances["share_service"] = share_service
    _api_instances["admin_service"] = admin_service
    _api_instances["permission_checker"] = permission_checker
    _api_instances["event_bus"] = event_bus

    # Mount static files
    _web_dir = str(Path(__file__).parent / "web")
    app.mount("/static", StaticFiles(directory=_web_dir), name="static")

    yield

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Service Access Helpers (FastAPI dependencies)
# ============================================================================

def get_auth_service() -> AuthService:
    return _api_instances.get("auth_service")

def get_file_service() -> FileService:
    return _api_instances.get("file_service")

def get_share_service() -> ShareService:
    return _api_instances.get("share_service")

def get_admin_service() -> AdminService:
    return _api_instances.get("admin_service")

def get_current_user_ctx(
    credentials = Depends(security),
) -> PermissionContext:
    """Return PermissionContext for the authenticated user."""
    auth_service = get_auth_service()
    if not auth_service:
        raise HTTPException(status_code=500, detail="Auth not configured")

    try:
        user = auth_service.get_user_from_token(credentials.credentials)
        return PermissionContext.from_authenticated_user(user)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============================================================================
# Health
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hermes-file-manager"}

@app.get("/")
async def root():
    return {"service": "Hermes File Manager", "version": "1.0.0", "docs": "/docs"}


# ============================================================================
# Auth Endpoints
# ============================================================================

@app.post("/api/v1/auth/login")
async def login(request: LoginRequestDTO, req: Request):
    from file_manager.api.middleware import LoginRateLimiter
    limiter = LoginRateLimiter()
    limiter.check_login_attempt(req)

    auth_service = get_auth_service()
    client_info = get_client_info(req)

    try:
        result = auth_service.authenticate(
            request,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )
        limiter.record_success(req)
        return LoginResponseDTO(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer",
            expires_in=result.expires_in,
            user=result.user.to_response(),
        ).model_dump()
    except ValueError as e:
        limiter.record_failed_attempt(req)
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/v1/auth/register")
async def register(request: RegisterRequestDTO, req: Request):
    auth_service = get_auth_service()
    client_info = get_client_info(req)

    try:
        user = auth_service.register(
            request,
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
        )
        return user.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/refresh")
async def refresh(request: RefreshRequestDTO):
    auth_service = get_auth_service()
    try:
        result = auth_service.refresh_tokens(request)
        return LoginResponseDTO(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
            token_type="bearer",
            expires_in=result.expires_in,
            user=result.user.to_response(),
        ).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/v1/auth/logout")
async def logout(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    auth_service = get_auth_service()
    auth_service.logout(user_ctx.user_id)
    return {"message": "Logged out"}


@app.get("/api/v1/auth/me")
async def get_me(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get current user info."""
    return {
        "id": user_ctx.user_id,
        "username": user_ctx.username,
        "role_name": user_ctx.role_name,
    }


# ============================================================================
# File Operation Endpoints
# ============================================================================

@app.get("/api/v1/files/list")
async def list_files(
    path: str = "",
    include_hidden: bool = False,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    req: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(req) if req else {}
    try:
        return file_service.list_directory(
            path=path,
            user_ctx=user_ctx,
            include_hidden=include_hidden,
            ip_address=client_info.get("ip_address"),
        ).model_dump()
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/read")
async def read_file(
    request: FileReadRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    req: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(req) if req else {}
    try:
        return file_service.read_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        ).model_dump()
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/write")
async def write_file(
    request: FileWriteRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    req: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(req) if req else {}
    try:
        return file_service.write_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/delete")
async def delete_file(
    request_body: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    body = await request_body.json()
    delete_req = FileDeleteRequestDTO(**body)
    try:
        return file_service.delete_file(
            request=delete_req,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/mkdir")
async def create_directory(
    request_body: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    body = await request_body.json()
    mkdir_req = MkDirRequestDTO(**body)
    try:
        return file_service.create_directory(
            request=mkdir_req,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
    except Exception as e:
        return _handle_service_error(e)


@app.get("/api/v1/files/stat")
async def get_stat(
    path: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    file_service = get_file_service()
    try:
        return file_service.get_stat(
            path=path,
            user_ctx=user_ctx,
        ).model_dump()
    except Exception as e:
        return _handle_service_error(e)


# ============================================================================
# Share Endpoints
# ============================================================================

@app.post("/api/v1/share")
async def create_share(
    request: CreateShareRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    req: Request = None,
):
    share_service = get_share_service()
    client_info = get_client_info(req) if req else {}
    try:
        return share_service.create_share_link(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
    except Exception as e:
        raise _handle_share_error(e)

@app.get("/api/v1/share/{token}")
async def get_share(token: str):
    share_service = get_share_service()
    try:
        return share_service.get_share_link(token=token)
    except Exception as e:
        raise _handle_share_error(e)

@app.get("/api/v1/share/{token}/content")
async def access_share_content(token: str, password: str = None, req: Request = None):
    share_service = get_share_service()
    client_info = get_client_info(req) if req else {}
    try:
        return share_service.access_share_content(
            token=token,
            password=password,
            ip_address=client_info.get("ip_address"),
        )
    except Exception as e:
        raise _handle_share_error(e)


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/api/v1/admin/users")
async def list_users(
    limit: int = 100,
    offset: int = 0,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    try:
        return admin_service.list_users(limit=limit, offset=offset, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)

@app.post("/api/v1/admin/users")
async def create_user(
    request_body: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    body = await request_body.json()
    create_req = CreateUserRequestDTO(**body)
    try:
        return admin_service.create_user(request=create_req, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)

@app.get("/api/v1/admin/roles")
async def list_roles(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    admin_service = get_admin_service()
    try:
        return admin_service.list_roles(user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)

@app.get("/api/v1/admin/audit")
async def query_audit(
    request: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    body = await request.json()
    query = AuditQueryRequestDTO(**body)
    try:
        return admin_service.query_audit_logs(query=query, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


# ============================================================================
# Error Handler
# ============================================================================

def _handle_service_error(e: Exception):
    """Map service-layer exceptions to HTTP responses."""
    from file_manager.services import FileAccessDenied, FileNotFound, FileAlreadyExists, DirectoryNotEmpty

    if isinstance(e, FileAccessDenied):
        raise HTTPException(status_code=403, detail=e.reason)
    if isinstance(e, FileNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, FileAlreadyExists):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, DirectoryNotEmpty):
        raise HTTPException(status_code=409, detail=str(e))
    # Re-raise unknown errors
    raise HTTPException(status_code=500, detail=str(e))


def _handle_share_error(e: Exception):
    """Map share service exceptions to HTTP responses."""
    from file_manager.services.share_service import ShareNotFound, ShareAccessDenied
    if isinstance(e, ShareNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, ShareAccessDenied):
        raise HTTPException(status_code=403, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


def _handle_admin_error(e: Exception):
    """Map admin service exceptions to HTTP responses."""
    from file_manager.services.admin_service import UserNotFound, RoleNotFound
    if isinstance(e, UserNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, RoleNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(app, host=config["host"], port=config["port"])
