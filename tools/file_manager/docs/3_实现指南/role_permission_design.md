# 角色权限设计 (Role & Permission Design)

> **版本**: 1.1
> **更新日期**: 2026-05-05
> **项目**: Hermes File Manager
> **状态**: ✅ 已实现
>
> **更新说明 v1.1**: T1/T2/T3 任务已全部完成，RBAC数据模型增强、权限检查引擎、角色权限API均已实现

---

## 一、领域分析

### 1.1 核心领域

| 领域 | 说明 | 关键概念 |
|------|------|---------|
| **资源管理** | 存储资源的分配与回收 | StoragePool, Space, Quota |
| **多租户** | 用户/团队资源隔离 | Tenant, Namespace |
| **RBAC权限** | 基于角色的访问控制 | Role, Permission, Rule |
| **生命周期** | 资源创建→使用→审批→回收 | Workflow, Approval |
| **商业化** | 资源购买与配额分配 | Purchase, Resource Plan |

### 1.2 资源层级结构

```
┌─────────────────────────────────────────────────────────────┐
│                     存储池 (Storage Pool)                     │
│  ├── 管理员可见/管理                                         │
│  └── 团队/空间从此分配配额                                    │
│        ↓                                                     │
│  ┌─────────────────────────────────────────────────────┐     │
│  │               团队 (Team)                            │     │
│  │  ├── 需要存储配额                                     │
│  │  ├── 成员: 普通用户                                   │
│  │  └── 管理者: 团队所有者                               │
│  │        ↓                                               │
│  │  ┌───────────────────────────────────────────────┐    │
│  │  │         空间 (Space)                           │    │
│  │  │  ├── 团队空间 (Team Space)                     │    │
│  │  │  ├── 私人空间 (Private Space - 需申请)         │    │
│  │  │  └── 工作流/笔记本/文件                        │    │
│  │  └───────────────────────────────────────────────┘    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、账号分类设计

### 2.1 三类用户角色

| 角色 | 角色标识 | 用户类型 | 可见范围 | 可申请 |
|------|---------|---------|---------|--------|
| **管理员** | `admin` | 系统管理员 | 全部功能 | 无需申请 |
| **团队管理者** | `team_owner` | 团队负责人 | 本团队资源 | 配额扩展 |
| **普通用户** | `user` | 一般使用者 | 文件/知识/回收站 | 加入团队/私人空间 |

### 2.2 角色定义

#### 管理员 (admin)
```python
ADMIN_ROLE = {
    "name": "admin",
    "description": "系统管理员，拥有所有资源的管理权限",
    "is_system": True,
    "permissions": [
        "storage_pool:create,read,update,delete",
        "team:create,read,update,delete,member_manage",
        "space:create,read,update,delete",
        "user:create,read,update,delete",
        "quota:allocate,adjust,回收",
        "approval:process,view_all",
        "system:config,view_logs"
    ]
}
```

#### 团队管理者 (team_owner)
```python
TEAM_OWNER_ROLE = {
    "name": "team_owner",
    "description": "团队所有者，管理本团队资源",
    "is_system": True,
    "permissions": [
        "team:read,update",
        "team_member:read,invite,remove",
        "team_space:create,read,update",
        "quota:view_own_team",
        "approval:request_extend"
    ]
}
```

#### 普通用户 (user)
```python
USER_ROLE = {
    "name": "user",
    "description": "普通用户，使用分配的资源",
    "is_system": True,
    "permissions": [
        "file:read,write,delete_own",
        "workflow:read,write,execute",
        "notebook:read,write",
        "recycle_bin:read,restore,delete_own",
        "approval:request_join_team",
        "approval:request_private_space",
        "approval:request_quota"
    ]
}
```

---

## 三、权限矩阵

### 3.1 功能权限矩阵

| 功能 | 管理员 | 团队所有者 | 普通用户 |
|------|--------|-----------|---------|
| **存储池管理** | | | |
| 创建存储池 | ✅ | ❌ | ❌ |
| 查看存储池 | ✅ | ❌ | ❌ |
| 分配存储池配额 | ✅ | ❌ | ❌ |
| **团队管理** | | | |
| 创建团队 | ✅ | ❌ | ❌ |
| 查看团队列表 | ✅ | ✅ (本团队) | ❌ |
| 管理团队成员 | ✅ | ✅ (本团队) | ❌ |
| 申请加入团队 | ✅ | ❌ | ✅ |
| **空间管理** | | | |
| 创建团队空间 | ✅ | ✅ (本团队) | ❌ |
| 申请私人空间 | ✅ | ✅ | ✅ |
| 查看空间 | ✅ | ✅ (本团队) | ✅ (已加入) |
| **文件操作** | | | |
| 上传文件 | ✅ | ✅ | ✅ (配额内) |
| 下载文件 | ✅ | ✅ | ✅ (已授权) |
| 删除文件 | ✅ | ✅ | ✅ (本人文件) |
| **知识库** | | | |
| 工作流 | ✅ | ✅ | ✅ (已加入空间) |
| 笔记本 | ✅ | ✅ | ✅ (已加入空间) |
| **资源申请** | | | |
| 申请配额扩展 | ✅ | ✅ | ✅ |
| 审批他人申请 | ✅ | ❌ | ❌ |

### 3.2 资源可见性矩阵

| 资源类型 | 管理员可见 | 团队所有者可见 | 普通用户可见 |
|---------|-----------|--------------|------------|
| 所有存储池 | ✅ | ❌ | ❌ |
| 所有团队 | ✅ | 仅本团队 | 仅加入的团队 |
| 所有空间 | ✅ | 仅本团队空间 | 仅已加入空间 |
| 所有用户 | ✅ | 仅本团队成员 | 仅本人 |
| 审批申请列表 | ✅ (全部) | 仅本团队相关 | 仅本人提交的 |

---

## 四、RBAC实现

### 4.1 数据模型

```python
class Role(Base):
    """角色"""
    __tablename__ = "hfm_roles"

    id = Column(String(36), primary_key=True)
    name = Column(String(32), unique=True, nullable=False)
    description = Column(Text)
    is_system = Column(Boolean, default=False)  # 系统内置角色不可删除
    priority = Column(Integer, default=0)  # 角色优先级，数字越大权限越高
    created_at = Column(DateTime, default=datetime.utcnow)

class Permission(Base):
    """权限定义"""
    __tablename__ = "hfm_permissions"

    id = Column(String(36), primary_key=True)
    resource = Column(String(32), nullable=False)  # 资源类型: file, space, team, storage_pool
    action = Column(String(32), nullable=False)   # 操作类型: create, read, update, delete
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class RolePermission(Base):
    """角色-权限关联"""
    __tablename__ = "hfm_role_permissions"

    role_id = Column(String(36), ForeignKey("hfm_roles.id"), primary_key=True)
    permission_id = Column(String(36), ForeignKey("hfm_permissions.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserRole(Base):
    """用户-角色关联（支持多角色）"""
    __tablename__ = "hfm_user_roles"

    user_id = Column(String(36), ForeignKey("hfm_users.id"), primary_key=True)
    role_id = Column(String(36), ForeignKey("hfm_roles.id"), primary_key=True)
    scope = Column(String(32), nullable=True)  # 范围限制，如团队ID
    granted_by = Column(String(36), ForeignKey("hfm_users.id"))
    granted_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 权限检查流程

```python
def check_permission(user_id: str, resource: str, action: str, scope: str = None) -> bool:
    """
    权限检查流程:
    1. 获取用户所有角色
    2. 检查角色是否有对应权限
    3. 如有scope限制，检查操作范围
    """
    user_roles = session.query(UserRole).filter(UserRole.user_id == user_id).all()

    for user_role in user_roles:
        role = session.query(Role).filter(Role.id == user_role.role_id).first()
        permissions = get_role_permissions(role.id)

        for perm in permissions:
            if perm.resource == resource and perm.action == action:
                # 检查scope范围
                if user_role.scope and scope:
                    if user_role.scope != scope:
                        continue
                return True

    return False
```

---

## 五、实施步骤

### 5.1 阶段一：角色模型更新

1. 添加 `priority` 字段到 Role 模型
2. 添加 `is_system` 字段区分系统角色
3. 创建 `RolePermission` 关联表

### 5.2 阶段二：权限迁移

1. 将现有 `BUILTIN_ROLES` 转换为新模型
2. 迁移用户角色关系
3. 更新权限检查逻辑

### 5.3 阶段三：功能适配

1. 前端：隐藏无权限的操作入口
2. 后端：强化权限校验
3. API：返回权限不足提示

---

## 六、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 1.0 | 2026-05-03 | 初始版本：角色权限设计方案 |