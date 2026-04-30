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
    Text, JSON, Enum, Index, create_engine, BigInteger
)
from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool, NullPool
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
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
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
            "_default_rules": [],
        },
        "editor": {
            "description": "Read and write access to assigned paths, cannot delete or manage",
            "is_system": True,
            "_default_rules": [
                {"path_pattern": "/**", "permissions": "read,write,list,delete"},
            ],
        },
        "viewer": {
            "description": "Read-only access to assigned paths",
            "is_system": True,
            "_default_rules": [
                {"path_pattern": "/**", "permissions": "read,list"},
            ],
        },
        "guest": {
            "description": "Minimal read access to shared resources",
            "is_system": True,
            "_default_rules": [
                {"path_pattern": "/**", "permissions": "read"},
            ],
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

    def to_primitive(self) -> str:
        """Return primitive string representation: 'perm1,perm2:path_pattern'."""
        perms = ",".join(self.get_permissions())
        return f"{perms}:{self.path_pattern}"


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


class StoragePool(Base):
    """Virtual storage pool - abstracts physical storage locations"""
    __tablename__ = "hfm_storage_pools"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False)                          # Display name e.g. "本地存储"
    base_path = Column(Text, nullable=False)                           # Physical path or URI
    protocol = Column(String(16), default="local")                     # "local" | "smb" | "nfs" | "s3" | "minio"
    total_bytes = Column(BigInteger, default=0)                        # Configured total space (0 = auto-detect)
    free_bytes = Column(BigInteger, default=0)                         # Cached free space, updated on access
    is_active = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = relationship("Team", back_populates="storage_pool")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "base_path": self.base_path,
            "protocol": self.protocol,
            "total_bytes": self.total_bytes,
            "free_bytes": self.free_bytes,
            "is_active": self.is_active,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Team(Base):
    """Team - a group of users sharing a storage quota"""
    __tablename__ = "hfm_teams"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(64), nullable=False)
    storage_pool_id = Column(String(36), ForeignKey("hfm_storage_pools.id"), nullable=False)
    max_bytes = Column(BigInteger, default=0)                         # Max bytes allowed (0 = unlimited within pool)
    used_bytes = Column(BigInteger, default=0)                        # Current usage
    owner_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    storage_pool = relationship("StoragePool", back_populates="teams")
    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    credentials = relationship("TeamCredential", back_populates="team", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_hfm_teams_pool", "storage_pool_id"),
    )

    def to_dict(self, include_members: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "storage_pool_id": self.storage_pool_id,
            "pool_name": self.storage_pool.name if self.storage_pool else None,
            "max_bytes": self.max_bytes,
            "used_bytes": self.used_bytes,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        return data


class TeamMember(Base):
    """Team membership"""
    __tablename__ = "hfm_team_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), ForeignKey("hfm_teams.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    role = Column(String(16), default="member")                        # "owner" | "member"
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        Index("ix_hfm_team_members_unique", "team_id", "user_id", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
        }


class TeamCredential(Base):
    """Invite token for joining a team"""
    __tablename__ = "hfm_team_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), ForeignKey("hfm_teams.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    max_uses = Column(Integer, nullable=True)                         # None = unlimited
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="credentials")
    creator = relationship("User", foreign_keys=[created_by])

    def is_valid(self) -> bool:
        """Check if credential can still be used"""
        if not self.is_active:
            return False
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def to_dict(self, include_token: bool = False) -> dict:
        data = {
            "id": self.id,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "max_uses": self.max_uses,
            "used_count": self.used_count,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_by": self.creator.username if self.creator else None,
            "is_active": self.is_active,
            "is_valid": self.is_valid(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_token:
            data["token"] = self.token
        return data


# Database initialization utilities

def init_db(database_url: str = "sqlite:///hfm.db") -> sessionmaker:
    """Initialize database and return session factory"""
    if "sqlite" in database_url:
        # NullPool creates a fresh connection for each request, avoiding the
        # "database is locked" error under concurrent async load.
        engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
            },
            poolclass=NullPool,
        )
    else:
        engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def create_builtin_roles(session: Session) -> None:
    """Create system roles with default permission rules if they don't exist"""
    for name, data in Role.BUILTIN_ROLES.items():
        existing = session.query(Role).filter(Role.name == name).first()
        if not existing:
            role = Role(name=name, description=data.get("description"), is_system=data.get("is_system", True))
            session.add(role)
            session.flush()  # get the role.id before committing

            # Seed default permission rules
            for rule_data in data.get("_default_rules", []):
                rule = PermissionRule(
                    role_id=role.id,
                    path_pattern=rule_data["path_pattern"],
                    permissions=rule_data["permissions"],
                    priority=rule_data.get("priority", 0),
                    created_by=None,
                )
                session.add(rule)
        else:
            # Role exists — seed default rules if the role has none
            if not existing.permission_rules:
                for rule_data in data.get("_default_rules", []):
                    rule = PermissionRule(
                        role_id=existing.id,
                        path_pattern=rule_data["path_pattern"],
                        permissions=rule_data["permissions"],
                        priority=rule_data.get("priority", 0),
                        created_by=None,
                    )
                    session.add(rule)
    session.commit()


def get_default_storage_path() -> str:
    """Get default file storage path"""
    import os
    from pathlib import Path
    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    return str(Path(hermes_home) / "file_manager" / "storage")
