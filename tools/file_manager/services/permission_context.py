"""
PermissionContext - Pure domain representation of a user's permission scope.

No ORM dependencies. Passed to PermissionEngine from the service layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class PermissionContext:
    """
    Immutable permission context for a user, created at the service layer
    boundary from AuthenticatedUser. Used to decouple PermissionEngine
    from ORM User objects.
    """
    user_id: str
    username: str
    role_name: Optional[str]       # None = no role assigned
    permission_rules: List[str]     # List["read,write:/projects/**", "read:/public/**"]
    active_team_id: Optional[str] = None   # Current active team for file operations

    @classmethod
    def from_authenticated_user(cls, user, active_team_id: Optional[str] = None) -> PermissionContext:
        """Create from AuthenticatedUser (services.auth_service)."""
        return cls(
            user_id=user.id,
            username=user.username,
            role_name=user.role_name,
            permission_rules=user.permission_rules,
            active_team_id=active_team_id,
        )
