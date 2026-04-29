"""
Admin API - User, Role, and Rule management
"""

from __future__ import annotations

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import HTTPException, Depends
from pydantic import BaseModel

from ..engine.models import User, Role, PermissionRule, AuditAction
from ..engine.audit import AuditLogger
from .auth import get_current_user


# ============================================================================
# Pydantic Models
# ============================================================================

class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role_id: Optional[str] = None


class UpdateUserRequest(BaseModel):
    email: Optional[str] = None
    role_id: Optional[str] = None
    is_active: Optional[bool] = None


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateRoleRequest(BaseModel):
    description: Optional[str] = None


class CreateRuleRequest(BaseModel):
    role_id: str
    path_pattern: str
    permissions: str  # "read,write,delete"
    priority: int = 0


class UpdateRuleRequest(BaseModel):
    path_pattern: Optional[str] = None
    permissions: Optional[str] = None
    priority: Optional[int] = None


class AuditQueryRequest(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    path: Optional[str] = None
    result: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 100
    offset: int = 0


# ============================================================================
# Admin API
# ============================================================================

class AdminAPI:
    """Admin operations API handlers"""
    
    def __init__(self, db_session_factory):
        self.db_factory = db_session_factory
    
    # -------------------------------------------------------------------------
    # User Management
    # -------------------------------------------------------------------------
    
    def list_users(
        self,
        admin: User,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List all users"""
        session = self.db_factory()
        try:
            users = (
                session.query(User)
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [u.to_dict() for u in users]
        finally:
            session.close()
    
    def get_user(
        self,
        user_id: str,
        admin: User,
    ) -> Dict[str, Any]:
        """Get user by ID"""
        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            return user.to_dict()
        finally:
            session.close()
    
    def create_user(
        self,
        request: CreateUserRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new user"""
        session = self.db_factory()
        try:
            # Check if username exists
            existing = session.query(User).filter(User.username == request.username).first()
            if existing:
                raise HTTPException(status_code=400, detail="Username already exists")
            
            # Get role if specified
            role = None
            if request.role_id:
                role = session.query(Role).filter(Role.id == request.role_id).first()
                if not role:
                    raise HTTPException(status_code=400, detail="Role not found")
            
            user = User(
                username=request.username,
                email=request.email,
                role_id=role.id if role else None,
            )
            user.set_password(request.password)
            
            session.add(user)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.USER_CREATE, admin, user.id,
                ip_address=ip_address,
                metadata={"username": user.username}
            )
            
            return user.to_dict()
        finally:
            session.close()
    
    def update_user(
        self,
        user_id: str,
        request: UpdateUserRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a user"""
        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Update fields
            if request.email is not None:
                user.email = request.email
            if request.role_id is not None:
                role = session.query(Role).filter(Role.id == request.role_id).first()
                if not role:
                    raise HTTPException(status_code=400, detail="Role not found")
                user.role_id = request.role_id
            if request.is_active is not None:
                user.is_active = request.is_active
            
            user.updated_at = datetime.utcnow()
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.USER_UPDATE, admin, user.id,
                ip_address=ip_address,
                metadata={"updated_fields": request.dict(exclude_none=True)}
            )
            
            return user.to_dict()
        finally:
            session.close()
    
    def delete_user(
        self,
        user_id: str,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete a user"""
        session = self.db_factory()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            if user.id == admin.id:
                raise HTTPException(status_code=400, detail="Cannot delete yourself")
            
            username = user.username
            session.delete(user)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.USER_DELETE, admin, user_id,
                ip_address=ip_address,
                metadata={"username": username}
            )
            
            return {"message": f"User '{username}' deleted"}
        finally:
            session.close()
    
    # -------------------------------------------------------------------------
    # Role Management
    # -------------------------------------------------------------------------
    
    def list_roles(
        self,
        admin: User,
    ) -> List[Dict[str, Any]]:
        """List all roles"""
        session = self.db_factory()
        try:
            roles = session.query(Role).all()
            return [r.to_dict() for r in roles]
        finally:
            session.close()
    
    def get_role(
        self,
        role_id: str,
        admin: User,
    ) -> Dict[str, Any]:
        """Get role by ID with its rules"""
        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            data = role.to_dict()
            data["rules"] = [r.to_dict() for r in role.permission_rules]
            return data
        finally:
            session.close()
    
    def create_role(
        self,
        request: CreateRoleRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new role"""
        session = self.db_factory()
        try:
            existing = session.query(Role).filter(Role.name == request.name).first()
            if existing:
                raise HTTPException(status_code=400, detail="Role already exists")
            
            role = Role(
                name=request.name,
                description=request.description,
                is_system=False,
            )
            
            session.add(role)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.ROLE_CREATE, admin, role.id,
                ip_address=ip_address,
                metadata={"name": role.name}
            )
            
            return role.to_dict()
        finally:
            session.close()
    
    def update_role(
        self,
        role_id: str,
        request: UpdateRoleRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a role"""
        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot modify system role")
            
            if request.description is not None:
                role.description = request.description
            
            role.updated_at = datetime.utcnow()
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.ROLE_UPDATE, admin, role.id,
                ip_address=ip_address,
            )
            
            return role.to_dict()
        finally:
            session.close()
    
    def delete_role(
        self,
        role_id: str,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete a role"""
        session = self.db_factory()
        try:
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                raise HTTPException(status_code=404, detail="Role not found")
            
            if role.is_system:
                raise HTTPException(status_code=400, detail="Cannot delete system role")
            
            # Check if any users have this role
            user_count = session.query(User).filter(User.role_id == role_id).count()
            if user_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete role with {user_count} assigned users"
                )
            
            role_name = role.name
            session.delete(role)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.ROLE_DELETE, admin, role_id,
                ip_address=ip_address,
                metadata={"name": role_name}
            )
            
            return {"message": f"Role '{role_name}' deleted"}
        finally:
            session.close()
    
    # -------------------------------------------------------------------------
    # Permission Rule Management
    # -------------------------------------------------------------------------
    
    def list_rules(
        self,
        admin: User,
        role_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List permission rules, optionally filtered by role"""
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
        request: CreateRuleRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new permission rule"""
        session = self.db_factory()
        try:
            # Verify role exists
            role = session.query(Role).filter(Role.id == request.role_id).first()
            if not role:
                raise HTTPException(status_code=400, detail="Role not found")
            
            rule = PermissionRule(
                role_id=request.role_id,
                path_pattern=request.path_pattern,
                permissions=request.permissions,
                priority=request.priority,
                created_by=admin.id,
            )
            
            session.add(rule)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.RULE_CREATE, admin, rule.id,
                ip_address=ip_address,
                metadata={"pattern": request.path_pattern, "role": role.name}
            )
            
            return rule.to_dict()
        finally:
            session.close()
    
    def update_rule(
        self,
        rule_id: str,
        request: UpdateRuleRequest,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a permission rule"""
        session = self.db_factory()
        try:
            rule = session.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
            if not rule:
                raise HTTPException(status_code=404, detail="Rule not found")
            
            if request.path_pattern is not None:
                rule.path_pattern = request.path_pattern
            if request.permissions is not None:
                rule.permissions = request.permissions
            if request.priority is not None:
                rule.priority = request.priority
            
            rule.updated_at = datetime.utcnow()
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.RULE_UPDATE, admin, rule_id,
                ip_address=ip_address,
            )
            
            return rule.to_dict()
        finally:
            session.close()
    
    def delete_rule(
        self,
        rule_id: str,
        admin: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete a permission rule"""
        session = self.db_factory()
        try:
            rule = session.query(PermissionRule).filter(PermissionRule.id == rule_id).first()
            if not rule:
                raise HTTPException(status_code=404, detail="Rule not found")
            
            session.delete(rule)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.RULE_DELETE, admin, rule_id,
                ip_address=ip_address,
            )
            
            return {"message": "Rule deleted"}
        finally:
            session.close()
    
    # -------------------------------------------------------------------------
    # Audit Log Access
    # -------------------------------------------------------------------------
    
    def query_audit_logs(
        self,
        request: AuditQueryRequest,
        admin: User,
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
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
            
            return [log.to_dict() for log in logs]
        finally:
            session.close()
    
    def export_audit_logs(
        self,
        admin: User,
        filepath: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Export audit logs to CSV"""
        from pathlib import Path
        
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            start = datetime.fromisoformat(start_date) if start_date else None
            end = datetime.fromisoformat(end_date) if end_date else None
            
            count = audit.export_csv(Path(filepath), start_date=start, end_date=end)
            
            return {"message": f"Exported {count} records to {filepath}"}
        finally:
            session.close()
