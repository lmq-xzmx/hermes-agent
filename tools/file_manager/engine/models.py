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
    Text, JSON, Enum, Index, create_engine, BigInteger, Numeric
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


class PermissionFlag(PyEnum):
    """Permission flags (legacy enum, use Permission model for resource-action)"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE = "manage"


# Backward compatibility alias
Permission = PermissionFlag


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
    role_change_records = relationship("RoleChangeRecord", foreign_keys="RoleChangeRecord.user_id", back_populates="user", cascade="all, delete-orphan")
    
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
    # Account type: "admin" | "member" | "guest"
    # - admin: 系统管理员，拥有全部权限
    # - member: 普通成员，可读写分配给它的资源
    # - guest: 访客，仅有最小权限
    account_type = Column(String(16), default="member")
    priority = Column(Integer, default=0)  # Role priority for permission resolution
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="role")
    permission_rules = relationship("PermissionRule", back_populates="role", cascade="all, delete-orphan")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    # Built-in role definitions (priority: admin > editor > viewer > guest)
    BUILTIN_ROLES = {
        "admin": {
            "description": "Full access to all resources and management capabilities",
            "is_system": True,
            "account_type": "admin",
            "priority": 100,
            "_default_rules": [],
        },
        "editor": {
            "description": "Read and write access to assigned paths, cannot delete or manage",
            "is_system": True,
            "account_type": "member",
            "priority": 50,
            "_default_rules": [
                {"path_pattern": "/**", "permissions": "read,write,list,delete"},
            ],
        },
        "viewer": {
            "description": "Read-only access to assigned paths",
            "is_system": True,
            "account_type": "member",
            "priority": 10,
            "_default_rules": [
                {"path_pattern": "/**", "permissions": "read,list"},
            ],
        },
        "guest": {
            "description": "Minimal read access to shared resources",
            "is_system": True,
            "account_type": "guest",
            "priority": 1,
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
            "account_type": self.account_type,
            "priority": self.priority,
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


class Permission(Base):
    """Permission definition - resource-action format for RBAC.

    Replaces the legacy PermissionRule path-based approach with a cleaner
    resource-action model. Permissions are assigned to roles via RolePermission.
    """
    __tablename__ = "hfm_permissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resource = Column(String(32), nullable=False, index=True)  # file, space, team, storage_pool, user, role
    action = Column(String(32), nullable=False, index=True)    # create, read, update, delete, manage
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    # Unique constraint on resource+action
    __table_args__ = (
        Index("ix_hfm_permissions_resource_action", "resource", "action", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "resource": self.resource,
            "action": self.action,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RolePermission(Base):
    """Role-Permission association table for RBAC.

    Links roles to permissions. A role can have many permissions,
    and a permission can be assigned to many roles.
    """
    __tablename__ = "hfm_role_permissions"

    role_id = Column(String(36), ForeignKey("hfm_roles.id"), primary_key=True)
    permission_id = Column(String(36), ForeignKey("hfm_permissions.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    def to_dict(self) -> dict:
        return {
            "role_id": self.role_id,
            "permission_id": self.permission_id,
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


class RoleChangeRecord(Base):
    """
    Role change record for identity lifecycle management.

    Tracks:
    - User role changes (admin ↔ member ↔ guest)
    - Asset state before/after change
    - Who performed the change
    - Change reason and rollback info

    This enables:
    - Audit trail of role changes
    - Asset recovery on role rollback
    - Compliance reporting
    """
    __tablename__ = "hfm_role_change_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False, index=True)
    changed_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)

    # Role state
    old_role_id = Column(String(36), ForeignKey("hfm_roles.id"), nullable=True)
    new_role_id = Column(String(36), ForeignKey("hfm_roles.id"), nullable=False)

    # Asset snapshot (JSON) - captures asset state before change
    asset_snapshot = Column(JSON, nullable=True)

    # Change metadata
    reason = Column(Text, nullable=True)
    change_type = Column(String(32), nullable=False)  # promotion | demotion | transfer | reset
    rollback_available = Column(Boolean, default=True)
    rolled_back = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    rolled_back_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="role_change_records")
    changed_by_user = relationship("User", foreign_keys=[changed_by])
    old_role = relationship("Role", foreign_keys=[old_role_id])
    new_role = relationship("Role", foreign_keys=[new_role_id])

    # Indexes
    __table_args__ = (
        Index("ix_hfm_role_change_user", "user_id"),
        Index("ix_hfm_role_change_created", "created_at"),
        Index("ix_hfm_role_change_change_type", "change_type"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "changed_by": self.changed_by,
            "old_role_id": self.old_role_id,
            "new_role_id": self.new_role_id,
            "old_role_name": self.old_role.name if self.old_role else None,
            "new_role_name": self.new_role.name if self.new_role else None,
            "asset_snapshot": self.asset_snapshot,
            "reason": self.reason,
            "change_type": self.change_type,
            "rollback_available": self.rollback_available,
            "rolled_back": self.rolled_back,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
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

    # A-1: 新增配额管理字段
    reserved_bytes = Column(BigInteger, default=0)       # 组织预留空间
    allow_overcommit = Column(Boolean, default=False)     # 允许透支
    soft_warning_ratio = Column(Numeric(5, 2), default=0.8)  # 软预警阈值 0.80
    hard_block_ratio = Column(Numeric(5, 2), default=1.0)   # 硬阻塞阈值 1.00
    buffer_ratio = Column(Numeric(5, 2), default=0.1)      # 缓冲比例 0.10

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
            "reserved_bytes": self.reserved_bytes,
            "allow_overcommit": self.allow_overcommit,
            "soft_warning_ratio": float(self.soft_warning_ratio) if self.soft_warning_ratio else 0.8,
            "hard_block_ratio": float(self.hard_block_ratio) if self.hard_block_ratio else 1.0,
            "buffer_ratio": float(self.buffer_ratio) if self.buffer_ratio else 0.1,
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

    # A-2: 新增配额字段
    quota_type = Column(String(16), default="committed")  # committed | reserved | unlimited
    committed_bytes = Column(BigInteger, default=0)       # 承诺配额
    actual_used_bytes = Column(BigInteger, default=0)    # 实际使用
    quota_source = Column(String(16), default="team")     # team | personal | org
    source_id = Column(String(36), nullable=True)        # 来源ID (team_id/user_id)

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
    incoming_links = relationship("SpaceLink", foreign_keys="SpaceLink.target_space_id", back_populates="target_space", cascade="all, delete-orphan")
    outgoing_links = relationship("SpaceLink", foreign_keys="SpaceLink.source_space_id", back_populates="source_space", cascade="all, delete-orphan")

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
            # A-2: 新增配额字段
            "quota_type": self.quota_type,
            "committed_bytes": self.committed_bytes,
            "actual_used_bytes": self.actual_used_bytes,
            "quota_source": self.quota_source,
            "source_id": self.source_id,
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
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


class SpaceLink(Base):
    """Cross-space collaboration link - share space with another space/team"""
    __tablename__ = "hfm_space_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    target_space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    created_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    permission = Column(String(16), default="read")  # "read" | "write" | "admin"
    status = Column(String(16), default="active")  # "active" | "revoked"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    source_space = relationship("Space", foreign_keys=[source_space_id], back_populates="outgoing_links")
    target_space = relationship("Space", foreign_keys=[target_space_id], back_populates="incoming_links")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("ix_hfm_space_links_unique", "source_space_id", "target_space_id", unique=True),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_space_id": self.source_space_id,
            "source_space_name": self.source_space.name if self.source_space else None,
            "target_space_id": self.target_space_id,
            "target_space_name": self.target_space.name if self.target_space else None,
            "created_by": self.created_by,
            "creator_name": self.creator.username if self.creator else None,
            "permission": self.permission,
            "status": self.status,
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


class FileUpload(Base):
    """上传跟踪表 - 记录正在进行的文件上传，用于配额预留计算"""
    __tablename__ = "hfm_file_uploads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)  # 预计总大小
    uploaded_bytes = Column(BigInteger, default=0)  # 已上传大小
    status = Column(String(16), default="uploading")  # "uploading" | "completed" | "failed" | "cancelled"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    space = relationship("Space")
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        Index("ix_hfm_file_uploads_space_status", "space_id", "status"),
        Index("ix_hfm_file_uploads_user", "user_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "space_id": self.space_id,
            "user_id": self.user_id,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "uploaded_bytes": self.uploaded_bytes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }

    def is_active(self) -> bool:
        return self.status == "uploading"

    def mark_completed(self):
        self.status = "completed"
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str = None):
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error

    def cancel(self):
        self.status = "cancelled"
        self.completed_at = datetime.utcnow()


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
        # Use StaticPool for in-memory SQLite so all connections share the same database.
        # NullPool creates a fresh connection per request, which means in-memory SQLite
        # each connection sees a different database instance.
        if ":memory:" in database_url:
            pool_class = StaticPool
        else:
            pool_class = NullPool
        engine = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
                "timeout": 30,
            },
            poolclass=pool_class,
        )
    else:
        engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def create_builtin_roles(session: Session) -> None:
    """Create system roles with default permission rules and RBAC permissions.

    Also creates default Permission and RolePermission entries based on role priority.
    """
    # Define default resource-action permissions for each role
    ROLE_PERMISSIONS = {
        "admin": [
            {"resource": "file", "action": "create"},
            {"resource": "file", "action": "read"},
            {"resource": "file", "action": "update"},
            {"resource": "file", "action": "delete"},
            {"resource": "space", "action": "create"},
            {"resource": "space", "action": "read"},
            {"resource": "space", "action": "update"},
            {"resource": "space", "action": "delete"},
            {"resource": "space", "action": "manage"},
            {"resource": "team", "action": "create"},
            {"resource": "team", "action": "read"},
            {"resource": "team", "action": "update"},
            {"resource": "team", "action": "delete"},
            {"resource": "team", "action": "manage"},
            {"resource": "user", "action": "create"},
            {"resource": "user", "action": "read"},
            {"resource": "user", "action": "update"},
            {"resource": "user", "action": "delete"},
            {"resource": "role", "action": "create"},
            {"resource": "role", "action": "read"},
            {"resource": "role", "action": "update"},
            {"resource": "role", "action": "delete"},
            {"resource": "storage_pool", "action": "create"},
            {"resource": "storage_pool", "action": "read"},
            {"resource": "storage_pool", "action": "update"},
            {"resource": "storage_pool", "action": "delete"},
        ],
        "editor": [
            {"resource": "file", "action": "create"},
            {"resource": "file", "action": "read"},
            {"resource": "file", "action": "update"},
            {"resource": "file", "action": "delete"},
            {"resource": "space", "action": "read"},
            {"resource": "space", "action": "update"},
        ],
        "viewer": [
            {"resource": "file", "action": "read"},
            {"resource": "space", "action": "read"},
        ],
        "guest": [
            {"resource": "file", "action": "read"},
        ],
    }

    for name, data in Role.BUILTIN_ROLES.items():
        existing = session.query(Role).filter(Role.name == name).first()
        if not existing:
            role = Role(
                name=name,
                description=data.get("description"),
                is_system=data.get("is_system", True),
                account_type=data.get("account_type", "member"),
                priority=data.get("priority", 0),
            )
            session.add(role)
            session.flush()

            # Seed default permission rules (legacy path-based)
            for rule_data in data.get("_default_rules", []):
                rule = PermissionRule(
                    role_id=role.id,
                    path_pattern=rule_data["path_pattern"],
                    permissions=rule_data["permissions"],
                    priority=rule_data.get("priority", 0),
                    created_by=None,
                )
                session.add(rule)

            # Seed RBAC permissions (new resource-action format)
            for perm_data in ROLE_PERMISSIONS.get(name, []):
                # Check if permission already exists
                perm = session.query(Permission).filter(
                    Permission.resource == perm_data["resource"],
                    Permission.action == perm_data["action"],
                ).first()
                if not perm:
                    perm = Permission(
                        resource=perm_data["resource"],
                        action=perm_data["action"],
                        description=f"{perm_data['action']} {perm_data['resource']}",
                    )
                    session.add(perm)
                    session.flush()
                # Link role to permission
                role_perm = RolePermission(role_id=role.id, permission_id=perm.id)
                session.add(role_perm)
        else:
            # Update priority if role exists but priority is not set
            if existing.priority is None or existing.priority == 0:
                existing.priority = data.get("priority", 0)
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
            # Seed RBAC permissions if none exist
            if not existing.role_permissions:
                for perm_data in ROLE_PERMISSIONS.get(name, []):
                    perm = session.query(Permission).filter(
                        Permission.resource == perm_data["resource"],
                        Permission.action == perm_data["action"],
                    ).first()
                    if not perm:
                        perm = Permission(
                            resource=perm_data["resource"],
                            action=perm_data["action"],
                            description=f"{perm_data['action']} {perm_data['resource']}",
                        )
                        session.add(perm)
                        session.flush()
                    role_perm = RolePermission(role_id=existing.id, permission_id=perm.id)
                    session.add(role_perm)
    session.commit()


def get_default_storage_path() -> str:
    """Get default file storage path"""
    import os
    from pathlib import Path
    hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    return str(Path(hermes_home) / "file_manager" / "storage")


# =============================================================================
# Approval Models (T4: 审批数据模型)
# =============================================================================

class ApprovalType(str, PyEnum):
    """审批类型枚举"""
    JOIN_TEAM = "join_team"
    PRIVATE_SPACE = "private_space"
    QUOTA_EXTEND = "quota_extend"
    STORAGE_POOL = "storage_pool"
    TEAM_CREATE = "team_create"


class RequestStatus(str, PyEnum):
    """申请状态枚举"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class ApprovalRequest(Base):
    """资源申请单"""
    __tablename__ = "hfm_approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    type = Column(String(32), nullable=False)  # ApprovalType
    applicant_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    target_id = Column(String(36), nullable=True)  # 目标资源ID
    status = Column(String(16), default=RequestStatus.PENDING.value)
    reason = Column(Text, nullable=True)
    params = Column(JSON, nullable=True)  # 申请参数
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    approval_comment = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_approval_request_applicant", "applicant_id"),
        Index("ix_approval_request_status", "status"),
        Index("ix_approval_request_type_status", "type", "status"),
    )

    # Relationships
    applicant = relationship("User", foreign_keys=[applicant_id])
    approver = relationship("User", foreign_keys=[approved_by])
    records = relationship("ApprovalRecord", back_populates="request", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "applicant_id": self.applicant_id,
            "target_id": self.target_id,
            "status": self.status,
            "reason": self.reason,
            "params": self.params,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approval_comment": self.approval_comment,
        }


class ApprovalRecord(Base):
    """审批记录"""
    __tablename__ = "hfm_approval_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    request_id = Column(String(36), ForeignKey("hfm_approval_requests.id"), nullable=False)
    approver_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    decision = Column(String(16), nullable=False)  # approve/reject
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_approval_record_request", "request_id"),
        Index("ix_approval_record_approver", "approver_id"),
    )

    # Relationships
    request = relationship("ApprovalRequest", back_populates="records")
    approver = relationship("User", foreign_keys=[approver_id])

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "approver_id": self.approver_id,
            "decision": self.decision,
            "comment": self.comment,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
        }


# =============================================================================
# Commercial Models (T10: 商业化配额预留)
# =============================================================================

class ResourcePlan(Base):
    """资源计划（商业化）- 订阅套餐定义"""
    __tablename__ = "hfm_resource_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    name = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    storage_bytes = Column(BigInteger, nullable=False)  # 存储字节数
    team_count = Column(Integer, nullable=False)  # 团队数量限制
    member_count = Column(Integer, nullable=False)  # 成员数量限制
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        Index("ix_resource_plans_active", "is_active"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "storage_bytes": self.storage_bytes,
            "storage_gb": self.storage_bytes / (1024**3),
            "team_count": self.team_count,
            "member_count": self.member_count,
            "price_monthly": float(self.price_monthly),
            "price_yearly": float(self.price_yearly),
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Subscription(Base):
    """用户订阅 - 记录用户的套餐订阅状态"""
    __tablename__ = "hfm_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("hfm_resource_plans.id"), nullable=False)
    status = Column(String(16), default="active")  # "active", "cancelled", "expired"
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    billing_cycle = Column(String(16), default="monthly")  # "monthly", "yearly"
    auto_renew = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    plan = relationship("ResourcePlan", back_populates="subscriptions")

    __table_args__ = (
        Index("ix_subscriptions_user", "user_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_expires", "expires_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_id": self.plan_id,
            "plan_name": self.plan.name if self.plan else None,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "billing_cycle": self.billing_cycle,
            "auto_renew": self.auto_renew,
        }

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def is_active(self) -> bool:
        return self.status == "active" and not self.is_expired()


# A-3: 新增 QuotaTransfer 模型
class QuotaTransfer(Base):
    """配额调配记录"""
    __tablename__ = "hfm_quota_transfers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    from_space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    to_space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    transfer_bytes = Column(BigInteger, nullable=False)
    reason = Column(Text, nullable=True)
    requested_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    approved_by = Column(String(36), ForeignKey("hfm_users.id"), nullable=True)
    status = Column(String(16), default="pending")  # pending | approved | rejected | expired | cancelled
    rejection_reason = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    from_space = relationship("Space", foreign_keys=[from_space_id])
    to_space = relationship("Space", foreign_keys=[to_space_id])
    requester = relationship("User", foreign_keys=[requested_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("ix_quota_transfers_from_space", "from_space_id"),
        Index("ix_quota_transfers_to_space", "to_space_id"),
        Index("ix_quota_transfers_status", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_space_id": self.from_space_id,
            "from_space_name": self.from_space.name if self.from_space else None,
            "to_space_id": self.to_space_id,
            "to_space_name": self.to_space.name if self.to_space else None,
            "transfer_bytes": self.transfer_bytes,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "requester_name": self.requester.username if self.requester else None,
            "approved_by": self.approved_by,
            "approver_name": self.approver.username if self.approver else None,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at

    def can_approve(self) -> bool:
        return self.status == "pending" and not self.is_expired()
