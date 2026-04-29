"""
AdminService - Pure business logic for admin operations.

No FastAPI, no HTTPException. Uses PermissionContext for user identity.
Uses EventBus for audit events. Uses db_factory for ORM operations
(since admin operations manage users/roles/rules in the DB).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable

from .permission_context import PermissionContext
from .event_bus import EventBus, EventType, Event, get_event_bus
from ..api.dto import (
    CreateUserRequestDTO, AuditQueryRequestDTO, AuditQueryResponseDTO,
    AuditLogEntryDTO, UserListItemDTO, UserListResponseDTO, RoleDTO,
    MessageResponseDTO,
)
from ..engine.models import User, Role, PermissionRule, AuditLog, AuditAction
from ..engine.audit import AuditLogger


# =============================================================================
# Service Errors (pure domain errors, not HTTP)
# =============================================================================

class AdminAccessDenied(Exception):
    """Admin access required but user is not an admin."""
    def __init__(self, reason: str = "Admin access required"):
        self.reason = reason
        super().__init__(reason)


class UserNotFound(Exception):
    """User not found."""
    pass


class UserAlreadyExists(Exception):
    """Username already exists."""
    pass


class RoleNotFound(Exception):
    """Role not found."""
    pass


class RoleAlreadyExists(Exception):
    """Role already exists."""
    pass


class RoleNotModifiable(Exception):
    """Cannot modify system role."""
    pass


class RuleNotFound(Exception):
    """Permission rule not found."""
    pass


class CannotDeleteSelf(Exception):
    """Cannot delete your own user account."""
    pass


class CannotDeleteRoleWithUsers(Exception):
    """Cannot delete role that has assigned users."""
    def __init__(self, user_count: int):
        self.user_count = user_count
        super().__init__(f"Cannot delete role with {user_count} assigned users")


# =============================================================================
# AdminService
# =============================================================================

class AdminService:
    """
    Admin operation business logic. Stateless.

    Flow:
      API route (thin HTTP) → AdminService (pure logic) → ORM (User, Role, Rule models)

    AdminService:
      - Checks that user has admin role via PermissionContext
      - Uses db_factory for ORM operations (exception to the rule - admin needs DB access)
      - Uses EventBus for audit logging
      - Returns DTOs for responses

    Note:
      This is the one service that DOES use ORM directly via db_factory,
      since it manages users/roles/rules in the database. Most other services
      (FileService, ShareService) use StorageEngine for filesystem operations.
    """

    def __init__(
        self,
        db_factory: Callable,
        event_bus: Optional[EventBus] = None,
    ):
        self.db_factory = db_factory
        self._event_bus = event_bus or get_event_bus()

    # -------------------------------------------------------------------------
    # Access Check Helper
    # -------------------------------------------------------------------------

    def _require_admin(self, ctx: PermissionContext) -> None:
        """Raise AdminAccessDenied if user is not an admin."""
        if ctx.role_name != "admin":
            raise AdminAccessDenied(f"User '{ctx.username}' is not an admin")

    # -------------------------------------------------------------------------
    # User Management
    # -------------------------------------------------------------------------

    def list_users(
        self,
        user_ctx: PermissionContext,
        limit: int = 100,
        offset: int = 0,
    ) -> UserListResponseDTO:
        """List all users. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            users = session.query(User).offset(offset).limit(limit).all()
            total = session.query(User).count()

            items = [
                UserListItemDTO(
                    id=u.id,
                    username=u.username,
                    email=u.email,
                    role_id=u.role_id,
                    role_name=u.role.name if u.role else None,
                    is_active=u.is_active,
                    created_at=u.created_at,
                    last_login=u.last_login,
                )
                for u in users
            ]

            self._event_bus.publish(Event.create(
                EventType.FILE_LIST,  # Reusing existing event type
                {"operation": "admin.list_users", "limit": limit, "offset": offset},
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return UserListResponseDTO(users=items, total=total)
        finally:
            session.close()

    def get_user(
        self,
        user_id: str,
        user_ctx: PermissionContext,
    ) -> UserListItemDTO:
        """Get user by ID. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFound(f"User not found: {user_id}")

            return UserListItemDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                role_id=user.role_id,
                role_name=user.role.name if user.role else None,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
            )
        finally:
            session.close()

    def create_user(
        self,
        request: CreateUserRequestDTO,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> UserListItemDTO:
        """Create a new user. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            # Check if username exists
            existing = session.query(User).filter(User.username == request.username).first()
            if existing:
                raise UserAlreadyExists(f"Username already exists: {request.username}")

            # Get role if specified
            role = None
            if request.role_id:
                role = session.query(Role).filter(Role.id == request.role_id).first()
                if not role:
                    raise RoleNotFound(f"Role not found: {request.role_id}")

            user = User(
                username=request.username,
                email=request.email,
                role_id=role.id if role else None,
            )
            user.set_password(request.password)

            session.add(user)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_USER_CREATE,
                {
                    "user_id": user.id,
                    "username": user.username,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return UserListItemDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                role_id=user.role_id,
                role_name=role.name if role else None,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
            )
        finally:
            session.close()

    def update_user(
        self,
        user_id: str,
        email: Optional[str],
        role_id: Optional[str],
        is_active: Optional[bool],
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> UserListItemDTO:
        """Update a user. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFound(f"User not found: {user_id}")

            updated_fields = {}

            if email is not None:
                user.email = email
                updated_fields["email"] = email
            if role_id is not None:
                role = session.query(Role).filter(Role.id == role_id).first()
                if not role:
                    raise RoleNotFound(f"Role not found: {role_id}")
                user.role_id = role_id
                updated_fields["role_id"] = role_id
            if is_active is not None:
                user.is_active = is_active
                updated_fields["is_active"] = is_active

            user.updated_at = datetime.utcnow()
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_USER_UPDATE,
                {
                    "user_id": user_id,
                    "updated_fields": updated_fields,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return UserListItemDTO(
                id=user.id,
                username=user.username,
                email=user.email,
                role_id=user.role_id,
                role_name=user.role.name if user.role else None,
                is_active=user.is_active,
                created_at=user.created_at,
                last_login=user.last_login,
            )
        finally:
            session.close()

    def delete_user(
        self,
        user_id: str,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> MessageResponseDTO:
        """Delete a user. Requires admin role. Cannot delete yourself."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise UserNotFound(f"User not found: {user_id}")

            if user.id == user_ctx.user_id:
                raise CannotDeleteSelf("Cannot delete your own user account")

            username = user.username
            session.delete(user)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_USER_DELETE,
                {
                    "user_id": user_id,
                    "username": username,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return MessageResponseDTO(message=f"User '{username}' deleted")
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Role Management
    # -------------------------------------------------------------------------

    def list_roles(
        self,
        user_ctx: PermissionContext,
    ) -> List[RoleDTO]:
        """List all roles. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            roles = session.query(Role).all()
            return [
                RoleDTO(
                    id=r.id,
                    name=r.name,
                    description=r.description,
                    permission_rules=[rule.to_primitive() for rule in r.permission_rules],
                )
                for r in roles
            ]
        finally:
            session.close()

    def get_role(
        self,
        role_id: str,
        user_ctx: PermissionContext,
    ) -> RoleDTO:
        """Get role by ID with its rules. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise RoleNotFound(f"Role not found: {role_id}")

            return RoleDTO(
                id=role.id,
                name=role.name,
                description=role.description,
                permission_rules=[rule.to_primitive() for rule in role.permission_rules],
            )
        finally:
            session.close()

    def create_role(
        self,
        name: str,
        description: Optional[str],
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> RoleDTO:
        """Create a new role. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            existing = session.query(Role).filter(Role.name == name).first()
            if existing:
                raise RoleAlreadyExists(f"Role already exists: {name}")

            role = Role(
                name=name,
                description=description,
                is_system=False,
            )

            session.add(role)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,  # Using existing event type
                {
                    "operation": "role_create",
                    "role_id": role.id,
                    "name": role.name,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return RoleDTO(
                id=role.id,
                name=role.name,
                description=role.description,
                permission_rules=[],
            )
        finally:
            session.close()

    def update_role(
        self,
        role_id: str,
        description: Optional[str],
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> RoleDTO:
        """Update a role. Requires admin role. Cannot modify system roles."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise RoleNotFound(f"Role not found: {role_id}")

            if role.is_system:
                raise RoleNotModifiable("Cannot modify system role")

            if description is not None:
                role.description = description

            role.updated_at = datetime.utcnow()
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,
                {
                    "role_id": role_id,
                    "description": description,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return RoleDTO(
                id=role.id,
                name=role.name,
                description=role.description,
                permission_rules=[rule.to_primitive() for rule in role.permission_rules],
            )
        finally:
            session.close()

    def delete_role(
        self,
        role_id: str,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> MessageResponseDTO:
        """Delete a role. Requires admin role. Cannot delete system roles or roles with users."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise RoleNotFound(f"Role not found: {role_id}")

            if role.is_system:
                raise RoleNotModifiable("Cannot delete system role")

            # Check if any users have this role
            user_count = session.query(User).filter(User.role_id == role_id).count()
            if user_count > 0:
                raise CannotDeleteRoleWithUsers(user_count)

            role_name = role.name
            session.delete(role)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,
                {
                    "operation": "role_delete",
                    "role_id": role_id,
                    "name": role_name,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return MessageResponseDTO(message=f"Role '{role_name}' deleted")
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Permission Rule Management
    # -------------------------------------------------------------------------

    def list_rules(
        self,
        user_ctx: PermissionContext,
        role_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List permission rules, optionally filtered by role. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            query = session.query(PermissionRule)
            if role_id:
                query = query.filter(PermissionRule.role_id == role_id)
            rules = query.all()
            return [r.to_dict() for r in rules]
        finally:
            session.close()

    def create_rule(
        self,
        role_id: str,
        path_pattern: str,
        permissions: str,
        priority: int,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new permission rule. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            # Verify role exists
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise RoleNotFound(f"Role not found: {role_id}")

            rule = PermissionRule(
                role_id=role_id,
                path_pattern=path_pattern,
                permissions=permissions,
                priority=priority,
                created_by=user_ctx.user_id,
            )

            session.add(rule)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,
                {
                    "operation": "rule_create",
                    "rule_id": rule.id,
                    "pattern": path_pattern,
                    "role": role.name,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return rule.to_dict()
        finally:
            session.close()

    def update_rule(
        self,
        rule_id: str,
        path_pattern: Optional[str],
        permissions: Optional[str],
        priority: Optional[int],
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a permission rule. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            rule = session.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
            if not rule:
                raise RuleNotFound(f"Rule not found: {rule_id}")

            if path_pattern is not None:
                rule.path_pattern = path_pattern
            if permissions is not None:
                rule.permissions = permissions
            if priority is not None:
                rule.priority = priority

            rule.updated_at = datetime.utcnow()
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,
                {
                    "operation": "rule_update",
                    "rule_id": rule_id,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return rule.to_dict()
        finally:
            session.close()

    def delete_rule(
        self,
        rule_id: str,
        user_ctx: PermissionContext,
        ip_address: Optional[str] = None,
    ) -> MessageResponseDTO:
        """Delete a permission rule. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            rule = session.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
            if not rule:
                raise RuleNotFound(f"Rule not found: {rule_id}")

            session.delete(rule)
            session.commit()

            # Audit via event bus
            self._event_bus.publish(Event.create(
                EventType.ADMIN_ROLE_UPDATE,
                {
                    "operation": "rule_delete",
                    "rule_id": rule_id,
                    "ip_address": ip_address,
                },
                user_id=user_ctx.user_id, username=user_ctx.username,
            ))

            return MessageResponseDTO(message="Rule deleted")
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Audit Log Access
    # -------------------------------------------------------------------------

    def query_audit_logs(
        self,
        request: AuditQueryRequestDTO,
        user_ctx: PermissionContext,
    ) -> AuditQueryResponseDTO:
        """Query audit logs with filters. Requires admin role."""
        self._require_admin(user_ctx)

        session = self.db_factory()
        try:
            audit = AuditLogger(session)

            # Parse dates if provided
            start_date = None
            end_date = None
            if request.start_date:
                start_date = datetime.fromisoformat(request.start_date)
            if request.end_date:
                end_date = datetime.fromisoformat(request.end_date)

            logs = audit.query(
                user_id=request.user_id,
                action=request.action,
                path=request.path,
                result=request.result,
                start_date=start_date,
                end_date=end_date,
                limit=request.limit,
                offset=request.offset,
            )

            entries = [
                AuditLogEntryDTO(
                    id=log.id,
                    timestamp=log.created_at,
                    action=log.action,
                    result=log.result,
                    user_id=log.user_id,
                    username=log.user.username if log.user else None,
                    path=log.path,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    extra=log.extra,
                )
                for log in logs
            ]

            return AuditQueryResponseDTO(logs=entries, total=len(entries))
        finally:
            session.close()
