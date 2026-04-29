"""
Audit Logger - Records all operations for security and compliance
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from sqlalchemy.orm import Session

from .models import AuditLog, AuditAction, User

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Centralized audit logging for HFM
    
    Records:
    - All authentication events (login, logout, failures)
    - All file operations (read, write, delete, etc.)
    - Admin actions (user/role/rule management)
    - Share link operations
    """
    
    def __init__(self, session: Session):
        self.session = session
    
    def log(
        self,
        action: AuditAction,
        result: str,
        user: Optional[User] = None,
        path: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create an audit log entry
        
        Args:
            action: The action being logged
            result: 'success', 'denied', or 'error'
            user: User performing the action (None for anonymous)
            path: File/directory path involved
            ip_address: Client IP address
            user_agent: Client user agent string
            metadata: Additional context as dict
        """
        entry = AuditLog(
            user_id=user.id if user else None,
            action=action.value,
            path=path,
            result=result,
            ip_address=self._redact_ip(ip_address),
            user_agent=self._truncate(user_agent, 512),
            extra=extra,
        )
        
        try:
            self.session.add(entry)
            self.session.commit()
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            self.session.rollback()
        
        return entry
    
    def log_login(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
    ) -> AuditLog:
        """Log a login attempt"""
        action = AuditAction.LOGIN if success else AuditAction.LOGIN_FAILED
        return self.log(
            action=action,
            result="success" if success else "denied",
            user=user if success else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra={"reason": "login_attempt"} if not success else None,
        )
    
    def log_logout(
        self,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a logout"""
        return self.log(
            action=AuditAction.LOGOUT,
            result="success",
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_file_operation(
        self,
        action: AuditAction,
        user: User,
        path: str,
        result: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a file operation"""
        return self.log(
            action=action,
            result=result,
            user=user,
            path=path,
            ip_address=ip_address,
            extra=metadata,
        )
    
    def log_permission_denied(
        self,
        user: User,
        action: "Operation | str",
        path: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log a permission denied event"""
        # Accept both Operation enum and string for convenience
        if hasattr(action, 'value'):
            action_str = action.value
        else:
            action_str = str(action)
        # Map to a corresponding AuditAction, fall back to OTHER if not found
        from ..engine.models import AuditAction as AA
        try:
            audit_action = AA(action_str)
        except ValueError:
            audit_action = AA.OTHER
        return self.log(
            action=audit_action,
            result="denied",
            user=user,
            path=path,
            ip_address=ip_address,
            extra=metadata,
        )
    
    def log_admin_action(
        self,
        action: "AuditAction | str",
        admin: Optional[User],
        target_id: str,
        result: str = "success",
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Log an admin action"""
        # Accept both AuditAction enum and string for convenience
        if isinstance(action, str):
            from ..engine.models import AuditAction as AA
            try:
                action = AA(action)
            except ValueError:
                from ..engine.models import AuditAction
                action = AuditAction.OTHER
        return self.log(
            action=action,
            result=result,
            user=admin,
            path=f"/admin/{target_id}",
            ip_address=ip_address,
            extra=metadata,
        )
    
    def query(
        self,
        user_id: Optional[str] = None,
        action: Optional[str] = None,
        path: Optional[str] = None,
        result: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        """
        Query audit logs with filters
        
        Returns list of matching AuditLog entries, newest first
        """
        query = self.session.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if path:
            query = query.filter(AuditLog.path.like(f"{path}%"))
        if result:
            query = query.filter(AuditLog.result == result)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)
        
        return (
            query
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def get_user_activity(
        self,
        user_id: str,
        days: int = 7,
    ) -> List[AuditLog]:
        """Get recent activity for a specific user"""
        start_date = datetime.utcnow() - timedelta(days=days)
        return self.query(user_id=user_id, start_date=start_date)
    
    def get_failed_logins(
        self,
        hours: int = 24,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Get recent failed login attempts"""
        start_date = datetime.utcnow() - timedelta(hours=hours)
        return self.query(
            action=AuditAction.LOGIN_FAILED.value,
            start_date=start_date,
            limit=limit,
        )
    
    def get_path_history(
        self,
        path: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get all operations on a specific path"""
        return self.query(path=path, limit=limit)
    
    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Delete audit logs older than retention period
        
        Returns number of deleted entries
        """
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        count = (
            self.session.query(AuditLog)
            .filter(AuditLog.created_at < cutoff)
            .delete()
        )
        self.session.commit()
        logger.info(f"Cleaned up {count} audit logs older than {retention_days} days")
        return count
    
    def export_csv(
        self,
        filepath: Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """
        Export audit logs to CSV file
        
        Returns number of records exported
        """
        import csv
        
        logs = self.query(start_date=start_date, end_date=end_date, limit=100000)
        
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "id", "username", "action", "path", "result",
                    "ip_address", "created_at", "metadata"
                ]
            )
            writer.writeheader()
            
            for log in logs:
                writer.writerow({
                    "id": log.id,
                    "username": log.user.username if log.user else "anonymous",
                    "action": log.action,
                    "path": log.path or "",
                    "result": log.result,
                    "ip_address": log.ip_address or "",
                    "created_at": log.created_at.isoformat() if log.created_at else "",
                    "metadata": json.dumps(log.extra) if log.extra else "",
                })
        
        return len(logs)
    
    @staticmethod
    def _redact_ip(ip: Optional[str]) -> Optional[str]:
        """Partially redact IP addresses for privacy"""
        if not ip:
            return None
        if ":" in ip:  # IPv6
            # Show first 3 groups
            parts = ip.split(":")
            if len(parts) >= 3:
                return ":".join(parts[:3]) + ":..."
        else:  # IPv4
            parts = ip.split(".")
            if len(parts) >= 2:
                return ".".join(parts[:2]) + ".x.x"
        return ip
    
    @staticmethod
    def _truncate(s: Optional[str], max_len: int) -> Optional[str]:
        """Truncate string to max length"""
        if not s:
            return None
        return s[:max_len] if len(s) > max_len else s


@contextmanager
def audit_context(
    logger: AuditLogger,
    action: AuditAction,
    user: Optional[User],
    path: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Context manager for automatic audit logging
    
    Usage:
        with audit_context(logger, AuditAction.FILE_READ, user, "/path/to/file"):
            # do something
            # automatically logs success or failure
    """
    result = "error"
    metadata = None
    try:
        yield
        result = "success"
    except PermissionError as e:
        result = "denied"
        metadata = {"error": str(e)}
        raise
    except Exception as e:
        result = "error"
        metadata = {"error": str(e)}
        raise
    finally:
        logger.log(
            action=action,
            result=result,
            user=user,
            path=path,
            ip_address=ip_address,
            extra=metadata,
        )
