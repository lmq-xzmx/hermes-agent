"""
AdminAnalyticsService - Pure business logic for admin analytics operations.

No FastAPI, no HTTPException. Uses PermissionContext for user identity.
Provides data for Admin Dashboard: storage pools, user-space relationships,
quota heatmaps, operation trends, and active users.

Caching Strategy (TTL: 5 minutes):
- Admin data changes infrequently, so a simple in-memory cache with TTL is effective
- Cache is invalidated on WebSocket data refresh broadcasts
- Cache key format: method_name:arg1:arg2 for methods with arguments
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable

from .permission_context import PermissionContext
from .event_bus import EventBus, EventType, Event, get_event_bus
from ..engine.models import User, Space, StoragePool, SpaceMember, AuditLog
from ..engine.audit import AuditLogger


# Cache configuration
_CACHE_TTL_SECONDS = 300  # 5 minutes
_CACHE_LOCK = threading.RLock()


class AdminAccessDenied(Exception):
    """Admin access required but user is not an admin."""
    pass


class AdminAnalyticsService:
    """
    Admin analytics business logic. Stateless.

    Provides data for the Admin Dashboard visualization:
      - Storage pool overview and usage statistics
      - User-Space relationship graph (for Sankey diagram)
      - Quota heatmap (warning/critical spaces)
      - Operation trends over time
      - Active users statistics

    Caching: All data-fetching methods are cached with 5-minute TTL.
    Cache is automatically invalidated when WebSocket broadcaster refreshes data.
    """

    # Class-level cache shared across all instances
    _cache: Dict[str, Any] = {}
    _cache_timestamps: Dict[str, datetime] = {}

    def __init__(
        self,
        db_factory: Callable,
        event_bus: Optional[EventBus] = None,
    ):
        self.db_factory = db_factory
        self._event_bus = event_bus or get_event_bus()

    def _require_admin(self, ctx: PermissionContext) -> None:
        """Raise AdminAccessDenied if user is not an admin."""
        if ctx.role_name != "admin":
            raise AdminAccessDenied(f"User '{ctx.username}' is not an admin")

    def _get_cache_key(self, method_name: str, *args) -> str:
        """Generate a cache key for the given method and arguments."""
        if args:
            return f"{method_name}:{':'.join(str(arg) for arg in args)}"
        return method_name

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry exists and is not expired."""
        if key not in self._cache_timestamps:
            return False
        age = (datetime.utcnow() - self._cache_timestamps[key]).total_seconds()
        return age < _CACHE_TTL_SECONDS

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if valid, thread-safe."""
        with _CACHE_LOCK:
            if self._is_cache_valid(key):
                return self._cache.get(key)
            return None

    def _set_cached(self, key: str, data: Any) -> None:
        """Store data in cache with current timestamp, thread-safe."""
        with _CACHE_LOCK:
            self._cache[key] = data
            self._cache_timestamps[key] = datetime.utcnow()

    def invalidate_cache(self, method_name: Optional[str] = None) -> None:
        """
        Invalidate cache entries.

        Args:
            method_name: If provided, only invalidate entries for this method.
                        If None, invalidate all entries.
        """
        with _CACHE_LOCK:
            if method_name:
                # Invalidate specific method entries
                keys_to_remove = [k for k in self._cache if k.startswith(f"{method_name}:") or k == method_name]
                for key in keys_to_remove:
                    self._cache.pop(key, None)
                    self._cache_timestamps.pop(key, None)
            else:
                # Invalidate all entries
                self._cache.clear()
                self._cache_timestamps.clear()

    # -------------------------------------------------------------------------
    # Storage Pools Analytics
    # -------------------------------------------------------------------------

    def get_storage_pools(self, ctx: PermissionContext) -> Dict[str, Any]:
        """Get all storage pools with usage statistics. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_storage_pools")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            pools = session.query(StoragePool).filter(StoragePool.is_active == True).all()

            pool_list = []
            total_bytes = 0
            total_used = 0

            for pool in pools:
                # Count spaces in this pool
                space_count = session.query(Space).filter(
                    Space.storage_pool_id == pool.id,
                    Space.status == "active"
                ).count()

                # Count teams (root spaces)
                team_count = session.query(Space).filter(
                    Space.storage_pool_id == pool.id,
                    Space.space_type == "team",
                    Space.status == "active"
                ).count()

                used_bytes = pool.total_bytes - pool.free_bytes
                usage_rate = used_bytes / pool.total_bytes if pool.total_bytes > 0 else 0
                status = "critical" if usage_rate > 0.9 else "warning" if usage_rate > 0.7 else "normal"

                pool_list.append({
                    "id": pool.id,
                    "name": pool.name,
                    "protocol": pool.protocol,
                    "base_path": pool.base_path,
                    "total_bytes": pool.total_bytes,
                    "used_bytes": used_bytes,
                    "free_bytes": pool.free_bytes,
                    "usage_rate": round(usage_rate, 4),
                    "team_count": team_count,
                    "space_count": space_count,
                    "status": status,
                })

                total_bytes += pool.total_bytes
                total_used += used_bytes

            result = {
                "pools": pool_list,
                "summary": {
                    "total_pools": len(pools),
                    "total_bytes": total_bytes,
                    "used_bytes": total_used,
                    "usage_rate": round(total_used / total_bytes, 4) if total_bytes > 0 else 0,
                }
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # User-Space Relationships (Sankey Diagram)
    # -------------------------------------------------------------------------

    def get_user_space_relationships(self, ctx: PermissionContext) -> Dict[str, Any]:
        """Get user-space relationships for Sankey diagram. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_user_space_relationships")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            nodes = []
            links = []

            # Add user nodes
            users = session.query(User).filter(User.is_active == True).all()
            for user in users:
                nodes.append({
                    "id": f"user_{user.id}",
                    "name": user.username,
                    "type": "user",
                    "role": user.role.name if user.role else "member",
                })

            # Get all spaces (teams only for Sankey clarity)
            spaces = session.query(Space).filter(
                Space.space_type.in_(["team", "root"]),
                Space.status == "active"
            ).all()

            team_nodes = []
            for space in spaces:
                if space.space_type == "team":
                    team_nodes.append(space)
                    nodes.append({
                        "id": f"space_{space.id}",
                        "name": space.name,
                        "type": "space",
                    })

            # Add space members and relationships
            for space in team_nodes:
                # Get members
                members = session.query(SpaceMember).filter(
                    SpaceMember.space_id == space.id
                ).all()

                for member in members:
                    # User -> Space link
                    links.append({
                        "source": f"user_{member.user_id}",
                        "target": f"space_{space.id}",
                        "value": 1,
                        "role": member.role,
                    })

            result = {
                "nodes": nodes,
                "links": links,
                "stats": {
                    "total_users": len(users),
                    "total_teams": len(team_nodes),
                    "total_spaces": len(spaces),
                }
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Quota Heatmap
    # -------------------------------------------------------------------------

    def get_quota_heatmap(self, ctx: PermissionContext) -> Dict[str, Any]:
        """Get quota usage heatmap for all team spaces. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_quota_heatmap")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            # Get all team spaces with quota usage
            spaces = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active",
                Space.max_bytes > 0
            ).all()

            heatmap = []
            for space in spaces:
                usage_rate = space.used_bytes / space.max_bytes if space.max_bytes > 0 else 0
                status = "critical" if usage_rate > 0.8 else "warning" if usage_rate > 0.6 else "normal"

                if status != "normal":
                    heatmap.append({
                        "space_id": space.id,
                        "space_name": space.name,
                        "usage_rate": round(usage_rate, 4),
                        "status": status,
                    })

            result = {
                "heatmap": heatmap,
                "legend": {
                    "normal": {"min": 0, "max": 0.6, "color": "#3fb950"},
                    "warning": {"min": 0.6, "max": 0.8, "color": "#d29922"},
                    "critical": {"min": 0.8, "max": 1.0, "color": "#f85149"}
                }
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Operation Trends
    # -------------------------------------------------------------------------

    def get_operation_trends(self, ctx: PermissionContext, days: int = 30) -> Dict[str, Any]:
        """Get operation trends over the specified number of days. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_operation_trends", days)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query audit logs
            logs = session.query(AuditLog).filter(
                AuditLog.created_at >= start_date
            ).order_by(AuditLog.created_at).all()

            # Aggregate by date and action
            daily_stats = {}
            action_types = set()

            for log in logs:
                date_key = log.created_at.strftime("%Y-%m-%d")
                action = log.action

                action_types.add(action)

                if date_key not in daily_stats:
                    daily_stats[date_key] = {}

                if action not in daily_stats[date_key]:
                    daily_stats[date_key][action] = 0

                daily_stats[date_key][action] += 1

            # Build date range
            dates = []
            current = start_date.date()
            end = datetime.utcnow().date()
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)

            # Build series for each action type
            series = []
            for action in sorted(action_types):
                series.append({
                    "name": action,
                    "data": [daily_stats.get(date, {}).get(action, 0) for date in dates]
                })

            result = {
                "dates": dates,
                "series": series
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Active Users
    # -------------------------------------------------------------------------

    def get_active_users(self, ctx: PermissionContext, days: int = 7) -> Dict[str, Any]:
        """Get active users in the last N days. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_active_users", days)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Query distinct users who performed actions
            active_user_ids = session.query(AuditLog.user_id).filter(
                AuditLog.created_at >= start_date,
                AuditLog.user_id.isnot(None)
            ).distinct().all()

            users = []
            total_actions = 0

            for (user_id,) in active_user_ids:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    continue

                # Count actions
                action_count = session.query(AuditLog).filter(
                    AuditLog.created_at >= start_date,
                    AuditLog.user_id == user_id
                ).count()

                # Get last action time
                last_log = session.query(AuditLog).filter(
                    AuditLog.user_id == user_id
                ).order_by(AuditLog.created_at.desc()).first()

                users.append({
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "action_count": action_count,
                    "last_action": last_log.created_at if last_log else None,
                })
                total_actions += action_count

            # Sort by action count descending
            users.sort(key=lambda x: x["action_count"], reverse=True)

            result = {
                "users": users,
                "total": len(users),
                "total_actions": total_actions,
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Overview (Combined)
    # -------------------------------------------------------------------------

    def get_overview(self, ctx: PermissionContext) -> Dict[str, Any]:
        """Get combined overview data for dashboard. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_overview")
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)

            # User stats
            total_users = session.query(User).count()
            active_users_7d = session.query(AuditLog.user_id).filter(
                AuditLog.created_at >= seven_days_ago,
                AuditLog.user_id.isnot(None)
            ).distinct().count()
            new_users_7d = session.query(User).filter(
                User.created_at >= seven_days_ago
            ).count()

            # Team/Space counts
            total_teams = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active"
            ).count()
            total_spaces = session.query(Space).filter(
                Space.status == "active"
            ).count()

            # Storage pool stats
            pools = session.query(StoragePool).filter(StoragePool.is_active == True).all()
            total_pools = len(pools)
            total_bytes = sum(p.total_bytes for p in pools)
            used_bytes = sum(p.total_bytes - p.free_bytes for p in pools)
            free_bytes = sum(p.free_bytes for p in pools)

            # Quota warnings
            spaces_with_quota = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active",
                Space.max_bytes > 0
            ).all()

            alerts = []
            for space in spaces_with_quota:
                usage_rate = space.used_bytes / space.max_bytes
                if usage_rate > 0.8:
                    alerts.append({
                        "id": f"alert_{space.id}",
                        "type": "quota_warning",
                        "level": "critical" if usage_rate > 0.9 else "warning",
                        "resource": "Space",
                        "resource_id": space.id,
                        "resource_name": space.name,
                        "usage_rate": round(usage_rate, 4),
                        "message": f"空间配额使用率超过{int(usage_rate * 100)}%",
                        "created_at": now,
                    })

            # Recent activities
            recent_logs = session.query(AuditLog).order_by(
                AuditLog.created_at.desc()
            ).limit(10).all()

            recent_activities = []
            for log in recent_logs:
                recent_activities.append({
                    "id": str(log.id),
                    "user_id": log.user_id or "",
                    "username": log.user.username if log.user else None,
                    "action": log.action,
                    "target": log.path or "",
                    "target_name": log.path.split("/")[-1] if log.path else None,
                    "result": log.result,
                    "created_at": log.created_at,
                })

            result = {
                "total_users": total_users,
                "active_users_7d": active_users_7d,
                "new_users_7d": new_users_7d,
                "total_teams": total_teams,
                "total_spaces": total_spaces,
                "total_pools": total_pools,
                "storage": {
                    "total_bytes": total_bytes,
                    "used_bytes": used_bytes,
                    "free_bytes": free_bytes,
                    "usage_rate": round(used_bytes / total_bytes, 4) if total_bytes > 0 else 0,
                },
                "alerts": alerts[:10],  # Limit to 10 most recent
                "recent_activities": recent_activities,
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Alerts (Standalone)
    # -------------------------------------------------------------------------

    def get_alerts(self, ctx: PermissionContext) -> Dict[str, Any]:
        """Get all quota alerts for admin dashboard."""
        self._require_admin(ctx)

        session = self.db_factory()
        try:
            now = datetime.utcnow()

            # Get all spaces with quota that have warnings
            spaces_with_quota = session.query(Space).filter(
                Space.space_type == "team",
                Space.status == "active",
                Space.max_bytes > 0
            ).all()

            alerts = []
            for space in spaces_with_quota:
                usage_rate = space.used_bytes / space.max_bytes
                if usage_rate > 0.8:
                    alerts.append({
                        "id": f"alert_{space.id}",
                        "type": "quota_warning",
                        "level": "critical" if usage_rate > 0.9 else "warning",
                        "resource": "Space",
                        "resource_id": space.id,
                        "resource_name": space.name,
                        "usage_rate": round(usage_rate, 4),
                        "message": f"空间配额使用率超过{int(usage_rate * 100)}%",
                        "created_at": now,
                    })

            # Sort by usage_rate descending (most critical first)
            alerts.sort(key=lambda x: x["usage_rate"], reverse=True)

            cache_key = self._get_cache_key("get_alerts")
            result = {"alerts": alerts, "total": len(alerts)}
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()

    # -------------------------------------------------------------------------
    # Teams by Pool (for lifecycle constraint: delete_pool)
    # -------------------------------------------------------------------------

    def get_teams_by_pool(self, ctx: PermissionContext, pool_id: str) -> Dict[str, Any]:
        """Get all teams using a specific storage pool. Used for STORAGE_POOL_IN_USE constraint. Cached with 5-min TTL."""
        self._require_admin(ctx)

        cache_key = self._get_cache_key("get_teams_by_pool", pool_id)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        session = self.db_factory()
        try:
            pool = session.query(StoragePool).filter(StoragePool.id == pool_id).first()
            if not pool:
                return {"pool_id": pool_id, "pool_name": None, "teams": [], "total": 0}

            # Get all team spaces (space_type == "team") using this pool
            teams = session.query(Space).filter(
                Space.storage_pool_id == pool_id,
                Space.space_type == "team",
                Space.status == "active"
            ).all()

            team_list = []
            for team in teams:
                # Get member count
                member_count = session.query(SpaceMember).filter(
                    SpaceMember.space_id == team.id
                ).count()

                # Get owner info
                owner = None
                if team.owner_id:
                    owner_user = session.query(User).filter(User.id == team.owner_id).first()
                    if owner_user:
                        owner = {"user_id": owner_user.id, "username": owner_user.username}

                team_list.append({
                    "team_id": team.id,
                    "team_name": team.name,
                    "member_count": member_count,
                    "storage_used": team.used_bytes,
                    "storage_quota": team.max_bytes,
                    "usage_rate": round(team.used_bytes / team.max_bytes, 4) if team.max_bytes > 0 else 0,
                    "owner": owner,
                    "created_at": team.created_at,
                })

            result = {
                "pool_id": pool_id,
                "pool_name": pool.name,
                "teams": team_list,
                "total": len(team_list),
            }
            self._set_cached(cache_key, result)
            return result
        finally:
            session.close()
