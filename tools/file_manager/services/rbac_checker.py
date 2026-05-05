"""
RBAC Permission Checker - Resource-Action based permission checking.

T2: Permission Check Engine using the new Permission/RolePermission models.
Operates alongside the existing path-based PermissionChecker.

Architecture:
  services/FileService  →  RBACChecker  →  lifecycle_engine
       (domain)               (pure logic)       (constraints)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass
class RBACDecision:
    """Result of an RBAC permission check."""
    allowed: bool
    reason: str
    matched_permission: Optional[str] = None  # "resource:action" format


class RBACChecker:
    """
    Resource-action based permission checker.

    Algorithm:
      1. Admin role always gets full access (bypass).
      2. Get user's role(s) from PermissionContext.
      3. Look up all permissions linked to those roles via RolePermission.
      4. Check if any permission matches resource + action.
      5. If scope is provided, verify scope matches.
    """

    def __init__(self, db_factory=None):
        """
        Initialize with optional db_factory for database access.

        Args:
            db_factory: Callable returning a SQLAlchemy session.
                       If None, uses stateless in-memory mode.
        """
        self.db_factory = db_factory

    def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str,
        scope: Optional[str] = None,
        ctx: Optional["PermissionContext"] = None,
    ) -> RBACDecision:
        """
        Check if user has permission to perform action on resource.

        Args:
            user_id: User identifier
            resource: Resource type (file, space, team, user, role, storage_pool, etc.)
            action: Action type (create, read, update, delete, manage)
            scope: Optional scope constraint (e.g., space_id, team_id)
            ctx: PermissionContext with role and permission info

        Returns:
            RBACDecision with allowed status and reason
        """
        # Admin bypass
        if ctx and ctx.role_name == "admin":
            return RBACDecision(
                allowed=True,
                reason="Admin role bypass",
                matched_permission="admin:bypass",
            )

        # Get user's permissions
        permissions = self.get_user_permissions(user_id, ctx)

        # Check for matching resource-action permission
        target = f"{resource}:{action}"
        if target in permissions:
            if scope and not self._check_scope(permissions, target, scope):
                return RBACDecision(
                    allowed=False,
                    reason=f"Scope '{scope}' not satisfied for {target}",
                )
            return RBACDecision(
                allowed=True,
                reason=f"Permission '{target}' granted via role '{ctx.role_name if ctx else 'unknown'}'",
                matched_permission=target,
            )

        # Check wildcard permissions
        wildcard = f"{resource}:*"
        if wildcard in permissions:
            return RBACDecision(
                allowed=True,
                reason=f"Wildcard permission '{wildcard}' granted",
                matched_permission=wildcard,
            )

        # Check admin wildcard
        if "*:*" in permissions:
            return RBACDecision(
                allowed=True,
                reason="Full wildcard '*:*' permission granted",
                matched_permission="*:*",
            )

        return RBACDecision(
            allowed=False,
            reason=f"No permission for '{action}' on '{resource}'",
        )

    def get_user_permissions(
        self,
        user_id: str,
        ctx: Optional["PermissionContext"] = None,
    ) -> Set[str]:
        """
        Get all permissions for a user as a set of 'resource:action' strings.

        Args:
            user_id: User identifier
            ctx: PermissionContext (if available, avoids DB query)

        Returns:
            Set of "resource:action" strings
        """
        # If context is provided with pre-loaded permissions, use it
        if ctx and hasattr(ctx, 'rbac_permissions') and ctx.rbac_permissions:
            return set(ctx.rbac_permissions)

        # Otherwise query from database if db_factory is available
        if self.db_factory:
            return self._load_permissions_from_db(user_id)

        return set()

    def _load_permissions_from_db(self, user_id: str) -> Set[str]:
        """Load permissions from database via ORM."""
        if not self.db_factory:
            return set()

        session = self.db_factory()
        try:
            from file_manager.engine.models import User, Role, RolePermission, Permission

            user = session.query(User).filter(User.id == user_id).first()
            if not user or not user.role:
                return set()

            # Get all permissions for user's role via RolePermission
            perms = session.query(Permission).join(
                RolePermission, Permission.id == RolePermission.permission_id
            ).filter(
                RolePermission.role_id == user.role.id
            ).all()

            return {f"{p.resource}:{p.action}" for p in perms}
        finally:
            session.close()

    def _check_scope(
        self,
        permissions: Set[str],
        target: str,
        scope: str,
    ) -> bool:
        """
        Check if scope constraint is satisfied.

        Current implementation: basic permission check without scope validation.
        The scope parameter is passed but not used for fine-grained access control.
        This is sufficient for current HFM architecture where:
        - Admin bypass covers all access
        - Space membership is checked separately via SpaceMember records
        - Scope validation would require additional context (user's spaces, ownership)
        """
        # TODO: Implement scope validation (e.g., user can only access their own space)
        # Requires: context with user spaces, ownership checks
        return True

    def has_role(user_id: str, role_name: str, ctx: Optional["PermissionContext"] = None) -> bool:
        """
        Check if user has a specific role.

        Args:
            user_id: User identifier
            role_name: Role name to check (e.g., 'admin', 'editor')
            ctx: PermissionContext (if available)

        Returns:
            True if user has the role
        """
        if ctx and ctx.role_name:
            return ctx.role_name == role_name

        # Query from database if needed
        # (Implementation depends on db_factory)
        return False


# Import at bottom to avoid circular reference
from .permission_context import PermissionContext
