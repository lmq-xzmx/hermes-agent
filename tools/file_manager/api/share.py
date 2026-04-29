"""
Share API - Public share link management
"""

from __future__ import annotations

import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import HTTPException
from pydantic import BaseModel

from ..engine.models import User, SharedLink, AuditAction
from ..engine.storage import StorageEngine, FileNotFoundError
from ..engine.audit import AuditLogger
from .auth import get_current_user


class CreateShareRequest(BaseModel):
    path: str
    password: Optional[str] = None
    permissions: str = "read"  # read or read_write
    expires_in_days: Optional[int] = 7
    max_access_count: Optional[int] = None


class UpdateShareRequest(BaseModel):
    password: Optional[str] = None
    permissions: Optional[str] = None
    expires_in_days: Optional[int] = None
    max_access_count: Optional[int] = None
    is_active: Optional[bool] = None


class ShareAPI:
    """Share link API handlers"""
    
    def __init__(self, db_session_factory, storage: StorageEngine):
        self.db_factory = db_session_factory
        self.storage = storage
    
    def create_share_link(
        self,
        request: CreateShareRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a share link for a file/directory"""
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            # Check user has at least read access to the path
            decision = self.storage.permission_engine.check_permission(
                user, "read", request.path,
                list(user.role.permission_rules) if user.role else []
            )
            
            if not decision.allowed:
                raise HTTPException(status_code=403, detail="No access to this path")
            
            # Verify path exists
            try:
                self.storage.get_stat(request.path)
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Path not found")
            
            # Generate unique token
            token = secrets.token_urlsafe(32)
            
            # Hash password if provided
            password_hash = None
            if request.password:
                from passlib.hash import bcrypt
                password_hash = bcrypt.hash(request.password, rounds=12)
            
            # Calculate expiration
            expires_at = None
            if request.expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
            
            # Validate permissions
            if request.permissions not in ("read", "read_write"):
                raise HTTPException(status_code=400, detail="permissions must be 'read' or 'read_write'")
            
            share_link = SharedLink(
                path=request.path,
                token=token,
                password_hash=password_hash,
                permissions=request.permissions,
                expires_at=expires_at,
                created_by=user.id,
                max_access_count=request.max_access_count,
            )
            
            session.add(share_link)
            session.commit()
            
            # Audit
            audit.log_admin_action(
                AuditAction.SHARE_CREATE, user, share_link.id,
                ip_address=ip_address,
                metadata={"path": request.path, "permissions": request.permissions}
            )
            
            return share_link.to_dict(include_token=True)
        finally:
            session.close()
    
    def list_share_links(
        self,
        user: User,
        path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List share links created by user"""
        session = self.db_factory()
        try:
            query = session.query(SharedLink).filter(SharedLink.created_by == user.id)
            
            if path:
                query = query.filter(SharedLink.path == path)
            
            links = query.all()
            
            return {
                "links": [link.to_dict() for link in links],
                "total": len(links),
            }
        finally:
            session.close()
    
    def get_share_link(
        self,
        token: str,
    ) -> Dict[str, Any]:
        """Get share link info (without sensitive data)"""
        session = self.db_factory()
        try:
            link = session.query(SharedLink).filter(SharedLink.token == token).first()
            if not link:
                raise HTTPException(status_code=404, detail="Share link not found")
            
            return link.to_dict()
        finally:
            session.close()
    
    def access_share_link(
        self,
        token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Access a share link - verify validity and return file info
        
        For share links with 'read' permission, returns file listing or content
        For share links with 'read_write' permission, also allows modifications
        """
        session = self.db_factory()
        try:
            audit = AuditLogger(session)
            
            link = session.query(SharedLink).filter(SharedLink.token == token).first()
            if not link:
                raise HTTPException(status_code=404, detail="Share link not found")
            
            # Check validity
            if not link.is_valid():
                if not link.is_active:
                    raise HTTPException(status_code=403, detail="Share link has been deactivated")
                if link.is_expired():
                    raise HTTPException(status_code=403, detail="Share link has expired")
                if link.max_access_count and link.access_count >= link.max_access_count:
                    raise HTTPException(status_code=403, detail="Share link access limit reached")
            
            # Check password
            if link.password_hash:
                if not password:
                    raise HTTPException(status_code=401, detail="Password required")
                from passlib.hash import bcrypt
                if not bcrypt.verify(password, link.password_hash):
                    raise HTTPException(status_code=401, detail="Invalid password")
            
            # Increment access count
            link.access_count += 1
            session.commit()
            
            # Audit
            audit.log_admin_action(
                AuditAction.SHARE_ACCESS, None, link.id,
                ip_address=ip_address,
                metadata={"path": link.path}
            )
            
            # Return share metadata and file info
            return {
                "path": link.path,
                "permissions": link.permissions,
                "file": self.storage.get_stat(link.path),
            }
        finally:
            session.close()
    
    def access_share_content(
        self,
        token: str,
        password: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get content listing for a share link"""
        session = self.db_factory()
        try:
            link = session.query(SharedLink).filter(SharedLink.token == token).first()
            if not link:
                raise HTTPException(status_code=404, detail="Share link not found")
            
            if not link.is_valid():
                if not link.is_active:
                    raise HTTPException(status_code=403, detail="Share link has been deactivated")
                if link.is_expired():
                    raise HTTPException(status_code=403, detail="Share link has expired")
            
            # Check password
            if link.password_hash:
                if not password:
                    raise HTTPException(status_code=401, detail="Password required")
                from passlib.hash import bcrypt
                if not bcrypt.verify(password, link.password_hash):
                    raise HTTPException(status_code=401, detail="Invalid password")
            
            # Get directory listing
            items = self.storage.list_directory(link.path)
            
            return {
                "path": link.path,
                "permissions": link.permissions,
                "items": items,
            }
        finally:
            session.close()
    
    def update_share_link(
        self,
        token: str,
        request: UpdateShareRequest,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update share link settings"""
        session = self.db_factory()
        try:
            link = session.query(SharedLink).filter(SharedLink.token == token).first()
            if not link:
                raise HTTPException(status_code=404, detail="Share link not found")
            
            # Verify ownership
            if link.created_by != user.id and (user.role is None or user.role.name != "admin"):
                raise HTTPException(status_code=403, detail="Not the owner")
            
            # Update fields
            if request.password is not None:
                if request.password:
                    from passlib.hash import bcrypt
                    link.password_hash = bcrypt.hash(request.password, rounds=12)
                else:
                    link.password_hash = None
            
            if request.permissions is not None:
                if request.permissions not in ("read", "read_write"):
                    raise HTTPException(status_code=400, detail="permissions must be 'read' or 'read_write'")
                link.permissions = request.permissions
            
            if request.expires_in_days is not None:
                if request.expires_in_days:
                    link.expires_at = datetime.utcnow() + timedelta(days=request.expires_in_days)
                else:
                    link.expires_at = None
            
            if request.max_access_count is not None:
                link.max_access_count = request.max_access_count
            
            if request.is_active is not None:
                link.is_active = request.is_active
            
            session.commit()
            
            return link.to_dict()
        finally:
            session.close()
    
    def delete_share_link(
        self,
        token: str,
        user: User,
        ip_address: Optional[str] = None,
    ) -> Dict[str, str]:
        """Delete a share link"""
        session = self.db_factory()
        try:
            link = session.query(SharedLink).filter(SharedLink.token == token).first()
            if not link:
                raise HTTPException(status_code=404, detail="Share link not found")
            
            # Verify ownership
            if link.created_by != user.id and (user.role is None or user.role.name != "admin"):
                raise HTTPException(status_code=403, detail="Not the owner")
            
            path = link.path
            session.delete(link)
            session.commit()
            
            # Audit
            audit = AuditLogger(session)
            audit.log_admin_action(
                AuditAction.SHARE_DELETE, user, token,
                ip_address=ip_address,
                metadata={"path": path}
            )
            
            return {"message": "Share link deleted"}
        finally:
            session.close()
