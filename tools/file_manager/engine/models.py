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
    team_memberships = relationship("SpaceMember", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    shared_links = relationship("SharedLink", back_populates="creator", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    
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


class Notification(Base):
    """In-app notification for users (quota warnings, etc.)"""
    __tablename__ = "hfm_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False, index=True)  # "quota_warning", "space_invite", "collaboration", "system"
    title = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)  # Optional link to related resource
    is_read = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("ix_hfm_notifications_user_read", "user_id", "is_read"),
        Index("ix_hfm_notifications_created", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "is_read": self.is_read,
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
    spaces = relationship("Space", back_populates="storage_pool")

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


class Space(Base):
    """
    Space - hierarchical storage space for teams and individuals.

    Hierarchy:
      Root Space (created by admin, binds to StoragePool)
        └── Team Space (shared by team members)
              └── Private Space (personal space granted to member)
    """
    __tablename__ = "hfm_spaces"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(16), nullable=True)  # Human-readable code, e.g. "SP-2026-001"
    name = Column(String(64), nullable=False)
    parent_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=True)  # null for root spaces
    storage_pool_id = Column(String(36), ForeignKey("hfm_storage_pools.id"), nullable=False)
    owner_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    max_bytes = Column(BigInteger, default=0)  # 0 = unlimited within pool
    used_bytes = Column(BigInteger, default=0)
    space_type = Column(String(16), default="team")  # "root" | "team" | "private"
    status = Column(String(16), default="active")  # "active" | "pending" | "archived"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    storage_pool = relationship("StoragePool", back_populates="spaces")
    owner = relationship("User", foreign_keys=[owner_id])
    parent = relationship("Space", remote_side=[id], back_populates="children")
    children = relationship("Space", back_populates="parent", cascade="all, delete-orphan")
    members = relationship("SpaceMember", back_populates="space", cascade="all, delete-orphan")
    credentials = relationship("SpaceCredential", back_populates="space", cascade="all, delete-orphan")
    requests = relationship("SpaceRequest", back_populates="space", cascade="all, delete-orphan")
    versions = relationship("FileVersion", back_populates="space", cascade="all, delete-orphan")
    workflows = relationship("Workflow", back_populates="space", cascade="all, delete-orphan")
    notebooks = relationship("Notebook", back_populates="space", cascade="all, delete-orphan")
    file_locks = relationship("FileLock", back_populates="space", cascade="all, delete-orphan")
    collaboration_sessions = relationship("CollaborationSession", back_populates="space", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_hfm_spaces_pool", "storage_pool_id"),
        Index("ix_hfm_spaces_parent", "parent_id"),
    )

    def to_dict(self, include_members: bool = False, include_stats: bool = False) -> dict:
        data = {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "parent_id": self.parent_id,
            "storage_pool_id": self.storage_pool_id,
            "pool_name": self.storage_pool.name if self.storage_pool else None,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else None,
            "max_bytes": self.max_bytes,
            "used_bytes": self.used_bytes,
            "space_type": self.space_type,
            "status": self.status,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        if include_stats:
            data["member_count"] = len([m for m in self.members if m.status == "active"])
            data["workflow_count"] = len(self.workflows)
            data["notebook_count"] = len(self.notebooks)
        return data


class SpaceMember(Base):
    """Space membership - user belongs to a space with a specific role"""
    __tablename__ = "hfm_space_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    role = Column(String(16), default="member")  # "owner" | "member" | "viewer"
    quota_bytes = Column(BigInteger, default=0)  # 0 = use space default
    joined_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(16), default="active")  # "active" | "pending" | "rejected"

    # Relationships
    space = relationship("Space", back_populates="members")
    user = relationship("User")

    __table_args__ = (
        Index("ix_hfm_space_members_unique", "space_id", "user_id", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_name": self.space.name if self.space else None,
            "user_id": self.user_id,
            "username": self.user.username if self.user else None,
            "role": self.role,
            "quota_bytes": self.quota_bytes,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "status": self.status,
        }


class SpaceCredential(Base):
    """Invite token for joining a space"""
    __tablename__ = "hfm_space_credentials"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    token = Column(String(64), unique=True, nullable=False, index=True)
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    used_count = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    space = relationship("Space", back_populates="credentials")
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
            "space_id": self.space_id,
            "space_name": self.space.name if self.space else None,
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


class SpaceRequest(Base):
    """Request for private sub-space within a parent space"""
    __tablename__ = "hfm_space_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    requester_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    requested_name = Column(String(64), nullable=False)
    requested_bytes = Column(BigInteger, default=0)
    reason = Column(Text, nullable=True)
    status = Column(String(16), default="pending")  # "pending" | "approved" | "rejected"
    reviewed_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    space = relationship("Space", back_populates="requests")
    requester = relationship("User", foreign_keys=[requester_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_name": self.space.name if self.space else None,
            "requester_id": self.requester_id,
            "requester_name": self.requester.username if self.requester else None,
            "requested_name": self.requested_name,
            "requested_bytes": self.requested_bytes,
            "reason": self.reason,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewer_name": self.reviewer.username if self.reviewer else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_note": self.review_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FileVersion(Base):
    """
    File version tracking for all file operations.
    Each create/update/delete operation creates a version record.
    """
    __tablename__ = "hfm_file_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    path = Column(Text, nullable=False)  # File path (unique within space + version)
    name = Column(String(255), nullable=False)
    is_directory = Column(Boolean, default=False)
    size = Column(BigInteger, default=0)
    checksum = Column(String(64), nullable=True)  # SHA256
    version = Column(Integer, nullable=False)  # Auto-increment per path
    action = Column(String(16), nullable=False)  # "create" | "update" | "delete"
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)

    # Relationships
    space = relationship("Space", back_populates="versions")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_hfm_file_versions_space", "space_id"),
        Index("ix_hfm_file_versions_path", "path"),
        Index("ix_hfm_file_versions_path_version", "path", "version"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "file_id": self.file_id,
            "space_id": self.space_id,
            "path": self.path,
            "name": self.name,
            "is_directory": self.is_directory,
            "size": self.size,
            "checksum": self.checksum,
            "version": self.version,
            "action": self.action,
            "created_by": self.created_by,
            "creator_name": self.creator.username if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_data,
        }


class DeletedFile(Base):
    """Soft-deleted file record for trash/recovery mechanism."""
    __tablename__ = "hfm_deleted_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    original_path = Column(Text, nullable=False)  # Original path before deletion
    name = Column(String(255), nullable=False)
    is_directory = Column(Boolean, default=False)
    file_size = Column(BigInteger, default=0)
    deleted_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    deleted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)  # Auto-purge after this time (30 days default)

    # Relationships
    space = relationship("Space")
    user = relationship("User", foreign_keys=[deleted_by])

    __table_args__ = (
        Index("ix_hfm_deleted_files_space", "space_id"),
        Index("ix_hfm_deleted_files_expires", "expires_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "original_path": self.original_path,
            "name": self.name,
            "is_directory": self.is_directory,
            "file_size": self.file_size,
            "deleted_by": self.deleted_by,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


class WorkflowStep(Base):
    """Workflow step - single command in a workflow"""
    __tablename__ = "hfm_workflow_steps"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String(36), ForeignKey("hfm_workflows.id"), nullable=False)
    order = Column(Integer, nullable=False)  # 1-based execution order
    command = Column(Text, nullable=False)  # Shell command
    explanation = Column(Text, nullable=True)  # Human-readable description
    confirm_required = Column(Boolean, default=False)  # Pause before exec
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    workflow = relationship("Workflow", back_populates="steps")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "order": self.order,
            "command": self.command,
            "explanation": self.explanation,
            "confirm_required": self.confirm_required,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Workflow(Base):
    """Workflow - saved command sequence, reusable like Warp Workflows"""
    __tablename__ = "hfm_workflows"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    owner_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    is_shared = Column(Boolean, default=False)  # Visible to space members
    tags = Column(JSON, nullable=True)  # ["git", "deploy", "db-migration"]
    usage_count = Column(Integer, default=0)  # Popularity metric
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    space = relationship("Space", back_populates="workflows")
    owner = relationship("User", foreign_keys=[owner_id])
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.order"
    )

    __table_args__ = (
        Index("ix_hfm_workflows_space", "space_id"),
        Index("ix_hfm_workflows_owner", "owner_id"),
    )

    def to_dict(self, include_steps: bool = False) -> dict:
        data = {
            "id": self.id,
            "space_id": self.space_id,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else None,
            "name": self.name,
            "description": self.description,
            "is_shared": self.is_shared,
            "tags": self.tags or [],
            "usage_count": self.usage_count,
            "step_count": len(self.steps),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_steps:
            data["steps"] = [s.to_dict() for s in self.steps]
        return data


class NotebookVariable(Base):
    """Predefined variable in a notebook"""
    __tablename__ = "hfm_notebook_variables"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    notebook_id = Column(String(36), ForeignKey("hfm_notebooks.id"), nullable=False)
    name = Column(String(64), nullable=False)  # Variable name e.g. "$DATABASE_URL"
    default_value = Column(Text, nullable=True)  # Default value
    description = Column(Text, nullable=True)  # Usage description
    is_required = Column(Boolean, default=True)  # Must be provided at runtime
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    notebook = relationship("Notebook", back_populates="variables")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "notebook_id": self.notebook_id,
            "name": self.name,
            "default_value": self.default_value,
            "description": self.description,
            "is_required": self.is_required,
        }


class Notebook(Base):
    """Notebook - interactive tutorial document like Warp Notebooks"""
    __tablename__ = "hfm_notebooks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    owner_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown content
    is_shared = Column(Boolean, default=False)
    tags = Column(JSON, nullable=True)  # ["tutorial", "onboarding", "devops"]
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    space = relationship("Space", back_populates="notebooks")
    owner = relationship("User", foreign_keys=[owner_id])
    variables = relationship(
        "NotebookVariable",
        back_populates="notebook",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_hfm_notebooks_space", "space_id"),
        Index("ix_hfm_notebooks_owner", "owner_id"),
    )

    def to_dict(self, include_variables: bool = False) -> dict:
        data = {
            "id": self.id,
            "space_id": self.space_id,
            "owner_id": self.owner_id,
            "owner_name": self.owner.username if self.owner else None,
            "name": self.name,
            "description": self.description,
            "content": self.content,
            "is_shared": self.is_shared,
            "tags": self.tags or [],
            "usage_count": self.usage_count,
            "variable_count": len(self.variables),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_variables:
            data["variables"] = [v.to_dict() for v in self.variables]
        return data


class FileLock(Base):
    """文件锁 - 防止并发编辑冲突"""
    __tablename__ = "hfm_file_locks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    path = Column(Text, nullable=False)  # 相对于 space 的路径
    locked_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    locked_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    lock_type = Column(String(16), default="edit")  # "edit" | "read"
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_hfm_file_locks_space_path", "space_id", "path"),
        Index("ix_hfm_file_locks_locked_by", "locked_by"),
    )

    # Relationships
    space = relationship("Space", back_populates="file_locks")
    user = relationship("User", foreign_keys=[locked_by])

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "path": self.path,
            "locked_by": self.locked_by,
            "locked_by_name": self.user.username if self.user else None,
            "locked_at": self.locked_at.isoformat() if self.locked_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "lock_type": self.lock_type,
            "is_active": self.is_active,
        }

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


class CollaborationSession(Base):
    """协作会话 - 跨 Space 临时授权"""
    __tablename__ = "hfm_collaboration_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    target_user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    permissions = Column(JSON)  # ["read", "write"] 等
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_hfm_collab_sessions_space", "space_id"),
        Index("ix_hfm_collab_sessions_target", "target_user_id"),
    )

    # Relationships
    space = relationship("Space", back_populates="collaboration_sessions")
    creator = relationship("User", foreign_keys=[created_by])
    target_user = relationship("User", foreign_keys=[target_user_id])

    def to_dict(self):
        return {
            "id": self.id,
            "space_id": self.space_id,
            "space_name": self.space.name if self.space else None,
            "created_by": self.created_by,
            "created_by_name": self.creator.username if self.creator else None,
            "target_user_id": self.target_user_id,
            "target_user_name": self.target_user.username if self.target_user else None,
            "permissions": self.permissions or [],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "is_active": self.is_active,
        }

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at


# Backward compatibility aliases (Deprecated: use Space/SpaceMember instead)
Team = Space
TeamMember = SpaceMember
TeamCredential = SpaceCredential


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
