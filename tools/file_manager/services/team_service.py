"""
TeamService - Business logic for StoragePools, Teams, TeamMembers, and Credentials.
Handles quota enforcement, pool detection, and invite-token lifecycle.
"""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ..engine.models import (
    StoragePool, Team, TeamMember, TeamCredential, User, Base
)
from ..engine.storage import StorageEngine


# =============================================================================
# Domain Errors
# =============================================================================

class StoragePoolNotFound(Exception):
    """Pool does not exist."""
    pass


class PoolOutOfSpace(Exception):
    """Pool has insufficient free space for this operation."""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"需要 {required} 字节，存储池剩余 {available} 字节")


class TeamNotFound(Exception):
    """Team does not exist."""
    pass


class TeamQuotaExceeded(Exception):
    """Team quota (max_bytes) reached."""
    def __init__(self, team_name: str, max_bytes: int, used_bytes: int, required: int):
        self.team_name = team_name
        self.max_bytes = max_bytes
        self.used_bytes = used_bytes
        self.required = required
        super().__init__(
            f"团队「{team_name}」配额已满（{used_bytes}/{max_bytes} 字节），"
            f"还需 {required} 字节"
        )


class CredentialNotFound(Exception):
    """Credential token not found or invalid."""
    pass


class CredentialExpired(Exception):
    """Credential token has expired or is fully used."""
    pass


class UserAlreadyInTeam(Exception):
    """User is already a member of this team."""
    pass


class NotTeamOwner(Exception):
    """Only the team owner can perform this action."""
    pass


# =============================================================================
# TeamService
# =============================================================================

class TeamService:
    """
    Stateless business-logic service for teams, pools, and credentials.

    Storage layout per team:
      {pool_base_path}/teams/{team_id}/
        members/
          {user_id}/           ← each member's personal directory
            ...

    Each user sees only their own member subdirectory, not the whole team tree.
    """

    def __init__(self, db_factory):
        self._db = db_factory

    # -------------------------------------------------------------------------
    # Storage Pool Management
    # -------------------------------------------------------------------------

    def list_pools(self) -> List[Dict[str, Any]]:
        """List all storage pools."""
        session = self._db()
        try:
            pools = session.query(StoragePool).all()
            return [p.to_dict() for p in pools]
        finally:
            session.close()

    def create_pool(
        self,
        name: str,
        base_path: str,
        protocol: str = "local",
        total_bytes: int = 0,
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Add a new storage pool.

        - base_path: absolute path on disk (or URI like smb://...)
        - protocol: "local" | "smb" | "nfs" | "s3" | "minio"
        - total_bytes: 0 = auto-detect from disk (local only)
        """
        session = self._db()
        try:
            # Resolve and ensure directory exists for local protocol
            if protocol == "local":
                resolved = str(Path(os.path.expanduser(base_path)).resolve())
                os.makedirs(resolved, exist_ok=True)
                if total_bytes == 0:
                    stat = shutil.disk_usage(resolved)
                    free = stat.free
                    total = stat.total
                else:
                    free = total_bytes  # trust admin's number
                    total = total_bytes
            else:
                resolved = base_path
                total = total_bytes
                free = 0  # can't auto-detect remote

            pool = StoragePool(
                name=name,
                base_path=resolved,
                protocol=protocol,
                total_bytes=total,
                free_bytes=free,
                description=description,
                is_active=True,
            )
            session.add(pool)
            session.commit()
            return pool.to_dict()
        finally:
            session.close()

    def refresh_pool_space(self, pool_id: str) -> Dict[str, Any]:
        """Re-probe free space on a local pool."""
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                raise StoragePoolNotFound(f"存储池 {pool_id} 不存在")
            if pool.protocol == "local":
                try:
                    stat = shutil.disk_usage(pool.base_path)
                    pool.free_bytes = stat.free
                    if pool.total_bytes == 0:
                        pool.total_bytes = stat.total
                except OSError:
                    pass  # disk not reachable; keep cached value
            session.commit()
            return pool.to_dict()
        finally:
            session.close()

    def delete_pool(self, pool_id: str) -> None:
        """Delete a pool (fails if any team uses it)."""
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                raise StoragePoolNotFound()
            team_count = session.query(Team).filter(Team.storage_pool_id == pool_id).count()
            if team_count > 0:
                raise RuntimeError(f"该存储池仍有 {team_count} 个团队使用，无法删除")
            session.delete(pool)
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Team Management
    # -------------------------------------------------------------------------

    def list_teams(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List teams. If user_id given, returns only teams that user is a member of.
        """
        session = self._db()
        try:
            query = session.query(Team)
            if user_id:
                team_ids = (
                    session.query(TeamMember.team_id)
                    .filter(TeamMember.user_id == user_id)
                    .all()
                )
                team_ids = [t[0] for t in team_ids]
                if not team_ids:
                    return []
                query = query.filter(Team.id.in_(team_ids))
            return [t.to_dict() for t in query.all()]
        finally:
            session.close()

    def get_team(self, team_id: str) -> Dict[str, Any]:
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound(f"团队 {team_id} 不存在")
            return team.to_dict(include_members=True)
        finally:
            session.close()

    def create_team(
        self,
        name: str,
        owner_id: str,
        storage_pool_id: str,
        max_bytes: int = 0,
    ) -> Dict[str, Any]:
        """
        Create a new team and make the owner its first member.

        - max_bytes: 0 means unlimited (bounded only by pool free space)
        """
        session = self._db()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == storage_pool_id).first()
            if not pool:
                raise StoragePoolNotFound(f"存储池 {storage_pool_id} 不存在")
            if not pool.is_active:
                raise RuntimeError("该存储池已停用")

            team = Team(
                name=name,
                owner_id=owner_id,
                storage_pool_id=storage_pool_id,
                max_bytes=max_bytes,
                used_bytes=0,
                is_active=True,
            )
            session.add(team)
            session.flush()  # get ID before adding member

            # Owner becomes first member
            member = TeamMember(
                team_id=team.id,
                user_id=owner_id,
                role="owner",
            )
            session.add(member)

            # Create physical team directory
            team_root = os.path.join(pool.base_path, "teams", team.id)
            members_dir = os.path.join(team_root, "members")
            os.makedirs(members_dir, exist_ok=True)

            session.commit()
            return team.to_dict(include_members=True)
        finally:
            session.close()

    def update_team(
        self,
        team_id: str,
        requesting_user_id: str,
        name: Optional[str] = None,
        max_bytes: Optional[int] = None,
        is_active: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update team settings. Only owner can do this."""
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()
            if team.owner_id != requesting_user_id:
                raise NotTeamOwner("只有团队所有者可以修改团队设置")
            if name is not None:
                team.name = name
            if max_bytes is not None:
                team.max_bytes = max_bytes
            if is_active is not None:
                team.is_active = is_active
            team.updated_at = datetime.utcnow()
            session.commit()
            return team.to_dict()
        finally:
            session.close()

    def delete_team(self, team_id: str, requesting_user_id: str) -> None:
        """Delete a team and all its files. Only owner can do this."""
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()
            if team.owner_id != requesting_user_id:
                raise NotTeamOwner()
            # Delete physical files
            pool = team.storage_pool
            if pool and pool.protocol == "local":
                team_root = os.path.join(pool.base_path, "teams", team.id)
                if os.path.exists(team_root):
                    shutil.rmtree(team_root)
            session.delete(team)
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Team Members
    # -------------------------------------------------------------------------

    def list_members(self, team_id: str) -> List[Dict[str, Any]]:
        session = self._db()
        try:
            members = session.query(TeamMember).filter(TeamMember.team_id == team_id).all()
            return [m.to_dict() for m in members]
        finally:
            session.close()

    def remove_member(
        self,
        team_id: str,
        target_user_id: str,
        requesting_user_id: str,
    ) -> None:
        """
        Remove a user from a team.
        - Only owner can remove others; users can remove themselves.
        - Cannot remove the last owner.
        """
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()

            member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == target_user_id)
                .first()
            )
            if not member:
                raise RuntimeError("该用户不是团队成员")

            is_owner = requesting_user_id == team.owner_id
            is_self = requesting_user_id == target_user_id

            if not is_owner and not is_self:
                raise NotTeamOwner()

            if member.role == "owner":
                owner_count = (
                    session.query(TeamMember)
                    .filter(TeamMember.team_id == team_id, TeamMember.role == "owner")
                    .count()
                )
                if owner_count <= 1:
                    raise RuntimeError("无法移除唯一的所有者；请先转移所有权或删除团队")

            session.delete(member)
            session.commit()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Credentials
    # -------------------------------------------------------------------------

    def list_credentials(
        self,
        team_id: str,
        requesting_user_id: str,
    ) -> List[Dict[str, Any]]:
        """List all credentials for a team (owner only)."""
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()
            if team.owner_id != requesting_user_id:
                raise NotTeamOwner()
            creds = session.query(TeamCredential).filter(TeamCredential.team_id == team_id).all()
            return [c.to_dict() for c in creds]
        finally:
            session.close()

    def create_credential(
        self,
        team_id: str,
        created_by: str,
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generate an invite token for a team.
        Returns the token (only time it is shown in full).
        """
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()
            if team.owner_id != created_by:
                raise NotTeamOwner()

            token = secrets.token_urlsafe(16)  # ~22 chars, URL-safe
            cred = TeamCredential(
                team_id=team_id,
                token=token,
                max_uses=max_uses,
                expires_at=expires_at,
                created_by=created_by,
                is_active=True,
            )
            session.add(cred)
            session.commit()
            return cred.to_dict(include_token=True)
        finally:
            session.close()

    def revoke_credential(self, credential_id: str, requesting_user_id: str) -> None:
        session = self._db()
        try:
            cred = session.query(TeamCredential).filter(TeamCredential.id == credential_id).first()
            if not cred:
                raise CredentialNotFound()
            team = cred.team
            if team.owner_id != requesting_user_id:
                raise NotTeamOwner()
            cred.is_active = False
            session.commit()
        finally:
            session.close()

    def join_via_credential(
        self,
        token: str,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Use an invite token to join a team.
        Creates the user's personal directory under the team.
        """
        session = self._db()
        try:
            cred = session.query(TeamCredential).filter(TeamCredential.token == token).first()
            if not cred:
                raise CredentialNotFound("凭证不存在")
            if not cred.is_valid():
                raise CredentialExpired("凭证已过期或已达使用次数上限")

            team = cred.team
            if not team.is_active:
                raise RuntimeError("该团队已停用")

            # Check if already a member
            existing = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team.id, TeamMember.user_id == user_id)
                .first()
            )
            if existing:
                raise UserAlreadyInTeam(f"你已经是团队「{team.name}」的成员了")

            member = TeamMember(
                team_id=team.id,
                user_id=user_id,
                role="member",
            )
            session.add(member)

            # Increment usage counter
            cred.used_count += 1

            # Create personal directory for this user in the team
            pool = team.storage_pool
            if pool and pool.protocol == "local":
                user_dir = os.path.join(pool.base_path, "teams", team.id, "members", user_id)
                os.makedirs(user_dir, exist_ok=True)

            session.commit()
            return team.to_dict()
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # User's teams (for the file-manager UI)
    # -------------------------------------------------------------------------

    def get_user_teams_summary(self, user_id: str) -> List[Dict[str, Any]]:
        """Return all teams a user belongs to, with quota info."""
        session = self._db()
        try:
            memberships = (
                session.query(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .all()
            )
            result = []
            for m in memberships:
                team = m.team
                pool = team.storage_pool
                result.append({
                    "member_id": m.id,
                    "team_id": team.id,
                    "team_name": team.name,
                    "role": m.role,
                    "pool_name": pool.name if pool else None,
                    "pool_protocol": pool.protocol if pool else None,
                    "max_bytes": team.max_bytes,
                    "used_bytes": team.used_bytes,
                    "pool_free_bytes": pool.free_bytes if pool else 0,
                    "pool_total_bytes": pool.total_bytes if pool else 0,
                })
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Quota Enforcement (called by FileService before writes)
    # -------------------------------------------------------------------------

    def check_quota_for_write(
        self,
        team_id: str,
        content_size: int,
    ) -> None:
        """
        Check whether a write of `content_size` bytes is allowed.

        Checks:
          1. Pool has enough free space
          2. Team quota (max_bytes) not exceeded
        Raises PoolOutOfSpace or TeamQuotaExceeded.
        """
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()

            pool = team.storage_pool
            if not pool:
                raise RuntimeError("团队未关联存储池")

            # 1. Pool free space check
            if pool.protocol == "local" and pool.free_bytes > 0:
                if content_size > pool.free_bytes:
                    raise PoolOutOfSpace(required=content_size, available=pool.free_bytes)
            elif pool.free_bytes == 0 and pool.protocol == "local":
                # Re-probe
                try:
                    stat = shutil.disk_usage(pool.base_path)
                    pool.free_bytes = stat.free
                    session.commit()
                    if content_size > pool.free_bytes:
                        raise PoolOutOfSpace(required=content_size, available=pool.free_bytes)
                except OSError:
                    pass  # can't probe; allow write attempt

            # 2. Team quota check (max_bytes == 0 means unlimited)
            if team.max_bytes > 0:
                if team.used_bytes + content_size > team.max_bytes:
                    raise TeamQuotaExceeded(
                        team_name=team.name,
                        max_bytes=team.max_bytes,
                        used_bytes=team.used_bytes,
                        required=content_size,
                    )
        finally:
            session.close()

    def record_write(self, team_id: str, bytes_written: int) -> None:
        """Called after a successful write to update used_bytes."""
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if team:
                team.used_bytes = max(0, team.used_bytes + bytes_written)
                session.commit()
        finally:
            session.close()

    def record_delete(self, team_id: str, bytes_freed: int) -> None:
        """Called after a successful delete to update used_bytes."""
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if team:
                team.used_bytes = max(0, team.used_bytes - bytes_freed)
                session.commit()
        finally:
            session.close()

    def get_user_personal_path(self, team_id: str, user_id: str) -> str:
        """
        Return the absolute personal directory path for a user within a team.
        Format: {pool_base_path}/teams/{team_id}/members/{user_id}
        """
        session = self._db()
        try:
            team = session.query(Team).filter(Team.id == team_id).first()
            if not team:
                raise TeamNotFound()
            pool = team.storage_pool
            if not pool:
                raise RuntimeError("团队未关联存储池")
            return os.path.join(pool.base_path, "teams", team.id, "members", user_id)
        finally:
            session.close()

    def get_user_storage_context(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Return storage context for all teams a user belongs to.
        Used by FileService to know which directories are accessible.
        """
        session = self._db()
        try:
            memberships = (
                session.query(TeamMember)
                .filter(TeamMember.user_id == user_id)
                .all()
            )
            contexts = []
            for m in memberships:
                team = m.team
                pool = team.storage_pool
                if not pool or not pool.is_active:
                    continue
                personal_path = os.path.join(
                    pool.base_path, "teams", team.id, user_id
                )
                contexts.append({
                    "team_id": team.id,
                    "team_name": team.name,
                    "role": m.role,
                    "pool_id": pool.id,
                    "pool_protocol": pool.protocol,
                    "personal_path": personal_path,
                    "max_bytes": team.max_bytes,
                    "used_bytes": team.used_bytes,
                    "pool_free_bytes": pool.free_bytes,
                })
            return contexts
        finally:
            session.close()

    def ensure_default_pool(self) -> Dict[str, Any]:
        """
        Ensure the default local pool exists at ~/.hermes/file_manager/storage.
        Creates it if missing. Safe to call multiple times.
        """
        session = self._db()
        try:
            existing = session.query(StoragePool).filter(
                StoragePool.protocol == "local",
                StoragePool.name == "本地存储（默认）",
            ).first()
            if existing:
                return existing.to_dict()

            import os
            from pathlib import Path
            hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
            default_path = str(Path(hermes_home) / "file_manager" / "storage")
            return self.create_pool(
                name="本地存储（默认）",
                base_path=default_path,
                protocol="local",
                total_bytes=0,  # auto-detect
                description="系统默认本地存储池",
            )
        finally:
            session.close()
