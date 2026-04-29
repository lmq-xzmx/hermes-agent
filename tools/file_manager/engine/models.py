"""
Data models for Hermes File Manager
Uses SQLAlchemy for persistence
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Boolean, Integer, DateTime, ForeignKey,
    Text, JSON, Enum, Index, create_engine
)
from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from passlib.hash import bcrypt
import uuid as uuid_lib

Base = declarative_base()


class Operation(PyEnum):
    """File operations that can be performed"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"
    LIST = "list"


class Permission(PyEnum):
    """Permission flags"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"


class AuditAction(PyEnum):
    """Audit log action types"""
    # Auth actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    
    # File actions
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_LIST = "file_list"
    FILE_CREATE = "file_create"
    FILE_MOVE = "file_move"
    FILE_COPY = "file_copy"
    
    # Admin actions
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    ROLE_CREATE = "role_create"
    ROLE_UPDATE = "role_update"
    ROLE_DELETE = "role_delete"
    RULE_CREATE = "rule_create"
    RULE_UPDATE = "rule_update"
    RULE_DELETE = "rule_delete"
    
    # Share actions
    SHARE_CREATE = "share_create"
    SHARE_ACCESS = "share_access"
    SHARE_DELETE = "share_delete"
    
    # Catch-all for unclassified actions
    OTHER = "other"


class User(Base):
    """User model"""
    __tablename__ = "hfm_users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=True)
    email = Column(String(255), nullable=True)
    role_id = Column(String(36), ForeignKey("hfm_roles.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    role = relationship("Role", back_populates="users")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    shared_links = relationship("SharedLink", back_populates="creator", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        """Hash and set password"""
        from passlib.hash import bcrypt
        self.password_hash = bcrypt.using(rounds=12).hash(password)
    
    def check_password(self, password: str) -> bool:
        """Verify password"""
        from passlib.hash import bcrypt
        if self.password_hash is None:
            return False
        return bcrypt.verify(password, self.password_hash)
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Serialize to dict"""
        data = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_sensitive:
            data["_warning"] = "Sensitive data included"
        return data


class Role(Base):
    """Role model for RBAC"""
    __tablename__ = "hfm_roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(32), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="role")
    permission_rules = relationship("PermissionRule", back_populates="role", cascade="all, delete-orphan")
    
    # Built-in role definitions
    BUILTIN_ROLES = {
        "admin": {
            "description": "Full access to all resources and management capabilities",
            "is_system": True,
        },
        "editor": {
            "description": "Read and write access to assigned paths, cannot delete or manage",
            "is_system": True,
        },
        "viewer": {
            "description": "Read-only access to assigned paths",
            "is_system": True,
        },
        "guest": {
            "description": "Minimal read access to shared resources",
            "is_system": True,
        },
    }
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_system": self.is_system,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PermissionRule(Base):
    """Permission rule for path-based access control"""
    __tablename__ = "hfm_permission_rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id = Column(String(36), ForeignKey("hfm_roles.id"), nullable=False)
    path_pattern = Column(Text, nullable=False)  # Glob pattern
    permissions = Column(Text, nullable=False)  # Comma-separated: "read,write,delete"
    priority = Column(Integer, default=0)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    role = relationship("Role", back_populates="permission_rules")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Index for faster lookups
    __table_args__ = (
        Index("ix_hfm_rules_role_priority", "role_id", "priority"),
    )
    
    def get_permissions(self) -> List[str]:
        """Parse permissions string to list"""
        return [p.strip() for p in self.permissions.split(",") if p.strip()]
    
    def has_permission(self, operation: str) -> bool:
        """Check if this rule grants the given operation"""
        return operation in self.get_permissions()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role_id": self.role_id,
            "role_name": self.role.name if self.role else None,
            "path_pattern": self.path_pattern,
            "permissions": self.get_permissions(),
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(Base):
    """Audit log for all operations"""
    __tablename__ = "hfm_audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    action = Column(String(64), nullable=False, index=True)
    path = Column(Text, nullable=True)  # File path involved
    result = Column(String(16), nullable=False)  # success, denied, error
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    extra = Column("metadata", JSON, nullable=True)  # Extra details
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_hfm_audit_user_action", "user_id", "action"),
        Index("ix_hfm_audit_path", "path"),
        Index("ix_hfm_audit_created", "created_at"),
    )
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else "anonymous",
            "action": self.action,
            "path": self.path,
            "result": self.result,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "extra": self.extra,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SharedLink(Base):
    """Shared link model"""
    __tablename__ = "hfm_shared_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    path = Column(Text, nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(128), nullable=True)  # Optional password
    permissions = Column(String(16), default="read")  # read or read_write
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    access_count = Column(Integer, default=0)
    max_access_count = Column(Integer, nullable=True)  # Optional limit
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="shared_links")
    
    def set_password(self, password: str) -> None:
        """Hash and set share link password"""
        from passlib.hash import bcrypt
        self.password_hash = bcrypt.using(rounds=12).hash(password)

    def check_password(self, password: str) -> bool:
        """Verify share link password"""
        if not self.password_hash:
            return True
        return bcrypt.verify(password, self.password_hash)
    
    def is_expired(self) -> bool:
        """Check if link has expired"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if link is valid"""
        if not self.is_active:
            return False
        if self.is_expired():
            return False
        if self.max_access_count and self.access_count >= self.max_access_count:
            return False
        return True
    
    def to_dict(self, include_token: bool = False) -> dict:
        data = {
            "id": self.id,
            "path": self.path,
            "permissions": self.permissions,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "access_count": self.access_count,
            "max_access_count": self.max_access_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by": self.creator.username if self.creator else None,
        }
        if include_token:
            data["token"] = self.token
        return data


class UserSession(Base):
    """User session for tracking active logins"""
    __tablename__ = "hfm_user_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    token_hash = Column(String(128), nullable=False)  # Hash of refresh token
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("ix_hfm_sessions_user", "user_id"),
        Index("ix_hfm_sessions_token", "token_hash"),
    )


# Database initialization utilities

def init_db(database_url: str = "sqlite:///hfm.db") -> sessionmaker:
    """Initialize database and return session factory"""
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        poolclass=StaticPool if "sqlite" in database_url else None,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def create_builtin_roles(session: Session) -> None:
    """Create system roles if they don't exist"""
    for name, data in Role.BUILTIN_ROLES.items():
        existing = session.query(Role).filter(Role.name == name).first()
        if not existing:
            role = Role(name=name, **data)
            session.add(role)
    session.commit()


def get_default_storage_path() -> str:
    """Get default file storage path"""
    import os
    from pathlib import Path
    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    return str(Path(hermes_home) / "file_manager" / "storage")
