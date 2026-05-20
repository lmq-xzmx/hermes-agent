# 领域分析表 (Domain Analysis)

> **版本**: 2.0
> **更新日期**: 2026-05-06
> **项目**: Hermes File Manager
> **状态**: 维护中
> **模式**: Web优先 + Tauri壳模式 (Vue 3 SPA)
> **术语标准**: GOALS.md v3.0
> **更新说明 v2.0**: 修正领域3多租户模型，Space替代Team作为核心实体，SpaceType区分访问模式

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v2.0 | 2026-05-06 | 修正领域3多租户模型，Space替代Team作为核心实体，SpaceType区分访问模式 |
| v1.0 | 2026-05-02 | 初始版本，16个核心领域定义 |

---

## 一、项目领域总览

Hermes File Manager (HFM) 是一个**企业级云存储协作平台**，涉及以下核心领域：

| 序号 | 领域分类 | 说明 | 核心实体 |
|------|---------|------|---------|
| 1 | 身份认证 | 用户注册、登录、会话管理 | User, UserSession, Role |
| 2 | 资源管理 | 存储资源（池、空间、配额）的分配与回收 | StoragePool, Space, Quota |
| 3 | 多租户 | 用户/团队资源隔离与计费 | Tenant, Team, SpaceMember |
| 4 | RBAC权限 | 基于角色的访问控制 | Role, Permission, PermissionRule |
| 5 | 生命周期 | 资源创建→使用→审批→回收 | Workflow, Approval, SpaceRequest |
| 6 | 文件操作 | 文件上传、下载、删除、版本控制 | FileVersion, DeletedFile, FileLock |
| 7 | 共享协作 | 文件分享、协作编辑、链接管理 | SharedLink, CollaborationSession |
| 8 | 通知审计 | 系统通知、操作审计 | Notification, AuditLog |
| 9 | 知识管理 | 工作流、笔记本、变量 | Workflow, Notebook, NotebookVariable |
| 10 | 计费商业 | 未来资源购买与配额分配 | ResourcePlan, Subscription |
| 11 | 用户引导 | 基于事件的引导系统、TourGuide | GuidanceEvent, TourGuide, GuidanceEngine |
| 12 | 需求管理 | 需求跟踪、需求依赖、版本追踪 | RTM, RDM, Requirement |
| 13 | 软件测试 | 测试生命周期、测试用例管理 | TestCase, TestSuite, TestResult |
| 14 | 跨平台混合应用 | Web/Tauri 共用一套 UI 源码，原生壳提供系统能力 | WebView, TauriBridge, PlatformAdapter |
| **15** | **Vue 3 前端架构** | **Vue 3 SPA 前端最佳实践，Composition API** | **Vue组件, Pinia Store, Router** |
| **16** | **代码质量管理** | **DRY原则、代码去重、冗余控制、模块边界** | **CodeReview, 重构, 边界定义** |

---

## 二、核心领域详解

### 领域 1: 身份认证 (Authentication & Identity)

| 属性 | 内容 |
|------|------|
| **领域代码** | AUTH |
| **描述** | 用户身份注册、登录验证、会话管理、JWT Token 发放 |
| **核心实体** | User, UserSession, Role |
| **服务** | auth_service.py |
| **关键操作** | register, login, logout, refresh_token, change_password |

**实体关系**:
```
User (1) ──→ (N) Role
User (1) ──→ (N) UserSession
```

---

### 领域 2: 资源管理 (Resource Management)

| 属性 | 内容 |
|------|------|
| **领域代码** | RESOURCE |
| **描述** | 存储资源（池、空间、配额）的分配、监控、回收 |
| **核心实体** | StoragePool, Space, SpaceMember |
| **服务** | space_service.py |
| **关键操作** | create_pool, allocate_quota, check_quota, reclaim_resource |

**资源层级**:
```
StoragePool (L1)
    └── Space (L2: root/team/private)
            └── SpaceMember (L3)
```

**说明**: Space 是核心资源实体，配额隔离单位。Space.space_type 区分访问模式。

---

### 2.1 存储池领域 (Storage Pool)

| 属性 | 内容 |
|------|------|
| **领域代码** | SPOOL |
| **描述** | 存储池的创建、配置、删除及生命周期约束 |
| **核心实体** | StoragePool |
| **前端组件** | StoragePoolView.vue |
| **状态管理** | usePoolStore.js |
| **关键操作** | create_pool, update_pool, delete_pool, run_cleanup |
| **约束规则** | STORAGE_POOL_IN_USE, POOL_TEAMS_MIGRATING |

**存储池类型**:
| 类型 | 说明 | 用途 |
|------|------|------|
| `standard` | 标准存储池 | 通用文件存储 |
| `high-performance` | 高性能存储池 | 大文件/高频访问 |
| `archival` | 归档存储池 | 冷数据长期存储 |

**存储池状态机**:
```
创建中 (creating) → 活跃 (active) → 停用 (inactive)
                          ↑
                   清理中 (cleaning)
```

**生命周期约束**:
| 约束 | 代码 | 检查条件 | 错误信息 |
|------|------|---------|---------|
| 池中有团队 | STORAGE_POOL_IN_USE | team_count == 0 | 该存储池仍有团队使用，无法删除 |
| 团队迁移中 | POOL_TEAMS_MIGRATING | team_migrating_count == 0 | 该存储池有团队正在迁移中 |

**账号类型权限表**:

| 账号类型 | 查看列表 | 查看详情 | 创建存储池 | 编辑存储池 | 删除存储池 | 清理存储池 |
|---------|---------|---------|----------|----------|----------|----------|
| **admin** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **member** (editor) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **viewer** | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **guest** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**前端集成状态**:

| 组件 | 功能 | 说明 |
|------|------|------|
| `StoragePoolView.vue` | ✅ 已实现 | 完整 CRUD + 详情面板 + 清理，权限控制 |
| `usePoolStore.js` | ✅ 已实现 | 状态管理 + API 调用 |

---

### 领域 3: 多租户 (Multi-Tenancy)

| 属性 | 内容 |
|------|------|
| **领域代码** | TENANT |
| **描述** | 用户/团队资源隔离，数据独立，配额分离 |
| **核心实体** | Space, SpaceMember, SpaceCredential, TeamCredential |
| **服务** | space_service.py |
| **关键操作** | create_space, join_space, invite_member, leave_space |

**TeamStatus 枚举定义**:

| 状态值 | 说明 | 触发条件 |
|--------|------|----------|
| `active` | 团队活跃，正常使用 | 团队创建并审核通过 |
| `inactive` | 团队已停用，禁止操作 | 管理员禁用或长期欠费 |
| `pending` | 待审核 | 团队创建申请等待审批 |
| `archived` | 已归档 | 团队解散后保留数据用于审计 |

**TeamCredential 实体 (邀请码)**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 邀请码唯一标识 |
| `team_id` | UUID | 所属团队 |
| `code` | string(8) | 邀请码（8位字母数字） |
| `created_by` | UUID | 创建者用户ID |
| `created_at` | datetime | 创建时间 |
| `expires_at` | datetime | 过期时间（null=永不过期） |
| `max_uses` | integer | 最大使用次数（null=无限） |
| `used_count` | integer | 已使用次数 |
| `status` | enum | active/expired/used_up/invalid |

**TeamCredential 状态机**:

```
┌─────────────┐   创建    ┌──────────────┐   过期    ┌──────────────┐
│    none     │ ─────────→│    active    │ ─────────→│   expired    │
└─────────────┘           └──────────────┘           └──────────────┘
                               │
                               │ used_count >= max_uses
                               ▼
                        ┌──────────────┐   管理员禁用  ┌──────────────┐
                        │   used_up    │ ←─────────────│   invalid    │
                        └──────────────┘               └──────────────┘
```

**租户隔离模型**:
```
StoragePool (存储池 - L1)
    └── Space (空间 - L2)
            ├── space_type="root" - 根空间 (管理员创建，绑定存储池)
            ├── space_type="team" - 团队空间 (成员共享文件，配额隔离)
            └── space_type="private" - 私人空间 (成员申请审批后创建)
                    └── SpaceMember (成员关系)
                            └── User
```

**重要说明**: Space 是核心实体，替代了传统 Team 概念。Space.space_type 区分访问模式：
- `team` = 多人协作空间（对应传统 Team）
- `private` = 个人专属空间（需审批创建）
- `root` = 存储池顶层空间（管理员使用）

---

### 领域 4: RBAC权限控制 (Role-Based Access Control)

| 属性 | 内容 |
|------|------|
| **领域代码** | RBAC |
| **描述** | 基于角色的访问控制，权限规则引擎 |
| **核心实体** | Role, Permission, PermissionRule |
| **服务** | permission_checker.py, permission_context.py |
| **关键操作** | check_permission, assign_role, grant_permission |

**权限模型**:
```
Role ──→ (N) PermissionRule ──→ Permission
User ──→ (N) Role
```

**系统级角色 (System Role)**:

| 角色名 | account_type | priority | 说明 |
|--------|-------------|----------|------|
| `admin` | "admin" | 100 | 完全访问所有资源，可管理其他用户和角色 |
| `editor` | "member" | 50 | 读写分配路径，不能删除或管理 |
| `viewer` | "member" | 10 | 只读访问分配路径 |
| `guest` | "guest" | 1 | 最小权限，仅读取共享资源 |

**Space 成员角色 (SpaceMember Role)**:

| 角色名 | 说明 | 文件操作权限 |
|--------|------|------------|
| `owner` | 空间所有者，拥有全部管理权限 | 上传/创建/删除/重命名/分享 |
| `member` | 普通成员 | 上传/创建/删除/重命名/分享 |
| `viewer` | 查看者（只读） | 读取/下载 |

**文件操作权限矩阵**:

| 操作 | admin | owner | member | viewer | guest |
|------|-------|-------|--------|--------|-------|
| 浏览文件 (list) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 下载文件 (download) | ✅ | ✅ | ✅ | ✅ | ❌ |
| 上传文件 (upload) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 创建文件夹 (mkdir) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 重命名 (rename) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 移动文件 (move) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 删除文件 (delete) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 分享文件 (share) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 恢复文件 (restore) | ✅ | ✅ | ✅ | ❌ | ❌ |
| 永久删除 (permanent) | ✅ | ❌ | ❌ | ❌ | ❌ |
| 清空回收站 (empty) | ✅ | ❌ | ❌ | ❌ | ❌ |

**前端权限判断实现**:

```javascript
// FileView.vue - 权限计算属性
const canWrite = computed(() => {
  if (isAdmin) return true
  const role = currentSpace?.my_role
  return role === 'owner' || role === 'member'
})

const canDelete = computed(() => {
  if (isAdmin) return true
  const role = currentSpace?.my_role
  return role === 'owner' || role === 'member'
})
```

**前端 RBAC 路由守卫**:

| 路由 | meta 属性 | 访问条件 |
|------|---------|---------|
| `/admin` | `requiresAuth: true, requiredPriority: 100` | admin 角色 |
| `/pools` | `requiresAuth: true, requiredPriority: 100` | admin 角色 |
| `/knowledge` | 无特殊要求 | 所有登录用户 |
| `/files` | 无特殊要求 | 所有登录用户 |

**路由守卫实现** (`router/index.js`):

```javascript
const ROLE_PRIORITY = {
  'admin': 100,
  'editor': 50,
  'viewer': 10,
  'guest': 1,
  'member': 50
}

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 认证检查
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    next({ name: 'Login' })
    return
  }

  // 权限等级检查
  if (to.meta.requiredPriority) {
    const userPriority = ROLE_PRIORITY[authStore.userRole] || 0
    if (userPriority < to.meta.requiredPriority) {
      next({ name: 'Files' }) // 权限不足跳转首页
      return
    }
  }

  next()
})
```

**前端权限工具** (`utils/permissions.js`):

| 函数 | 说明 |
|------|------|
| `hasPermission(userRole, requiredRole)` | 基于优先级检查权限 |
| `isAdmin(userRole)` | 是否管理员 |
| `isEditor(userRole)` | 是否编辑者+ |
| `canAccessKnowledgeFeature(feature, userRole)` | 知识库功能检查 |
| `canAccessPoolFeature(feature, userRole)` | 存储池功能检查 |

**注意事项**:
- `guest` 角色不可访问文件操作（无 `file:read` 以外权限）
- `viewer` 只能浏览和下载，无法执行写操作
- `owner` 和 `member` 权限相同，区别仅在于管理操作（删除空间、邀请成员等）
- 永久删除和清空回收站仅 `admin` 可执行

**权限层级继承 (Role Hierarchy)**:

| 上级角色 | 可继承的下级角色 |
|---------|-----------------|
| `admin` | editor, viewer, guest |
| `editor` | viewer, guest |
| `viewer` | guest |

**前端权限字段统一**:

| 位置 | 字段 | 说明 |
|------|------|------|
| `authStore.js` | `user.role` | 主字段，系统级角色 |
| `authStore.js` | `userRole` | 计算属性，返回 `user.role \|\| 'member'` |

**注意事项**:
- 统一使用 `user.role` 字段判断权限
- 不应混用 `role_name`、`hfm_role` 等不同字段
- 前端判断 admin 权限：`authStore.userRole === 'admin'`

---

### 领域 5: 生命周期管理 (Lifecycle Management)

| 属性 | 内容 |
|------|------|
| **领域代码** | LIFECYCLE |
| **描述** | 资源创建→使用→审批→回收的全生命周期 |
| **核心实体** | SpaceRequest, Workflow, WorkflowStep |
| **服务** | lifecycle_engine.py, workflow_service.py |
| **关键操作** | request_space, approve_request, reject_request |

**生命周期阶段**:
```
创建 (CREATE) → 审批 (PENDING) → 使用 (ACTIVE) → 回收 (ARCHIVED/DELETED)
```

#### 5.1 生命周期约束规则 (Lifecycle Constraints)

**操作约束表**:

| 操作 | 前置条件 | 约束代码 | 违反提示 | 引导操作 |
|------|---------|---------|---------|---------|
| `upload_file` | 是空间成员且配额充足 | `NOT_SPACE_MEMBER`, `QUOTA_EXCEEDED` | "您不是空间成员" / "配额不足" | ["申请加入空间"] |
| `create_team` | 有可用存储池 | `NO_AVAILABLE_POOL` | "没有可用存储池" | ["联系管理员"] |
| `create_private_space` | 是团队成员 | `NOT_TEAM_MEMBER` | "您不是团队成员" | ["加入团队"] |
| `delete_pool` | 存储池未被使用 | `STORAGE_POOL_IN_USE` | "存储池正在使用中" | ["迁移数据后重试"] |
| `delete_space` | 空间无成员 | `SPACE_HAS_MEMBERS` | "空间仍有成员" | ["移除所有成员"] |
| `invite_member` | 是空间所有者 | `NOT_SPACE_OWNER` | "只有空间所有者可以邀请" | ["联系空间所有者"] |
| `join_team` | 邀请码有效且未过期 | `INVALID_INVITATION_CODE`, `EXPIRED_INVITATION_CODE`, `USED_UP_INVITATION_CODE` | "邀请码无效/已过期/次数已用完" | ["获取新邀请码"] |
| `delete_team` | 是团队所有者 | `NOT_TEAM_OWNER` | "只有团队所有者可以删除" | ["联系团队所有者"] |
| `update_quota` | 是空间所有者 | `NOT_SPACE_OWNER` | "只有空间所有者可以更新配额" | ["联系管理员"] |
| `transfer_quota` | 是目标空间所有者 | `NOT_SPACE_OWNER` | "只有空间所有者可以转移配额" | ["联系管理员"] |
| `restore_file` | 文件在回收站中 | `FILE_NOT_IN_TRASH` | "文件不在回收站中，无法恢复" | ["查看文件"] |
| `batch_delete` | 有批量操作权限 | `NO_BATCH_PERMISSION` | "您没有批量删除权限" | ["联系管理员"] |

**join_team 操作详细约束**:

| 约束类型 | 代码 | 触发条件 | 错误信息 |
|----------|------|----------|----------|
| 邀请码无效 | `INVALID_INVITATION_CODE` | 邀请码不存在或已被撤销 | "邀请码无效" |
| 邀请码过期 | `EXPIRED_INVITATION_CODE` | `expires_at < now()` | "邀请码已过期" |
| 次数用完 | `USED_UP_INVITATION_CODE` | `used_count >= max_uses` | "邀请码使用次数已用完" |
| 团队已归档 | `TEAM_ARCHIVED` | `Team.status === archived` | "团队已解散，无法加入" |
| 用户已是成员 | `ALREADY_MEMBER` | 用户已在团队中 | "您已是团队成员" |

**前端 LIFECYCLE 预检**:

| 场景 | 预检位置 | 检查内容 |
|------|---------|---------|
| 上传文件 | `FileView.vue` | 检查配额是否充足（`quota.used < quota.total`） |
| 加入团队 | `TeamView.vue` | 调用 `/teams/{teamId}/validate-invite` 验证邀请码 |
| 创建空间 | `SpaceView.vue` | 检查是否有可用存储池 |

---

### 领域 6: 文件操作 (File Operations)

| 属性 | 内容 |
|------|------|
| **领域代码** | FILE |
| **描述** | 文件上传、下载、删除、读写、版本控制、回收站管理 |
| **核心实体** | FileVersion, DeletedFile, FileLock, FileUpload, TrashItem |
| **服务** | file_service.py, file_lock_service.py, trash_service.py |
| **关键操作** | upload, download, delete, read, write, lock, unlock |

**文件状态流转**:
```
上传中 (uploading) → 已完成 (completed) → 已删除 (deleted) → 回收站 (recycled)
```

#### 回收站生命周期 (Trash Lifecycle)

回收站管理文件删除后的临时存储，支持恢复或永久删除。

**核心实体: TrashItem**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 回收站记录唯一标识 |
| `space_id` | UUID | 所属空间 |
| `original_path` | string | 原始文件路径 |
| `name` | string | 文件/文件夹名称 |
| `is_directory` | boolean | 是否为文件夹 |
| `deleted_at` | datetime | 删除时间 |
| `deleted_by` | UUID | 删除操作者 |
| `file_size` | integer | 文件大小（字节） |
| `restored_at` | datetime | 恢复时间（恢复后记录） |
| `permanent_deleted_at` | datetime | 永久删除时间 |

**回收站操作权限矩阵**:

| 操作 | admin | owner | member | viewer | 说明 |
|------|-------|-------|--------|--------|------|
| `list_trash` | ✓ | ✓ | ✓ | ✓ | 所有空间成员可查看回收站列表 |
| `restore` | ✓ | ✓ | 只能恢复自己的文件 | ✗ | 成员只能恢复自己删除的文件 |
| `permanent_delete` | ✓ | ✓ | ✗ | ✗ | 只有所有者和admin可永久删除 |
| `empty_trash` | ✓ | ✓ | ✗ | ✗ | 只有所有者和admin可清空回收站 |
| `auto_purge` | ✓ | - | - | - | 仅admin可触发自动清理 |

**回收站操作约束**:

| 操作 | 前置条件 | 约束代码 | 违反提示 |
|------|---------|---------|---------|
| `list_trash` | 是空间成员 | `NOT_SPACE_MEMBER` | "您不是该空间的成员" |
| `restore` | 文件未过期 | `TRASH_EXPIRED` | "文件已过期，无法恢复" |
| `restore` | 成员只能恢复自己的文件 | `NOT_OWNER_OF_FILE` | "您只能恢复自己删除的文件" |
| `permanent_delete` | 是所有者或admin | `NOT_SPACE_OWNER` | "只有空间所有者可以永久删除" |
| `empty_trash` | 是所有者或admin | `NOT_SPACE_OWNER` | "只有空间所有者可以清空回收站" |

**TrashItem 状态机**:

```
┌─────────────┐     delete      ┌──────────────┐    restore    ┌──────────────┐
│  completed  │ ────────────────→│    deleted    │ ────────────→ │   restored   │
│  (正常文件)  │                  │   (回收站中)   │               │  (已恢复)     │
└─────────────┘                  └──────────────┘               └──────────────┘
                                       │
                                       │ permanent_delete / auto_cleanup
                                       ▼
                               ┌──────────────┐
                               │   recycled    │
                               │  (已销毁)      │
                               └──────────────┘
```

| 状态 | 说明 | 触发条件 |
|------|------|---------|
| `deleted` | 回收站中，等待恢复或销毁 | 用户删除文件 |
| `restored` | 已恢复到原始位置 | 用户点击恢复 |
| `recycled` | 已永久删除，无法恢复 | 用户永久删除或自动清理 |

**回收站 API 端点**:

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/spaces/{spaceId}/trash` | 获取回收站列表 |
| `POST` | `/spaces/{spaceId}/trash/{itemId}/restore` | 恢复文件 |
| `DELETE` | `/spaces/{spaceId}/trash/{itemId}` | 永久删除 |
| `DELETE` | `/spaces/{spaceId}/trash` | 清空回收站 |

**前端集成状态**:

| 组件 | 回收站支持 | 说明 |
|------|----------|------|
| `FileView.vue` | ❌ 未集成 | 仅实现 delete 操作 |
| `TrashView.vue` | ✅ 已实现 | 完整回收站管理界面 |

**自动清理规则**:

| 规则 | 条件 | 处理 |
|------|------|------|
| 保留期限 | 删除后 30 天 | 自动永久删除 |
| 空间配额 | 回收站占用 > 50% 空间配额 | 自动清理最旧文件 |
| 存储池枯竭 | 存储池可用空间 < 10% | 管理员触发清理 |

---

### 领域 7: 共享协作 (Sharing & Collaboration)

| 属性 | 内容 |
|------|------|
| **领域代码** | COLLAB |
| **描述** | 文件分享、协作编辑、链接管理 |
| **核心实体** | SharedLink, CollaborationSession |
| **服务** | share_service.py, collaboration_service.py |
| **关键操作** | create_share_link, invite_collaborator, start_collaboration |

---

### 领域 8: 通知审计 (Notification & Audit)

| 属性 | 内容 |
|------|------|
| **领域代码** | AUDIT |
| **描述** | 系统通知、操作审计日志 |
| **核心实体** | Notification, AuditLog |
| **服务** | notification_service.py, audit_subscriber.py |
| **关键操作** | send_notification, log_action, query_audit_log |

---

### 领域 9: 知识管理 (Knowledge Management)

| 属性 | 内容 |
|------|------|
| **领域代码** | KNOWLEDGE |
| **描述** | 工作流、笔记本、变量的创建与管理，知识库同步 |
| **核心实体** | Workflow, Notebook, NotebookVariable, KnowledgeSync |
| **服务** | knowledge_service.py |
| **关键操作** | sync_to_knowledge, search_knowledge, check_status |

**账号类型与功能可见性**:

| 账号类型 | 检查状态 | 同步设置 | 同步文件 | 搜索知识库 |
|----------|---------|---------|---------|-----------|
| admin | ✅ | ✅ | ✅ | ✅ |
| editor | ✅ | ✅ | ✅ | ✅ |
| viewer | ✅ | ❌ | ❌ | ✅ |
| guest | ✅ | ❌ | ❌ | ✅ |

**生命周期约束**:

| 操作 | 前置条件 | 约束代码 | 错误信息 |
|------|---------|---------|---------|
| sync_to_knowledge | editor+ 角色且配额充足 | `NO_LLM_WIKI_SERVICE`, `QUOTA_EXCEEDED` | "llm_wiki 服务未启动" / "配额不足" |
| search_knowledge | 已登录用户 | `NOT_AUTHENTICATED` | "请先登录" |

**前端组件**: `KnowledgeView.vue`

**最佳实践对应**:
- ARCH-003: 生命周期约束前置检查
- RBAC-001: 权限分层控制

| 属性 | 内容 |
|------|------|
| **领域代码** | KNOWLEDGE |
| **描述** | 工作流、笔记本、变量管理、知识库同步 |
| **核心实体** | Workflow, WorkflowStep, Notebook, NotebookVariable, KnowledgeBase, SyncJob, SearchResult |
| **服务** | workflow_service.py, notebook_service.py, knowledge_service.py |
| **关键操作** | create_workflow, execute_step, save_notebook, sync_to_knowledge, search_knowledge |

**核心实体详情**:

**KnowledgeBase (知识库)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 知识库唯一标识 |
| `name` | string | 知识库名称 |
| `project` | string | 所属项目 |
| `description` | string | 描述 |
| `synced_at` | datetime | 最后同步时间 |
| `created_by` | UUID | 创建者 |

**SyncJob (同步任务)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 同步任务唯一标识 |
| `source_path` | string | 源文件路径 |
| `target_project` | string | 目标项目 |
| `status` | enum | pending/running/completed/failed |
| `mode` | enum | manual/interval/webhook |
| `created_at` | datetime | 创建时间 |
| `completed_at` | datetime | 完成时间 |

**SearchResult (搜索结果)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 结果唯一标识 |
| `title` | string | 文档标题 |
| `snippet` | string | 匹配片段 |
| `score` | float | 相关度分数 |
| `path` | string | 文档路径 |

**知识库 API 端点**:

| 方法 | 端点 | 说明 |
|------|------|------|
| `GET` | `/knowledge/status` | 获取 llm_wiki 服务状态 |
| `POST` | `/knowledge/sync` | 同步文档到知识库 |
| `GET` | `/knowledge/search` | 搜索知识库 |
| `GET` | `/knowledge/projects` | 获取项目列表 |

**前端集成**:

| 组件 | 状态 | 说明 |
|------|------|------|
| `KnowledgeView.vue` | ✅ 已实现 | 知识库管理界面 |
| `sync_source_path` | ✅ | 同步源路径输入 |
| `sync_project` | ✅ | 目标项目选择 |
| `searchQuery` | ✅ | 搜索关键词 |

---

### 领域 10: 计费商业 (Billing & Commerce) [规划中]

| 属性 | 内容 |
|------|------|
| **领域代码** | BILLING |
| **描述** | 资源购买、配额分配、订阅管理 |
| **核心实体** | ResourcePlan, Subscription |
| **服务** | (待实现) |
| **关键操作** | subscribe_plan, extend_quota, billing_cycle |

---

### 领域 11: 用户引导 (User Guidance)

| 属性 | 内容 |
|------|------|
| **领域代码** | GUIDANCE |
| **描述** | 基于事件的引导系统、TourGuide、CoachMark |
| **核心实体** | GuidanceEvent, TourGuide, GuidanceEngine |
| **服务** | guidance_engine.py |
| **关键操作** | trigger_guide, dismiss_guide, track_progress |

**引导场景**:
```
用户操作 → 事件触发 → 检查是否已引导 → 显示引导 → 记录已完成
```

---

### 领域 12: 需求管理 (Requirements Management)

| 属性 | 内容 |
|------|------|
| **领域代码** | REQMGT |
| **描述** | 需求跟踪、需求依赖、版本追踪 |
| **核心实体** | RTM (需求跟踪矩阵), RDM (需求依赖矩阵), Requirement |
| **服务** | 无独立服务（文档化管理） |
| **关键操作** | track_requirement, analyze_dependency, resolve_conflict |

**工具说明**:
| 工具 | 全称 | 用途 |
|------|------|------|
| RTM | Requirements Traceability Matrix | 追踪需求→实现→验证 |
| RDM | Requirements Dependency Matrix | 识别需求间矛盾/依赖/重叠 |

---

### 领域 13: 软件测试 (Software Testing)

| 属性 | 内容 |
|------|------|
| **领域代码** | TEST |
| **描述** | 测试生命周期、测试用例管理、测试金字塔 |
| **核心实体** | TestCase, TestSuite, TestResult |
| **服务** | tests/ 目录 |
| **关键操作** | unit_test, integration_test, e2e_test |

**测试层级**:
```
E2E (端到端测试) ← 少量，验证关键路径
Integration (集成测试) ← 中量，验证模块协作
Unit (单元测试) ← 大量，快速反馈
```

### 14.1 Vue 3 SPA 技术栈规范 (HYBRID-VUE3)

> **子领域**: HYBRID
> **版本**: v1.0
> **更新日期**: 2026-05-05
> **适用场景**: "Web优先 + Tauri壳"模式下的 Vue 3 前端开发

#### 14.1.1 核心原则

| 原则 | 说明 | 约束 |
|------|------|------|
| **SSOT** | web/dist 是唯一构建产物 | Vue SPA 和 Tauri 共用同一份构建产物 |
| **平台适配下沉** | 平台差异在 PlatformAdapter 层处理 | 业务组件不应感知运行环境 |
| **构建时注入** | API_BASE、WS_BASE、TAURI_MODE 通过 Vite define 注入 | 避免运行时检测 |
| **单一入口** | vue.html 为主入口，floating-vue.html 为浮窗入口 | 不应混用或动态切换 |

#### 14.1.2 目录结构规范

```
web/
├── src/
│   ├── views/          # 页面组件 (Vue SFC)
│   ├── components/    # 可复用组件
│   ├── stores/        # Pinia 状态管理
│   ├── services/      # API 服务层
│   ├── router/        # Vue Router 配置
│   └── platformAdapter.js  # 平台适配器（内联到 HTML）
├── dist/              # Vite 构建产物 ← 唯一构建输出
├── vue.html           # 主窗口入口
└── floating-vue.html  # 浮窗入口
```

#### 14.1.3 HTML 入口规范

每个 HTML 入口**必须内联 Platform Adapter**，禁止外部引用：

```html
<!-- ✅ 正确：内联 Platform Adapter -->
<script>
(function(global) {
  var API_BASE = typeof __API_BASE__ !== 'undefined' ? __API_BASE__ : '/api/v1';
  var TAURI_MODE = typeof __TAURI_MODE__ !== 'undefined' ? __TAURI_MODE__ : 'web';
  // ... platform adapter code
})(window);
</script>

<!-- ❌ 错误：外部引用 -->
<script type="module" src="/src/platformAdapter.js"></script>
```

#### 14.1.4 Vite 构建配置要求

```javascript
// vite.config.js 必须包含
define: {
  __API_BASE__: JSON.stringify(process.env.NODE_ENV === 'production'
    ? 'http://localhost:8080/api/v1'
    : '/api/v1'),
  __TAURI_MODE__: JSON.stringify(process.env.NODE_ENV === 'production' ? 'tauri' : 'web'),
  __WS_BASE__: JSON.stringify('ws://localhost:8080'),
},
build: {
  outDir: 'dist',
  rollupOptions: {
    input: {
      vue: resolve(__dirname, 'vue.html'),
      floating: resolve(__dirname, 'floating-vue.html'),
    },
  },
},
```

#### 14.1.5 组件规范

| 规范 | 说明 |
|------|------|
| **SFC 格式** | 使用 `.vue` 单文件组件 |
| **Props 类型声明** | 必须使用 `defineProps` 和 TypeScript 类型 |
| **Emit 类型声明** | 必须使用 `defineEmits` |
| **Scoped CSS** | 样式必须使用 `scoped`，避免污染 |
| **Composables** | 逻辑复用使用 `composables` 而非 Mixins |

#### 14.1.6 状态管理规范

| 规范 | 说明 |
|------|------|
| **Pinia Store** | 全局状态使用 Pinia |
| **Store 分割** | 按领域分割 Store（如 spaceStore, userStore） |
| **SSR 安全** | Store 不应直接依赖 window/document |

#### 14.1.7 路由规范

| 规范 | 说明 |
|------|------|
| **Hash 模式** | 桌面应用使用 hash 模式，避免服务端配置 |
| **懒加载** | 页面组件使用 `() => import()` 懒加载 |
| **路由守卫** | 权限验证在 beforeEach 中处理 |

#### 14.1.8 WebSocket 规范

| 规范 | 说明 |
|------|------|
| **心跳机制** | 每 30 秒发送 ping 保持连接 |
| **自动重连** | 连接断开后自动重连，带指数退避 |
| **消息解析** | JSON 解析失败时记录 warn 而非抛出 |

```javascript
socket.onmessage = function(event) {
  try {
    var data = JSON.parse(event.data);
    if (onMessage) onMessage(data);
  } catch (e) {
    console.warn('[Platform WS] Failed to parse message:', e);
  }
};
```


---

### 14.2 桌面应用版本管理最佳实践 (HYBRID-DEPLOY)

> **领域**: HYBRID (跨平台混合应用) - 领域 14 的子领域
> **适用场景**: Tauri/Electron 等混合桌面应用的多版本管理、发布与部署

#### 14.2.1 核心问题

混合桌面应用面临的版本混乱问题：

| 现象 | 原因 |
|------|------|
| 有托盘 vs 无托盘 | 旧版本编译时未包含托盘代码，新版本才有 |
| 布局错乱 | CSS 修复在源码但 /Applications 安装的是旧版 |
| 功能不一致 | 开发构建 vs 发布构建差异 |
| 多个实例同时运行 | 未统一管理启动入口 |

#### 14.2.2 版本管理原则

**原则 1: 单一真相源 (Single Source of Truth)**
```
源码 (source) → 唯一构建产物 → 唯一安装位置
```
- 每次发布前必须 clean build，确保没有旧资源残留
- 安装位置只用一个：/Applications (macOS)

**原则 2: 进程统一管理**
```bash
# 启动前必须停止所有旧实例
pkill -f <app_name> || true  # 静默处理无进程情况
```
- 避免多个实例同时运行导致状态不一致
- 开发环境和生产环境使用不同的配置文件

**原则 3: 版本一致性检查**
```bash
# 构建后验证
ls -la /Applications/<App>.app/Contents/MacOS/<binary>
stat /path/to/binary  # 检查时间戳是否最新
```

**原则 4: 分阶段验证**
```
1. 停止所有旧进程
2. 执行 clean build (cargo clean && cargo build --release)
3. 打包 (cargo tauri bundle)
4. 验证 bundle 内容
5. 备份旧版本（以防回滚）
6. 替换 /Applications 中的版本
7. 启动并验证功能（托盘、UI、API 连接）
```

#### 14.2.3 构建验证清单

```bash
# 检查清单
[ ] cargo clean  # 确保干净构建
[ ] cargo build --release  # 发布版本
[ ] cargo tauri bundle  # 创建可分发 bundle
[ ] 验证 _up_/web/ 目录包含最新资源
[ ] 验证托盘代码已编译（二进制中有 tray 相关符号）
[ ] 替换 /Applications 中的旧版本
[ ] 启动应用并检查：
    [ ] 托盘图标显示
    [ ] UI 布局正确
    [ ] API 正确连接
    [ ] 无 "Not Found" 错误
```

#### 14.2.4 相关标准与规范

| 标准 | 说明 |
|------|------|
| Semantic Versioning (SemVer) | 语义化版本控制 |
| Code Signing | macOS 应用签名与公证 |
| Clean Build | 干净构建原则 |
| Single Source of Truth | 单一真相源原则 |

#### 14.2.5 常见问题与解决

| 问题 | 根因 | 解决 |
|------|------|------|
| 托盘不显示 | 旧版本二进制未包含托盘代码 | 重新构建并替换 |
| {"detail":"Not Found"} | 后端 API 未启动或路径错误 | 检查 PYTHON_API_URL 配置 |
| 多个实例运行 | 未执行进程统一管理 | 启动前执行 pkill |
| CSS 未生效 | 旧版本 bundle 中的资源未更新 | clean build 并重新打包 |

---

### 14.3 Vue 3 SPA "Web优先 + Tauri壳" 最佳实践 (HYBRID-VUE3)

> **领域**: HYBRID (跨平台混合应用) - Vue 3 SPA 特化子领域
> **适用场景**: 使用 Vue 3 + Tauri 构建跨平台桌面应用

#### 14.3.1 核心原则

| 原则 | 说明 | G1-G8 映射 |
|------|------|------------|
| **SSOT** | web/dist 是唯一构建产物 | G3 |
| **Tauri 壳最低维护** | Rust ≤ 200 行，无业务逻辑 | G1 |
| **Web 主导交付** | Vue 3 SPA 为产品交付层 | G2 |
| **一次构建** | 前端只构建一次，Web 和 Tauri 共用 | G4 |

#### 14.3.2 Vue 3 SPA 架构要求

| 要求 | 说明 | 实现 |
|------|------|------|
| **单一入口** | vue.html 作为主窗口入口 | `tauri.conf.json` → `vue.html` |
| **浮窗入口** | floating-vue.html 作为浮窗入口 | `tauri.conf.json` → `floating-vue.html` |
| **Platform Adapter** | 统一抽象接口调用 Tauri 能力 | `src/platformAdapter.js` |
| **API 统一** | 统一 API_BASE 注入 | `vite.config.js` define |
| **资源嵌入** | web/dist 打包进 Tauri bundle | `bundle.resources` |

#### 14.3.3 目录结构规范

```
web/                          # 产品交付层 (SSOT)
├── src/
│   ├── main.js             # Vue 应用入口
│   ├── App.vue             # 根组件
│   ├── platformAdapter.js   # Tauri 平台适配器 ✅
│   ├── router/             # Vue Router 配置
│   ├── stores/             # Pinia 状态管理
│   ├── views/             # 页面组件
│   ├── components/         # 公共组件
│   └── services/           # API 服务
├── dist/                   # Vite 构建产物 ← 唯一构建输出
├── vue.html               # Vue SPA 主入口 ✅
└── floating-vue.html     # 浮窗入口 ✅
```

#### 14.3.4 Tauri 窗口配置要求

| 窗口 | 入口文件 | 用途 | 配置 |
|------|---------|------|------|
| **main** | vue.html | 主窗口 | Tauri 主窗口 |
| **floating** | floating-vue.html | 快捷浮窗 | alwaysOnTop, hidden |

#### 14.3.5 Platform Adapter 模式

```javascript
// src/platformAdapter.js - 统一抽象接口

const platformAdapter = {
  // 环境检测
  isTauri: typeof window.__TAURI__ !== 'undefined',

  // 文件系统操作
  async openFile(path) {
    if (this.isTauri) {
      return await window.__TAURI__.fs.open(path);
    }
    // Web 降级实现
    return this.webFallback.openFile(path);
  },

  // 窗口操作
  async showWindow(label) {
    if (this.isTauri) {
      return await window.__TAURI__.window.getWindow(label).show();
    }
  },

  // 事件监听
  onEvent(event, callback) {
    if (this.isTauri) {
      return window.__TAURI__.event.listen(event, callback);
    }
    // Web 降级实现
    return this.webFallback.onEvent(event, callback);
  }
};
```

#### 14.3.6 IPC 命令注册规范

| 命令类型 | 说明 | Rust 端 | Vue 端 |
|---------|------|---------|--------|
| **窗口管理** | show/hide window | `show_floating_window` | `invoke('show_floating_window')` |
| **系统能力** | 文件系统、系统对话框 | Tauri API | platformAdapter |
| **事件推送** | Rust → 前端 | `app.emit()` | `listen()` |

#### 14.3.7 构建验证清单

```bash
# Vue 3 SPA 构建验证
[ ] vue.html 入口存在
[ ] floating-vue.html 入口存在
[ ] platformAdapter.js 实现
[ ] dist/ 包含 vue-*.js, floating-*.js
[ ] Tauri bundle 包含 web/dist

# Tauri 配置验证
[ ] tauri.conf.json windows.main.url = "vue.html"
[ ] tauri.conf.json windows.floating.url = "floating-vue.html"
[ ] bundle.resources 指向 web/dist
```

#### 14.3.8 Vue 3 组件规范

| 规范 | 说明 | 优先级 |
|------|------|--------|
| **Composition API** | 使用 `<script setup>` 语法 | 必须 |
| **Pinia 状态管理** | 集中状态管理替代 Vuex | 必须 |
| **Vue Router** | 路由管理替代手动视图切换 | 必须 |
| **TypeScript** | JS 或 TS，但需类型标注 | 建议 |
| **单文件组件** | .vue 文件包含 template/script/style | 必须 |

#### 14.3.9 相关文档

| 文档 | 说明 |
|------|------|
| `GOALS.md` | 目标体系 (G1-G11) |
| `「Web优先 + Tauri壳」模式/RTM.md` | 需求跟踪矩阵 |
| `「Web优先 + Tauri壳」模式/RDM_Requirements_Dependency_Matrix.md` | 需求依赖矩阵 |

---



## 三、领域关联图

| 原则 | 说明 | 来源 |
|------|------|------|
| **最小权限原则** | Rust 端只实现无法在 Web 端完成的功能（窗口管理、文件系统、系统托盘） | G1 |
| **职责分离原则** | Web 做 UI/业务，Tauri 做窗口/打包，API 做数据 | G2 |
| **单向依赖原则** | Web 不直接依赖 Tauri，通过抽象接口调用 | G1 |
| **配置驱动原则** | 通过 tauri.conf.json 声明式配置，避免 Rust 硬编码 | G8 |

#### 14.3.2 层级架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Hermes File Manager                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │   Vue 3 SPA │ ←── │   产品交付层 (Vite + Vue 3)                     │   │
│  │  (vue.html) │     │   - npm run dev (开发)                          │   │
│  │             │     │   - npm run build (构建)                        │   │
│  └──────┬──────┘     │   - platformAdapter.js (平台抽象)               │   │
│         │ SSOT       └─────────────────────────────────────────────────┘   │
│         ↓                                                                  │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ Tauri 壳    │ ←── │   桌面包装层 (最低维护)                         │   │
│  │ (Rust ≤200行│     │   - cargo tauri build                          │   │
│  │  无业务逻辑) │     │   - 仅做桌面窗口包装                            │   │
│  └─────────────┘     └─────────────────────────────────────────────────┘   │
│  ┌─────────────┐     ┌─────────────────────────────────────────────────┐   │
│  │ Python API  │ ←── │   后端服务层                                   │   │
│  │ (:8080)    │     │   - FastAPI (server.py)                        │   │
│  └─────────────┘     └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 14.3.3 Vue 3 组件规范

| 规范 | 说明 | 最佳实践编号 |
|------|------|-------------|
| Composition API | 使用 script setup 语法 | FE-004 |
| 状态管理 | 使用 Pinia 进行全局状态 | FE-005 |
| 平台适配 | 通过 platformAdapter.js 抽象 | FE-006 |
| 构建注入 | 通过 vite define 注入配置 | FE-007 |
| 代码分割 | 通过 manualChunks 优化 bundle | FE-008 |
| 单向数据流 | Props 向下、Emit 向上 | FE-009 |
| API 封装 | 统一 api.js 服务层 | FE-010 |

#### 14.3.4 platformAdapter 模式详解

```javascript
// src/platformAdapter.js - Web/Tauri 统一接口
const platform = {
  api: {
    isTauri: __TAURI_MODE__ === 'tauri',
    base: __API_BASE__,
    wsBase: __WS_BASE__,
    openPath: (path) => tauri.invoke('open_path_in_finder', { path }),
    switchWindow: () => tauri.invoke('switch_window'),
  },
  ws: {
    connect: (token, onMessage) => { /* WebSocket 连接 */ }
  }
}

// 组件中使用
import { platform } from '@/platformAdapter.js'

async function handleOpenFile(path) {
  await platform.api.openPath(path)
}
```

#### 14.3.5 构建产物结构

```
dist/
├── vue.html              # Vue SPA 主入口 (Tauri 主窗口)
├── floating-vue.html     # 浮窗 Vue 入口 (Tauri 浮窗)
└── assets/
    ├── vue-vendor-*.js  # Vue 框架 (~107 KB)
    ├── vue-*.js          # 主应用代码 (~120 KB)
    ├── echarts-*.js      # ECharts 图表 (~1.1 MB，库本身较大)
    ├── marked-*.js       # Markdown 解析 (~42 KB)
    ├── api-*.js          # API 服务 (~6 KB)
    ├── floating-*.js     # 浮窗代码 (~4 KB)
    └── style-*.css       # 样式 (~48 KB)
```

#### 14.3.6 vite.config.js 关键配置

```javascript
// vite.config.js
export default defineConfig({
  plugins: [vue()],
  base: './',
  define: {
    // 构建时注入，运行时零检测
    __API_BASE__: JSON.stringify(process.env.VITE_API_BASE || '/api/v1'),
    __TAURI_MODE__: JSON.stringify(process.env.NODE_ENV === 'production' ? 'tauri' : 'web'),
    __WS_BASE__: JSON.stringify(process.env.VITE_WS_BASE || 'ws://localhost:8080'),
  },
  build: {
    outDir: 'dist',
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'echarts': ['echarts', 'vue-echarts'],
          'marked': ['marked'],
        }
      }
    }
  }
})
```

#### 14.3.7 Tauri 窗口配置

```json
// tauri.conf.json
{
  "windows": [
    {
      "title": "Hermes File Manager",
      "url": "vue.html",       // Vue SPA 主入口
      "label": "main"
    },
    {
      "title": "快捷浮窗",
      "url": "floating-vue.html", // 浮窗 Vue 入口
      "label": "floating",
      "visible": false,
      "alwaysOnTop": true
    }
  ]
}
```

#### 14.3.8 与 GOALS.md 目标映射

| 目标 | 说明 | Vue 3 实践 |
|------|------|------------|
| G1 | Tauri ≤200行，无业务逻辑 | Rust 只做窗口管理，UI 逻辑全在 Vue |
| G2 | Web 主导产品交付 | Vue 3 SPA 是产品交付层 |
| G3 | SSOT | web/dist 是唯一构建产物 |
| G4 | 一次构建 | 前端只构建一次，Web 和 Tauri 共用 |
| G5 | API 统一 | vite define 注入 __API_BASE__ |
| G6 | 资源正确嵌入 | bundle.resources 正确打包 web/dist |
| G7 | 构建失败回滚 | 验证失败自动回滚 |
| G8 | 窗口 URL 标准化 | vue.html / floating-vue.html |

#### 14.3.9 验证检查清单

```bash
# 构建验证
pnpm run build  # 使用 pnpm 避免 rollup 原生模块问题
ls -lh dist/assets/*.js  # 检查 chunk 大小

# 预期 chunk 大小
# vue-vendor:  ~107 KB ✅
# vue:         ~120 KB ✅
# echarts:   ~1,119 KB ⚠️ (echarts 库本身)
# marked:      ~42 KB ✅
# api:          ~6 KB ✅

# Dev server 验证
pnpm run dev  # 启动开发服务器
# 访问 http://localhost:5173/vue.html

# Tauri 构建验证
cargo tauri build
# 验证 dist 内容正确嵌入 bundle
```

#### 14.3.10 相关最佳实践

| 编号 | 标题 | 说明 |
|------|------|------|
| FE-004 | Vue 3 Composition API 规范 | script setup 语法 |
| FE-005 | Pinia 状态管理规范 | Store 设计与使用 |
| FE-006 | PlatformAdapter 模式 | Web/Tauri 统一抽象 |
| FE-007 | 构建时配置注入 | vite define |
| FE-008 | 代码分割与按需加载 | manualChunks |
| FE-009 | 组件单向数据流 | Props/Emit |
| FE-010 | API 服务层封装 | api.js 统一封装 |


---

## 九、代码质量与冗余管理 (CODE QUALITY)

### 9.1 重复代码问题识别

| 问题类型 | 示例 | 影响 |
|---------|------|------|
| **文件级重复** | `TeamView.vue` + `Team.vue` | 维护成本高，容易不一致 |
| **函数级重复** | 相同逻辑在多个函数中复制 | 修改一处可能遗漏其他 |
| **模块级重复** | `lifecycle_engine.py` + `lifecycle.py` | 职责不清，难以定位 |

### 9.2 当前识别的冗余文件

> **更新时间**: 2026-05-05
> **识别方式**: 代码审查发现同功能多版本文件共存

**前端 (Vue)**:
| 冗余文件 | 问题 | 建议操作 |
|---------|------|---------|
| `FileView.vue` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| `AdminDashboard.vue` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| `FloatingWindow.vue` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| `FileItem.vue` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| ~~`StoragePool.vue`~~ | 与 `StoragePoolView.vue` 重复 | ~~合并到 `StoragePoolView.vue`~~ (待清理) |
| ~~`Team.vue`~~ | 与 `TeamView.vue` 重复 | ~~合并到 `TeamView.vue`~~ (待清理) |
| ~~`Space.vue`~~ | 与 `SpaceView.vue` 重复 | ~~合并到 `SpaceView.vue`~~ (待清理) |

**后端 (Python)**:
| 冗余文件 | 问题 | 建议操作 |
|---------|------|---------|
| `lifecycle_engine.py` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| `space_service.py` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| `file_service.py` (多版本) | 相同功能存在多个版本 | 合并为一个 |
| ~~`lifecycle.py`~~ | 与 `lifecycle_engine.py` 重复 | ~~合并到 `lifecycle_engine.py`~~ (待清理) |
| ~~`permission.py`~~ | 与 `permission_checker.py` 重复 | ~~合并到 `permission_checker.py`~~ (待清理) |
| ~~`space.py`~~ | 与 `space_service.py` 重复 | ~~合并到 `space_service.py`~~ (待清理) |
| ~~`team.py`~~ | 与 `team_service.py` 重复 | ~~合并到 `team_service.py`~~ (待清理) |

**冗余判定标准**:
| 判定条件 | 说明 |
|---------|------|
| 同名文件多版本 | `Xxx.vue` 或 `Xxx.py` 存在 2+ 个版本 |
| 同功能不同名 | `Team.vue` 和 `TeamView.vue` 做相同的事 |
| 版本后缀 | `Xxx_v1.py`, `Xxx_v2.py` 应合并 |

### 9.3 消除冗余的标准流程

```
1. 识别 (Identify)
   ↓
   diff file1.py file2.py  # 对比差异

2. 评估 (Assess)
   ↓
   - 确定保留目标文件
   - 识别需要迁移的独特功能

3. 合并 (Merge)
   ↓
   - 将独特功能迁移到目标文件
   - 更新所有引用

4. 验证 (Verify)
   ↓
   - 运行测试确保功能正常
   - 代码审查确认无遗漏

5. 清理 (Cleanup)
   ↓
   - 删除冗余文件
   - 提交变更
```

### 9.4 代码审查检查清单

| 检查项 | 说明 |
|-------|------|
| 有无重复文件？ | `*View.vue` + `*.vue` (同一功能) |
| 有无重复函数？ | 相同逻辑多处出现 |
| 命名是否一致？ | 前后端相同功能命名模式 |
| 职责是否单一？ | 一个文件只做一件事 |

### 9.5 相关最佳实践

| 编号 | 标题 | 说明 |
|------|------|------|
| CODE-005 | 消除重复代码与文件合并 | DRY 原则实施 |
| CODE-006 | 文件命名一致性规范 | 前后端命名模式 |
| CODE-007 | 模块职责单一原则 | SRP 原则 |

## 三、领域关联图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        身份认证 (AUTH)                             │
│                              │                                     │
│          ┌───────────────────┼───────────────────┐                   │
│          ↓                   ↓                   ↓                  │
│    ┌─────────┐         ┌─────────┐         ┌─────────┐             │
│    │  RBAC   │         │ TENANT  │         │ AUDIT   │             │
│    └────┬────┘         └────┬────┘         └────┬────┘             │
│         │                   │                   │                  │
│         │         ┌─────────┴─────────┐         │                  │
│         │         ↓                   ↓         │                  │
│         │    ┌─────────┐         ┌─────────┐    │                  │
│         └──→│ RESOURCE│←────────│ LIFECYCLE│←───┘                  │
│              └────┬────┘         └─────────┘                        │
│                   │                                              │
│         ┌─────────┴─────────┐                                     │
│         ↓                   ↓                                     │
│    ┌─────────┐         ┌─────────┐                               │
│    │  FILE   │         │ COLLAB  │                               │
│    └────┬────┘         └────┬────┘                               │
│         │                   │                                    │
│         └─────────┬─────────┘                                     │
│                   ↓                                               │
│            ┌─────────────┐                                        │
│            │ KNOWLEDGE   │                                        │
│            └──────┬──────┘                                        │
│                   │                                              │
│                   ↓ (未来)                                       │
│            ┌─────────────┐                                        │
│            │  BILLING    │                                        │
│            └─────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 四、领域与服务映射

| 领域 | 服务文件 | 状态 |
|------|---------|------|
| AUTH | auth_service.py | ✅ 已实现 |
| RBAC | permission_checker.py, permission_context.py | ✅ 已实现 |
| TENANT | team_service.py, space_service.py | ✅ 已实现 |
| RESOURCE | space_service.py, admin_service.py | ✅ 已实现 |
| LIFECYCLE | lifecycle_engine.py, workflow_service.py | ✅ 已实现 |
| FILE | file_service.py, file_lock_service.py | ✅ 已实现 |
| COLLAB | share_service.py, collaboration_service.py | ✅ 已实现 |
| AUDIT | notification_service.py, audit_subscriber.py | ✅ 已实现 |
| KNOWLEDGE | workflow_service.py, notebook_service.py | ✅ 已实现 |
| BILLING | (待实现) | ⏳ 规划中 |
| GUIDANCE | guidance_engine.py | ✅ 已实现 |
| REQMGT | (文档化管理) | ✅ 已实现 |
| TEST | tests/ 目录 | ✅ 已实现 |

---

## 五、核心实体清单

### 5.1 用户与认证

| 实体 | 模块 | 说明 |
|------|------|------|
| User | engine/models.py | 用户账号 |
| Role | engine/models.py | 角色定义 |
| UserSession | engine/models.py | 用户会话 |
| Permission | engine/models.py | 权限定义 |
| PermissionRule | engine/models.py | 权限规则 |

### 5.2 资源与空间

| 实体 | 模块 | 说明 |
|------|------|------|
| StoragePool | engine/models.py | 存储池 |
| Space | engine/models.py | 空间（团队/私人） |
| SpaceMember | engine/models.py | 空间成员 |
| SpaceRequest | engine/models.py | 空间申请 |
| SpaceCredential | engine/models.py | 邀请凭证 |
| SpaceLink | engine/models.py | 跨团队链接 |

### 5.3 文件与版本

| 实体 | 模块 | 说明 |
|------|------|------|
| FileVersion | engine/models.py | 文件版本 |
| DeletedFile | engine/models.py | 删除记录 |
| FileLock | engine/models.py | 文件锁 |
| FileUpload | engine/models.py | 上传记录 |

### 5.4 工作流与知识

| 实体 | 模块 | 说明 |
|------|------|------|
| Workflow | engine/models.py | 工作流 |
| WorkflowStep | engine/models.py | 工作流步骤 |
| Notebook | engine/models.py | 笔记本 |
| NotebookVariable | engine/models.py | 笔记本变量 |

### 5.5 共享与协作

| 实体 | 模块 | 说明 |
|------|------|------|
| SharedLink | engine/models.py | 分享链接 |
| CollaborationSession | engine/models.py | 协作会话 |

### 5.6 系统

| 实体 | 模块 | 说明 |
|------|------|------|
| AuditLog | engine/models.py | 审计日志 |
| Notification | engine/models.py | 通知 |

---

## 六、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **1.6** | **2026-05-05** | **对齐GOALS.md v3.0**：新增G9 Web独立部署领域说明，与「Web优先+Tauri壳」模式文档同步 |
| **1.6** | **2026-05-05** | **新增章节**：九、代码质量与冗余管理 (CODE QUALITY) |
| **1.5** | **2026-05-05** | **新增章节**：14.3 Vue 3 + Web优先+Tauri壳 最佳实践 |
| **1.4** | **2026-05-03** | **新增章节**：RESOURCE & CAPACITY MANAGEMENT (资源配额管理体系)，三级空间模型、承诺制/预留制、配额管理仪表盘 |
| **1.3** | **2026-05-03** | **新增领域**：AUTH (身份认证与会话管理)，Remember Me 最佳实践 |
| **1.2** | **2026-05-03** | **新增领域**：HYBRID (跨平台混合应用)，Web/Tauri 共用 UI 源码架构 |
| **1.1** | **2026-05-03** | **新增领域**：GUIDANCE (用户引导)、REQMGT (需求管理)、TEST (软件测试) |
| 1.0 | 2026-05-03 | 初始版本：领域分析表 |

---

## 七、身份认证与会话管理补充 (AUTH)

### 7.1 核心概念

| 概念 | 英文 | 领域 | 说明 |
|------|------|------|------|
| 身份认证 | Authentication | Web 安全 | 验证用户是谁的过程 |
| 授权 | Authorization | Web 安全 | 验证用户能做什么 |
| 记住我 | Remember Me | Web 认证 | 持久登录功能，允许跨会话保持登录状态 |
| 令牌刷新 | Token Refresh | 身份认证 | 更新即将过期的访问令牌 |
| 令牌撤销 | Token Revocation | 身份认证 | 主动使令牌失效 |
| 选择加入 | Opt-in | UX 设计 | 默认关闭，用户主动开启 |
| 选择退出 | Opt-out | UX 设计 | 默认开启，用户主动关闭 |

### 7.2 Remember Me 功能详解

**实现方式**：
```
登录流程:
1. 用户输入用户名/密码，勾选"记住我"
2. 服务器验证凭据，创建访问令牌(Token)
3. 如果勾选了"记住我"：
   - 发行长期令牌(Refresh Token)，通常 7-30 天
   - 将长期令牌存储在持久 Cookie/LocalStorage
4. 如果未勾选"记住我"：
   - 只发行短期令牌(Access Token)，通常 15分钟-24小时
   - 关闭浏览器后令牌消失
```

**令牌类型对比**：

| 令牌类型 | 生命周期 | 存储位置 | 用途 |
|----------|----------|----------|------|
| Access Token | 15分钟-24小时 | 内存 | API 访问 |
| Refresh Token | 7-30天 | HttpOnly Cookie / LocalStorage | 续期 Access Token |
| Session Token | 浏览器会话 | 内存 | 传统会话模式 |

### 7.3 最佳实践

**必须做**：
- ✅ "记住我"应该是**选择加入(Opt-in)**，而非默认勾选
- ✅ 注销时必须清除所有持久令牌
- ✅ Refresh Token 应该使用 HttpOnly Cookie 防止 XSS
- ✅ 长期令牌应该有明确的过期时间
- ✅ 用户修改密码后应该撤销所有活跃会话

**禁止做**：
- ❌ 禁止将 Access Token 永久存储
- ❌ 禁止在注销后保留"记住我"凭据
- ❌ 禁止使用长期令牌作为唯一认证方式

### 7.4 注销(Logout)核心原则

> **用户明确点击"退出"代表一次性的、明确的意图声明。系统必须尊重这个决定。**

**正确的注销流程**：
```javascript
function logout() {
  // 1. 清除会话令牌
  token = null;
  localStorage.removeItem(TOKEN_KEY);

  // 2. 【关键】清除"记住我"状态
  //    用户明确点击"退出"，代表明确的意图声明
  //    系统必须尊重这个决定，不能在刷新后重新登录
  localStorage.removeItem('hfm_remember');
  localStorage.removeItem('hfm_username');
  localStorage.removeItem('hfm_password');

  // 3. 清除其他会话状态
  currentPath = '/';
  currentView = 'files';
  myTeams = [];
  myStorageContexts = [];

  // 4. 更新 UI
  if (loginScreen) loginScreen.style.display = 'flex';
  if (appContainer) appContainer.classList.remove('active');
}
```

**场景对比**：

| 场景 | 期望行为 | 错误行为 |
|------|----------|----------|
| 用户退出后刷新页面 | 显示登录页 | 自动重新登录 |
| 用户退出后关闭浏览器再打开 | 显示登录页 | 自动重新登录 |
| 用户勾选"记住我"登录后 | 关闭浏览器再打开仍保持登录 | - |

### 7.5 相关标准与规范

| RFC | 标题 | 说明 |
|-----|------|------|
| RFC 6749 | OAuth 2.0 Authorization Framework | 包含 Refresh Token 规范 |
| RFC 7519 | JSON Web Token (JWT) | JWT 令牌结构规范 |
| RFC 6750 | OAuth 2.0 Bearer Token Usage | 访问令牌使用规范 |

**参考资料**：
- OWASP Session Management Cheat Sheet
- NIST SP 800-63B: Digital Identity Guidelines
- "The Roots of the Remember Me Feature" - Interaction Design Foundation

---

### 7.6 身份生命周期管理 (Identity Lifecycle Management)

#### 7.6.1 概念定义

| 概念 | 英文 | 领域 | 说明 |
|------|------|------|------|
| 身份生命周期管理 | Identity Lifecycle Management | IDM | 用户账户的创建、修改、冻结、删除全过程管理 |
| 账号类型变更 | Role Change | IAM | 用户权限等级的提升或降低 |
| 资产回收 | Asset Revocation | 安全 | 变更时对原有资产的重新分配或回收 |
| 变更回滚 | Rollback | 运维 | 将变更恢复到之前的状态 |

#### 7.6.2 账号类型变更流程

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    账号类型变更生命周期                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. 申请(Apply)          2. 审批(Approve)        3. 执行(Execute)       │
│  ┌──────────────┐        ┌──────────────┐        ┌──────────────┐        │
│  │ 用户/管理员   │   →    │  admin 审批  │   →   │ 更新用户角色  │        │
│  │ 请求变更角色  │        │  检查约束     │        │ 记录资产快照  │        │
│  └──────────────┘        └──────────────┘        └──────────────┘        │
│         ↓                       ↓                       ↓                    │
│  触发事件:                 检查:                   审计:                    │
│  - ROLE_CHANGE_REQUEST    - 资产是否可转移         - 记录变更日志          │
│  - 记录申请原因           - 目标角色是否存在         - 通知用户               │
│                          - 权限是否足够           - 刷新权限缓存            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 7.6.3 变更类型判定

| 变更类型 | 说明 | 优先级变化 |
|----------|------|------------|
| **promotion** | 权限提升 | guest(1) → viewer(10) → editor(50) → admin(100) |
| **demotion** | 权限降低 | admin(100) → editor(50) → viewer(10) → guest(1) |
| **transfer** | 同级调整 | viewer(10) → viewer(10) |
| **initial_assignment** | 初始分配 | 无 → 任意角色 |

#### 7.6.4 资产处理策略

| 变更场景 | 资产处理 | 回滚支持 |
|----------|----------|----------|
| admin → viewer/guest | **阻塞变更**（必须先转移管理的空间） | 不适用 |
| viewer/guest → admin | 授予管理能力 | 支持 |
| viewer ↔ guest | 无资产变化 | 支持 |
| 任意 → 任意 | 记录资产快照供回滚 | 支持 |

#### 7.6.5 RoleChangeRecord 模型

```python
class RoleChangeRecord(Base):
    """角色变更记录 - 身份生命周期管理的核心审计模型"""
    user_id: str              # 变更目标用户
    changed_by: str           # 变更执行者
    old_role_id: str          # 原角色
    new_role_id: str          # 新角色
    asset_snapshot: JSON      # 资产快照（变更前状态）
    change_type: str          # 变更类型
    rollback_available: bool  # 是否可回滚
    rolled_back: bool         # 是否已回滚
```

#### 7.6.6 相关标准与规范

| 标准 | 说明 |
|------|------|
| ISO/IEC 27001 | 信息安全管理体系 - 访问控制 |
| NIST SP 800-63 | 数字身份指南 - 生命周期管理 |
| ITIL v4 | IT 服务管理 - 变更管理 |
| SOC 2 | 服务组织控制 - 账户管理 |

#### 7.6.7 核心原则

> **身份生命周期管理的核心原则**：
> 1. **可审计性**：每次身份变更都必须记录
> 2. **可回滚性**：关键变更必须支持回滚
> 3. **资产保护**：降级时必须处理用户持有的敏感资产
> 4. **最小权限**：仅授予完成任务所需的最小权限

---

## 八、资源配额管理体系 (RESOURCE & CAPACITY MANAGEMENT)

### 8.1 核心理论模型

#### 8.1.1 三级空间模型

| 空间类型 | 英文 | 归属 | 配额类型 | 说明 |
|----------|------|------|----------|------|
| **私有空间** | Private Space | 单用户 | 承诺制 | 用户独享，独立配额，超用阻塞 |
| **团队空间** | Team Space | 多用户共享 | 承诺制 + 资源共享 | 团队共享配额池，可内部调配 |
| **组织空间** | Organization Space | 全组织共享 | 预留制 | 系统级预分配，管理员专属，不参与用户配额 |

#### 8.1.2 资源分配层次关系

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        物理存储池 (Storage Pool)                            │
│                        总容量 = 硬盘实际可用空间                             │
│                        例: 2TB SSD                                          │
└─────────────────────────────────────────────────────────────────────────────┘
         │                         │                        │
         ▼                         ▼                        ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────────┐
│   组织预留区        │    │   团队配额池        │    │   个人配额池            │
│   (Reserved)      │    │   (Committed)     │    │   (Committed)         │
│                   │    │                   │    │                       │
│  ├─ 系统空间       │    │  ├─ 团队A: 500GB  │    │  ├─ lmq: 10GB         │
│  ├─ 回收站         │    │  ├─ 团队B: 300GB  │    │  ├─ admin: 无限制      │
│  └─ 临时缓存       │    │  └─ 团队C: 200GB  │    │  └─ viewer: 1GB      │
│   预留制           │    │   承诺制           │    │   承诺制               │
│   (不参与分配)     │    │   (可超用警告)     │    │   (超用阻塞写入)       │
└───────────────────┘    └───────────────────┘    └───────────────────────┘
         │                         │                        │
         ▼                         ▼                        ▼
    系统管理员              团队管理员              空间所有者
    独享                   共享配额              独立配额
```

#### 8.1.3 配额模型对比

| 维度 | 承诺制 (Committed) | 预留制 (Reserved) |
|------|-------------------|------------------|
| **配额归属** | 配额是"信用额度" | 配额是"专属空间" |
| **超用处理** | 软限制：警告/限速/阻塞 | 硬限制：物理隔离，无法超用 |
| **资源利用** | 高：未使用空间可供他人 | 低：预留空间未用也占用 |
| **计费模式** | 按实际使用计费 (Pay-as-you-go) | 按预留容量计费 (Reserved) |
| **灵活性** | 高：可动态调整 | 低：调整需要迁移数据 |

---

### 8.2 网盘空间管理最佳实践

#### 8.2.1 云厂商配额模型参考

| 服务 | 免费配额 | 付费配额 | 超用策略 |
|------|---------|---------|---------|
| **Google Drive** | 15GB (共享) | 100GB/200GB/2TB/30TB | 到达后必须购买，无法临时借用 |
| **Dropbox** | 2GB | Plus 2TB, Professional 3TB | 到达后必须购买 |
| **OneDrive** | 5GB | 100GB/1TB/Microsoft 365 无限 | 企业版无上限，按用户数计费 |
| **AWS S3** | 无免费层级 | 按 GB/月计费 | 无用户级配额概念，按实际使用计费 |
| **Azure Blob** | 30GB | 按 GB/月计费 | 无配额上限，按实际使用计费 |

**核心原则**: 商业网盘多使用**按量计费模式**，而非预留制。

#### 8.2.2 Admin 视角的资源池视图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        存储容量管理仪表盘 (Admin Dashboard)                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  物理资源池总容量:                2,000 GB (2TB)                            │
│  ────────────────────────────────────────────────────────────────────────  │
│  已分配预留:                      500 GB   (组织空间/系统预留)                │
│  可分配承诺总额:                 1,500 GB  (团队+个人)                      │
│  ────────────────────────────────────────────────────────────────────────  │
│  已承诺配额总和:                 2,200 GB  ← 超额警告！                      │
│  实际使用总量:                    850 GB                                    │
│  剩余可用:                        650 GB                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  配额透支策略配置:                                                   [配置]  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ☑ 允许承诺总额超过资源池 (超用时按比例分配)                          │   │
│  │ ☑ 启用软配额预警 (使用达80%时通知)                                  │   │
│  │ ☑ 启用硬配额阻塞 (使用达100%时禁止写入)                             │   │
│  │                                                                       │   │
│  │ 缓冲比例: [10%] ▾                                                   │   │
│  │ 超用预警阈值: [80%] ▾                                                │   │
│  │ 超用阻塞阈值: [100%] ▾                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  团队配额详情:                                               [展开全部]     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 团队A        │ 承诺: 500GB  │ 使用: 200GB (40%)  │ 状态: 正常     │   │
│  │ 团队B        │ 承诺: 300GB  │ 使用: 280GB (93%)  │ 状态: ⚠️ 预警  │   │
│  │ 团队C        │ 承诺: 200GB  │ 使用: 150GB (75%)  │ 状态: 正常     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  个人配额详情:                                               [展开全部]     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ admin        │ 承诺: 无限制  │ 使用: 100GB           │ 状态: 正常     │   │
│  │ lmq          │ 承诺: 10GB    │ 使用: 2GB (20%)      │ 状态: 正常     │   │
│  │ viewer       │ 承诺: 1GB     │ 使用: 0.5GB (50%)    │ 状态: 正常     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.3 承诺制与预留制的实际管理

#### 8.3.1 存储引擎内部管理模型

```python
class StoragePool:
    """存储池元数据模型"""
    # 物理属性
    total_bytes: int          # 物理总容量 (2TB)
    reserved_bytes: int       # 组织预留 (500GB)
    
    # 配额管理
    committed_bytes: int      # 已承诺配额总和 (2.2TB)
    actual_used_bytes: int    # 实际使用 (850GB)
    
    # 策略配置
    allow_overcommit: bool    # 允许透支
    soft_warning_ratio: float # 软预警比例 (0.8)
    hard_block_ratio: float   # 硬阻塞比例 (1.0)
    buffer_ratio: float       # 缓冲比例 (0.1)

    @property
    def available_for_commit(self) -> int:
        """剩余可用于承诺的空间 = 总容量 - 预留"""
        return self.total_bytes - self.reserved_bytes

    @property
    def effective_quota_ratio(self) -> float:
        """有效配额比例 (超用时用于比例分配)"""
        if self.committed_bytes <= self.available_for_commit:
            return 1.0  # 配额足够，无需限制
        return self.available_for_commit / self.committed_bytes

    @property
    def usage_ratio(self) -> float:
        """实际使用率"""
        return self.actual_used_bytes / self.total_bytes

    @property
    def committed_ratio(self) -> float:
        """承诺使用率"""
        return self.committed_bytes / self.available_for_commit

    def check_write(self, file_size: int) -> WriteResult:
        """写入前的配额检查"""
        if self.actual_used_bytes + file_size > self.total_bytes:
            return WriteResult.BLOCKED_NO_SPACE
        
        effective_limit = self.available_for_commit * self.effective_quota_ratio
        if self.actual_used_bytes + file_size > effective_limit:
            if self.soft_warning_ratio < (self.actual_used_bytes + file_size) / self.total_bytes:
                return WriteResult.WARNING_OVERCOMMIT
            return WriteResult.BLOCKED_QUOTA_EXCEEDED
        
        return WriteResult.ALLOWED
```

#### 8.3.2 承诺制管理策略

| 环境 | 推荐策略 | 理由 |
|------|---------|------|
| **开发环境** | 承诺制 + 硬配额阻塞 | 便于测试配额机制，记录实际需求 |
| **测试环境** | 承诺制 + 启用弹性透支 | 模拟真实超用场景 |
| **生产环境** | 承诺制 + 超用预警 | 按实际使用计费，允许临时超用但监控 |

#### 8.3.3 配额透支策略

| 策略 | 描述 | 适用场景 |
|------|------|---------|
| **严格预留** | 承诺总额 ≤ 资源池，禁止透支 | 追求稳定，不希望任何超用 |
| **弹性透支** | 承诺总额 > 资源池，实际使用未超时正常 | 信任用户，按实际使用计费 |
| **配额预留** | 预留 X% 作为缓冲，禁止承诺超过 (资源池 - 缓冲) | 保守策略，防止极端情况 |

---

### 8.4 灵活配置项清单

所有配置项均支持 Admin 通过界面配置，高度解耦：

#### 8.4.1 资源池配置

| 配置项 | 字段名 | 类型 | 默认值 | 说明 |
|--------|--------|------|--------|------|
| 物理总容量 | `total_bytes` | int | - | 实际硬盘可用空间 |
| 预留空间 | `reserved_bytes` | int | 10% | 组织空间/系统预留 |
| 缓冲比例 | `buffer_ratio` | float | 0.1 | 超用预留缓冲 |
| 允许透支 | `allow_overcommit` | bool | false | 是否允许承诺超资源池 |

#### 8.4.2 配额策略配置

| 配置项 | 字段名 | 类型 | 默认值 | 说明 |
|--------|--------|------|--------|------|
| 软预警阈值 | `soft_warning_ratio` | float | 0.8 | 达80%时预警 |
| 硬阻塞阈值 | `hard_block_ratio` | float | 1.0 | 达100%时阻塞 |
| 透支告警间隔 | `overcommit_alert_interval` | int | 300 | 告警间隔(秒) |

#### 8.4.3 空间类型配置

| 空间类型 | 配置项 | 说明 |
|----------|--------|------|
| **组织空间** | `org_reserved_bytes` | 预留空间大小 |
| | `org_quota_type` | 预留制/无限制 |
| | `org_auto_cleanup` | 是否自动清理回收站 |
| **团队空间** | `team_default_quota` | 新团队默认配额 |
| | `team_max_quota` | 团队最大配额上限 |
| | `team_quota_transferable` | 是否支持团队间调配 |
| **个人空间** | `private_default_quota` | 新用户默认配额 |
| | `private_max_quota` | 个人最大配额上限 |
| | `private_overage_allowed` | 是否允许超用 |

#### 8.4.4 售卖配置

| 配置项 | 字段名 | 类型 | 说明 |
|--------|--------|------|------|
| 套餐名称 | `plan_name` | string | 套餐显示名 |
| 套餐配额 | `plan_quota` | int | 套餐容量 |
| 价格 | `plan_price` | decimal | 月费/年费 |
| 超用费率 | `overage_rate` | decimal | 超用 GB/元 |
| 超用允许 | `overage_allowed` | bool | 是否允许超用 |
| 最大透支 | `max_overage` | int | 最大透支量 |
| 时限 | `plan_duration` | int | 有效期(天) |

---

### 8.5 团队间配额调配机制

**场景**: 团队A (500GB配额) 只用了 100GB，团队B (300GB配额) 快用完了

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  配额调配请求                                                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│  来自: 团队B                                                                │
│  目标: 团队A                                                                │
│  申请量: 200GB                                                             │
│  理由: 项目冲刺，需要临时扩容                                                │
│  时限: 7天后自动回收                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
           ↓ 团队A 管理员审批
┌─────────────────────────────────────────────────────────────────────────────┐
│  调配结果                                                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  团队A: 500GB → 300GB (减少200GB)                                          │
│  团队B: 300GB → 500GB (增加200GB)                                          │
│  有效期: 7天                                                                │
│  到期后: 自动回收，无需人工干预                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.6 三级空间视图与管理

#### 8.6.1 组织空间视图 (Admin Only)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    组织空间管理 (Organization Space)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  系统预留空间:                      500 GB                                   │
│  回收站保留空间:                    50 GB                                    │
│  临时缓存空间:                      10 GB                                    │
│  ────────────────────────────────────────────────────────────────────────  │
│  已分配总计:                       560 GB                                   │
│  剩余可用:                       1,440 GB                                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  [配置预留空间]  [清空回收站]  [查看系统日志]                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.6.2 团队空间视图 (Admin + Team Owner)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    团队空间管理 (Team Space Management)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  团队列表:                                          [+ 创建团队]              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 团队A (Engineering)                              Owner: @admin       │   │
│  │ 配额: 500GB / 使用: 200GB (40%)                  [管理] [配额调配]    │   │
│  │ 成员: 5人                                        状态: 正常           │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 团队B (Product)                                  Owner: @pm         │   │
│  │ 配额: 300GB / 使用: 280GB (93%)                  [管理] [配额调配]    │   │
│  │ 成员: 3人                                        状态: ⚠️ 预警        │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │ 团队C (Design)                                   Owner: @designer   │   │
│  │ 配额: 200GB / 使用: 150GB (75%)                  [管理] [配额调配]    │   │
│  │ 成员: 2人                                        状态: 正常           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  批量操作: [导出配额报告]  [设置默认配额模板]  [超用告警配置]                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.6.3 个人空间视图 (User)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    我的空间 (My Space)                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  我的私有空间:                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  lmq 的空间                                                         │   │
│  │  配额: 10GB    已用: 2GB (20%)    剩余: 8GB                        │   │
│  │  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 20%             │   │
│  │                                                                     │   │
│  │  [申请扩容]  [查看使用详情]  [清理回收站]                            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  加入的团队:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 团队A (Engineering)      我的配额: 100GB / 已用: 40GB                │   │
│  │ 团队B (Product)          我的配额: 50GB / 已用: 45GB ⚠️            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  空间申请记录:  [待审批: 1]  [已通过: 3]  [已拒绝: 0]                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.7 Admin 权限配置与空间管理看板

#### 8.7.1 Admin 综合管理看板

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Hermes File Manager - Admin Console                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  [资源总览]  [用户管理]  [团队管理]  [角色权限]  [配额配置]  [系统设置]       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  快捷操作:                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐              │
│  │ 👥 用户    │ │ 👔 团队    │ │ 📦 配额    │ │ ⚙️ 配置    │              │
│  │ 总数: 50   │ │ 总数: 10   │ │ 已用: 850GB│ │ 系统正常   │              │
│  │ +3 本月    │ │ +1 本月    │ │ /2TB      │ │            │              │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘              │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  容量健康度:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │
│  │  42% 已用                                              850GB / 2TB  │   │
│  │                                                                   │   │
│  │  ⚠️ 警告: 团队B 配额使用率达 93%，即将触发预警                       │   │
│  │  ℹ️ 提示: 团队A 有 400GB 未使用配额，可考虑临时调配                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  待处理事项:                                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ ⏳ 空间申请 (3)    ⏳ 配额调配请求 (1)    ⏳ 团队解散审批 (0)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  最近操作日志:                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ 10:30  用户 lmq 申请扩容 (10GB → 50GB)                    [审批]   │   │
│  │ 10:15  团队B 配额调配请求: 团队A → 团队B (200GB)            [审批]  │   │
│  │ 09:45  用户 viewer 创建团队申请: Design Team               [审批]   │   │
│  │ 09:30  角色变更: @pm viewer → editor                       [查看]   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.7.2 角色权限配置视图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    角色权限配置 (Role Permission Configuration)               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  角色列表:                                                                  │
│  ┌──────────┬──────────┬──────────┬──────────────┐                          │
│  │ admin    │ editor   │ viewer   │ guest        │                          │
│  │ (管理员) │ (编辑者) │ (查看者) │ (访客)       │                          │
│  │ 2人      │ 15人     │ 30人     │ 3人          │                          │
│  │ [编辑]   │ [编辑]   │ [编辑]   │ [编辑]       │                          │
│  └──────────┴──────────┴──────────┴──────────────┘                          │
│                                                                             │
│  admin 权限详情:                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  文件操作                                                            │   │
│  │    ☑ file:create  ☑ file:read  ☑ file:update  ☑ file:delete        │   │
│  │                                                                     │   │
│  │  空间操作                                                            │   │
│  │    ☑ space:create  ☑ space:read  ☑ space:update  ☑ space:delete   │   │
│  │    ☑ space:manage                                                │   │
│  │                                                                     │   │
│  │  团队操作                                                            │   │
│  │    ☑ team:create  ☑ team:read  ☑ team:update  ☑ team:delete     │   │
│  │    ☑ team:manage                                                │   │
│  │                                                                     │   │
│  │  存储池操作                                                          │   │
│  │    ☑ storage_pool:create  ☑ storage_pool:read                     │   │
│  │    ☑ storage_pool:update  ☑ storage_pool:delete                   │   │
│  │                                                                     │   │
│  │  角色权限                                                            │   │
│  │    ☑ role:create  ☑ role:read  ☑ role:update  ☑ role:delete     │   │
│  │                                                                     │   │
│  │  用户管理                                                            │   │
│  │    ☑ user:create  ☑ user:read  ☑ user:update  ☑ user:delete     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  viewer 权限详情:                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  文件操作                                                            │   │
│  │    ☐ file:create  ☑ file:read  ☐ file:update  ☐ file:delete     │   │
│  │                                                                     │   │
│  │  空间操作                                                            │   │
│  │    ☐ space:create  ☑ space:read  ☐ space:update  ☐ space:delete  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  [+ 创建新角色]  [导入角色模板]  [导出权限配置]                               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 8.7.3 生命周期状态与权限联动

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              生命周期状态 × 角色权限 联动视图                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  空间生命周期状态机:                                                        │
│                                                                             │
│  ┌──────────┐    申请     ┌──────────┐    审批通过  ┌──────────┐           │
│  │ PENDING  │ ────────→  │ APPROVED │ ─────────→  │  ACTIVE  │           │
│  │  待审批   │            │  已审批   │             │   活跃   │           │
│  └──────────┘            └──────────┘             └──────────┘           │
│       │                        │                        │                  │
│       │ 拒绝/取消               │ 过期/撤回              │ 解散/归档         │
│       ▼                       ▼                       ▼                  │
│  ┌──────────┐           ┌──────────┐            ┌──────────┐           │
│  │ REJECTED │           │ EXPIRED  │            │ ARCHIVED │           │
│  │   拒绝   │           │   过期   │            │   归档   │           │
│  └──────────┘           └──────────┘            └──────────┘           │
│                                                                             │
│  状态 × 角色 权限矩阵:                                                      │
│  ┌────────────┬────────┬────────┬────────┬────────┬────────┐                │
│  │ 操作       │ admin │ editor │ viewer │ guest │ 创建者 │                │
│  ├────────────┼────────┼────────┼────────┼────────┼────────┤                │
│  │ 申请空间   │   ✓   │   ✓    │   ✓    │   ✗   │   -   │                │
│  │ 审批空间   │   ✓   │   ✗    │   ✗    │   ✗   │   ✗   │                │
│  │ 上传文件   │   ✓   │   ✓    │   ✗    │   ✗   │   ✓   │                │
│  │ 下载文件   │   ✓   │   ✓    │   ✓    │   ✗   │   ✓   │                │
│  │ 删除空间   │   ✓   │   ✗    │   ✗    │   ✗   │   ✓*  │                │
│  │ 转让空间   │   ✓   │   ✗    │   ✗    │   ✗   │   ✓   │                │
│  └────────────┴────────┴────────┴────────┴────────┴────────┘                │
│  * 需要 admin 最终确认                                                      │
│                                                                             │
│  角色变更时的空间处理:                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  admin → viewer:                                                    │   │
│  │    - 管理的空间: 转移给其他 admin 或指定用户                          │   │
│  │    - 配额: 降低为 viewer 默认配额                                     │   │
│  │    - 托管团队: 必须先转让所有权                                       │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │  viewer → admin:                                                    │   │
│  │    - 自动获得所有空间的管理权限                                       │   │
│  │    - 配额: 调整为无限制或 admin 默认配额                              │   │
│  │    - 托管团队: 自动成为所有团队的管理员                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 8.8 相关标准与最佳实践

| 标准/实践 | 说明 |
|-----------|------|
| AWS Well-Architected Framework - Sustainability | 云资源配额管理最佳实践 |
| Google Cloud Resource Quotas | 多租户配额管理参考 |
| Kubernetes Resource Quota & Limit Range | 命名空间级资源配额模型 |
| ISO/IEC 27001 - Access Control | 信息安全管理体系 - 资源访问控制 |
| ITIL v4 - Capacity Management | 容量管理流程 |

---

### 8.9 核心原则

> **资源配额管理体系的核心原则**：
> 1. **分层隔离**：组织/团队/个人三级空间独立配额，互不干扰
> 2. **承诺灵活**：承诺制为主，预留制为辅，支持弹性透支与调配
> 3. **可观测性**：实时监控容量健康度，提前预警超用风险
> 4. **Admin 可配置**：所有策略参数均可通过界面配置，高度解耦
> 5. **生命周期联动**：配额管理与空间生命周期、角色变更紧密联动

---

## 九、Vue 3 SPA 前端架构 (VUE3-SPA)

### 9.1 领域概述

| 属性 | 内容 |
|------|------|
| **领域代码** | VUE3-SPA |
| **描述** | Vue 3 + Pinia + Vue Router 前端架构，作为"Web优先 + Tauri壳"模式的产品交付层 |
| **核心实体** | Vue SFC, Pinia Store, Vue Router, PlatformAdapter |
| **关键操作** | 组件渲染、状态管理、路由导航、平台能力调用 |
| **目标对齐** | G2 (Web 主导产品交付), G3 (SSOT), G8 (窗口 URL 标准化) |

**架构位置**:
```
┌─────────────────────────────────────────────────────────────┐
│                    Vue 3 SPA (web/)                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────┐  │
│  │ Views   │  │Components│  │ Stores  │  │   Router    │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────┘  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              PlatformAdapter (platformAdapter.js)     │   │
│  │  - 统一接口: platform.api, platform.ws, platform.platform│ │
│  │  - 环境检测: Web Mode / Tauri Mode                   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
         │                                    │
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────────┐
│   后端 API      │                │   Tauri 原生壳      │
│ (localhost:8080)│                │   (Rust ≤ 200行)   │
└─────────────────┘                └─────────────────────┘
```

### 9.2 核心组件

| 组件 | 说明 | 目标 |
|------|------|------|
| **vue.html** | Vue SPA 主入口，桌面主窗口加载 | G8 |
| **floating-vue.html** | Vue SPA 浮窗入口，桌面浮窗加载 | G8 |
| **platformAdapter.js** | 平台适配器，统一 Web/Tauri API | G1 |
| **Pinia Stores** | 状态管理（authStore, fileStore, spaceStore 等） | G2 |
| **Vue Router** | 路由管理，命名路由避免警告 | G2 |

### 9.3 Vue Router 规范

**命名路由原则**:
```javascript
// ✅ 正确：所有子路由都有 name
{
  path: '/',
  name: 'Main',
  component: MainLayout,
  children: [
    { path: '', name: 'Home', redirect: '/files' },  // 有 name
    { path: 'files', name: 'Files', component: FileView },
    { path: 'teams', name: 'Teams', component: TeamView },
  ]
}

// ❌ 错误：空路径子路由没有 name，会导致 Vue Router 警告
{
  path: '/',
  name: 'Main',
  children: [
    { path: '', redirect: '/files' },  // 缺少 name！
  ]
}
```

### 9.4 Pinia Store 规范

**延迟初始化原则**:
```javascript
// ✅ 正确：延迟创建 store 实例
let storeInstance = null
const getStore = () => {
  if (!storeInstance) {
    storeInstance = useMyStore()
  }
  return storeInstance
}

// ❌ 错误：在 Pinia 安装前直接调用
const store = useMyStore()  // 会在 Vue app.use(pinia) 之前报错
```

**Window 暴露原则**:
```javascript
// 暴露到 window 供 Vanilla JS 或 Tauri 调用
if (typeof window !== 'undefined') {
  window.__vueGuidance = {
    trigger: (event, context) => getGuidanceStore().trigger(event, context),
    // ...
  }
}
```

### 9.5 PlatformAdapter 模式

**统一接口定义**:
```javascript
const platform = {
  api: {
    base: API_BASE,           // http://localhost:8080/api/v1
    wsBase: WS_BASE,         // ws://localhost:8080
    isTauri: TAURI_MODE === 'tauri',
    mode: TAURI_MODE,
    getSystemStatus: () => tauriInvoke('get_system_status'),
    openPath: (path) => tauriInvoke('open_path_in_finder', { path }),
  },
  ws: { /* WebSocket 连接 */ },
  platform: {
    isTauri: TAURI_MODE === 'tauri',
    mode: TAURI_MODE,
    openUrl: (url) => window.open(url, '_blank'),
    listen: tauriListen,
    emit: tauriEmit,
  },
  invoke: tauriInvoke,
  listen: tauriListen,
  emit: tauriEmit,
}
```

### 9.6 Tauri 窗口配置

**tauri.conf.json 窗口规范**:
```json
{
  "windows": [
    {
      "title": "Hermes File Manager",
      "url": "vue.html",
      "label": "main"
    },
    {
      "title": "快捷浮窗",
      "url": "floating-vue.html",
      "label": "floating",
      "visible": false,
      "alwaysOnTop": true
    }
  ]
}
```

### 9.7 构建产物规范

**web/dist 输出结构**:
```
dist/
├── vue.html           # Vue SPA 主入口 (G8)
├── floating-vue.html # 浮窗 Vue 入口 (G8)
└── assets/
    ├── vue-*.js      # Vue 框架 bundle
    ├── api-*.js       # API 服务 bundle
    ├── floating-*.js  # 浮窗 bundle
    └── *.css          # 样式
```

**关键指标**:
| 指标 | 目标 | 实际 |
|------|------|------|
| Rust 代码行数 | ≤ 200 行 | 200 行 ✅ |
| 构建产物 | 唯一输出 (SSOT) | web/dist ✅ |
| 入口文件 | vue.html / floating-vue.html | ✅ |

### 9.8 核心原则

> **Vue 3 SPA 前端架构的核心原则**：
> 1. **Web 优先**：产品功能在 Web 端开发和测试，Tauri 仅做桌面集成
> 2. **SSOT**：web/dist 是唯一构建产物，前端只构建一次
> 3. **延迟初始化**：Pinia Store 在 app.use(pinia) 之后才能调用
> 4. **命名路由**：所有子路由必须有名，避免 Vue Router 警告
> 5. **平台适配下沉**：平台差异化代码下沉到 PlatformAdapter 层

---

## 九、Vue 3 + Tauri 集成领域规范 (VUE-TAURI)

### 9.1 领域概述

| 属性 | 内容 |
|------|------|
| **领域代码** | VUETAURI |
| **描述** | Vue 3 前端与 Tauri 桌面壳的集成架构、最佳实践与技术要求 |
| **核心实体** | Vue SPA, PlatformAdapter, Tauri Commands, Tauri Events |
| **关键文件** | vue.html, floating-vue.html, platformAdapter.js, vite.config.js |
| **目标** | G1-G8 全部达成，SSOT 架构 |

### 9.2 层级架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Vue 3 SPA 产品交付层                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Vue 3 + Composition API + Pinia + Vue Router                       │   │
│  │  - 视图层: views/*.vue                                              │   │
│  │  - 组件层: components/*.vue                                          │   │
│  │  - 状态层: stores/*.js (Pinia)                                      │   │
│  │  - 服务层: services/api.js                                           │   │
│  │  - 平台适配: platformAdapter.js                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                │ SSOT                                     │
│                                ↓                                          │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Tauri 桌面壳层                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Rust (≤200行，无业务逻辑)                                           │   │
│  │  - 窗口管理: 创建、切换、隐藏、显示                                  │   │
│  │  - 系统托盘: 图标、菜单、事件                                        │   │
│  │  - 原生能力: 文件对话框、系统打开、URL打开                           │   │
│  │  - IPC通信: Commands (invoke) + Events (emit/listen)                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.3 核心目标映射 (G1-G8)

| 目标编号 | 目标描述 | Vue 3 实现要求 | 状态 |
|---------|---------|---------------|------|
| **G1** | Tauri 最低维护量（Rust ≤200行） | Rust 代码仅做窗口管理和系统能力调用，无业务逻辑 | ✅ 已达成 |
| **G2** | Web 主导产品交付 | Vue 3 SPA 产品功能在 Web 端开发和测试 | ✅ 已达成 |
| **G3** | SSOT（web/dist 唯一构建） | Vite 构建产物为唯一构建输出，Tauri bundle 直接使用 | ✅ 已达成 |
| **G4** | 一次构建 | 前端只构建一次，同时用于 Web 和 Tauri | ✅ 已达成 |
| **G5** | API 统一 | 统一使用 `http://localhost:8080/api/v1` | ✅ 已达成 |
| **G6** | 资源正确嵌入 | bundle.resources 正确打包 web/dist | ✅ 已达成 |
| **G7** | 构建失败回滚 | 构建或验证失败时自动恢复上一可用版本 | ✅ 已达成 |
| **G8** | 窗口 URL 标准化 | 使用 `vue.html` 作为主入口 | ✅ 已达成 |

### 9.4 PlatformAdapter 模式

PlatformAdapter 是 Vue 3 与 Tauri 通信的核心抽象层：

```javascript
// platformAdapter.js - 内联在 vue.html / floating-vue.html 中
const platform = {
  api: {
    base: API_BASE,           // 构建时注入
    wsBase: WS_BASE,          // 构建时注入
    isTauri: TAURI_MODE === 'tauri',
    mode: TAURI_MODE,
    getSystemStatus: () => invoke('get_system_status'),
    openPath: (path) => invoke('open_path_in_finder', { path }),
    toggleWindow: (label) => invoke('toggle_window', { label }),
    switchWindow: () => invoke('switch_window'),
  },
  ws: {
    base: WS_BASE,
    connect: (token, onMessage) => { /* WebSocket 连接 */ },
  },
  platform: {
    isTauri: TAURI_MODE === 'tauri',
    mode: TAURI_MODE,
    openUrl: (url) => window.open(url, '_blank'),
    listen: (eventName, callback) => listen(eventName, callback),
    emit: (eventName, payload) => emit(eventName, payload),
  },
  invoke,
  listen,
  emit,
};
```

**关键原则**:
- Web 端通过 `platform` 对象访问所有原生能力
- Tauri 模式下 `invoke` 调用 Rust Commands
- Web 模式下 `invoke` 抛出错误（或提供 mock）
- 始终使用 `data-*` 事件委托，不直接暴露 `window` 函数

### 9.5 入口文件规范

| 文件 | 用途 | 入口配置 |
|------|------|---------|
| `vue.html` | 主窗口入口 | Vite `rollupOptions.input.vue` |
| `floating-vue.html` | 浮窗入口 | Vite `rollupOptions.input.floating` |
| `app.html` | **已废弃** | 仅保留 50 行占位页 |

**vite.config.js 配置**:
```javascript
build: {
  rollupOptions: {
    input: {
      vue: resolve(__dirname, 'vue.html'),      // 主窗口
      floating: resolve(__dirname, 'floating-vue.html'),  // 浮窗
    },
  },
},
define: {
  __API_BASE__: JSON.stringify(production ? 'http://localhost:8080/api/v1' : '/api/v1'),
  __TAURI_MODE__: JSON.stringify(production ? 'tauri' : 'web'),
  __WS_BASE__: JSON.stringify('ws://localhost:8080'),
},
```

### 9.6 事件委托模式（替代 window 暴露）

**旧模式（已废弃）**:
```javascript
// ❌ 禁止：window 暴露函数
window.deletePool = function(poolId) { /* ... */ };
<button onclick="window.deletePool('123')">删除</button>
```

**新模式（推荐）**:
```javascript
// ✅ 推荐：事件委托
document.addEventListener('click', (e) => {
  const btn = e.target.closest('[data-pool-action]');
  if (!btn) return;
  const action = btn.dataset.poolAction;
  const poolId = btn.dataset.poolId;
  switch (action) {
    case 'delete': deletePool(poolId); break;
    case 'confirmDelete': confirmDeletePool(poolId); break;
  }
});
```
```html
<button data-pool-action="delete" data-pool-id="123">删除</button>
```

### 9.7 Tauri IPC 通信规范

| 机制 | 方向 | Vue 3 调用 | Rust 实现 |
|------|------|-----------|----------|
| **Commands/invoke** | 前端 → Rust | `invoke('cmd_name', args)` | `#[tauri::command]` |
| **Events (listen)** | Rust → 前端 | `listen('event_name', cb)` | `emit('event_name', payload)` |
| **Events (emit)** | 前端 → Rust | `emit('event_name', payload)` | `listen('event_name', cb)` |

**Rust Command 示例**:
```rust
#[tauri::command]
fn get_system_status() -> Result<SystemStatus, String> {
    Ok(SystemStatus { /* ... */ })
}
```

**Vue 3 调用**:
```javascript
import { invoke } from '@tauri-apps/api/tauri';
const status = await invoke('get_system_status');
```

### 9.8 窗口管理规范

| 窗口 | 文件 | 用途 | 生命周期 |
|------|------|------|---------|
| 主窗口 | `vue.html` | 应用主界面 | 始终存在 |
| 浮窗 | `floating-vue.html` | 快捷上传/下载 | 按需创建/销毁 |

**窗口配置 (tauri.conf.json)**:
```json
{
  "tauri": {
    "windows": [
      {
        "label": "main",
        "url": "vue.html",
        "title": "Hermes File Manager"
      }
    ]
  }
}
```

### 9.9 构建产物验证

| 产物 | 路径 | 验证方法 |
|------|------|---------|
| Vue 构建 | `web/dist/` | `ls -la web/dist/` |
| Tauri bundle | `src-tauri/target/release/bundle/` | `find . -name "*.app"` |
| 资源嵌入 | `*.app/Contents/resources/` | 应包含 `web/dist/` 内容 |

### 9.10 目录结构规范

```
tools/file_manager/
├── web/                          # Vue 3 SPA (SSOT)
│   ├── src/                      # Vue 组件源码
│   │   ├── views/                # 页面视图
│   │   ├── components/           # 公共组件
│   │   ├── stores/               # Pinia 状态
│   │   ├── services/             # API 服务
│   │   └── platformAdapter.js    # Tauri 平台适配
│   ├── dist/                     # Vite 构建产物 ← SSOT
│   ├── vue.html                  # 主窗口入口 ✅
│   ├── floating-vue.html         # 浮窗入口 ✅
│   ├── app.html                  # 废弃占位页 (50行) ❌
│   └── vite.config.js            # Vite 配置 ✅
│
├── src-tauri/                    # Tauri 壳 (最低维护)
│   ├── src/main.rs              # Rust 入口 ≤200行 ✅
│   ├── tauri.conf.json          # Tauri 配置
│   └── Cargo.toml               # Rust 依赖
│
└── docs/
    └── 2_design/
        ├── domain_table.md       # 本文档
        └── best_practices.md     # Vue 3 + Tauri 最佳实践
```

### 9.11 核心原则

> **Vue 3 + Tauri 集成的核心原则**：
> 1. **SSOT 原则**：web/dist 是唯一构建产物，Tauri 直接使用
> 2. **壳层最小化**：Rust ≤200 行，无业务逻辑
> 3. **接口抽象**：通过 PlatformAdapter 统一访问原生能力
> 4. **事件委托**：使用 data-* 属性，不直接暴露 window 函数
> 5. **构建一次**：前端构建一次，Web 和 Tauri 共用
> 6. **窗口标准化**：vue.html 为主入口，浮窗独立管理

---

## 十、代码质量管理领域 (CODEQUALITY)

### 10.1 核心概念

| 概念 | 英文 | 说明 |
|------|------|------|
| **DRY** | Don't Repeat Yourself | 不要重复自己，每份知识只有一个表示 |
| **冗余控制** | Redundancy Control | 消除重复代码和功能，防止知识分裂 |
| **模块边界** | Module Boundary | 定义模块/组件的职责边界 |
| **代码审查** | Code Review | 代码合并前的人工审查 |
| **冗余整合** | Redundancy Consolidation | 将功能重复的文件/组件合并为一个 |

### 10.2 DRY 原则核心要求

| 要求 | 前端 (Vue) | 后端 (Python) |
|------|-----------|---------------|
| **相同UI模式** | 抽取为公共组件 | - |
| **相同业务逻辑** | 抽取为 composable/hook | 抽取为 service/tool |
| **相同工具函数** | 抽取为 utils | 抽取为 common/utils |
| **相同 API 调用** | 抽取为 api service | 抽取为 client/sdk |
| **相同常量定义** | 抽取为 constants | 抽取为 constants/enums |

### 10.3 前端去重规范 (FE-DEDUP)

#### 10.3.1 组件去重检查清单

```
新组件开发前检查：
□ 是否有相同功能的组件？
□ 是否有相似的组件可以抽象？
□ 是否可以复用现有组件 + props 扩展？

新页面开发前检查：
□ 是否有相同结构的页面？
□ 是否有相似的布局可以抽取为 Layout 组件？
□ 导航结构是否与现有页面重复？
```

#### 10.3.2 组件合并判定规则

| 场景 | 判定 | 处理方式 |
|------|------|---------|
| 功能完全相同 | **合并** | 直接复用现有组件 |
| 功能相似，UI不同 | **抽象** | props 控制 UI 差异 |
| 功能部分重叠 | **扩展** | 扩展现有组件功能 |
| 功能完全不同 | **新建** | 无需复用 |

#### 10.3.3 常见冗余模式与解决

| 冗余模式 | 问题 | 解决 |
|----------|------|------|
| 多个页面都有相同的头部/侧边栏 | 维护成本高 | 使用 Layout 组件统一 |
| 多个组件都有相同的加载状态 | 代码重复 | 统一 Loading 组件 |
| 多个页面都有相同的列表结构 | 样式不一致 | 使用 ListContainer 组件 |
| 多个按钮有相同的确认逻辑 | 行为不一致 | 使用 ConfirmButton 组件 |
| 多个地方有相同的格式逻辑 | 计算结果不一致 | 统一 formatUtils |

### 10.4 后端去重规范 (BE-DEDUP)

#### 10.4.1 服务层去重检查清单

```
新服务开发前检查：
□ 是否有相同功能的服务？
□ 是否有相似的服务可以抽象？
□ 现有服务是否可以扩展？

新 API 开发前检查：
□ 是否有相同的 API endpoint？
□ 是否有相似的逻辑可以复用？
□ 现有 API 是否可以组合？
```

#### 10.4.2 服务合并判定规则

| 场景 | 判定 | 处理方式 |
|------|------|---------|
| 相同数据库操作 | **合并** | 共用同一 service |
| 相同业务逻辑 | **抽取** | 抽取为独立 service |
| 相似业务逻辑 | **抽象** | 使用通用 service + 参数 |
| **功能完全一样** | **直接触发合并** | 开发者自行执行 |
| **功能有差异** | **提交审核** | 提 Issue/MR，由 Maintainer 决策 |

#### 10.4.3 功能合并决策流程

```
发现疑似重复代码
        ↓
    功能是否完全一样？
    ↓yes             ↓no
直接合并         提交审核 (Issue/MR)
    ↓                   ↓
开发者执行       Maintainer 决策
    ↓                   ↓
更新文档          - 接受合并方案
                  - 接受差异化方案
                  - 拒绝（需重构）
```

#### 10.4.4 直接合并判定标准

| 检查项 | 标准 | 说明 |
|--------|------|------|
| 函数签名 | 100% 相同 | 参数类型、返回值完全一致 |
| 功能逻辑 | 100% 相同 | 业务逻辑完全等价 |
| 依赖关系 | 可兼容 | 合并后不影响现有调用 |

#### 10.4.5 提交审核内容

| 内容 | 说明 |
|------|------|
| 现状描述 | 两个相似功能的现状 |
| 差异分析 | 功能差异点列表 |
| 合并提案 | 推荐的合并/差异化方案 |
| 影响评估 | 合并/保留的利弊 |

### 10.5 代码审查检查项

#### 10.5.1 合并前必查

| 检查项 | 说明 | 通过标准 |
|--------|------|---------|
| **重复检测** | 是否有与现有代码重复 | 新代码与已有代码重复率 < 5% |
| **边界清晰** | 模块边界是否清晰 | 无循环依赖 |
| **命名一致** | 命名是否与现有规范一致 | 遵循项目命名规范 |
| **文档更新** | 是否需要更新文档 | API/组件变更需更新文档 |

#### 10.5.2 冗余检测工具

| 工具 | 用途 | 使用场景 |
|------|------|---------|
| ESLint (no-duplicate) | 前端重复代码检测 | `npm run lint` |
| SonarQube | 代码质量综合检测 | CI/CD 集成 |
| DeepSource | 静态分析 + 冗余检测 | GitHub Integration |
| Pylint (duplicate-code) | 后端重复代码检测 | `pylint --disable=all --enable=duplicate-code` |

### 10.6 重构触发条件

| 条件 | 阈值 | 处理 |
|------|------|------|
| **重复代码块** | > 3 处相同逻辑 | 必须重构 |
| **组件相似度** | > 70% 结构相同 | 必须合并 |
| **API 重复** | > 2 个相同 endpoint | 必须合并 |
| **函数过长** | > 100 行 | 建议拆分 |
| **文件过大** | > 500 行 | 建议拆分 |

### 10.7 相关最佳实践

| 编号 | 名称 | 说明 |
|------|------|------|
| **CODE-005** | DRY 原则与代码去重 | 不要重复自己 |
| **CODE-006** | 模块边界定义 | 明确职责边界 |
| **CODE-008** | 备份文件禁止规范 | 禁止 `*_backup/`、`*_old/`、`*-副本/` |
| **CODE-009** | 页面/组件冗余检测与整合 | 冗余检测矩阵、合并决策树 |
| **CODE-010** | 视图层级结构扁平化 | 避免深层嵌套子目录 |
| **FE-014** | 组件/页面去重规范 | 前端去重检查清单 |
| **ARCH-005** | 服务层抽象规范 | 后端服务去重 |

### 10.8 备份文件禁止规范

**问题**: 代码库中存在 `lifecycle_old/`、`models_backup/`、`FileView-Backup.vue` 等备份文件和目录，导致：

| 问题 | 影响 |
|------|------|
| 版本混淆 | 不确定哪个是正式版本 |
| 维护困难 | 修改一处忘记另一处 |
| CI/CD 污染 | 冗余文件进入构建产物 |
| 搜索干扰 | 搜索结果包含多个相似文件 |

**禁止模式**:
```
# 前端禁止
FileView-Backup.vue      # -Backup 后缀
TeamView_old.vue         # _old 后缀
SpaceView-copy.vue       # -copy 后缀

# 后端禁止
lifecycle_old/           # _old 后缀
lifecycle_backup/        # _backup 后缀
models - 副本/           # - 副本 后缀
api_20260503backup.py    # 日期 + backup
```

**正确做法**: 使用 Git 管理历史，而非物理备份文件

```bash
# ✅ 正确：使用 git stash 临时保存
git stash push -m "WIP: 重构 lifecycle"

# ✅ 正确：使用 git branch 保留分支
git branch backup/lifecycle-refactor

# ✅ 正确：使用 git log 查看历史
git log --oneline --all | grep lifecycle
```

**CI/CD 检测**:
```yaml
# .github/workflows/check-no-backup.yml
- name: Check for backup files
  run: |
    BACKUP_FILES=$(find . -type d \( -name "*_old*" -o -name "*_backup*" -o -name "*副本*" \) 2>/dev/null)
    if [ -n "$BACKUP_FILES" ]; then
      echo "❌ 发现备份文件: $BACKUP_FILES"
      exit 1
    fi
```

---

## 十一、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **1.8** | **2026-05-05** | **CODE-008 备份文件禁止规范**: 10.7新增CODE-008引用、10.8新增「备份文件禁止规范」章节，禁止 `*_backup/`、`*_old/`、`*-副本/` 目录，使用Git管理历史 |
| **1.7** | **2026-05-05** | **页面冗余整合**: 新增第十一章「代码冗余检测与功能整合」，覆盖冗余类型分类、检测方法、整合原则；前端去重规范 (FE-DEDUP)、后端去重规范 (BE-DEDUP) |
| **1.7** | **2026-05-05** | **新增合并决策规则**: 功能完全一样直接触发合并，功能有差异提交审核；10.4.3决策流程、10.4.4判定标准、10.4.5审核内容 |
| **1.6** | **2026-05-05** | **新增领域16**: CODEQUALITY (代码质量管理)，DRY原则、前后端去重规范、代码审查检查项、重构触发条件 |
| **1.5** | **2026-05-05** | **新增章节九**: VUETAURI (Vue 3 + Tauri 集成领域规范)，包含层级架构、G1-G8目标映射、PlatformAdapter模式、入口文件规范、事件委托模式、Tauri IPC规范、窗口管理规范 |
| 1.4 | 2026-05-03 | **新增章节**：RESOURCE & CAPACITY MANAGEMENT (资源配额管理体系)，三级空间模型、承诺制/预留制、配额管理仪表盘 |
| 1.3 | 2026-05-03 | **新增领域**：AUTH (身份认证与会话管理)，Remember Me 最佳实践 |
| 1.2 | 2026-05-03 | **新增领域**：HYBRID (跨平台混合应用)，Web/Tauri 共用 UI 源码架构 |
| 1.1 | 2026-05-03 | **新增领域**：GUIDANCE (用户引导)、REQMGT (需求管理)、TEST (软件测试) |
| 1.0 | 2026-05-03 | 初始版本：领域分析表 |
---

## 十一、代码冗余检测与功能整合

> **领域代码**: DRY (Don't Repeat Yourself)
> **版本**: v1.0
> **更新日期**: 2026-05-05

### 11.1 问题定义

代码冗余是指相同或相似的代码逻辑在多个地方重复出现，导致：
- **维护成本增加**：修改一处需同步多处
- **一致性风险**：相似功能可能表现不一致
- **代码膨胀**：冗余代码占据大量空间

### 11.2 冗余类型分类

| 类型 | 描述 | 示例 |
|------|------|------|
| **完全重复** | 相同代码完全复制 | 同一个函数复制粘贴到多个文件 |
| **结构相似** | 代码结构相同，细节不同 | 多个组件渲染相似列表 |
| **功能重叠** | 不同模块实现相同功能 | `getUserInfo()` 和 `fetchUserData()` |
| **职责扩散** | 单一职责被分散到多处 | 用户验证逻辑散落在多个服务 |

### 11.3 检测方法

| 方法 | 工具 | 说明 |
|------|------|------|
| **代码审查** | GitHub PR Review | 人工检测冗余模式 |
| **静态分析** | ESLint (no-duplicate), SonarQube | 自动检测重复代码 |
| **复杂度分析** | Code Climate, COCOMO | 识别过度复杂的模块 |
| **依赖分析** | dependency-cruiser | 分析模块依赖关系 |

### 11.4 整合原则

| 原则 | 描述 | 应用场景 |
|------|------|---------|
| **DRY** | Don't Repeat Yourself | 消除重复逻辑 |
| **KISS** | Keep It Simple, Stupid | 避免过度设计 |
| **YAGNI** | You Aren't Gonna Need It | 不做过早抽象 |
| **SRP** | Single Responsibility Principle | 单一职责 |

### 11.5 前端 Vue 整合规范

**整合策略**:
| 冗余类型 | 整合方式 | 示例 |
|----------|---------|------|
| 相似组件 | 抽象公共组件 | `FileListItem` → `FileCard` |
| 重复逻辑 | 提取 Composable | 多组件文件操作 → `useFileOperations()` |
| 相似页面 | 路由参数化 | `/teams/:id` 替代 `/team-a`, `/team-b` |
| 重复 API 调用 | 统一 Service 层 | 各组件直接调用 → `fileService` 封装 |

**组件合并检查表**:
```
[ ] 多个组件渲染相同的 UI 结构？
[ ] 多个组件使用相同的 API 调用？
[ ] 多个组件有相似的状态管理逻辑？
[ ] 组件间是否有大量 props 传递？
```

### 11.6 后端 Python 整合规范

**整合策略**:
| 冗余类型 | 整合方式 | 示例 |
|----------|---------|------|
| 重复业务逻辑 | 提取 Service 层 | 多 endpoint 调用相同逻辑 → `user_service.py` |
| 相似数据模型 | 统一 Model 定义 | 多个文件定义相似 Schema → `engine/models.py` |
| 重复验证逻辑 | 中间件/装饰器 | 各 endpoint 重复验证 → `@require_auth` 装饰器 |
| 相似 API 端点 | RESTful 资源重构 | `/getTeam`, `/getTeamInfo` → `/teams/{id}` |

**服务合并检查表**:
```
[ ] 多个 service 文件处理相同的领域实体？
[ ] 多个 endpoint 调用相同的底层函数？
[ ] 多个文件定义了相似的数据模型？
[ ] 是否有不必要的继承层次？
```

### 11.7 整合流程

```
1. 识别冗余 (Detection)
   - 代码审查发现重复模式
   - 静态分析工具标记相似代码
   
2. 评估影响 (Assessment)
   - 分析冗余代码的使用范围
   - 评估整合风险和依赖关系
   
3. 设计方案 (Design)
   - 确定合并后的接口/组件
   - 制定迁移策略（渐进式 vs 一次性）
   
4. 实施整合 (Implementation)
   - 创建新的公共模块
   - 更新调用方引用
   - 确保向后兼容
   
5. 验证测试 (Verification)
   - 运行现有测试
   - 补充新测试用例
   - 确认功能一致
```

### 11.8 相关标准

| 标准 | 说明 |
|------|------|
| **SOLID** | 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置 |
| **DRY** | Don't Repeat Yourself |
| ** AHA** | Avoid Hasty Abstractions |
| **Code Review Checklist** | 冗余检测清单 |

### 11.9 代码审查标准

**冗余检测审查点**:
```
前端审查:
[ ] 是否有相似的 Vue 组件可以合并？
[ ] 是否有重复的 composable 逻辑？
[ ] 是否有冗余的 API 服务封装？
[ ] 组件 props 是否过于复杂？

后端审查:
[ ] 是否有重复的业务逻辑？
[ ] 是否有相似的 API 端点可以合并？
[ ] 是否有冗余的数据模型定义？
[ ] 是否有重复的验证逻辑？
```

---

## 十二、服务/组件粒度设计

> **领域代码**: GRANULARITY
> **版本**: v1.0
> **更新日期**: 2026-05-05

### 12.1 粒度原则

| 原则 | 描述 | 过度表现 |
|------|------|---------|
| **内聚性** | 相关功能放一起 | 单个文件过大/过小 |
| **正交性** | 功能不重叠 | 相似功能重复实现 |
| **封装性** | 内部实现隐藏 | 暴露过多细节 |

### 12.2 前端组件粒度

| 粒度级别 | 组件类型 | 职责 | 示例 |
|----------|---------|------|------|
| **原子** | Button, Icon, Input | 基础 UI 元素 | `BaseButton.vue` |
| **分子** | FileCard, UserAvatar | 组合 UI 单元 | `FileCard.vue` |
| **有机** | FileList, TeamPanel | 功能模块 | `FileList.vue` |
| **模板** | PageLayout, ModalContainer | 页面结构 | `MainLayout.vue` |

### 12.3 后端服务粒度

| 粒度级别 | 服务类型 | 职责 | 示例 |
|----------|---------|------|------|
| **基础设施** | 工具函数 | 通用计算/转换 | `utils/format.py` |
| **领域服务** | 业务逻辑 | 领域操作 | `auth_service.py` |
| **聚合服务** | 跨领域协调 | 多领域组合 | `workspace_service.py` |
| **门面服务** | API 入口 | 路由分发 | FastAPI Router |

### 12.4 粒度检测清单

```
粒度过粗（需要拆分）:
[ ] 单个文件超过 500 行
[ ] 单个函数超过 100 行
[ ] 单个 service 处理多个领域
[ ] 单个组件有超过 10 个 props

粒度过细（需要合并）:
[ ] 每个小函数都单独文件
[ ] 相似组件仅细节不同
[ ] 微小服务间强依赖
[ ] 过度抽象导致调用层级过深
```

### 12.5 重构时机

| 时机 | 触发条件 | 重构方式 |
|------|---------|---------|
| **检测到冗余** | 相似代码出现 2 次以上 | 提取公共模块 |
| **职责扩散** | 单个模块处理多个领域 | 分离职责 |
| **过度设计** | 抽象层数超过 5 层 | 简化层次 |
| **性能问题** | 过细粒度导致调用开销 | 合并服务 |
