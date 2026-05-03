"""
Services Layer - Business logic independent of HTTP layer.

Architecture:
  api/          → FastAPI routes (HTTP layer, thin wrappers)
  services/     → Business logic (pure Python, no FastAPI, no ORM)
  engine/       → Data access and storage primitives

NOTE: This __init__.py does NOT eagerly import from submodules to avoid
circular import chains with api/__init__.py → auth.py → services.auth_service.
Always import directly from submodules:
    from file_manager.services.auth_service import AuthService
    from file_manager.services.file_service import FileService
"""

# Lazy import facade — actual imports happen at runtime inside functions/methods.
# This avoids the circular import: services → auth_service → api.dto → api.__init__
def __getattr__(name):
    if name == "AuthService":
        from .auth_service import AuthService
        return AuthService
    if name == "AuthenticatedUser":
        from .auth_service import AuthenticatedUser
        return AuthenticatedUser
    if name == "AuthResult":
        from .auth_service import AuthResult
        return AuthResult
    if name == "FileService":
        from .file_service import FileService
        return FileService
    if name in ("FileAccessDenied", "FileNotFound", "FileAlreadyExists", "DirectoryNotEmpty"):
        from .file_service import FileAccessDenied, FileNotFound, FileAlreadyExists, DirectoryNotEmpty
        return locals()[name]
    if name == "PermissionChecker":
        from .permission_checker import PermissionChecker
        return PermissionChecker
    if name == "PermissionContext":
        from .permission_context import PermissionContext
        return PermissionContext
    if name == "PermissionDecision":
        from .permission_checker import PermissionDecision
        return PermissionDecision
    if name == "Operation":
        from .permission_checker import Operation
        return Operation
    if name in ("EventBus", "EventType", "Event", "get_event_bus"):
        from .event_bus import EventBus, EventType, Event, get_event_bus
        return locals()[name]
    if name == "AuditEventSubscriber":
        from .audit_subscriber import AuditEventSubscriber
        return AuditEventSubscriber
    if name == "ShareService":
        from .share_service import ShareService
        return ShareService
    if name == "AdminService":
        from .admin_service import AdminService
        return AdminService
    if name in ("ShareNotFound", "ShareAccessDenied", "ShareExpired", "ShareDeactivated",
                "ShareLimitReached", "SharePasswordRequired", "ShareInvalidPassword",
                "ShareValidationError"):
        from .share_service import (
            ShareNotFound, ShareAccessDenied, ShareExpired, ShareDeactivated,
            ShareLimitReached, SharePasswordRequired, ShareInvalidPassword,
            ShareValidationError,
        )
        return locals()[name]
    if name in ("AdminAccessDenied", "UserNotFound", "UserAlreadyExists",
                "RoleNotFound", "RoleAlreadyExists", "RoleNotModifiable",
                "RuleNotFound", "CannotDeleteSelf", "CannotDeleteRoleWithUsers"):
        from .admin_service import (
            AdminAccessDenied, UserNotFound, UserAlreadyExists,
            RoleNotFound, RoleAlreadyExists, RoleNotModifiable,
            RuleNotFound, CannotDeleteSelf, CannotDeleteRoleWithUsers,
        )
        return locals()[name]
    if name == "SpaceService":
        from .space_service import SpaceService
        return SpaceService
    if name in ("SpaceNotFound", "SpaceQuotaExceeded", "SpaceRequestNotFound",
                "SpaceRequestInvalid", "NotSpaceOwner", "UserAlreadyInSpace",
                "CredentialNotFound", "CredentialExpired", "QuotaExceeded"):
        from .space_service import (
            SpaceNotFound, SpaceQuotaExceeded, SpaceRequestNotFound,
            SpaceRequestInvalid, NotSpaceOwner, UserAlreadyInSpace,
            CredentialNotFound, CredentialExpired, QuotaExceeded,
        )
        return locals()[name]
    if name == "AdminAnalyticsService":
        from .admin_analytics_service import AdminAnalyticsService
        return AdminAnalyticsService
    if name == "AdminAccessDenied":
        from .admin_analytics_service import AdminAccessDenied
        return AdminAccessDenied
    if name == "ConstraintContext":
        from .lifecycle_engine import ConstraintContext
        return ConstraintContext
    if name == "ConstraintResult":
        from .lifecycle_engine import ConstraintResult
        return ConstraintResult
    if name == "ConstraintRule":
        from .lifecycle_engine import ConstraintRule
        return ConstraintRule
    if name == "ConstraintRegistry":
        from .lifecycle_engine import ConstraintRegistry
        return ConstraintRegistry
    if name == "LifecycleViolation":
        from .lifecycle_engine import LifecycleViolation
        return LifecycleViolation
    if name == "get_constraint_registry":
        from .lifecycle_engine import get_constraint_registry
        return get_constraint_registry
    if name == "QuotaService":
        from .quota_service import QuotaService
        return QuotaService
    if name in ("QuotaExceeded",):
        from .space_service import QuotaExceeded
        return QuotaExceeded
    if name == "ApprovalService":
        from .approval_service import ApprovalService
        return ApprovalService
    if name in ("ApprovalNotFound", "ApprovalInvalidStatus", "NotAuthorized", "ApprovalRequired"):
        from .approval_service import (
            ApprovalNotFound, ApprovalInvalidStatus, NotAuthorized, ApprovalRequired,
        )
        return locals()[name]
    if name == "SubscriptionService":
        from .subscription_service import SubscriptionService
        return SubscriptionService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
