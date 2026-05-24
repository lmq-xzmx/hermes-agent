"""
OrgSync Service - 企业微信/飞书组织架构同步

职责：
- 从企业微信/飞书获取组织架构
- 同步到 Hermes Team/Member/Role
- 支持手动和定时同步
"""

from __future__ import annotations

import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Types
# =============================================================================

class OrgProvider(str, Enum):
    WECHAT_WORK = "wechat_work"    # 企业微信
    FEISHU = "feishu"              # 飞书
    DINGTALK = "dingtalk"          # 钉钉


# =============================================================================
# Domain Types
# =============================================================================

@dataclass
class OrgUser:
    """Organization user"""
    provider: OrgProvider
    provider_user_id: str
    name: str
    email: Optional[str] = None
    department_id: Optional[str] = None
    department_name: Optional[str] = None
    is_leader: bool = False


@dataclass
class OrgDepartment:
    """Organization department"""
    provider: OrgProvider
    department_id: str
    parent_id: Optional[str]
    name: str
    order: int = 0


@dataclass
class SyncResult:
    """同步结果"""
    provider: OrgProvider
    started_at: float
    completed_at: float
    users_added: int = 0
    users_updated: int = 0
    users_removed: int = 0
    departments_added: int = 0
    departments_updated: int = 0
    departments_removed: int = 0
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    @property
    def total_changes(self) -> int:
        return (
            self.users_added + self.users_updated + self.users_removed +
            self.departments_added + self.departments_updated + self.departments_removed
        )


# =============================================================================
# Provider Adapters
# =============================================================================

class OrgProviderAdapter:
    """Base adapter for organization providers"""

    provider: OrgProvider = None

    def __init__(
        self,
        corp_id: str,
        agent_id: Optional[str] = None,
        secret: Optional[str] = None,
    ):
        self._corp_id = corp_id
        self._agent_id = agent_id
        self._secret = secret

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL"""
        raise NotImplementedError

    def exchange_code(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token"""
        raise NotImplementedError

    def get_users(self) -> List[OrgUser]:
        """Get all users from organization"""
        raise NotImplementedError

    def get_departments(self) -> List[OrgDepartment]:
        """Get all departments from organization"""
        raise NotImplementedError

    def get_department_users(self, department_id: str) -> List[OrgUser]:
        """Get users in a specific department"""
        raise NotImplementedError


class WeChatWorkAdapter(OrgProviderAdapter):
    """企业微信 SSO 适配器"""

    provider = OrgProvider.WECHAT_WORK

    def __init__(self, corp_id: str, agent_id: str, secret: str):
        super().__init__(corp_id, agent_id, secret)
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> str:
        """Get or refresh access token"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        import requests

        url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
        params = {
            "corpid": self._corp_id,
            "corpsecret": self._secret,
        }

        resp = requests.get(url, params=params)
        data = resp.json()

        if data.get("errcode") != 0:
            raise RuntimeError(f"Failed to get access token: {data}")

        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + data.get("expires_in", 7200) - 300

        return self._access_token

    def get_departments(self) -> List[OrgDepartment]:
        """获取部门列表"""
        import requests

        token = self._get_access_token()
        url = "https://qyapi.weixin.qq.com/cgi-bin/department/list"

        resp = requests.get(url, params={"access_token": token})
        data = resp.json()

        if data.get("errcode") != 0:
            logger.error(f"Failed to get departments: {data}")
            return []

        return [
            OrgDepartment(
                provider=self.provider,
                department_id=str(dept["id"]),
                parent_id=str(dept.get("parentid", "")),
                name=dept["name"],
                order=dept.get("order", 0),
            )
            for dept in data.get("department", [])
        ]

    def get_department_users(self, department_id: str) -> List[OrgUser]:
        """获取部门成员"""
        import requests

        token = self._get_access_token()
        url = "https://qyapi.weixin.qq.com/cgi-bin/user/list"

        resp = requests.get(url, params={
            "access_token": token,
            "department_id": department_id,
            "fetch_child": 1,
            "status": 1,  # Active only
        })

        data = resp.json()
        if data.get("errcode") != 0:
            logger.error(f"Failed to get department users: {data}")
            return []

        return [
            OrgUser(
                provider=self.provider,
                provider_user_id=user["userid"],
                name=user["name"],
                email=user.get("email"),
                department_id=str(user.get("department", [""])[0]),
                department_name=None,
                is_leader=bool(user.get("is_leader_in_dept")),
            )
            for user in data.get("userlist", [])
        ]

    def get_users(self) -> List[OrgUser]:
        """获取所有成员"""
        departments = self.get_departments()
        all_users = []

        for dept in departments:
            users = self.get_department_users(dept.department_id)
            for user in users:
                user.department_name = dept.name
                all_users.append(user)

        return all_users


class FeishuAdapter(OrgProviderAdapter):
    """飞书 SSO 适配器"""

    provider = OrgProvider.FEISHU

    def __init__(self, app_id: str, app_secret: str):
        super().__init__(app_id, None, app_secret)
        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0

    def _get_access_token(self) -> str:
        """Get or refresh tenant access token"""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        import requests

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = requests.post(
            url,
            json={
                "app_id": self._corp_id,
                "app_secret": self._secret,
            }
        )

        data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Failed to get tenant access token: {data}")

        self._access_token = data["tenant_access_token"]
        self._token_expires_at = time.time() + data.get("expire", 7200) - 300

        return self._access_token

    def get_departments(self) -> List[OrgDepartment]:
        """获取部门列表"""
        import requests

        token = self._get_access_token()
        url = "https://open.feishu.cn/open-apis/organization/v2/departments"
        params = {"department_id": "0", "fetch_child": True}

        resp = requests.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {token}"}
        )

        data = resp.json()
        if data.get("code") != 0:
            logger.error(f"Failed to get departments: {data}")
            return []

        return [
            OrgDepartment(
                provider=self.provider,
                department_id=dept["department_id"],
                parent_id=dept.get("parent_id"),
                name=dept["name"],
                order=dept.get("order", 0),
            )
            for dept in data.get("data", {}).get("items", [])
        ]

    def get_department_users(self, department_id: str) -> List[OrgUser]:
        """获取部门成员"""
        import requests

        token = self._get_access_token()
        url = "https://open.feishu.cn/open-apis/contact/v3/users"

        params = {
            "department_id": department_id,
            "department_id_type": "open_department_id",
            "user_id_type": "open_id",
            "page_size": 100,
        }

        all_users = []

        while True:
            resp = requests.get(
                url,
                params=params,
                headers={"Authorization": f"Bearer {token}"}
            )

            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"Failed to get users: {data}")
                break

            for user in data.get("data", {}).get("items", []):
                all_users.append(OrgUser(
                    provider=self.provider,
                    provider_user_id=user["open_id"],
                    name=user["name"],
                    email=user.get("email"),
                    department_id=department_id,
                    department_name=None,
                    is_leader=user.get("is_leader_in_dept", False),
                ))

            # Check for next page
            page_token = data.get("data", {}).get("page_token")
            if not page_token:
                break

            params["page_token"] = page_token

        return all_users

    def get_users(self) -> List[OrgUser]:
        """获取所有成员"""
        departments = self.get_departments()
        all_users = []

        for dept in departments:
            users = self.get_department_users(dept.department_id)
            for user in users:
                user.department_name = dept.name
                all_users.append(user)

        return all_users


# =============================================================================
# OrgSync Service
# =============================================================================

class OrgSyncService:
    """
    组织架构同步服务。

    将企业微信/飞书等平台的组织架构同步到 Hermes 系统。
    """

    def __init__(
        self,
        db_factory,
        default_role: str = "viewer",
        sync_interval_seconds: int = 3600,  # 1 hour
    ):
        self._db_factory = db_factory
        self._default_role = default_role
        self._sync_interval = sync_interval_seconds

        # Provider registry
        self._providers: Dict[str, OrgProviderAdapter] = {}

        # Sync state
        self._last_sync: Dict[str, float] = {}  # provider -> last_sync_timestamp

    def register_provider(
        self,
        provider_id: str,
        adapter: OrgProviderAdapter,
    ) -> None:
        """Register an organization provider"""
        self._providers[provider_id] = adapter
        logger.info(f"Registered org provider: {provider_id} ({adapter.provider})")

    def sync_from_provider(self, provider_id: str) -> SyncResult:
        """
        从指定 provider 同步组织架构。

        Returns:
            SyncResult with counts and errors
        """
        if provider_id not in self._providers:
            # Return a generic error result for unknown provider
            return SyncResult(
                provider=None,
                started_at=time.time(),
                completed_at=time.time(),
                errors=[f"Provider {provider_id} not found"],
            )

        adapter = self._providers[provider_id]
        started_at = time.time()

        try:
            # Get organization data
            departments = adapter.get_departments()
            users = adapter.get_users()

            # Sync to Hermes
            with self._db_factory() as session:
                # First sync departments to teams
                team_map = self._sync_departments_to_teams(session, departments, provider_id)

                # Then sync users to team members
                self._sync_users_to_members(session, users, team_map, provider_id)

                session.commit()

            completed_at = time.time()
            result = SyncResult(
                provider=adapter.provider,
                started_at=started_at,
                completed_at=completed_at,
                users_added=0,  # Would need before/after comparison
                users_updated=0,
                departments_added=len(departments),
                departments_updated=0,
            )

            self._last_sync[provider_id] = completed_at

            logger.info(
                f"OrgSync completed for {provider_id}: "
                f"{len(departments)} departments, {len(users)} users"
            )

            return result

        except Exception as e:
            logger.error(f"OrgSync failed for {provider_id}: {e}")
            return SyncResult(
                provider=adapter.provider,
                started_at=started_at,
                completed_at=time.time(),
                errors=[str(e)],
            )

    def _sync_departments_to_teams(
        self,
        session,
        departments: List[OrgDepartment],
        provider_id: str,
    ) -> Dict[str, str]:
        """
        Sync departments to Hermes Teams.

        Returns:
            {department_id: team_id} mapping
        """
        from ..engine.models import Team

        team_map: Dict[str, str] = {}

        for dept in departments:
            # Check if team exists with this external ID
            existing = session.query(Team).filter(
                Team.external_id == f"{provider_id}:{dept.department_id}"
            ).first()

            if existing:
                # Update
                existing.name = dept.name
                team_map[dept.department_id] = existing.id
            else:
                # Create
                team = Team(
                    name=dept.name,
                    external_id=f"{provider_id}:{dept.department_id}",
                    provider=provider_id,
                )
                session.add(team)
                session.flush()
                team_map[dept.department_id] = team.id

        return team_map

    def _sync_users_to_members(
        self,
        session,
        users: List[OrgUser],
        team_map: Dict[str, str],
        provider_id: str,
    ) -> None:
        """Sync users to team members"""
        from ..engine.models import TeamMember, User

        for org_user in users:
            # Map department to team
            if org_user.department_id not in team_map:
                continue

            team_id = team_map[org_user.department_id]

            # Find or create user
            user = session.query(User).filter(
                User.external_id == f"{provider_id}:{org_user.provider_user_id}"
            ).first()

            if not user:
                user = User(
                    username=org_user.name,
                    email=org_user.email,
                    external_id=f"{provider_id}:{org_user.provider_user_id}",
                    provider=provider_id,
                )
                session.add(user)
                session.flush()

            # Find or create team member
            existing = session.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user.id,
            ).first()

            role = "admin" if org_user.is_leader else self._default_role

            if existing:
                existing.role = role
            else:
                member = TeamMember(
                    team_id=team_id,
                    user_id=user.id,
                    role=role,
                )
                session.add(member)

    def get_last_sync_time(self, provider_id: str) -> Optional[float]:
        """Get last successful sync timestamp"""
        return self._last_sync.get(provider_id)


# =============================================================================
# Global Service
# =============================================================================

_org_sync_service: Optional[OrgSyncService] = None


def get_org_sync_service() -> OrgSyncService:
    """Get global org sync service"""
    global _org_sync_service
    if _org_sync_service is None:
        from ..server import _api_instances
        db_factory = _api_instances.get("db_factory")
        if db_factory:
            _org_sync_service = OrgSyncService(db_factory=db_factory)
    return _org_sync_service


def setup_org_sync_service(db_factory) -> OrgSyncService:
    """Initialize org sync service"""
    global _org_sync_service
    _org_sync_service = OrgSyncService(db_factory=db_factory)
    return _org_sync_service