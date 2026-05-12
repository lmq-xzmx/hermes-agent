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
import logging

logger = logging.getLogger(__name__)

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from file_manager.engine.models import init_db, create_builtin_roles, User, Role
from file_manager.engine.storage import StorageEngine
from file_manager.services import (
    AuthService, FileService, PermissionChecker, PermissionContext,
    EventBus, get_event_bus, AuditEventSubscriber,
)
from file_manager.services.file_lock_service import FileLockService
from file_manager.services.collaboration_service import CollaborationService
from file_manager.services.trash_service import TrashService
from file_manager.api.dto import (
    LoginRequestDTO, RegisterRequestDTO, RefreshRequestDTO,
    LoginResponseDTO, UserResponseDTO,
    FileReadRequestDTO, FileWriteRequestDTO, FileDeleteRequestDTO,
    MkDirRequestDTO, FileCopyRequestDTO, FileMoveRequestDTO,
    CreateShareRequestDTO, CreateUserRequestDTO, CreateRuleRequestDTO, AuditQueryRequestDTO,
    FileListResponseDTO, FileContentResponseDTO, FileStatResponseDTO,
    AuditLogEntryDTO, AuditQueryResponseDTO, UserListItemDTO,
    RoleDTO, UserListResponseDTO, MessageResponseDTO,
)
from file_manager.api.webhook import (
    init_publisher, shutdown_publisher, publish_file_event,
    EventType, get_publisher
)
from file_manager.api.auth import security, get_client_info
from file_manager.services.share_service import ShareService
from file_manager.services.admin_service import AdminService
from file_manager.services.admin_analytics_service import AdminAnalyticsService
from file_manager.services.team_service import TeamService
from file_manager.services.space_service import SpaceService
from file_manager.services.workflow_service import WorkflowService
from file_manager.services.notebook_service import NotebookService
from file_manager.services.approval_service import ApprovalService
from file_manager.services.storage_pool_service import StoragePoolService
from file_manager.services.quota_transfer_service import QuotaTransferService
from file_manager.services.capacity_alert_service import CapacityAlertService
from file_manager.services.space_lifecycle_service import SpaceLifecycleService
from file_manager.services.resource_plan_service import ResourcePlanService
from file_manager.services.config_service import ConfigService


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
        db_factory=db_factory,
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
    admin_analytics_service = AdminAnalyticsService(
        db_factory=db_factory,
        event_bus=event_bus,
    )
    team_service = TeamService(db_factory=db_factory)
    space_service = SpaceService(db_factory=db_factory)
    workflow_service = WorkflowService(db_factory=db_factory)
    notebook_service = NotebookService(db_factory=db_factory)
    file_lock_service = FileLockService(db_factory=db_factory)
    collaboration_service = CollaborationService(db_factory=db_factory)
    approval_service = ApprovalService(db_factory=db_factory)
    storage_pool_service = StoragePoolService(db_factory=db_factory)
    quota_transfer_service = QuotaTransferService(db_factory=db_factory)
    capacity_alert_service = CapacityAlertService(db_factory=db_factory)
    space_lifecycle_service = SpaceLifecycleService(db_factory=db_factory)
    resource_plan_service = ResourcePlanService(db_factory=db_factory)
    config_service = ConfigService(db_factory=db_factory)

    # Start file lock cleanup background thread
    file_lock_service.start_cleanup_thread(interval_seconds=300)

    # Start trash purge scheduler (runs every 24 hours)
    trash_service = TrashService(db_factory, storage, storage_root)
    TrashService.start_scheduler(db_factory, storage, interval_hours=24)
    logger.info("TrashService scheduler started")

    # Ensure default pool exists
    team_service.ensure_default_pool()

    # Register all existing pools in FileService
    pools_data = team_service.list_pools()
    for pool in pools_data.get("pools", []):
        if pool.get("is_active", True):
            pool_storage = StorageEngine(pool["base_path"])
            file_service.register_pool(pool["pool_id"], pool_storage)

    # Audit subscriber (consumes events → DB writes)
    audit_subscriber = AuditEventSubscriber(db_factory=db_factory, event_bus=event_bus)
    audit_subscriber.register()

    # Initialize AnalyticsBroadcaster for WebSocket real-time updates
    from file_manager.api.analytics_ws import AnalyticsBroadcaster, get_connection_manager
    connection_manager = get_connection_manager()
    analytics_broadcaster = AnalyticsBroadcaster(
        manager=connection_manager,
        db_factory=db_factory,
        event_bus=event_bus
    )
    await analytics_broadcaster.start()
    logger.info("AnalyticsBroadcaster started")

    # Store in app state
    _api_instances["config"] = config
    _api_instances["db_factory"] = db_factory
    _api_instances["storage"] = storage
    _api_instances["auth_service"] = auth_service
    _api_instances["file_service"] = file_service
    _api_instances["share_service"] = share_service
    _api_instances["admin_service"] = admin_service
    _api_instances["admin_analytics_service"] = admin_analytics_service
    _api_instances["team_service"] = team_service
    _api_instances["space_service"] = space_service
    _api_instances["workflow_service"] = workflow_service
    _api_instances["notebook_service"] = notebook_service
    _api_instances["file_lock_service"] = file_lock_service
    _api_instances["collaboration_service"] = collaboration_service
    _api_instances["approval_service"] = approval_service
    _api_instances["storage_pool_service"] = storage_pool_service
    _api_instances["quota_transfer_service"] = quota_transfer_service
    _api_instances["capacity_alert_service"] = capacity_alert_service
    _api_instances["space_lifecycle_service"] = space_lifecycle_service
    _api_instances["resource_plan_service"] = resource_plan_service
    _api_instances["config_service"] = config_service
    _api_instances["permission_checker"] = permission_checker
    _api_instances["event_bus"] = event_bus
    _api_instances["analytics_broadcaster"] = analytics_broadcaster

    # Mount static files
    _web_dir = str(Path(__file__).parent / "web")
    _dist_dir = str(Path(__file__).parent / "web" / "dist")
    app.mount("/static", StaticFiles(directory=_web_dir), name="static")
    app.mount("/assets", StaticFiles(directory=_dist_dir + "/assets"), name="assets")

    # Initialize webhook publisher
    await init_publisher()

    # Auto-register webhooks from config
    webhooks = config.get("webhooks", [])
    publisher = get_publisher()
    for wh in webhooks:
        publisher.register(
            url=wh["url"],
            secret=wh.get("secret"),
            events=[EventType(e) for e in wh.get("events", [])],
            enabled=wh.get("enabled", True),
        )

    yield

    # Shutdown webhook publisher and analytics broadcaster
    await shutdown_publisher()
    if "analytics_broadcaster" in _api_instances:
        await _api_instances["analytics_broadcaster"].stop()

    # Stop trash purge scheduler
    TrashService.stop_scheduler()
    logger.info("TrashService scheduler stopped")

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

# CORS 配置：通过环境变量控制允许的来源
# 开发环境: HFM_CORS_ORIGINS="http://localhost:5173,http://localhost:8080"
# 生产环境: HFM_CORS_ORIGINS="https://your-app.vercel.app,https://your-app-staging.vercel.app"
_cors_env = os.environ.get("HFM_CORS_ORIGINS", "")
if _cors_env:
    _allowed_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
else:
    _allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins if _allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register lifecycle violation handler
from file_manager.api.lifecycle_handler import register_lifecycle_handlers
register_lifecycle_handlers(app)


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

def get_admin_analytics_service() -> AdminAnalyticsService:
    return _api_instances.get("admin_analytics_service")

def get_team_service() -> TeamService:
    return _api_instances.get("team_service")

def get_space_service() -> SpaceService:
    return _api_instances.get("space_service")

def get_workflow_service() -> WorkflowService:
    return _api_instances.get("workflow_service")

def get_notebook_service() -> NotebookService:
    return _api_instances.get("notebook_service")

def get_file_lock_service() -> FileLockService:
    return _api_instances.get("file_lock_service")

def get_collaboration_service() -> CollaborationService:
    return _api_instances.get("collaboration_service")

def get_approval_service() -> ApprovalService:
    return _api_instances.get("approval_service")

def get_storage_pool_service() -> StoragePoolService:
    return _api_instances.get("storage_pool_service")

def get_quota_transfer_service() -> QuotaTransferService:
    return _api_instances.get("quota_transfer_service")

def get_capacity_alert_service() -> CapacityAlertService:
    return _api_instances.get("capacity_alert_service")

def get_space_lifecycle_service() -> SpaceLifecycleService:
    return _api_instances.get("space_lifecycle_service")

def get_resource_plan_service() -> ResourcePlanService:
    return _api_instances.get("resource_plan_service")

def get_config_service() -> ConfigService:
    return _api_instances.get("config_service")

def get_notification_service() -> "NotificationService":
    from services.notification_service import NotificationService
    return NotificationService(db_factory=_api_instances.get("db_factory"))

def get_trash_service() -> "TrashService":
    from file_manager.services.trash_service import TrashService
    file_svc = get_file_service()
    config = _api_instances.get("config", {})
    storage_root = os.path.expanduser(config.get("storage_root", ""))
    return TrashService(
        db_factory=_api_instances.get("db_factory"),
        storage=file_svc.storage if file_svc else None,
        default_pool_storage_path=storage_root,
    )

def _handle_space_error(e: Exception):
    """Handle space-related exceptions."""
    from file_manager.services.space_service import (
        SpaceNotFound, SpaceQuotaExceeded, SpaceRequestNotFound,
        SpaceRequestInvalid, NotSpaceOwner, UserAlreadyInSpace,
        CredentialNotFound, CredentialExpired, QuotaExceeded,
    )
    from file_manager.services.trash_service import (
        TrashItemNotFound, TrashAccessDenied, TrashExpired,
        TrashPermissionDenied,
    )
    if isinstance(e, SpaceNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, (SpaceRequestNotFound, CredentialNotFound, TrashItemNotFound)):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, (SpaceQuotaExceeded, QuotaExceeded, SpaceRequestInvalid)):
        raise HTTPException(status_code=507, detail=str(e))
    if isinstance(e, NotSpaceOwner):
        raise HTTPException(status_code=403, detail=str(e))
    if isinstance(e, UserAlreadyInSpace):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, CredentialExpired):
        raise HTTPException(status_code=410, detail=str(e))
    if isinstance(e, (TrashAccessDenied, TrashPermissionDenied)):
        raise HTTPException(status_code=403, detail=str(e))
    if isinstance(e, TrashExpired):
        raise HTTPException(status_code=410, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))

def get_current_user_ctx(
    credentials = Depends(security),
    request: Request = None,
) -> PermissionContext:
    """Return PermissionContext for the authenticated user."""
    auth_service = get_auth_service()
    if not auth_service:
        raise HTTPException(status_code=500, detail="Auth not configured")

    try:
        user = auth_service.get_user_from_token(credentials.credentials)
        # Determine active space for file operations
        # Priority: 1. X-Space-Id header (from frontend UI), 2. first accessible space (default)
        active_team_id = None
        active_space_id = None

        # Check X-Space-Id header from frontend (set when user switches space in UI)
        if request and request.headers.get("X-Space-Id"):
            active_space_id = request.headers.get("X-Space-Id")

        # Fall back to first accessible space
        if not active_space_id:
            space_service = get_space_service()
            if space_service:
                contexts = space_service.get_user_storage_context(user_id=str(user.id))
                # Pick first active space as the default
                if contexts:
                    ctx0 = contexts[0]
                    active_space_id = ctx0.get("space_id")
                    active_team_id = ctx0.get("space_id")  # Legacy alias
        return PermissionContext.from_authenticated_user(
            user,
            active_team_id=active_team_id,
            active_space_id=active_space_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


# ============================================================================
# Health
# ============================================================================

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "hermes-file-manager"}

@app.get("/system/status")
async def system_status():
    """Return system status for frontend knowledge toolbar"""
    import httpx

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            hermes_resp = await client.get("http://localhost:8080/health")
            hermes_ok = hermes_resp.status_code == 200
        except Exception:
            hermes_ok = False

        try:
            llm_gui_resp = await client.get("http://localhost:19827/health")
            llm_gui_ok = llm_gui_resp.status_code == 200
        except Exception:
            llm_gui_ok = False

        try:
            llm_api_resp = await client.get("http://localhost:1421/health")
            llm_api_ok = llm_api_resp.status_code == 200
        except Exception:
            llm_api_ok = False

    return {
        "hermes_backend_running": hermes_ok,
        "llm_wiki_gui_running": llm_gui_ok,
        "llm_wiki_api_running": llm_api_ok,
        "llm_wiki_gui_url": "http://localhost:19827",
        "llm_wiki_api_url": "http://localhost:19827",
    }

@app.get("/api/v1/knowledge/status")
async def knowledge_status():
    """Return knowledge base status for frontend."""
    import httpx

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # LLM Wiki FM 提供 /status 端点在 19827 端口
            llm_api_resp = await client.get("http://localhost:19827/status")
            llm_api_ok = llm_api_resp.status_code == 200 and llm_api_resp.json().get("ok") == True
        except Exception:
            llm_api_ok = False

    # 获取同步模式和设置（从数据库或缓存）
    sync_mode = "manual"
    sync_interval = 30
    try:
        from file_manager.services.knowledge_service import get_knowledge_service
        svc = get_knowledge_service()
        sync_mode = svc.get_sync_mode("default")
        sync_interval = svc.get_sync_interval("default")
    except Exception:
        pass

    return {
        "running": llm_api_ok,
        "sync_mode": sync_mode,
        "sync_interval": sync_interval,
        "llm_wiki_gui_url": "http://localhost:19827"
    }

@app.post("/api/v1/knowledge/start")
async def start_knowledge_service():
    """启动 LLM Wiki 服务（供浏览器环境调用）"""
    import httpx
    import asyncio
    import subprocess
    import sys

    # 先检查是否已经在运行
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:19827/status")
            if resp.status_code == 200:
                return {"status": "already_running", "url": "http://127.0.0.1:19827"}
    except Exception:
        pass

    # 未运行，尝试启动
    try:
        if sys.platform == "darwin":
            # macOS: 启动 LLM Wiki 应用
            subprocess.Popen(
                ["open", "-a", "LLM Wiki.app"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "", "LLM Wiki FM.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            return {"status": "unsupported_platform"}

        # 等待服务启动（最多 10 秒）
        for _ in range(20):
            await asyncio.sleep(0.5)
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get("http://127.0.0.1:19827/status")
                    if resp.status_code == 200:
                        return {"status": "started", "url": "http://127.0.0.1:19827"}
            except Exception:
                continue

        return {"status": "timeout", "message": "LLM Wiki 启动超时"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/v1/knowledge/open")
async def open_knowledge_base():
    """打开知识库（启动服务 + 返回 URL）"""
    import httpx
    import asyncio
    import subprocess
    import sys

    # 先检查是否已经在运行
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:19827/status")
            if resp.status_code == 200:
                return {"url": "http://127.0.0.1:19827", "started": False}
    except Exception:
        pass

    # 未运行，尝试启动
    try:
        if sys.platform == "darwin":
            subprocess.Popen(
                ["open", "-a", "LLM Wiki.app"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        elif sys.platform == "win32":
            subprocess.Popen(
                ["cmd", "/c", "start", "", "LLM Wiki FM.exe"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            return {"error": "unsupported_platform"}

        # 等待服务启动（最多 10 秒）
        for _ in range(20):
            await asyncio.sleep(0.5)
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.get("http://127.0.0.1:19827/status")
                    if resp.status_code == 200:
                        return {"url": "http://127.0.0.1:19827", "started": True}
            except Exception:
                continue

        return {"error": "LLM Wiki 启动超时"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/knowledge/settings")
async def get_knowledge_settings(
    user_ctx: PermissionContext = Depends(get_current_user_ctx)
):
    """获取知识库同步设置"""
    from file_manager.services.knowledge_service import get_knowledge_service
    svc = get_knowledge_service()
    settings = svc.get_user_settings(user_ctx.user_id)
    return settings

@app.put("/api/v1/knowledge/settings")
async def update_knowledge_settings(
    request: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx)
):
    """更新知识库同步设置"""
    from file_manager.services.knowledge_service import get_knowledge_service
    body = await request.json()
    svc = get_knowledge_service()
    svc.update_user_settings(user_ctx.user_id, body)
    return {"status": "ok"}

@app.get("/api/v1/knowledge/sync/status")
async def get_sync_status(
    project: str = "default",
    user_ctx: PermissionContext = Depends(get_current_user_ctx)
):
    """获取当前同步状态和历史"""
    from file_manager.services.knowledge_service import get_knowledge_service
    svc = get_knowledge_service()
    history = svc.get_sync_history(project)
    return {
        "jobs": [
            {
                "id": job.id,
                "source_path": job.source_path,
                "status": job.status.value,
                "mode": job.mode.value,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            }
            for job in history[-10:]  # 最近10条
        ]
    }

@app.post("/api/v1/knowledge/sync")
async def sync_to_knowledge(
    request: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx)
):
    """同步文档到知识库

    权限: 空间成员或管理员
    """
    from file_manager.services.knowledge_service import get_knowledge_service

    body = await request.json()
    source_path = body.get("source_path")
    project_name = body.get("project_name", "default")

    if not source_path:
        raise HTTPException(status_code=400, detail="source_path is required")

    # 检查用户是否是空间成员
    space_service = get_space_service()
    is_admin = user_ctx.role_name == "admin"
    is_space_member = False

    if space_service and user_ctx.active_space_id:
        contexts = space_service.get_user_storage_context(user_id=user_ctx.user_id)
        is_space_member = any(
            ctx.get("space_id") == user_ctx.active_space_id
            for ctx in contexts
        )

    # 如果没有活动的 space，检查是否有任何可访问的空间
    if not is_space_member and not is_admin:
        if space_service:
            contexts = space_service.get_user_storage_context(user_id=user_ctx.user_id)
            is_space_member = len(contexts) > 0

    try:
        svc = get_knowledge_service()
        job = await svc.sync_to_knowledge(
            source_path=source_path,
            target_project=project_name,
            user_id=user_ctx.user_id,
            is_space_member=is_space_member,
            is_admin=is_admin
        )
        return {
            "job_id": job.id,
            "status": job.status.value,
            "source_path": job.source_path,
            "target_project": job.target_project
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.get("/api/v1/knowledge/search")
async def search_knowledge(
    q: str = "",
    project: str = "default",
    user_ctx: PermissionContext = Depends(get_current_user_ctx)
):
    """搜索知识库

    权限: 空间成员或管理员
    """
    from file_manager.services.knowledge_service import get_knowledge_service

    if not q:
        return {"results": []}

    # 检查用户是否是空间成员
    space_service = get_space_service()
    is_admin = user_ctx.role_name == "admin"
    is_space_member = False

    if space_service:
        contexts = space_service.get_user_storage_context(user_id=user_ctx.user_id)
        is_space_member = len(contexts) > 0

    try:
        svc = get_knowledge_service()
        results = await svc.search_knowledge(
            query=q,
            project=project,
            is_space_member=is_space_member,
            is_admin=is_admin
        )
        return {
            "results": [
                {
                    "id": r.id,
                    "title": r.title,
                    "snippet": r.snippet,
                    "score": r.score,
                    "path": r.path
                }
                for r in results
            ]
        }
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/api/v1/llm_wiki/open")
async def open_llm_wiki():
    """Open LLM Wiki GUI by spawning the process."""
    import subprocess
    import platform

    llm_wiki_paths = [
        "/Users/xzmx/Downloads/my-project/hermes-agent/llm_wiki_FM/src-tauri/target/release/bundle/macos/LLM Wiki FM.app/Contents/MacOS/llm-wiki-fm",
        "/Users/xzmx/Downloads/my-project/hermes-agent/llm_wiki_FM/src-tauri/target/release/llm-wiki-fm",
    ]

    for path in llm_wiki_paths:
        if Path(path).exists():
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-a", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.Popen([path, "gui"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return {"status": "ok", "message": "LLM Wiki started"}

    return {"status": "error", "message": "LLM Wiki not found"}

@app.get("/llm_wiki")
async def llm_wiki_redirect():
    """Redirect to LLM Wiki GUI."""
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:19827", status_code=302)

@app.get("/")
async def root():
    html_path = Path(__file__).parent / "web" / "app.html"
    if html_path.exists():
        return HTMLResponse(content=html_path.read_text(), status_code=200)
    return HTMLResponse(content="<html><body><h1>Not found</h1></body></html>", status_code=404)


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
# Notification Endpoints
# ============================================================================

@app.get("/api/v1/notifications", tags=["notifications"])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    offset: int = 0,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """List current user's notifications."""
    svc = get_notification_service()
    return svc.list_notifications(
        user_id=str(user_ctx.user_id),
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@app.get("/api/v1/notifications/unread-count", tags=["notifications"])
async def get_unread_count(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get count of unread notifications."""
    svc = get_notification_service()
    return {"count": svc.get_unread_count(str(user_ctx.user_id))}


@app.put("/api/v1/notifications/{notification_id}/read", tags=["notifications"])
async def mark_notification_read(
    notification_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Mark a notification as read."""
    svc = get_notification_service()
    try:
        return svc.mark_as_read(notification_id, str(user_ctx.user_id)).to_dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.put("/api/v1/notifications/read-all", tags=["notifications"])
async def mark_all_notifications_read(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Mark all notifications as read."""
    svc = get_notification_service()
    count = svc.mark_all_as_read(str(user_ctx.user_id))
    return {"message": f"Marked {count} notifications as read", "count": count}


@app.delete("/api/v1/notifications/{notification_id}", tags=["notifications"])
async def delete_notification(
    notification_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a notification."""
    svc = get_notification_service()
    deleted = svc.delete_notification(notification_id, str(user_ctx.user_id))
    if not deleted:
        raise HTTPException(status_code=404, detail="Notification not found")
    return {"message": "Notification deleted"}


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
        result = file_service.write_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
        # Publish webhook event
        from file_manager.api.webhook import publish_file_event, EventType
        username = user_ctx.username
        publish_file_event(
            EventType.FILE_UPDATED if not request.overwrite else EventType.FILE_CREATED,
            request.path,
            user=username,
            metadata={"overwrite": request.overwrite},
        )
        return result
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/delete")
async def delete_file(
    request: FileDeleteRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    try:
        result = file_service.delete_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
        # Publish webhook event
        from file_manager.api.webhook import publish_file_event, EventType
        username = user_ctx.username
        publish_file_event(
            EventType.FILE_DELETED,
            request.path,
            user=username,
        )
        return result
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/mkdir")
async def create_directory(
    request: MkDirRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    import sys, traceback
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    try:
        result = file_service.create_directory(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
        # Publish webhook event
        from file_manager.api.webhook import publish_file_event, EventType
        username = user_ctx.username
        publish_file_event(
            EventType.FILE_CREATED,
            request.path,
            user=username,
            metadata={"type": "directory"},
        )
        return result
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        return _handle_service_error(e)


@app.post("/api/v1/files/move")
async def move_file(
    space_id: str,
    request: FileMoveRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    """Move/rename a file or directory."""
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    try:
        # Set active space for permission check
        user_ctx.active_space_id = space_id
        result = file_service.move_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
        # Publish webhook event
        from file_manager.api.webhook import publish_file_event, EventType
        username = user_ctx.username
        publish_file_event(
            EventType.FILE_MOVED,
            request.from_path,
            user=username,
        )
        return result
    except Exception as e:
        return _handle_service_error(e)


@app.post("/api/v1/files/copy")
async def copy_file(
    space_id: str,
    request: FileCopyRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
    http_request: Request = None,
):
    """Copy a file or directory."""
    file_service = get_file_service()
    client_info = get_client_info(http_request) if http_request else {}
    try:
        # Set active space for permission check
        user_ctx.active_space_id = space_id
        result = file_service.copy_file(
            request=request,
            user_ctx=user_ctx,
            ip_address=client_info.get("ip_address"),
        )
        # Publish webhook event
        from file_manager.api.webhook import publish_file_event, EventType
        username = user_ctx.username
        publish_file_event(
            EventType.FILE_COPIED,
            request.from_path,
            user=username,
        )
        return result
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
# File Lock Endpoints
# ============================================================================

@app.get("/api/v1/files/{space_id}/locks", tags=["file_locks"])
async def list_space_locks(
    space_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all active locks in a space."""
    svc = get_file_lock_service()
    return {"locks": svc.get_space_locks(space_id)}


@app.post("/api/v1/files/locks", tags=["file_locks"])
async def acquire_file_lock(
    path: str,
    space_id: str,
    lock_type: str = "edit",
    timeout_minutes: int = 30,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Acquire a lock on a file."""
    svc = get_file_lock_service()
    try:
        lock = svc.acquire_lock(
            space_id=space_id,
            path=path,
            user_id=str(user_ctx.user_id),
            lock_type=lock_type,
            timeout_minutes=timeout_minutes,
        )
        return lock
    except Exception as e:
        from file_manager.services.file_lock_service import LockHeldByOther, LockNotFound
        if isinstance(e, LockHeldByOther):
            raise HTTPException(status_code=423, detail=str(e))
        if isinstance(e, LockNotFound):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/files/locks/{lock_id}", tags=["file_locks"])
async def release_file_lock(
    lock_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Release a file lock."""
    svc = get_file_lock_service()
    try:
        svc.release_lock(lock_id, str(user_ctx.user_id))
        return {"message": "Lock released"}
    except Exception as e:
        from file_manager.services.file_lock_service import LockNotFound, FileLockError
        if isinstance(e, (LockNotFound, FileLockError)):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/files/locks/{lock_id}/extend", tags=["file_locks"])
async def extend_file_lock(
    lock_id: str,
    minutes: int = 30,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Extend a lock's expiration time."""
    svc = get_file_lock_service()
    try:
        svc.extend_lock(lock_id, str(user_ctx.user_id), minutes)
        return {"message": f"Lock extended by {minutes} minutes"}
    except Exception as e:
        from file_manager.services.file_lock_service import LockNotFound, LockExpired, FileLockError
        if isinstance(e, (LockNotFound, LockExpired, FileLockError)):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/files/locks/my", tags=["file_locks"])
async def get_my_locks(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all locks held by the current user."""
    svc = get_file_lock_service()
    return {"locks": svc.get_user_locks(str(user_ctx.user_id))}


# ============================================================================
# Collaboration Session Endpoints
# ============================================================================

@app.get("/api/v1/spaces/{space_id}/collaborations", tags=["collaborations"])
async def list_space_collaborations(
    space_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all active collaboration sessions for a space."""
    svc = get_collaboration_service()
    return {"collaborations": svc.get_space_collaborations(space_id)}


@app.post("/api/v1/spaces/{space_id}/collaborations", tags=["collaborations"])
async def create_collaboration(
    space_id: str,
    request: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a collaboration session (space owner only)."""
    body = await request.json()
    target_user_id = body.get("target_user_id")
    permissions = body.get("permissions", ["read"])
    expires_hours = body.get("expires_hours", 24)
    svc = get_collaboration_service()
    try:
        collab = svc.create_session(
            space_id=space_id,
            creator_id=str(user_ctx.user_id),
            target_user_id=target_user_id,
            permissions=permissions,
            expires_hours=expires_hours,
        )
        return collab
    except Exception as e:
        from file_manager.services.collaboration_service import PermissionDenied, CollaborationError
        if isinstance(e, (PermissionDenied, CollaborationError)):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/api/v1/collaborations/{session_id}", tags=["collaborations"])
async def revoke_collaboration(
    session_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Revoke a collaboration session."""
    svc = get_collaboration_service()
    try:
        svc.revoke_session(session_id, str(user_ctx.user_id))
        return {"message": "Collaboration session revoked"}
    except Exception as e:
        from file_manager.services.collaboration_service import SessionNotFound, PermissionDenied
        if isinstance(e, (SessionNotFound, PermissionDenied)):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/collaborations/my", tags=["collaborations"])
async def get_my_collaborations(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all collaboration sessions where the user is the target."""
    svc = get_collaboration_service()
    return {"collaborations": svc.get_user_collaborations(str(user_ctx.user_id))}


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
    request: CreateUserRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    try:
        return admin_service.create_user(request=request, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)

@app.get("/api/v1/admin/roles")
async def list_roles(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    admin_service = get_admin_service()
    try:
        return admin_service.list_roles(user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


# =============================================================================
# RBAC Permission API (T3)
# =============================================================================

@app.get("/api/v1/permissions")
async def list_permissions(
    resource: str = None,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """List all permissions, optionally filtered by resource."""
    admin_service = get_admin_service()
    try:
        return admin_service.list_permissions(resource=resource, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/permissions/{permission_id}")
async def get_permission(
    permission_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get a permission by ID."""
    admin_service = get_admin_service()
    try:
        return admin_service.get_permission(permission_id=permission_id, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/permissions")
async def create_permission(
    request: CreatePermissionRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a new permission."""
    admin_service = get_admin_service()
    try:
        return admin_service.create_permission(
            resource=request.resource,
            action=request.action,
            description=request.description,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_admin_error(e)


@app.delete("/api/v1/permissions/{permission_id}")
async def delete_permission(
    permission_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a permission."""
    admin_service = get_admin_service()
    try:
        return admin_service.delete_permission(permission_id=permission_id, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/roles/{role_id}/permissions")
async def list_role_permissions(
    role_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """List all permissions assigned to a role."""
    admin_service = get_admin_service()
    try:
        return admin_service.list_role_permissions(role_id=role_id, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/roles/{role_id}/permissions")
async def assign_permission_to_role(
    role_id: str,
    request: CreateRolePermissionRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Assign a permission to a role."""
    admin_service = get_admin_service()
    try:
        return admin_service.assign_permission_to_role(
            role_id=role_id,
            permission_id=request.permission_id,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_admin_error(e)


@app.delete("/api/v1/roles/{role_id}/permissions/{permission_id}")
async def remove_permission_from_role(
    role_id: str,
    permission_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Remove a permission from a role."""
    admin_service = get_admin_service()
    try:
        return admin_service.remove_permission_from_role(
            role_id=role_id,
            permission_id=permission_id,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/users/{user_id}/roles")
async def get_user_roles(
    user_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all roles assigned to a user."""
    admin_service = get_admin_service()
    try:
        return admin_service.get_user_roles(target_user_id=user_id, user_ctx=user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/users/{user_id}/roles")
async def assign_role_to_user(
    user_id: str,
    request: AssignRoleRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Assign a role to a user."""
    admin_service = get_admin_service()
    try:
        return admin_service.assign_role_to_user(
            target_user_id=user_id,
            role_id=request.role_id,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/admin/rules")
async def create_rule(
    request: CreateRuleRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    try:
        return admin_service.create_rule(
            role_id=request.role_id,
            path_pattern=request.path_pattern,
            permissions=request.permissions,
            priority=request.priority,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/admin/audit")
async def query_audit(
    request: AuditQueryRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    admin_service = get_admin_service()
    try:
        return admin_service.query_audit_logs(request, user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.post("/api/v1/admin/cleanup")
async def cleanup_expired(
    target: str = "all",  # "trash" | "audit" | "all"
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """
    Manually trigger cleanup of expired data.
    Admin only. Purges expired trash items and/or old audit logs.
    """
    admin_service = get_admin_service()
    try:
        results = {}
        if target in ("trash", "all"):
            from file_manager.services.trash_service import TrashService
            trash_svc = get_trash_service()
            results["trash_purged"] = trash_svc.purge_expired().get("count", 0)
        if target in ("audit", "all"):
            from file_manager.engine.audit import AuditLogger
            audit = AuditLogger(db_factory=_api_instances.get("db_factory"))
            results["audit_cleaned"] = audit.cleanup_old_logs(retention_days=90)
        return results
    except Exception as e:
        raise _handle_admin_error(e)


# ============================================================================
# Admin Analytics Endpoints
# ============================================================================

@app.get("/api/v1/admin/analytics/overview", tags=["admin"])
async def get_analytics_overview(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get combined overview data for admin dashboard."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_overview(user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/storage-pools", tags=["admin"])
async def get_storage_pools_analytics(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get storage pool statistics."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_storage_pools(user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/user-spaces", tags=["admin"])
async def get_user_spaces_analytics(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get user-space relationships for Sankey diagram."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_user_space_relationships(user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/quota-heatmap", tags=["admin"])
async def get_quota_heatmap(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get quota usage heatmap."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_quota_heatmap(user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/operation-trends", tags=["admin"])
async def get_operation_trends(
    days: int = 30,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get operation trends over time."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_operation_trends(user_ctx, days=days)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/active-users", tags=["admin"])
async def get_active_users(
    days: int = 7,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get active users statistics."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_active_users(user_ctx, days=days)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/alerts", tags=["admin"])
async def get_alerts(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get quota alerts for admin dashboard."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_alerts(user_ctx)
    except Exception as e:
        raise _handle_admin_error(e)


@app.get("/api/v1/admin/analytics/teams-by-pool/{pool_id}", tags=["admin"])
async def get_teams_by_pool(
    pool_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get all teams using a specific storage pool. Used for STORAGE_POOL_IN_USE constraint."""
    svc = get_admin_analytics_service()
    try:
        return svc.get_teams_by_pool(user_ctx, pool_id)
    except Exception as e:
        raise _handle_admin_error(e)


# ============================================================================
# WebSocket Endpoints
# ============================================================================

@app.websocket("/ws/admin/analytics")
async def websocket_admin_analytics(websocket):
    """
    WebSocket endpoint for real-time admin analytics updates.
    Clients connect with auth token as query param: /ws/admin/analytics?token=xxx
    """
    import sys
    print(f"DEBUG: WebSocket handler called! query_params={dict(websocket.query_params)}", file=sys.stderr)
    sys.stderr.flush()
    import jwt

    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001, reason="Missing token")
            return

        # Decode token directly (without DB lookup for performance)
        jwt_secret = os.environ.get("HFM_JWT_SECRET", "change-me-in-production")
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])

        role = payload.get("role")
        import sys
        print(f"DEBUG WS AUTH: role={repr(role)} type={type(role).__name__}, cmp result: {role == 'admin'}", file=sys.stderr)
        sys.stderr.flush()
        logger.info(f"WebSocket auth debug: role={repr(role)} type={type(role).__name__}, 'admin'==role is {role == 'admin'}, ord('admin')={ord('admin') if isinstance(role, str) else 'N/A'}")
        if role != "admin":
            logger.warning(f"WebSocket auth failed: role={repr(role)} != 'admin'")
            await websocket.close(code=4001, reason="Unauthorized")
            return
    except jwt.ExpiredSignatureError:
        logger.warning("WebSocket auth failed: token expired")
        await websocket.close(code=4001, reason="Token expired")
        return
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=4001, reason="Invalid token")
        return

    manager = get_connection_manager()
    await manager.connect(websocket)

    try:
        from fastapi import WebSocketDisconnect
        while True:
            data = await websocket.receive_text()
            import json
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass
    except Exception:
        manager.disconnect(websocket)


# ============================================================================
# Team / Storage Pool Endpoints
# ============================================================================

from datetime import datetime as dt


def _handle_team_error(e: Exception):
    from file_manager.services.team_service import (
        StoragePoolNotFound, PoolOutOfSpace, TeamNotFound,
        TeamQuotaExceeded, CredentialNotFound, CredentialExpired,
        UserAlreadyInTeam, NotTeamOwner,
    )
    if isinstance(e, StoragePoolNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, PoolOutOfSpace):
        raise HTTPException(status_code=507, detail=str(e))
    if isinstance(e, TeamNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, TeamQuotaExceeded):
        raise HTTPException(status_code=507, detail=str(e))
    if isinstance(e, CredentialNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, CredentialExpired):
        raise HTTPException(status_code=410, detail=str(e))
    if isinstance(e, UserAlreadyInTeam):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, NotTeamOwner):
        raise HTTPException(status_code=403, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


class CreatePoolRequest(BaseModel):
    name: str
    base_path: str
    protocol: str = "local"
    total_bytes: int = 0
    description: str = ""


class CreateTeamRequest(BaseModel):
    name: str
    storage_pool_id: str
    max_bytes: int = 0


class UpdateTeamRequest(BaseModel):
    name: Optional[str] = None
    max_bytes: Optional[int] = None
    is_active: Optional[bool] = None


class CreateCredentialRequest(BaseModel):
    max_uses: Optional[int] = None
    expires_at: Optional[dt] = None


@app.get("/api/v1/pools", tags=["pools"])
async def list_pools(
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.list_pools()
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/pools", tags=["pools"])
async def create_pool(
    req: CreatePoolRequest,
    user_ctx=Depends(get_current_user_ctx),
):
    # Admin only
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以创建存储池")
    svc = get_team_service()
    try:
        pool = svc.create_pool(
            name=req.name,
            base_path=req.base_path,
            protocol=req.protocol,
            total_bytes=req.total_bytes,
            description=req.description,
        )
        # Register storage engine for this pool
        from file_manager.engine.storage import StorageEngine
        pool_storage = StorageEngine(req.base_path)
        file_service = get_file_service()
        file_service.register_pool(pool["pool_id"], pool_storage)
        return pool
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/pools/{pool_id}/refresh", tags=["pools"])
async def refresh_pool(
    pool_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    # Admin only
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以刷新存储池")
    svc = get_team_service()
    try:
        return svc.refresh_pool_space(pool_id)
    except Exception as e:
        raise _handle_team_error(e)


@app.delete("/api/v1/pools/{pool_id}", tags=["pools"])
async def delete_pool(
    pool_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    # Admin only
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以删除存储池")
    svc = get_team_service()
    try:
        svc.delete_pool(pool_id)
        file_service = get_file_service()
        file_service.unregister_pool(pool_id)
        return {"message": "存储池已删除"}
    except Exception as e:
        raise _handle_team_error(e)


@app.get("/api/v1/teams", tags=["teams"])
async def list_teams(
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.list_teams(user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_team_error(e)


@app.get("/api/v1/my/teams", tags=["teams"])
async def my_teams(
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.get_user_teams_summary(user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_team_error(e)


@app.get("/api/v1/teams/{team_id}", tags=["teams"])
async def get_team(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.get_team(team_id)
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/teams", tags=["teams"])
async def create_team(
    req: CreateTeamRequest,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.create_team(
            name=req.name,
            owner_id=str(user_ctx.user_id),
            storage_pool_id=req.storage_pool_id,
            max_bytes=req.max_bytes,
        )
    except Exception as e:
        raise _handle_team_error(e)


@app.patch("/api/v1/teams/{team_id}", tags=["teams"])
async def update_team(
    team_id: str,
    req: UpdateTeamRequest,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.update_team(
            team_id=team_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            max_bytes=req.max_bytes,
            is_active=req.is_active,
        )
    except Exception as e:
        raise _handle_team_error(e)


@app.delete("/api/v1/teams/{team_id}", tags=["teams"])
async def delete_team(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        svc.delete_team(team_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "团队已删除"}
    except Exception as e:
        raise _handle_team_error(e)


@app.get("/api/v1/teams/{team_id}/members", tags=["teams"])
async def list_team_members(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.list_members(team_id)
    except Exception as e:
        raise _handle_team_error(e)


@app.delete("/api/v1/teams/{team_id}/members/{user_id}", tags=["teams"])
async def remove_team_member(
    team_id: str,
    user_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        svc.remove_member(team_id, target_user_id=user_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "已移除成员"}
    except Exception as e:
        raise _handle_team_error(e)


@app.get("/api/v1/teams/{team_id}/credentials", tags=["teams"])
async def list_team_credentials(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.list_credentials(team_id, requesting_user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/teams/{team_id}/credentials", tags=["teams"])
async def create_team_credential(
    team_id: str,
    req: CreateCredentialRequest,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        return svc.create_credential(
            team_id=team_id,
            created_by=str(user_ctx.user_id),
            max_uses=req.max_uses,
            expires_at=req.expires_at,
        )
    except Exception as e:
        raise _handle_team_error(e)


@app.delete("/api/v1/teams/{team_id}/credentials/{cred_id}", tags=["teams"])
async def revoke_credential(
    team_id: str,
    cred_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_team_service()
    try:
        svc.revoke_credential(cred_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "凭证已撤销"}
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/teams/validate-invite", tags=["teams"])
async def validate_invite_credential(
    request: Request,
    user_ctx=Depends(get_current_user_ctx),
):
    """Validate an invite credential without joining the team. Used for FE-022 pre-validation."""
    body = await request.json()
    code = body.get("code", "")
    svc = get_team_service()
    try:
        return svc.validate_credential(token=code)
    except Exception as e:
        raise _handle_team_error(e)


@app.post("/api/v1/teams/join", tags=["teams"])
async def join_team_via_credential(
    request: Request,
    user_ctx=Depends(get_current_user_ctx),
):
    body = await request.json()
    token = body.get("token", "")
    svc = get_team_service()
    try:
        return svc.join_via_credential(token=token, user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_team_error(e)


# ========== 新增团队配额与成员管理端点 ==========

@app.get("/api/v1/teams/{team_id}/quota-status", tags=["teams"])
async def get_team_quota_status(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """获取团队配额状态"""
    svc = get_team_service()
    try:
        status = svc.get_team_quota_status(team_id)
        return status
    except TeamNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/teams/{team_id}/members/request-exit", tags=["teams"])
async def request_team_exit(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """成员申请退出团队（生成待办任务给管理员）"""
    svc = get_space_service()
    try:
        request = svc.create_member_exit_request(
            team_id=team_id,
            member_id=str(user_ctx.user_id),
            reason="成员主动申请退出"
        )
        return {"request_id": request.id, "status": "pending"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/teams/{team_id}/members/{member_id}/remove", tags=["teams"])
async def remove_team_member_by_admin(
    team_id: str,
    member_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """管理员移除团队成员"""
    svc = get_space_service()
    try:
        result = svc.remove_member_with_notification(
            team_id=team_id,
            member_id=member_id,
            operator_id=str(user_ctx.user_id),
            action="remove_by_admin"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/teams/{team_id}/pending-tasks", tags=["teams"])
async def get_pending_tasks(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """获取团队待处理任务列表"""
    svc = get_approval_service()
    try:
        requests = svc.get_pending_requests(approver_id=str(user_ctx.user_id))
        # 过滤出该团队的任务
        team_requests = [r for r in requests if r.get("target_id") == team_id]
        return {"tasks": team_requests}
    except Exception as e:
        logger.error(f"Error fetching pending tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/my/storage-context", tags=["spaces"])
async def my_storage_context(
    user_ctx=Depends(get_current_user_ctx),
):
    svc = get_space_service()
    try:
        return {"contexts": svc.get_user_storage_context(user_id=str(user_ctx.user_id))}
    except Exception as e:
        raise _handle_space_error(e)


# ============================================================================
# Space Endpoints (New hierarchical space system)
# ============================================================================

from file_manager.api.dto import (
    CreateSpaceRequestDTO, UpdateSpaceRequestDTO,
    CreateCredentialRequestDTO, CredentialDTO,
    CreatePrivateSpaceRequestDTO, SpaceRequestDTO,
    ApproveRejectRequestDTO,
    FileVersionDTO, FileVersionListResponseDTO, RestoreVersionRequestDTO,
)


@app.get("/api/v1/spaces", tags=["spaces"])
async def list_spaces(
    user_ctx=Depends(get_current_user_ctx),
):
    """List all spaces the user has access to."""
    svc = get_space_service()
    try:
        spaces = svc.list_spaces(user_id=str(user_ctx.user_id))
        return {"spaces": spaces, "total": len(spaces)}
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/spaces/{space_id}", tags=["spaces"])
async def get_space(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Get space details with members."""
    svc = get_space_service()
    try:
        return svc.get_space(space_id)
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces", tags=["spaces"])
async def create_space(
    req: CreateSpaceRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Create a new space (admin only)."""
    svc = get_space_service()
    try:
        return svc.create_space(
            name=req.name,
            owner_id=str(user_ctx.user_id),
            storage_pool_id=req.storage_pool_id,
            parent_id=req.parent_id,
            max_bytes=req.max_bytes,
            space_type=req.space_type,
            description=req.description,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.patch("/api/v1/spaces/{space_id}", tags=["spaces"])
async def update_space(
    space_id: str,
    req: UpdateSpaceRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Update space settings."""
    svc = get_space_service()
    try:
        return svc.update_space(
            space_id=space_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            max_bytes=req.max_bytes,
            status=req.status,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/spaces/{space_id}", tags=["spaces"])
async def delete_space(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Delete a space (owner only)."""
    svc = get_space_service()
    try:
        svc.delete_space(space_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Space deleted"}
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/spaces/{space_id}/quota", tags=["spaces"])
async def get_space_quota(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Get space quota usage and status."""
    svc = get_space_service()
    try:
        return svc.get_quota_status(space_id)
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/spaces/{space_id}/activity", tags=["spaces"])
async def get_space_activity(
    space_id: str,
    limit: int = 50,
    offset: int = 0,
    user_ctx=Depends(get_current_user_ctx),
):
    """Get recent activity for a space."""
    svc = get_space_service()
    try:
        return svc.get_activity(space_id=space_id, limit=limit, offset=offset)
    except Exception as e:
        raise _handle_space_error(e)


# -----------------------------------------------------------------------------
# Trash API
# -----------------------------------------------------------------------------

@app.get("/api/v1/spaces/{space_id}/trash", tags=["spaces"])
async def list_trash(
    space_id: str,
    limit: int = 50,
    offset: int = 0,
    user_ctx=Depends(get_current_user_ctx),
):
    """List items in trash for a space."""
    from file_manager.services.trash_service import TrashService
    svc = get_trash_service()
    try:
        return svc.list_trash(
            space_id=space_id,
            user_id=str(user_ctx.user_id),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces/{space_id}/trash/{deleted_file_id}/restore", tags=["spaces"])
async def restore_trash(
    space_id: str,
    deleted_file_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Restore a file from trash."""
    from file_manager.services.trash_service import TrashService
    svc = get_trash_service()
    try:
        return svc.restore_from_trash(
            space_id=space_id,
            deleted_file_id=deleted_file_id,
            user_id=str(user_ctx.user_id),
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/spaces/{space_id}/trash/{deleted_file_id}", tags=["spaces"])
async def permanent_delete_trash(
    space_id: str,
    deleted_file_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Permanently delete a file from trash (cannot be restored)."""
    from file_manager.services.trash_service import TrashService
    svc = get_trash_service()
    try:
        return svc.permanent_delete(
            space_id=space_id,
            deleted_file_id=deleted_file_id,
            user_id=str(user_ctx.user_id),
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/spaces/{space_id}/trash", tags=["spaces"])
async def empty_trash(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Empty all items in trash for a space."""
    from file_manager.services.trash_service import TrashService
    svc = get_trash_service()
    try:
        return svc.empty_trash(
            space_id=space_id,
            user_id=str(user_ctx.user_id),
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/spaces/{space_id}/members", tags=["spaces"])
async def list_space_members(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """List all members of a space."""
    svc = get_space_service()
    try:
        return svc.list_members(space_id)
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces/{space_id}/members", tags=["spaces"])
async def add_space_member(
    space_id: str,
    user_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Add a user to a space (owner only)."""
    svc = get_space_service()
    try:
        return svc.add_member(
            space_id=space_id,
            user_id=user_id,
            requesting_user_id=str(user_ctx.user_id),
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/spaces/{space_id}/members/{target_user_id}", tags=["spaces"])
async def remove_space_member(
    space_id: str,
    target_user_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Remove a user from a space."""
    svc = get_space_service()
    try:
        svc.remove_member(
            space_id=space_id,
            target_user_id=target_user_id,
            requesting_user_id=str(user_ctx.user_id),
        )
        return {"message": "Member removed"}
    except Exception as e:
        raise _handle_space_error(e)


# ============================================================================
# Space Links (Cross-team Collaboration)
# ============================================================================

@app.get("/api/v1/spaces/{space_id}/links", tags=["space_links"])
async def list_space_links(
    space_id: str,
    user_ctx = Depends(get_current_user_ctx),
):
    """List all cross-space collaboration links."""
    svc = get_space_service()
    try:
        return {"links": svc.list_space_links(space_id)}
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces/{space_id}/links", tags=["space_links"])
async def create_space_link(
    space_id: str,
    request: Request,
    user_ctx = Depends(get_current_user_ctx),
):
    """Create a cross-space collaboration link."""
    body = await request.json()
    target_space_id = body.get("target_space_id")
    permission = body.get("permission", "read")

    if not target_space_id:
        raise HTTPException(status_code=400, detail="target_space_id is required")

    svc = get_space_service()
    try:
        return svc.create_space_link(
            source_space_id=space_id,
            target_space_id=target_space_id,
            created_by=str(user_ctx.user_id),
            permission=permission,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/space-links/{link_id}", tags=["space_links"])
async def revoke_space_link(
    link_id: str,
    user_ctx = Depends(get_current_user_ctx),
):
    """Revoke a cross-space collaboration link."""
    svc = get_space_service()
    try:
        svc.revoke_space_link(link_id, str(user_ctx.user_id))
        return {"message": "Link revoked"}
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/cross-team-spaces", tags=["space_links"])
async def get_cross_team_spaces(
    user_ctx = Depends(get_current_user_ctx),
):
    """Get all spaces accessible through cross-team collaboration."""
    svc = get_space_service()
    try:
        return {"spaces": svc.get_cross_team_spaces(str(user_ctx.user_id))}
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces/{space_id}/invite", tags=["spaces"])
async def create_space_credential(
    space_id: str,
    req: CreateCredentialRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Generate an invite credential for a space."""
    svc = get_space_service()
    try:
        return svc.create_credential(
            space_id=space_id,
            created_by=str(user_ctx.user_id),
            max_uses=req.max_uses,
            expires_at=req.expires_at,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/spaces/{space_id}/credentials", tags=["spaces"])
async def list_space_credentials(
    space_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """List all credentials for a space (owner only)."""
    svc = get_space_service()
    try:
        return svc.list_credentials(space_id, requesting_user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_space_error(e)


@app.delete("/api/v1/spaces/{space_id}/credentials/{cred_id}", tags=["spaces"])
async def revoke_space_credential(
    space_id: str,
    cred_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Revoke a space credential."""
    svc = get_space_service()
    try:
        svc.revoke_credential(cred_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Credential revoked"}
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/spaces/join", tags=["spaces"])
async def join_space_via_credential(
    req: Request,
    user_ctx=Depends(get_current_user_ctx),
):
    """Join a space using an invite credential."""
    body = await req.json()
    token = body.get("token", "")
    svc = get_space_service()
    try:
        return svc.join_via_credential(token=token, user_id=str(user_ctx.user_id))
    except Exception as e:
        raise _handle_space_error(e)


# Space Requests (Private Sub-Space)
@app.post("/api/v1/spaces/{space_id}/request", tags=["spaces"])
async def create_space_request(
    space_id: str,
    req: CreatePrivateSpaceRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Request a private sub-space within a parent space."""
    svc = get_space_service()
    try:
        return svc.create_request(
            space_id=space_id,
            requester_id=str(user_ctx.user_id),
            requested_name=req.requested_name,
            requested_bytes=req.requested_bytes,
            reason=req.reason,
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/space-requests", tags=["spaces"])
async def list_space_requests(
    space_id: str = None,
    status: str = None,
    user_ctx=Depends(get_current_user_ctx),
):
    """List space requests (admin/owner only)."""
    svc = get_space_service()
    try:
        return svc.list_requests(space_id=space_id, status=status)
    except Exception as e:
        raise _handle_space_error(e)


@app.put("/api/v1/space-requests/{request_id}", tags=["spaces"])
async def approve_reject_request(
    request_id: str,
    req: ApproveRejectRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Approve or reject a space request."""
    svc = get_space_service()
    try:
        if req.status == "approved":
            return svc.approve_request(
                request_id=request_id,
                reviewer_id=str(user_ctx.user_id),
                note=req.note,
            )
        else:
            return svc.reject_request(
                request_id=request_id,
                reviewer_id=str(user_ctx.user_id),
                note=req.note,
            )
    except Exception as e:
        raise _handle_space_error(e)


@app.get("/api/v1/storage/info", tags=["storage"])
async def get_storage_info(
    user_ctx=Depends(get_current_user_ctx),
):
    """Get storage root path for physical file operations."""
    config = get_config()
    storage_root = os.path.expanduser(config["storage_root"])
    return {"storage_root": storage_root}


# ============================================================================
# Storage Pools
# ============================================================================

@app.get("/api/v1/storage-pools", tags=["storage"])
async def list_pools(
    user_ctx=Depends(get_current_user_ctx),
):
    """List all storage pools."""
    svc = get_space_service()
    try:
        return svc.list_pools()
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/storage-pools", tags=["storage"])
async def create_pool(
    req: Request,
    user_ctx=Depends(get_current_user_ctx),
):
    """Create a new storage pool (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以创建存储池")
    body = await req.json()
    svc = get_space_service()
    try:
        return svc.create_pool(
            name=body.get("name"),
            base_path=body.get("base_path"),
            protocol=body.get("protocol", "local"),
            total_bytes=body.get("total_bytes", 0),
            description=body.get("description", ""),
        )
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/storage-pools/{pool_id}/refresh", tags=["storage"])
async def refresh_pool_space(
    pool_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Refresh storage pool space info (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="只有管理员可以刷新存储池")
    svc = get_space_service()
    try:
        return svc.refresh_pool_space(pool_id)
    except Exception as e:
        raise _handle_space_error(e)


# ============================================================================
# File Version Endpoints
# ============================================================================

@app.get("/api/v1/files/{file_id}/versions", tags=["files"])
async def list_file_versions(
    file_id: str,
    path: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """List all versions for a file."""
    svc = get_space_service()
    try:
        # Use file_service for version listing
        file_svc = get_file_service()
        versions = file_svc.list_versions(path=path, user_ctx=user_ctx)
        return {"versions": versions, "total": len(versions)}
    except Exception as e:
        raise _handle_space_error(e)


@app.post("/api/v1/files/{file_id}/restore", tags=["files"])
async def restore_file_version(
    file_id: str,
    path: str,
    req: RestoreVersionRequestDTO,
    user_ctx=Depends(get_current_user_ctx),
):
    """Restore a file to a previous version."""
    file_svc = get_file_service()
    try:
        return file_svc.restore_version(
            path=path,
            version=req.version,
            user_ctx=user_ctx,
        )
    except Exception as e:
        raise _handle_space_error(e)


# ============================================================================
# Webhook Endpoints
# ============================================================================

from pydantic import BaseModel
from typing import List, Optional


class WebhookRegisterRequest(BaseModel):
    url: str
    secret: Optional[str] = None
    events: List[str] = []
    enabled: bool = True


@app.get("/api/v1/webhooks", tags=["webhooks"])
async def list_webhooks(
    user_ctx=Depends(get_current_user_ctx),
):
    """List all registered webhooks."""
    publisher = get_publisher()
    return {"webhooks": publisher.list_subscribers()}


@app.post("/api/v1/webhooks", tags=["webhooks"])
async def register_webhook(
    request: WebhookRegisterRequest,
    user_ctx=Depends(get_current_user_ctx),
):
    """Register a new webhook subscriber."""
    from file_manager.api.webhook import EventType

    publisher = get_publisher()
    events = [EventType(e) for e in request.events] if request.events else None
    subscriber_id = publisher.register(
        url=request.url,
        secret=request.secret,
        events=events,
        enabled=request.enabled,
    )
    return {"id": subscriber_id, "message": "Webhook registered"}


@app.delete("/api/v1/webhooks/{subscriber_id}", tags=["webhooks"])
async def unregister_webhook(
    subscriber_id: str,
    user_ctx=Depends(get_current_user_ctx),
):
    """Unregister a webhook subscriber."""
    publisher = get_publisher()
    if publisher.unregister(subscriber_id):
        return {"message": "Webhook unregistered"}
    raise HTTPException(status_code=404, detail="Webhook not found")


# ============================================================================
# Error Handler
# ============================================================================

def _handle_service_error(e: Exception):
    """Map service-layer exceptions to HTTP responses."""
    from file_manager.services import FileAccessDenied, FileNotFound, FileAlreadyExists, DirectoryNotEmpty
    from file_manager.services.file_service import FileLocked
    from file_manager.services.team_service import TeamQuotaExceeded

    if isinstance(e, FileAccessDenied):
        raise HTTPException(status_code=403, detail=e.reason)
    if isinstance(e, FileNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, FileAlreadyExists):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, DirectoryNotEmpty):
        raise HTTPException(status_code=409, detail=str(e))
    if isinstance(e, FileLocked):
        raise HTTPException(status_code=423, detail=str(e))
    if isinstance(e, TeamQuotaExceeded):
        raise HTTPException(status_code=507, detail=str(e))
    # Also handle QuotaExceeded from space_service
    from file_manager.services.space_service import QuotaExceeded
    if isinstance(e, QuotaExceeded):
        raise HTTPException(status_code=507, detail=str(e))
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
    from file_manager.services.lifecycle_engine import LifecycleViolation
    if isinstance(e, UserNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, RoleNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, LifecycleViolation):
        raise HTTPException(status_code=422, detail=e.to_dict())
    raise HTTPException(status_code=500, detail=str(e))


def _handle_workflow_error(e: Exception):
    """Map workflow service exceptions to HTTP responses."""
    from file_manager.services.workflow_service import (
        WorkflowNotFound, WorkflowStepNotFound,
        NotWorkflowOwner, WorkflowAccessDenied,
    )
    if isinstance(e, WorkflowNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, WorkflowStepNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, NotWorkflowOwner):
        raise HTTPException(status_code=403, detail=str(e))
    if isinstance(e, WorkflowAccessDenied):
        raise HTTPException(status_code=403, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


def _handle_notebook_error(e: Exception):
    """Map notebook service exceptions to HTTP responses."""
    from file_manager.services.notebook_service import (
        NotebookNotFound, NotebookVariableNotFound,
        NotNotebookOwner, NotebookAccessDenied,
    )
    if isinstance(e, NotebookNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, NotebookVariableNotFound):
        raise HTTPException(status_code=404, detail=str(e))
    if isinstance(e, NotNotebookOwner):
        raise HTTPException(status_code=403, detail=str(e))
    if isinstance(e, NotebookAccessDenied):
        raise HTTPException(status_code=403, detail=str(e))
    raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Workflow Endpoints
# ============================================================================

from file_manager.api.dto import (
    CreateWorkflowRequestDTO, UpdateWorkflowRequestDTO,
    CreateWorkflowStepRequestDTO, WorkflowDTO, WorkflowDetailDTO,
    WorkflowListResponseDTO, ReorderStepsRequestDTO,
    DuplicateWorkflowRequestDTO, ExecuteWorkflowRequestDTO,
)


@app.get("/api/v1/spaces/{space_id}/workflows", tags=["workflows"])
async def list_space_workflows(
    space_id: str,
    tags: Optional[str] = None,  # comma-separated
    include_shared: bool = True,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """List all workflows in a space."""
    wf_svc = get_workflow_service()
    tag_list = tags.split(",") if tags else None
    try:
        workflows = wf_svc.list_workflows(
            space_id=space_id,
            user_id=str(user_ctx.user_id),
            tags=tag_list,
            include_shared=include_shared,
        )
        return {"workflows": workflows, "total": len(workflows)}
    except Exception as e:
        raise _handle_workflow_error(e)


@app.get("/api/v1/workflows/{workflow_id}", tags=["workflows"])
async def get_workflow(
    workflow_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get workflow details with steps."""
    wf_svc = get_workflow_service()
    try:
        return wf_svc.get_workflow(workflow_id)
    except Exception as e:
        raise _handle_workflow_error(e)


@app.post("/api/v1/spaces/{space_id}/workflows", tags=["workflows"])
async def create_workflow(
    space_id: str,
    req: CreateWorkflowRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a new workflow in a space."""
    wf_svc = get_workflow_service()
    try:
        steps_data = [s.model_dump() for s in req.steps] if req.steps else None
        return wf_svc.create_workflow(
            space_id=space_id,
            owner_id=str(user_ctx.user_id),
            name=req.name,
            description=req.description,
            is_shared=req.is_shared,
            tags=list(req.tags) if req.tags else None,
            steps=steps_data,
        )
    except Exception as e:
        raise _handle_workflow_error(e)


@app.patch("/api/v1/workflows/{workflow_id}", tags=["workflows"])
async def update_workflow(
    workflow_id: str,
    req: UpdateWorkflowRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update workflow metadata."""
    wf_svc = get_workflow_service()
    try:
        return wf_svc.update_workflow(
            workflow_id=workflow_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            description=req.description,
            is_shared=req.is_shared,
            tags=list(req.tags) if req.tags else None,
        )
    except Exception as e:
        raise _handle_workflow_error(e)


@app.delete("/api/v1/workflows/{workflow_id}", tags=["workflows"])
async def delete_workflow(
    workflow_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a workflow."""
    wf_svc = get_workflow_service()
    try:
        wf_svc.delete_workflow(workflow_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Workflow deleted"}
    except Exception as e:
        raise _handle_workflow_error(e)


@app.post("/api/v1/workflows/{workflow_id}/steps", tags=["workflows"])
async def add_workflow_step(
    workflow_id: str,
    req: CreateWorkflowStepRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Add a step to a workflow."""
    wf_svc = get_workflow_service()
    try:
        return wf_svc.add_step(
            workflow_id=workflow_id,
            requesting_user_id=str(user_ctx.user_id),
            order=req.order,
            command=req.command,
            explanation=req.explanation,
            confirm_required=req.confirm_required,
        )
    except Exception as e:
        raise _handle_workflow_error(e)


@app.patch("/api/v1/workflows/steps/{step_id}", tags=["workflows"])
async def update_workflow_step(
    step_id: str,
    req: CreateWorkflowStepRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update a workflow step."""
    wf_svc = get_workflow_service()
    try:
        return wf_svc.update_step(
            step_id=step_id,
            requesting_user_id=str(user_ctx.user_id),
            order=req.order,
            command=req.command,
            explanation=req.explanation,
            confirm_required=req.confirm_required,
        )
    except Exception as e:
        raise _handle_workflow_error(e)


@app.delete("/api/v1/workflows/steps/{step_id}", tags=["workflows"])
async def delete_workflow_step(
    step_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a workflow step."""
    wf_svc = get_workflow_service()
    try:
        wf_svc.delete_step(step_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Step deleted"}
    except Exception as e:
        raise _handle_workflow_error(e)


@app.post("/api/v1/workflows/{workflow_id}/reorder", tags=["workflows"])
async def reorder_workflow_steps(
    workflow_id: str,
    req: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Reorder workflow steps."""
    body = await req.json()
    step_ids = body.get("step_ids", [])
    wf_svc = get_workflow_service()
    try:
        return {"steps": wf_svc.reorder_steps(
            workflow_id=workflow_id,
            requesting_user_id=str(user_ctx.user_id),
            step_ids=step_ids,
        )}
    except Exception as e:
        raise _handle_workflow_error(e)


@app.post("/api/v1/workflows/{workflow_id}/duplicate", tags=["workflows"])
async def duplicate_workflow(
    workflow_id: str,
    req: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Duplicate a workflow (creates private copy)."""
    body = await req.json() or {}
    wf_svc = get_workflow_service()
    try:
        return wf_svc.duplicate_workflow(
            workflow_id=workflow_id,
            new_owner_id=str(user_ctx.user_id),
            new_name=body.get("new_name"),
        )
    except Exception as e:
        raise _handle_workflow_error(e)


@app.post("/api/v1/workflows/{workflow_id}/execute", tags=["workflows"])
async def execute_workflow(
    workflow_id: str,
    req: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Execute a workflow (increments usage counter)."""
    body = await req.json() or {}
    variables = body.get("variables", {})
    wf_svc = get_workflow_service()
    try:
        wf = wf_svc.get_workflow(workflow_id)
        wf_svc.increment_usage(workflow_id)
        return {
            "workflow": wf,
            "variables": variables,
            "ready": True,
        }
    except Exception as e:
        raise _handle_workflow_error(e)


# ============================================================================
# Notebook Endpoints
# ============================================================================

from file_manager.api.dto import (
    CreateNotebookRequestDTO, UpdateNotebookRequestDTO,
    CreateNotebookVariableRequestDTO,
    NotebookDTO, NotebookDetailDTO, NotebookListResponseDTO,
    DuplicateNotebookRequestDTO,
)


@app.get("/api/v1/spaces/{space_id}/notebooks", tags=["notebooks"])
async def list_space_notebooks(
    space_id: str,
    tags: Optional[str] = None,
    include_shared: bool = True,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """List all notebooks in a space."""
    nb_svc = get_notebook_service()
    tag_list = tags.split(",") if tags else None
    try:
        notebooks = nb_svc.list_notebooks(
            space_id=space_id,
            user_id=str(user_ctx.user_id),
            tags=tag_list,
            include_shared=include_shared,
        )
        return {"notebooks": notebooks, "total": len(notebooks)}
    except Exception as e:
        raise _handle_notebook_error(e)


@app.get("/api/v1/notebooks/{notebook_id}", tags=["notebooks"])
async def get_notebook(
    notebook_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get notebook details with variables and content."""
    nb_svc = get_notebook_service()
    try:
        nb = nb_svc.get_notebook(notebook_id)
        nb_svc.increment_usage(notebook_id)
        return nb
    except Exception as e:
        raise _handle_notebook_error(e)


@app.post("/api/v1/spaces/{space_id}/notebooks", tags=["notebooks"])
async def create_notebook(
    space_id: str,
    req: CreateNotebookRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a new notebook."""
    nb_svc = get_notebook_service()
    try:
        variables_data = [v.model_dump() for v in req.variables] if req.variables else None
        return nb_svc.create_notebook(
            space_id=space_id,
            owner_id=str(user_ctx.user_id),
            name=req.name,
            content=req.content,
            description=req.description,
            is_shared=req.is_shared,
            tags=list(req.tags) if req.tags else None,
            variables=variables_data,
        )
    except Exception as e:
        raise _handle_notebook_error(e)


@app.patch("/api/v1/notebooks/{notebook_id}", tags=["notebooks"])
async def update_notebook(
    notebook_id: str,
    req: UpdateNotebookRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update notebook."""
    nb_svc = get_notebook_service()
    try:
        return nb_svc.update_notebook(
            notebook_id=notebook_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            description=req.description,
            content=req.content,
            is_shared=req.is_shared,
            tags=list(req.tags) if req.tags else None,
        )
    except Exception as e:
        raise _handle_notebook_error(e)


@app.delete("/api/v1/notebooks/{notebook_id}", tags=["notebooks"])
async def delete_notebook(
    notebook_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a notebook."""
    nb_svc = get_notebook_service()
    try:
        nb_svc.delete_notebook(notebook_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Notebook deleted"}
    except Exception as e:
        raise _handle_notebook_error(e)


@app.post("/api/v1/notebooks/{notebook_id}/variables", tags=["notebooks"])
async def add_notebook_variable(
    notebook_id: str,
    req: CreateNotebookVariableRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Add a variable to a notebook."""
    nb_svc = get_notebook_service()
    try:
        return nb_svc.add_variable(
            notebook_id=notebook_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            default_value=req.default_value,
            description=req.description,
            is_required=req.is_required,
        )
    except Exception as e:
        raise _handle_notebook_error(e)


@app.patch("/api/v1/notebooks/variables/{variable_id}", tags=["notebooks"])
async def update_notebook_variable(
    variable_id: str,
    req: CreateNotebookVariableRequestDTO,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update a notebook variable."""
    nb_svc = get_notebook_service()
    try:
        return nb_svc.update_variable(
            variable_id=variable_id,
            requesting_user_id=str(user_ctx.user_id),
            name=req.name,
            default_value=req.default_value,
            description=req.description,
            is_required=req.is_required,
        )
    except Exception as e:
        raise _handle_notebook_error(e)


@app.delete("/api/v1/notebooks/variables/{variable_id}", tags=["notebooks"])
async def delete_notebook_variable(
    variable_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Delete a notebook variable."""
    nb_svc = get_notebook_service()
    try:
        nb_svc.delete_variable(variable_id, requesting_user_id=str(user_ctx.user_id))
        return {"message": "Variable deleted"}
    except Exception as e:
        raise _handle_notebook_error(e)


@app.post("/api/v1/notebooks/{notebook_id}/duplicate", tags=["notebooks"])
async def duplicate_notebook(
    notebook_id: str,
    req: Request,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Duplicate a notebook (creates private copy)."""
    body = await req.json() or {}
    nb_svc = get_notebook_service()
    try:
        return nb_svc.duplicate_notebook(
            notebook_id=notebook_id,
            new_owner_id=str(user_ctx.user_id),
            new_name=body.get("new_name"),
        )
    except Exception as e:
        raise _handle_notebook_error(e)


# ============================================================================
# Approvals API
# ============================================================================

class CreateApprovalRequest(BaseModel):
    type: str  # join_team, private_space, quota_extend, team_create, storage_pool
    target_id: Optional[str] = None
    reason: Optional[str] = None
    params: Optional[dict] = None


class ProcessApprovalRequest(BaseModel):
    decision: str  # approved, rejected
    comment: Optional[str] = None


@app.post("/api/v1/approvals", tags=["approvals"])
async def create_approval(
    request: CreateApprovalRequest,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a new approval request."""
    svc = get_approval_service()
    try:
        return svc.create_approval_request(
            approval_type=request.type,
            applicant_id=str(user_ctx.user_id),
            target_id=request.target_id,
            reason=request.reason,
            params=request.params,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/approvals/my", tags=["approvals"])
async def get_my_approvals(
    status: Optional[str] = None,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get my approval requests."""
    svc = get_approval_service()
    try:
        return svc.get_my_requests(
            user_id=str(user_ctx.user_id),
            status=status,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/approvals/pending", tags=["approvals"])
async def get_pending_approvals(
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get pending approvals for admin."""
    svc = get_approval_service()
    try:
        return svc.get_pending_requests(approver_id=str(user_ctx.user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/approvals/{request_id}", tags=["approvals"])
async def get_approval(
    request_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get approval request details."""
    svc = get_approval_service()
    try:
        return svc.get_request(request_id=request_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/approvals/{request_id}/decide", tags=["approvals"])
async def process_approval_decision(
    request_id: str,
    body: ProcessApprovalRequest,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Process an approval decision (approve/reject)."""
    svc = get_approval_service()
    try:
        return svc.process_approval(
            request_id=request_id,
            approver_id=str(user_ctx.user_id),
            decision=body.decision,
            comment=body.comment,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/approvals/{request_id}", tags=["approvals"])
async def cancel_approval(
    request_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Cancel an approval request (by applicant)."""
    svc = get_approval_service()
    try:
        return svc.cancel_request(
            request_id=request_id,
            user_id=str(user_ctx.user_id),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Quota & Storage Pool APIs (Module C)
# ============================================================================

# --- Admin Storage Pool Management (C-1) ---
# All endpoints require admin role

@app.get("/api/v1/admin/pools", tags=["admin", "storage"])
async def get_storage_pools(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get all storage pools with statistics (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="管理员权限required")
    svc = get_storage_pool_service()
    try:
        return svc.get_all_pools_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/pools/{pool_id}", tags=["admin", "storage"])
async def get_storage_pool(pool_id: str, user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get storage pool details (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="管理员权限required")
    svc = get_storage_pool_service()
    try:
        result = svc.get_pool(pool_id)
        if not result:
            raise HTTPException(status_code=404, detail="Pool not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/admin/pools/{pool_id}/config", tags=["admin", "storage"])
async def update_pool_config(
    pool_id: str,
    reserved_bytes: Optional[int] = None,
    allow_overcommit: Optional[bool] = None,
    soft_warning_ratio: Optional[float] = None,
    hard_block_ratio: Optional[float] = None,
    buffer_ratio: Optional[float] = None,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update storage pool configuration (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="管理员权限required")
    svc = get_storage_pool_service()
    try:
        svc.update_pool_config(
            pool_id=pool_id,
            reserved_bytes=reserved_bytes,
            allow_overcommit=allow_overcommit,
            soft_warning_ratio=soft_warning_ratio,
            hard_block_ratio=hard_block_ratio,
            buffer_ratio=buffer_ratio,
        )
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/pools/{pool_id}/stats", tags=["admin", "storage"])
async def get_pool_stats(pool_id: str, user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get storage pool statistics (admin only)."""
    if user_ctx.role_name != "admin":
        raise HTTPException(status_code=403, detail="管理员权限required")
    svc = get_storage_pool_service()
    try:
        return svc.get_pool_stats(pool_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Quota Management (C-2) ---

@app.get("/api/v1/admin/quotas", tags=["admin", "quota"])
async def get_all_quotas(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get all quota allocations (admin)."""
    from file_manager.engine.models import Space
    session = get_space_lifecycle_service()._get_session()
    try:
        spaces = session.query(Space).filter(Space.committed_bytes > 0).all()
        return [
            {
                "space_id": s.id,
                "space_name": s.name,
                "owner_id": s.owner_id,
                "source_id": s.source_id,
                "quota_source": s.quota_source,
                "quota_type": s.quota_type,
                "committed_bytes": s.committed_bytes,
                "actual_used_bytes": s.actual_used_bytes,
            }
            for s in spaces
        ]
    finally:
        session.close()


@app.get("/api/v1/admin/quotas/spaces/{space_id}", tags=["admin", "quota"])
async def get_space_quota(space_id: str, user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get space quota details."""
    svc = get_space_lifecycle_service()
    try:
        result = svc.get_space_with_quota(space_id)
        if not result:
            raise HTTPException(status_code=404, detail="Space not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/admin/quotas/spaces/{space_id}", tags=["admin", "quota"])
async def update_space_quota(
    space_id: str,
    new_quota: int,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Update space quota."""
    svc = get_space_lifecycle_service()
    try:
        svc.update_space_quota(space_id, new_quota, updated_by=str(user_ctx.user_id))
        return {"status": "ok", "space_id": space_id, "new_quota": new_quota}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Quota Transfer API (C-3) ---

class QuotaTransferRequest(BaseModel):
    from_space_id: str
    to_space_id: str
    transfer_bytes: int
    reason: str
    duration_days: int = 7


@app.get("/api/v1/quota/transfers", tags=["quota"])
async def get_quota_transfers(
    space_id: Optional[str] = None,
    user_id: Optional[str] = None,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get quota transfer history."""
    svc = get_quota_transfer_service()
    try:
        return svc.get_transfer_history(space_id=space_id, user_id=user_id or str(user_ctx.user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/quota/transfers", tags=["quota"])
async def request_quota_transfer(
    request: QuotaTransferRequest,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Request quota transfer."""
    from file_manager.services.quota_transfer_service import QuotaTransferRequest as QTRequest
    svc = get_quota_transfer_service()
    try:
        qt_request = QTRequest(
            from_space_id=request.from_space_id,
            to_space_id=request.to_space_id,
            transfer_bytes=request.transfer_bytes,
            reason=request.reason,
            requested_by=str(user_ctx.user_id),
            duration_days=request.duration_days,
        )
        return svc.request_transfer(qt_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/quota/transfers/{transfer_id}/approve", tags=["quota"])
async def approve_quota_transfer(
    transfer_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Approve quota transfer."""
    svc = get_quota_transfer_service()
    try:
        svc.approve_transfer(transfer_id, approved_by=str(user_ctx.user_id))
        return {"status": "ok", "transfer_id": transfer_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/quota/transfers/{transfer_id}/reject", tags=["quota"])
async def reject_quota_transfer(
    transfer_id: str,
    reason: str = "",
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Reject quota transfer."""
    svc = get_quota_transfer_service()
    try:
        svc.reject_transfer(transfer_id, rejected_by=str(user_ctx.user_id), reason=reason)
        return {"status": "ok", "transfer_id": transfer_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v1/quota/transfers/{transfer_id}", tags=["quota"])
async def cancel_quota_transfer(
    transfer_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Cancel quota transfer request."""
    svc = get_quota_transfer_service()
    try:
        svc.cancel_transfer(transfer_id, user_id=str(user_ctx.user_id))
        return {"status": "ok", "transfer_id": transfer_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Capacity Alert API (C-4) ---

@app.get("/api/v1/admin/alerts", tags=["admin", "alerts"])
async def get_alerts(
    space_id: Optional[str] = None,
    pool_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Get capacity alert history."""
    svc = get_capacity_alert_service()
    try:
        return svc.get_alert_history(space_id=space_id, pool_id=pool_id, acknowledged=acknowledged)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/alerts/unacknowledged", tags=["admin", "alerts"])
async def get_unacknowledged_alerts(user_ctx: PermissionContext = Depends(get_current_user_ctx)):
    """Get unacknowledged alerts."""
    svc = get_capacity_alert_service()
    try:
        return svc.get_unacknowledged_alerts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v1/admin/alerts/{alert_id}/ack", tags=["admin", "alerts"])
async def acknowledge_alert(
    alert_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Acknowledge an alert."""
    svc = get_capacity_alert_service()
    try:
        svc.acknowledge_alert(alert_id, acknowledged_by=str(user_ctx.user_id))
        return {"status": "ok", "alert_id": alert_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Resource Plan API (C-5) ---

@app.get("/api/v1/plans", tags=["plans"])
async def get_available_plans():
    """Get available resource plans."""
    svc = get_resource_plan_service()
    try:
        return svc.get_available_plans()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/plans/{plan_id}", tags=["plans"])
async def get_plan(plan_id: str):
    """Get resource plan details."""
    svc = get_resource_plan_service()
    try:
        result = svc.get_plan(plan_id)
        if not result:
            raise HTTPException(status_code=404, detail="Plan not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/users/{user_id}/subscription", tags=["plans"])
async def subscribe_plan(
    user_id: str,
    plan_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Subscribe to a plan."""
    svc = get_resource_plan_service()
    try:
        svc.subscribe_plan(user_id=user_id, plan_id=plan_id)
        return {"status": "ok", "user_id": user_id, "plan_id": plan_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/{user_id}/subscription", tags=["plans"])
async def get_user_subscription(user_id: str):
    """Get user's subscription."""
    svc = get_resource_plan_service()
    try:
        result = svc.get_user_subscription(user_id)
        if not result:
            raise HTTPException(status_code=404, detail="No active subscription")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/users/{user_id}/usage", tags=["plans"])
async def get_user_usage(user_id: str):
    """Get user's resource usage."""
    svc = get_resource_plan_service()
    try:
        return svc.get_user_usage(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Space Lifecycle API (C-6) ---

class CreateSpaceRequest(BaseModel):
    name: str
    owner_id: str
    storage_pool_id: Optional[str] = None
    space_type: str = "private"
    team_id: Optional[str] = None
    quota_bytes: int = 0


@app.post("/api/v1/spaces", tags=["spaces"])
async def create_space(
    request: CreateSpaceRequest,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Create a new space with quota allocation."""
    from file_manager.services.space_lifecycle_service import CreateSpaceRequest as CSRequest
    svc = get_space_lifecycle_service()
    try:
        # Use storage_pool_id if provided, otherwise fall back to team_id
        pool_id = request.storage_pool_id or request.team_id
        cs_request = CSRequest(
            name=request.name,
            owner_id=request.owner_id,
            space_type=request.space_type,
            team_id=pool_id,
            quota_bytes=request.quota_bytes,
        )
        return svc.create_space_with_quota(cs_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/spaces/{space_id}/archive", tags=["spaces"])
async def archive_space(
    space_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Archive a space (reclaim quota)."""
    svc = get_space_lifecycle_service()
    try:
        svc.archive_space(space_id)
        return {"status": "ok", "space_id": space_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/spaces/{space_id}/transfer", tags=["spaces"])
async def transfer_space_ownership(
    space_id: str,
    new_owner_id: str,
    user_ctx: PermissionContext = Depends(get_current_user_ctx),
):
    """Transfer space ownership."""
    svc = get_space_lifecycle_service()
    try:
        svc.transfer_space_ownership(space_id, new_owner_id)
        return {"status": "ok", "space_id": space_id, "new_owner_id": new_owner_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Config API (Module F) ---

@app.get("/api/v1/config", tags=["config"])
async def get_config_api():
    """Get system configuration."""
    svc = get_config_service()
    try:
        return svc.get_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/config/{key}", tags=["config"])
async def get_config_value(key: str):
    """Get configuration value by key."""
    svc = get_config_service()
    try:
        value = svc.get(key)
        if value is None:
            raise HTTPException(status_code=404, detail="Config key not found")
        return {"key": key, "value": value}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SPA Fallback (must be last route)
# ============================================================================

@app.get("/{path:path}")
async def serve_spa(path: str):
    """Serve SPA for any non-API path (SPA fallback)."""
    from starlette.responses import FileResponse
    html_path = Path(__file__).parent / "web" / "app.html"
    if html_path.exists():
        return FileResponse(str(html_path))
    return HTMLResponse(content="<html><body><h1>Not found</h1></body></html>", status_code=404)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    config = get_config()
    uvicorn.run(app, host=config["host"], port=config["port"], reload=False)
