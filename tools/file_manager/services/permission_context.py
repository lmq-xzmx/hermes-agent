"""
PermissionContext - Pure domain representation of a user's permission scope.

No ORM dependencies. Passed to PermissionEngine from the service layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class PermissionContext:
    """
    Immutable permission context for a user, created at the service layer
    boundary from AuthenticatedUser. Used to decouple PermissionEngine
    from ORM User objects.

    Supports both legacy path-based (PermissionRule) and new RBAC (Permission/RolePermission) models.
    """
    user_id: str
    username: str
    role_name: Optional[str]       # None = no role assigned
    permission_rules: List[str] = field(default_factory=list)     # Legacy: List["read,write:/projects/**"]
    rbac_permissions: List[str] = field(default_factory=list)     # RBAC: List["file:read", "space:create"]
    active_team_id: Optional[str] = None   # Deprecated: use active_space_id instead
    active_space_id: Optional[str] = None   # Current active space for file operations

    @classmethod
    def from_authenticated_user(cls, user, active_team_id: Optional[str] = None, active_space_id: Optional[str] = None) -> PermissionContext:
        """Create from AuthenticatedUser (services.auth_service)."""
        return cls(
            user_id=user.id,
            username=user.username,
            role_name=user.role_name,
            permission_rules=user.permission_rules if hasattr(user, 'permission_rules') else [],
            rbac_permissions=cls._load_rbac_permissions(user),
            active_team_id=active_team_id,
            active_space_id=active_space_id,
        )

    @classmethod
    def _load_rbac_permissions(cls, user) -> List[str]:
        """Load RBAC permissions from user role via RolePermission.

        Supports both ORM User objects (with .role relationship) and
        AuthenticatedUser domain objects (with .role_id only).
        """
        perms = []
        # For ORM User objects with loaded role relationship
        if hasattr(user, 'role') and user.role and hasattr(user.role, 'role_permissions'):
            for rp in user.role.role_permissions:
                if rp.permission:
                    perms.append(f"{rp.permission.resource}:{rp.permission.action}")
        # For AuthenticatedUser domain objects - permissions are pre-computed
        elif hasattr(user, 'rbac_permissions') and user.rbac_permissions:
            perms = list(user.rbac_permissions)
        # For AuthenticatedUser without pre-computed permissions, use role_id
        elif hasattr(user, 'role_id') and user.role_id:
            # Need to load from DB - this requires a db session which we don't have here
            # For now, return empty list; permissions can be loaded via separate API
            pass
        return perms

    def get_rbac_permission_set(self) -> Set[str]:
        """Return RBAC permissions as a set for O(1) lookup."""
        return set(self.rbac_permissions)
