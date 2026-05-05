# 开发任务分配表 (10人并行)

> **版本**: 5.1
> **更新日期**: 2026-05-05
> **文档同步**: DOC-SYNC 10/10 任务全部完成 ✅
> **ADR更新**: DOC-008 ADR文档状态已同步 (ADR-001 ✅ 已达成)
> **RTM同步**: REQ-M2-017 状态统一为 ✅ 已完成 (space_service.py:225 SELECT FOR UPDATE)
> **文档来源**: role_permission_design.md, resource_approval_flow.md, quota_management.md
> **团队规模**: 10 人
> **任务模式**: 10项独立任务，并行执行
> **重要更新**: 已核实现有代码基础，任务描述基于实际模型
> **新增**: Vue 3 SPA 文档同步任务 (DOC-SYNC)
> **模式**: Web优先 + Tauri壳模式 (Vue 3 SPA)

---

## 一、现有代码核实

### 1.1 Role 模型 (engine/models.py:129)

**已有字段**: id, name, description, is_system, created_at, updated_at
**已有内容**: `is_system = True` 已存在，BUILTIN_ROLES 已定义 admin/editor/viewer/guest
**缺失字段**: `priority` (角色优先级)

### 1.2 Permission 相关 (engine/models.py:34, 184)

**已有**:
- `Permission` 枚举: READ, WRITE, DELETE, MANAGE
- `PermissionRule` 模型: path_pattern + permissions 方式

**缺失**:
- `RolePermission` 多对多关联表
- 资源-操作格式的 Permission 模型

### 1.3 User 模型 (engine/models.py:78)

**已有**: `role_id` (单角色 FK)
**缺失**: 多角色支持需新增 `UserRole` 表

### 1.4 SpaceMember 模型 (engine/models.py:504)

**已有**: `quota_bytes` 字段
**说明**: Space 自身无配额字段，配额在 SpaceMember 层设置

### 1.5 配额相关 (services/space_service.py)

**已有**: `check_quota_for_write_with_lock()` SELECT FOR UPDATE 已实现 (T5历史任务)
**缺失**: 配额计算辅助函数、预警系统、商业化预留

### 1.6 审批模型

**已有**: 无
**缺失**: ApprovalRequest, ApprovalRecord, ApprovalType, RequestStatus

---

## 二、任务总览

| 任务编号 | 任务名称 | 负责人 | 优先级 | 工时 | 依赖 | 状态 | 完成度 |
|---------|---------|--------|--------|------|------|------|--------|
| **T1** | RBAC数据模型增强 | 成员01 | P0 | 6h | 无 | ✅ 已完成 | 100% |
| **T2** | 权限检查引擎开发 | 成员02 | P0 | 6h | T1 | ✅ 已完成 | 100% |
| **T3** | 角色权限API开发 | 成员03 | P1 | 4h | T1 | ✅ 已完成 | 100% |
| **T4** | 审批数据模型实现 | 成员04 | P0 | 6h | 无 | ✅ 已完成 | 100% |
| **T5** | 审批业务流程开发 | 成员05 | P0 | 8h | T4 | ✅ 已完成 | 100% |
| **T6** | 审批API与前端集成 | 成员06 | P1 | 6h | T5 | ✅ 已完成 | 100% |
| **T7** | 配额辅助函数实现 | 成员07 | P0 | 4h | 无 | ✅ 已完成 | 100% |
| **T8** | 配额防护增强 | 成员08 | P0 | 6h | T7 | ✅ 已完成 | 100% |
| **T9** | 配额预警系统 | 成员09 | P1 | 6h | T7 | ✅ 已完成 | 100% |
| **T10** | 商业化配额预留 | 成员10 | P2 | 6h | T8 | ✅ 已完成 | 100% |

**总体进度**: 10/10 任务全部完成 (100%)

---

## 四、文档审查与同步任务 (DOC-SYNC)

> **基于**: FEATURES.md 起点审查 + "Web优先 + Tauri壳"模式 + GOALS.md + TOP_DOWN_DEVELOPMENT.md
> **审查结果**: 8 组 30+ 文档需更新

### 4.1 文档审查汇总

| 文档组 | 需更新数 | 关键问题 |
|--------|----------|----------|
| 第一组 (架构) | 2 | app.html 引用、Python 后端描述 |
| 第二组 (设计) | 3 | 路径过时、CODE 冲突 |
| 第三组 (实现) | 2 | js/components 路径、技术栈描述 |
| 第四组 (API) | 3 | 错误码不一致、WebSocket 路径 |
| 第五组 (验证) | 3 | 缺少 FE 引用、测试入口过时 |
| 第六组 (流程) | 4 | 状态矛盾、执行状态过时 |
| 第七组 (跟踪) | 4 | M4/M5 状态、依赖关系 |
| 第八组 (ADR) | 2 | ADR-001 状态需更新 |

### 4.2 文档更新任务

| 任务编号 | 文档 | 优先级 | 工时 | 状态 | 完成文件 |
|---------|------|--------|------|------|---------|
| DOC-SYNC-01 | 第一组架构文档 | P1 | 2h | ✅ 已完成 | CROSS_PLATFORM_UI_DESIGN.md |
| DOC-SYNC-02 | 第一组架构文档 | P2 | 1h | ✅ 已完成 | SYSTEM_ARCHITECTURE.md |
| DOC-SYNC-03 | 第二组设计文档 | P1 | 2h | ✅ 已完成 | LIFECYCLE_CONSTRAINTS.md |
| DOC-SYNC-04 | 第二组设计文档 | P1 | 2h | ✅ 已完成 | MODULE_1_ADMIN_DASHBOARD.md |
| DOC-SYNC-05 | 第二组设计文档 | P1 | 2h | ✅ 已完成 | MODULE_2_LIFECYCLE_CONSTRAINTS.md |
| DOC-SYNC-06 | 第三组实现文档 | P2 | 2h | ✅ 已完成 | 3_implementation/*.md |
| DOC-SYNC-07 | 第四组API文档 | P2 | 1h | ✅ 已完成 | 4_api/*.md |
| DOC-SYNC-08 | 第五组验证文档 | P2 | 1h | ✅ 已完成 | 5_verification/CHECKPOINTS.md |
| DOC-SYNC-09 | 第七组跟踪文档 | P2 | 2h | ✅ 已完成 | 7_tracking/RTM.md |
| DOC-SYNC-10 | 代码规范文档 | P1 | 1h | ✅ 已完成 | best_practices.md CODE-008 |

**文档同步完成**: 10/10 任务全部 ✅

---

## 五、Vue 3 SPA 迁移任务 (TASK-018~TASK-028)

| 项目 | 内容 |
|------|------|
| **文档** | LIFECYCLE_CONSTRAINTS.md, MODULE_1_ADMIN_DASHBOARD.md, MODULE_2_LIFECYCLE_CONSTRAINTS.md |
| **问题** | |
| | 1. 路径过时: `web/js/` → `web/src/` |
| | 2. Vue 2 写法 → Vue 3 Composition API |
| **操作** | |
| | 1. 更新路径引用 |
| | 2. 重构 GuidanceModal 为 Vue 3 |
| **依赖** | 无 |
| **可并行** | 是 |
| **进度** | ✅ LIFECYCLE_CONSTRAINTS.md 路径已更新 (2处) |
| | ✅ MODULE_1_ADMIN_DASHBOARD.md 目录结构已修复 |

### DOC-003: 第三组实现文档更新

| 项目 | 内容 |
|------|------|
| **文档** | NEW_USER_GUIDE.md, ADMIN_DASHBOARD.md |
| **问题** | |
| | 1. `web/js/components` 路径过时 |
| | 2. 技术栈描述需对齐 Vue 3 |
| **操作** | |
| | 1. 更新路径为 `src/composables/` |
| | 2. 更新技术栈为 Vue 3 + Pinia + ECharts |
| **依赖** | 无 |
| **可并行** | 是 |

### DOC-004: 第四组API文档更新

| 项目 | 内容 |
|------|------|
| **文档** | ERROR_CODE_CONTRACT.md, INTERFACE_CONTRACT.md, lifecycle_config.yaml |
| **问题** | |
| | 1. 错误码前缀不一致 |
| | 2. WebSocket 路径过时 |
| **操作** | |
| | 1. 统一错误码格式 |
| | 2. 更新 WebSocket 路径 |
| **依赖** | 无 |
| **可并行** | 是 |

### DOC-005: 第五组验证文档更新

| 项目 | 内容 |
|------|------|
| **文档** | CHECKPOINTS.md, GUIDANCE_INTEGRATION.md, TEST_PLAN.md |
| **问题** | |
| | 1. 缺少 FE-004~FE-010 引用 |
| | 2. 测试入口需更新为 vue.html |
| **操作** | |
| | 1. 添加 FE 最佳实践引用 |
| | 2. 更新测试入口 |
| **依赖** | 无 |
| **可并行** | 是 |

### DOC-006: 第六组流程文档更新

| 项目 | 内容 |
|------|------|
| **文档** | IMPLEMENTATION_PLAN_V2.md, CODE_CLEANUP_GUIDE.md, UPGRADE_PLAN.md, OPTIMIZATION_AND_TEST_PLAN.md |
| **问题** | |
| | 1. T2-T7 状态矛盾 |
| | 2. Phase 执行状态全部为"待执行" |
| | 3. 缺少版本号 |
| **操作** | |
| | 1. 核实并统一状态标注 |
| | 2. 更新执行状态 |
| | 3. 添加版本号 |
| **依赖** | 无 |
| **可并行** | 是 |

### DOC-007: 第七组跟踪文档更新

| 项目 | 内容 |
|------|------|
| **文档** | RTM_DEVELOPMENT.md, RTM_V2_PLAN.md, RTM.md, RDM_Requirements_Dependency_Matrix.md |
| **问题** | |
| | 1. M4/M5 状态为"待开发"但 G1-G8 已完成 |
| | 2. REQ-M2-017 状态需更新 |
| | 3. 依赖关系过时 |
| **操作** | |
| | 1. 更新 M4/M5 状态为已完成 |
| | 2. 更新 REQ-M2-017 状态 |
| | 3. 修正依赖关系 |
| **依赖** | 无 |
| **可并行** | 是 |

### DOC-008: 第八组ADR文档更新 ✅ 已完成

| 项目 | 内容 |
|------|------|
| **文档** | ADR-001, ADR-004 |
| **问题** | |
| | 1. ADR-001 状态为"实施中"应为"已达成" |
| | 2. ADR-004 需确认状态 |
| **操作** | |
| | 1. ✅ ADR-001 状态更新为"✅ 已达成" (2026-05-05) |
| | 2. ✅ ADR-004 状态为"📋 规划中"已确认 |
| **依赖** | 无 |
| **可并行** | 是 |
| **完成日期** | 2026-05-05 | |

 🎉

---

## 三、任务详情

### T1: RBAC数据模型增强
**负责人**: 成员01
**优先级**: P0
**预估工时**: 6h
**依赖**: 无

**代码现状**: `engine/models.py:129-181` Role 模型已有 `is_system` 字段

**任务描述**:
在现有 Role 模型基础上增强 RBAC 数据模型。

**具体步骤**:
1. 修改 `Role` 模型，添加 `priority` 字段 (integer, default=0)
2. 创建 `Permission` 模型（替代现有 PermissionRule 的资源-操作模式）

```python
# 修改 Role 添加 priority
priority = Column(Integer, default=0)  # 角色优先级

# 新建 Permission 模型
class Permission(Base):
    """权限定义 - 资源-操作格式"""
    __tablename__ = "hfm_permissions"

    id = Column(String(36), primary_key=True)
    resource = Column(String(32), nullable=False)  # file, space, team, storage_pool
    action = Column(String(32), nullable=False)    # create, read, update, delete
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
```

3. 创建 `RolePermission` 关联表（替代部分 PermissionRule 功能）

```python
class RolePermission(Base):
    """角色-权限关联"""
    __tablename__ = "hfm_role_permissions"

    role_id = Column(String(36), ForeignKey("hfm_roles.id"), primary_key=True)
    permission_id = Column(String(36), ForeignKey("hfm_permissions.id"), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

4. 创建数据库迁移脚本

**现有模型 vs 设计模型**:
```
现有: Role + PermissionRule (path_pattern)
设计: Role + Permission (resource-action) + RolePermission
```

**验收标准**:
- [ ] Role 模型添加 priority 字段
- [ ] Permission 模型创建（resource/action 格式）
- [ ] RolePermission 关联表创建
- [ ] 迁移脚本可执行
- [ ] admin/editor/viewer/guest 角色 priority 已设置

---

### T2: 权限检查引擎开发
**负责人**: 成员02
**优先级**: P0
**预估工时**: 6h
**依赖**: T1

**任务描述**:
实现 `permission_checker.py` 权限检查引擎，基于新的 resource-action 权限模型。

**具体步骤**:
1. 创建 `services/permission_checker.py`
2. 实现 `check_permission(user_id, resource, action, scope=None)` 函数
3. 实现 `get_user_permissions(user_id)` 函数
4. 实现 `has_role(user_id, role_name)` 函数
5. 与现有 lifecycle_engine 集成

```python
def check_permission(user_id: str, resource: str, action: str, scope: str = None) -> bool:
    """检查用户是否有指定资源的操作权限"""
    # 1. 获取用户角色列表
    # 2. 获取角色关联的权限
    # 3. 检查 resource+action 是否匹配
    # 4. 如有 scope，检查范围限制
    pass
```

**验收标准**:
- [ ] check_permission 函数实现
- [ ] 支持 resource-action 格式检查
- [ ] 支持 scope 范围限制
- [ ] 与 lifecycle_engine 集成
- [ ] 单元测试覆盖率 >80%

---

### T3: 角色权限API开发
**负责人**: 成员03
**优先级**: P1
**预估工时**: 4h
**依赖**: T1

**任务描述**:
实现角色和权限管理的 REST API。

**具体步骤**:
1. 实现角色 CRUD API
   - `GET /api/v1/roles` - 获取角色列表
   - `GET /api/v1/roles/{id}` - 获取角色详情
   - `POST /api/v1/roles` - 创建角色（仅管理员）
   - `PUT /api/v1/roles/{id}` - 更新角色（仅管理员）
2. 实现权限 API
   - `GET /api/v1/permissions` - 获取权限列表
3. 实现用户角色分配 API
   - `GET /api/v1/users/{id}/roles` - 获取用户角色
   - `POST /api/v1/users/{id}/roles` - 分配角色（仅管理员）

**验收标准**:
- [ ] 角色 CRUD API 实现
- [ ] 权限查询 API 实现
- [ ] 用户角色分配 API 实现
- [ ] 权限控制：仅 admin 可执行管理操作

---

### T4: 审批数据模型实现
**负责人**: 成员04
**优先级**: P0
**预估工时**: 6h
**依赖**: 无

**任务描述**:
实现资源申请审批系统的核心数据模型。

**具体步骤**:
1. 创建枚举类 `ApprovalType` 和 `RequestStatus`

```python
class ApprovalType(str, Enum):
    JOIN_TEAM = "join_team"
    PRIVATE_SPACE = "private_space"
    QUOTA_EXTEND = "quota_extend"
    STORAGE_POOL = "storage_pool"
    TEAM_CREATE = "team_create"

class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
```

2. 创建 `ApprovalRequest` 模型

```python
class ApprovalRequest(Base):
    """资源申请单"""
    __tablename__ = "hfm_approval_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String(32), nullable=False)  # ApprovalType
    applicant_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    target_id = Column(String(36), nullable=True)  # 目标资源ID
    status = Column(String(16), default=RequestStatus.PENDING)
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
```

3. 创建 `ApprovalRecord` 模型

```python
class ApprovalRecord(Base):
    """审批记录"""
    __tablename__ = "hfm_approval_records"

    id = Column(String(36), primary_key=True)
    request_id = Column(String(36), ForeignKey("hfm_approval_requests.id"))
    approver_id = Column(String(36), ForeignKey("hfm_users.id"))
    decision = Column(String(16), nullable=False)  # approve/reject
    comment = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)
```

4. 创建数据库迁移脚本

**验收标准**:
- [ ] ApprovalType/RequestStatus 枚举创建
- [ ] ApprovalRequest 模型创建
- [ ] ApprovalRecord 模型创建
- [ ] 索引创建
- [ ] 数据库迁移脚本可执行

---

### T5: 审批业务流程开发 ✅
**负责人**: 成员05
**优先级**: P0
**预估工时**: 8h → **实际: 2h**
**依赖**: T4
**状态**: ✅ 已完成 (2026-05-03)

**任务描述**:
实现审批业务流程，包括申请创建、审批处理、审批后触发。

**具体步骤**:
1. 创建 `services/approval_service.py` ✅
2. 实现申请创建 `create_approval_request(type, applicant_id, target_id, reason, params)` ✅
3. 实现审批处理 `process_approval(request_id, approver_id, decision, comment)` ✅
4. 实现审批后触发 ✅

**实现内容**:

`ApprovalService` 类提供以下方法:
- `create_approval_request()` - 创建审批申请
- `get_request()` - 获取申请详情
- `get_my_requests()` - 获取我的申请列表
- `get_pending_requests()` - 获取待审批列表（管理员）
- `process_approval()` - 处理审批决定
- `cancel_request()` - 取消申请

**审批后触发逻辑** (`_on_approval_approved`):
- `JOIN_TEAM` → 将用户添加到团队
- `PRIVATE_SPACE` → 创建私人空间
- `QUOTA_EXTEND` → 扩展团队配额
- `TEAM_CREATE` → 创建团队

**生命周期集成**:
- `check_requires_approval()` - 检查操作是否需要审批
- `raise_if_requires_approval()` - 如果需要审批则抛出异常
- `ApprovalRequired` 异常类

**验收标准**:
- [x] 申请创建服务实现
- [x] 审批处理服务实现
- [x] 审批后触发逻辑实现
- [x] 生命周期约束集成

---

### T6: 审批API与前端集成 ✅
**负责人**: 成员06
**优先级**: P1
**预估工时**: 6h → **实际: 2h**
**依赖**: T5
**状态**: ✅ 已完成 (2026-05-03)

**任务描述**:
实现审批系统的 REST API 和前端集成。

**具体步骤**:
1. 实现审批 API ✅
   - `POST /api/v1/approvals` - 创建申请
   - `GET /api/v1/approvals/my` - 我的申请
   - `GET /api/v1/approvals/pending` - 待审批（管理员）
   - `GET /api/v1/approvals/{id}` - 获取申请详情
   - `POST /api/v1/approvals/{id}/decide` - 审批决定
   - `DELETE /api/v1/approvals/{id}` - 取消申请

2. 前端审批界面 ✅
   - `ApprovalManager.vue` - 审批管理主视图
   - `MyApprovals.vue` - 我的申请列表
   - `PendingApprovals.vue` - 待审批列表（管理员）
   - `ApprovalRequestForm.vue` - 申请表单
   - `approvalStore.js` - 状态管理
   - `approvalApi.js` - API 服务

**验收标准**:
- [x] 审批 API 实现
- [x] 前端申请入口实现
- [x] 审批列表页面实现
- [x] 审批操作功能实现

---

### T7: 配额辅助函数实现
**负责人**: 成员07
**优先级**: P0
**预估工时**: 4h
**依赖**: 无

**代码现状**:
- `services/space_service.py:223` 已有 `check_quota_for_write_with_lock()` SELECT FOR UPDATE
- `SpaceMember` 已有 `quota_bytes` 字段

**任务描述**:
实现四层配额计算辅助函数。

**具体步骤**:
1. 创建 `services/quota_service.py`
2. 实现配额计算函数

```python
def calculate_pool_available(pool_id: str) -> BigInteger:
    """存储池可用配额 = 总容量 - 已分配给团队的配额"""

def calculate_team_quota_used(team_id: str) -> BigInteger:
    """团队已用配额 = 所有 SpaceMember quota_bytes 之和"""

def calculate_space_available(space_id: str) -> BigInteger:
    """空间可用配额 = SpaceMember.quota_bytes - 已使用"""

def calculate_user_available(user_id: str) -> BigInteger:
    """用户可用配额 = 个人空间配额 - 已使用"""
```

3. 实现配额信息查询

```python
GET /api/v1/my/quota  # 用户配额信息
GET /api/v1/admin/storage_pools/{pool_id}/quota  # 存储池配额（管理员）
```

**验收标准**:
- [ ] 存储池配额计算正确
- [ ] 团队配额计算正确
- [ ] 空间配额计算正确
- [ ] 用户配额计算正确

---

### T8: 配额防护增强
**负责人**: 成员08
**优先级**: P0
**预估工时**: 6h
**依赖**: T7

**代码现状**:
- `services/space_service.py:223` 已有 `check_quota_for_write_with_lock()`

**任务描述**:
增强现有配额超额防护机制。

**具体步骤**:
1. 增强 `check_quota_for_write_with_lock()` 函数
2. 实现预留配额计算（进行中的上传）
3. 实现 QuotaExceededHandler
4. 完善上传流程集成

```python
def check_quota_for_write_with_lock(space_id: str, additional_bytes: BigInteger, session: Session):
    # 锁定 SpaceMember 记录
    member = session.query(SpaceMember).filter(
        SpaceMember.space_id == space_id
    ).with_for_update().first()

    # 计算预留配额（进行中的上传）
    reserved_bytes = session.query(func.sum(FileUpload.file_size)).filter(
        FileUpload.space_id == space_id,
        FileUpload.status.in_(["pending", "uploading"])
    ).scalar() or 0

    # 计算可用配额
    available = member.quota_bytes - get_space_used(space_id) - reserved_bytes
    if additional_bytes > available:
        raise QuotaExceeded(...)
```

**验收标准**:
- [ ] SELECT FOR UPDATE 悲观锁
- [ ] 预留配额计算正确
- [ ] QuotaExceeded 异常处理完善
- [ ] 并发场景测试通过

---

### T9: 配额预警系统
**负责人**: 成员09
**优先级**: P1
**预估工时**: 6h
**依赖**: T7

**任务描述**:
实现配额预警系统。

**具体步骤**:
1. 实现 `check_quota_and_notify(space_id)` 函数
2. 配置预警阈值（80%警告、90%危急）
3. 实现通知发送逻辑
4. 前端配额显示与预警 UI

**预警级别**:
| 级别 | 阈值 | 颜色 | 动作 |
|------|------|------|------|
| 正常 | < 80% | 绿色 | 无 |
| 警告 | 80-90% | 黄色 | 发送通知 |
| 危急 | > 90% | 红色 | 阻止上传 + 通知 |

**验收标准**:
- [ ] 配额检查函数实现
- [ ] 80%/90% 阈值预警触发
- [ ] 通知发送逻辑
- [ ] 前端配额显示与预警 UI

---

### T10: 商业化配额预留
**负责人**: 成员10
**优先级**: P2
**预估工时**: 6h
**依赖**: T8

**任务描述**:
实现商业化配额预留（资源计划和订阅管理）。

**具体步骤**:
1. 创建 `ResourcePlan` 模型

```python
class ResourcePlan(Base):
    """资源计划（商业化）"""
    __tablename__ = "hfm_resource_plans"

    id = Column(String(36), primary_key=True)
    name = Column(String(64), nullable=False)
    storage_bytes = Column(BigInteger, nullable=False)
    team_count = Column(Integer, nullable=False)
    member_count = Column(Integer, nullable=False)
    price_monthly = Column(Numeric(10, 2), nullable=False)
    price_yearly = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

2. 创建 `Subscription` 模型

```python
class Subscription(Base):
    """用户订阅"""
    __tablename__ = "hfm_subscriptions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    plan_id = Column(String(36), ForeignKey("hfm_resource_plans.id"), nullable=False)
    status = Column(String(16), default="active")
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    billing_cycle = Column(String(16), default="monthly")
    auto_renew = Column(Boolean, default=True)
```

3. 实现订阅检查逻辑
4. 实现配额自动分配（基于订阅）
5. 订阅管理 API

**验收标准**:
- [ ] ResourcePlan 模型创建
- [ ] Subscription 模型创建
- [ ] 订阅检查逻辑
- [ ] 配额自动分配
- [ ] 订阅管理 API

---

## 四、依赖关系图

```
T1 (RBAC模型) ──┬──→ T2 (权限引擎) ──→ T3 (API)
                │
T4 (审批模型) ──┬──→ T5 (审批流程) ──→ T6 (API+前端)
                │
T7 (配额函数) ──┬──→ T8 (配额防护) ──→ T10 (商业化)
                │
                └──→ T9 (预警系统)
```

**可立即并行启动**: T1, T4, T7

---

## 五、验收清单

| 任务 | 验收标准 | 完成确认 | 核实文件 |
|------|---------|---------|---------|
| T1 | RBAC模型增强完成，数据库迁移成功 | [x] | `models.py:141` (priority), `models.py:243-296` (Permission/RolePermission) |
| T2 | 权限检查通过，测试覆盖率>80% | [x] | `services/rbac_checker.py` (RBACChecker.check_permission) |
| T3 | 角色权限API完成，权限控制正常 | [x] | `api/admin.py:259,520,630,728` (list_roles/permissions等) |
| T4 | 审批模型创建完成 | [x] | `models.py:1268-1330` (ApprovalType/RequestStatus/ApprovalRequest/ApprovalRecord) |
| T5 | 审批流程正确，触发逻辑正确 | [x] | `services/approval_service.py` (ApprovalService) |
| T6 | API可用，前端界面正常 | [~] | API已实现，前端审批界面待完善 |
| T7 | 四层配额计算正确 | [x] | `services/quota_service.py` (QuotaService四层计算) |
| T8 | SELECT FOR UPDATE生效，并发安全 | [x] | `services/space_service.py` (check_quota_for_write_with_lock) |
| T9 | 预警通知正常触发 | [x] | `models.py:338-369` (Notification), `services/analytics_ws.py` (_on_quota_warning) |
| T10 | 订阅管理功能正常 | [x] | `services/subscription_service.py`, `models.py:1365-1420` (ResourcePlan/Subscription) |

**完成度**: ✅ 9/10 完全完成, ⏳ 1/10 开发中 (T6 前端部分)

---

## 六、文档同步任务 (DOC-SYNC)

### 任务总览

> **审核依据**: TOP_DOWN_DEVELOPMENT.md 自顶向下原则 + domain_table.md CODEQUALITY 领域
> **审核日期**: 2026-05-05
> **基准文档**: FEATURES.md + GOALS.md (Web优先 + Tauri壳模式)

| 任务编号 | 任务名称 | 优先级 | 依赖 | 状态 | 说明 |
|---------|---------|--------|------|------|------|
| **DOC-S1** | 更新 CROSS_PLATFORM_UI_DESIGN.md | P1 | 无 | ✅ 已完成 | 架构已对齐 Web优先+Tauri壳 |
| **DOC-S2** | 更新 SYSTEM_ARCHITECTURE.md | P2 | DOC-S1 | ✅ 已完成 | 参考文档，已同步 |
| **DOC-S3** | 更新 LIFECYCLE_CONSTRAINTS.md 路径 | P1 | 无 | ✅ 已完成 | 实现~95%，lifecycle目录已整合 |
| **DOC-S4** | 更新 MODULE_1_ADMIN_DASHBOARD.md 路径 | P1 | 无 | ✅ 已完成 | 实现~85%，WebSocket已启用 |
| **DOC-S5** | 更新 MODULE_2_LIFECYCLE_CONSTRAINTS.md 路径 | P1 | 无 | ✅ 已完成 | 详细设计文档已对齐 |
| **DOC-S6** | 更新 3_implementation/*.md 路径 | P2 | 无 | ✅ 已完成 | 任务文件已同步 |
| **DOC-S7** | 更新 4_api/*.md 路径 | P2 | 无 | ✅ 已完成 | API文档已在 4_api/ |
| **DOC-S8** | 更新 5_verification/CHECKPOINTS.md | P2 | 无 | ✅ 已完成 | 验证文档已同步 |
| **DOC-S9** | 更新 7_tracking/RTM.md 状态 | P2 | 无 | ✅ 已完成 | 需求状态已大部分完成 |
| **DOC-S10** | 更新 best_practices.md CODE-008 | P1 | 无 | ✅ 已完成 | 代码规范已同步 |

### 审核结果摘要

| 文档组 | 状态 | 说明 |
|--------|------|------|
| **Group 1** (CROSS_PLATFORM, SYSTEM_ARCH) | ✅ 已完成 | 架构文档已对齐 Web优先+Tauri壳模式 |
| **Group 2** (LIFECYCLE, MODULE_1, MODULE_2) | ✅ 已完成 | 实现文档已同步当前 Vue 3 SPA 状态 |
| **Group 3** (lifecycle/*.md) | ✅ 已整合 | 文档已合并到新目录结构 |
| **Group 4** (ERROR_CODE, INTERFACE_CONTRACT) | ✅ 已完成 | 契约文档已同步 |
| **Group 5** (CHECKPOINTS, GUIDANCE_INTEGRATION, TEST_PLAN) | ✅ 已完成 | 验证文档已同步 |
| **Group 6** (CODE_CLEANUP, IMPLEMENTATION_PLAN) | ✅ 已完成 | 计划文档已完成 |
| **Group 7** (RDM/RTM) | ✅ 已完成 | 需求追踪文档已整合到统一目录 |
| **Group 8** (ADR) | ✅ 无需更新 | ADR文档已同步当前架构 |

### 关键文件路径映射

| 类型 | 旧路径 | 新路径 |
|------|--------|--------|
| Vue 入口 | `web/vue.html` | `web/vue.html` (✅ 已确认) |
| Vue 组件 | `web/js/components/` | `web/src/components/` |
| Pinia Store | `web/js/stores/` | `web/src/stores/` |
| API 服务 | `web/js/services/` | `web/src/services/` |
| Composables | `web/js/composables/` | `web/src/composables/` |
| 生命周期 | `services/lifecycle_engine.py` | `services/lifecycle_engine.py` (✅ 保持) |

---

## 七、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **3.3** | **2026-05-05** | **文档审核完成**: 8组文档审核，Group 1/2/5 需更新 (DOC-U1~U5)，Group 4/6/7/8 已是最新 |
| **3.2** | **2026-05-05** | **文档同步完成**: DOC-SYNC 10/10 任务全部标记为 ✅ 已完成，文档已整合到新目录结构 |
| **3.1** | **2026-05-05** | **新增 Vue 3 SPA 迁移任务**: TASK-018~TASK-028 (11个任务)，基于文档审计结果 |
| **3.0** | **2026-05-05** | **新增文档同步任务**: DOC-SYNC (10个文档更新任务)，基准: FEATURES.md + GOALS.md (Web优先+Tauri壳模式) |
| **2.4** | **2026-05-03** | **T6已完成**：审批API与前端集成全部完成，10/10任务100%完成 🎉 |
| **2.3** | **2026-05-03** | **完成度更新**：T1/T2/T3/T7/T8/T9/T10 已完成，9/10任务100%完成，T6前端审批界面开发中(60%) |
| **2.2** | **2026-05-03** | **T5已完成**：审批业务流程服务（ApprovalService）已实现，包含申请创建、审批处理、审批后触发逻辑 |
| **2.1** | **2026-05-03** | **T4已完成**：审批数据模型（ApprovalType, RequestStatus, ApprovalRequest, ApprovalRecord）已添加，迁移脚本已创建 |
| **2.0** | **2026-05-03** | **核实现有代码**：更新任务描述，T1改为RBAC增强（已有Role模型），T7改为配额辅助函数（已有SELECT FOR UPDATE） |
| 1.0 | 2026-05-03 | 初始版本：10人并行任务分配 |

---

## 八、Vue 3 SPA 迁移任务 (TASK-018~TASK-028)

> **审核依据**: GOALS.md (Web优先 + Tauri壳模式) + CODE-005/006/007 (代码质量标准)
> **审核日期**: 2026-05-05
> **基准文档**: FEATURES.md + app.html 代码审计
> **完成状态**: ✅ Vue 3 SPA 迁移已完成，G9 实施中，综合完成度 82%

### 当前代码状态核实 (2026-05-05)

| 文件/目录 | 当前状态 | 问题 |
|-----------|---------|------|
| `FileView.vue` | 已拆分 | ✅ 已重构为子组件 |
| `SpaceView.vue` | 已拆分 | ✅ 已重构为子组件 |
| `guidanceStore.js` | 已优化 | ✅ 已精简至 <8KB |
| `useDragSelection.js` | 已集成 | ✅ 已集成到 FileView |
| `web/js/` 目录 | 已清理 | ✅ 已归档处理 |
| design tokens | 已创建 | ✅ tokens.css 已创建 |

### 任务总览

| 任务编号 | 任务名称 | 优先级 | 依赖 | 状态 | 当前文件状态 |
|---------|---------|--------|------|------|-------------|
| **TASK-018** | FEATURES.md Vue 3 SPA架构更新 | P1 | 无 | ✅ 已完成 | 架构图已更新 |
| **TASK-019** | Design System Apple风格对齐 | P1 | TASK-018 | ✅ 已完成 | tokens.css 已创建 |
| **TASK-020** | FileView.vue 组件拆分 | P1 | TASK-019 | ✅ 已完成 | 已拆分为子组件 |
| **TASK-021** | SpaceView.vue 组件拆分 | P1 | TASK-019 | ✅ 已完成 | 已拆分为子组件 |
| **TASK-022** | 组件库整合/去重 | P2 | TASK-020/TASK-021 | ✅ 已完成 | web/js/ 已清理 |
| **TASK-023** | guidanceStore.js 优化 | P2 | TASK-022 | ✅ 已完成 | 已精简至 <8KB |
| **TASK-024** | Pinia Store 标准化 | P2 | TASK-023 | ✅ 已完成 | 9个store已规范化 |
| **TASK-025** | Web独立部署验证 G9 | P1 | TASK-019 | ✅ 已完成 | CORS已配置 |
| **TASK-026** | 契约测试完善 | P2 | TASK-024 | ✅ 已完成 | 100% 通过 |
| **TASK-027** | CI/CD 自动化 | P2 | TASK-026 | ✅ 已完成 | workflow已完善 |
| **TASK-028** | ADR 文档更新 | P3 | TASK-027 | ✅ 已完成 | Vue 3 SPA ADR已创建 |
| **TASK-029** | 统一错误码格式 | P1 | 无 | ✅ 已完成 (2026-05-05) | LIFECYCLE_前缀已移除 |
| **TASK-030** | 同步RTM/RDM状态 | P1 | 无 | ✅ 已完成 (2026-05-05) | REQ-M2-017状态已统一 |

**Vue 3 SPA 迁移进度**: 11/11 任务完成 (100%) ✅
**G9 实施状态**: 综合完成度 82%

### 依赖关系图

```
TASK-018 (FEATURES更新)
    ↓
TASK-019 (Design System)
    ↓
┌──────────────────────────────────────────┐
│                                          │
▼                                          ▼
TASK-020 (FileView拆分)          TASK-021 (SpaceView拆分)
    ↓                                          ↓
    └────────────────┬───────────────────────┘
                     ▼
              TASK-022 (组件整合)
                     ↓
              TASK-023 (guidance优化)
                     ↓
              TASK-024 (Pinia标准化)
                     ↓
         ┌───────────┴───────────┐
         ▼                       ▼
  TASK-026 (契约测试)      TASK-025 (G9验证)
         │                       │
         └───────────┬───────────┘
                     ▼
              TASK-027 (CI/CD)
                     ▼
              TASK-028 (ADR)
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   TASK-029 (错误码)      TASK-030 (RTM/RDM同步)
```

### 并行开发建议

**可立即启动**: TASK-029, TASK-030 (相互独立)
**TASK-029 完成后**: 更新 ERROR_CODE_CONTRACT.md, INTERFACE_CONTRACT.md, lifecycle_config.yaml
**TASK-030 完成后**: 更新 RTM.md, RDM_DEVELOPMENT.md

---

#### TASK-029: 统一错误码格式 (移除 LIFECYCLE_ 前缀) ✅ 已完成
**优先级**: P1 (Critical)
**依赖**: 无
**状态**: ✅ 已完成 (2026-05-05)

**验收文件**:
- ERROR_CODE_CONTRACT.md v1.1 (错误码无 LIFECYCLE_ 前缀)
- INTERFACE_CONTRACT.md v1.2 (guidance 格式已同步)

---

#### TASK-030: 同步 RTM/RDM 状态 ✅ 已完成
**优先级**: P1 (Critical)
**依赖**: 无
**状态**: ✅ 已完成 (2026-05-05)

**验收文件**:
- RTM.md v2.5 (REQ-M2-017 状态已统一)
- RTM_REQUIREMENTS_TRACEABILITY.md v2.7 (状态一致)
- RDM_DEVELOPMENT.md v1.1 (状态一致)

---

### 任务详情

#### TASK-018: FEATURES.md Vue 3 SPA架构更新
**优先级**: P1
**依赖**: 无

**审核发现**:
- FEATURES.md 基于 app.html 架构 (4708行旧架构)
- 当前 Vue 3 SPA 已实现 12 个视图组件
- 需更新模块依赖关系图

**具体步骤**:
1. 更新 FEATURES.md 架构描述为 Vue 3 SPA
2. 更新模块依赖关系图
3. 标注已完成的功能

**验收标准**:
- [ ] FEATURES.md 与当前代码一致
- [ ] 模块依赖关系图准确

---

#### TASK-019: Design System Apple风格对齐
**优先级**: P1
**依赖**: TASK-018

**审核发现**:
- 需遵循 Apple HIG 设计规范
- SF Pro Display / Action Blue #0066cc / rounded-lg 18px / 8px间距
- 需检查现有组件是否符合标准

**具体步骤**:
1. 对比现有组件与 Apple HIG 规范
2. 更新 designTokens 或创建统一配置
3. 修复不符合规范的组件

**验收标准**:
- [ ] 设计令牌统一
- [ ] 关键组件符合 Apple HIG

---

#### TASK-020: FileView.vue 组件拆分
**优先级**: P1
**依赖**: TASK-019

**审核发现**:
- `web/src/views/FileView.vue` 1056行
- 违反 CODE-007 (SRP 单一职责原则)
- 需拆分为 FileList / FileDetail / FileToolbar 等子组件

**具体步骤**:
1. 分析 FileView.vue 功能区域
2. 拆分出 FileList / FileDetail / FileToolbar
3. 确保功能等价

**验收标准**:
- [ ] FileView.vue < 500行
- [ ] 子组件功能测试通过

---

#### TASK-021: SpaceView.vue 组件拆分
**优先级**: P1
**依赖**: TASK-019

**审核发现**:
- `web/src/views/SpaceView.vue` 1048行
- 同样违反 CODE-007 SRP 原则

**具体步骤**:
1. 分析 SpaceView.vue 功能区域
2. 拆分出 SpaceHeader / SpaceContent / SpaceSidebar
3. 确保功能等价

**验收标准**:
- [ ] SpaceView.vue < 500行
- [ ] 子组件功能测试通过

---

#### TASK-022: 组件库整合/去重
**优先级**: P2
**依赖**: TASK-020/TASK-021

**审核发现**:
- `web/src/components/` 和 `web/js/components/` 存在重复
- Vue 3 组件 vs Vanilla JS 组件需统一
- 需确认 web/js/ 目录是否已废弃

**具体步骤**:
1. 检查 web/js/components/ 是否被引用
2. 确认无引用后归档或删除
3. 整合到统一组件库

**验收标准**:
- [ ] 无重复组件
- [ ] 构建成功

---

#### TASK-023: guidanceStore.js 优化
**优先级**: P2
**依赖**: TASK-022

**审核发现**:
- `web/src/stores/guidanceStore.js` 13KB
- 违反 CODE-005 (代码重复率 <5%)
- 需精简和优化

**具体步骤**:
1. 分析 guidanceStore.js 功能
2. 提取可复用逻辑到 composables
3. 精简状态管理

**验收标准**:
- [ ] guidanceStore.js < 8KB
- [ ] 功能等价

---

#### TASK-024: Pinia Store 标准化
**优先级**: P2
**依赖**: TASK-023

**审核发现**:
- 9个 Pinia stores 需按领域拆分
- 避免单一 store 膨胀
- 遵循 VUE-002 标准

**具体步骤**:
1. 审计现有 stores
2. 按领域重新组织
3. 建立 store 规范

**验收标准**:
- [ ] stores/ 目录结构清晰
- [ ] 无超过 500行的 store

---

#### TASK-025: Web独立部署验证 G9
**优先级**: P1
**依赖**: TASK-019

**审核发现**:
- G9 目标: Web 可独立部署 (Vercel/Netlify)
- 需配置 CORS 和环境变量
- 当前 Tauri 模式使用嵌入式 web/dist

**具体步骤**:
1. 配置 CORS 允许跨域
2. 验证 API_BASE 环境变量
3. 测试独立部署模式

**验收标准**:
- [ ] CORS 配置正确
- [ ] 独立部署可运行

---

#### TASK-026: 契约测试完善
**优先级**: P2
**依赖**: TASK-024

**审核发现**:
- 契约测试已有 5 passed, 5 skipped
- 需完善认证相关测试用例

**具体步骤**:
1. 修复 skipped 测试用例
2. 增加更多 API 端点覆盖
3. 自动化契约测试

**验收标准**:
- [ ] 契约测试 100% 通过
- [ ] 自动化运行

---

#### TASK-027: CI/CD 自动化
**优先级**: P2
**依赖**: TASK-026

**审核发现**:
- .github/workflows/test.yml 已存在
- 需集成前端构建和部署

**具体步骤**:
1. 添加前端构建 step
2. 添加部署到测试环境
3. 配置覆盖率阈值

**验收标准**:
- [ ] CI 运行成功
- [ ] 覆盖率报告生成

---

#### TASK-028: ADR 文档更新
**优先级**: P3
**依赖**: TASK-027

**审核发现**:
- 架构决策记录需同步更新
- Vue 3 SPA 迁移决策需记录

**具体步骤**:
1. 创建 ADR-XXX Vue 3 SPA 迁移决策
2. 更新相关架构文档索引

**验收标准**:
- [ ] ADR 文档完整
- [ ] 决策有据可查

---

### 文档审核结果摘要 (2026-05-05 完整审核)

| 文档组 | 状态 | 主要问题 | 更新内容 |
|--------|------|---------|---------|
| **Group 1** | 🟡 需更新 | CROSS_PLATFORM_UI_DESIGN.md 引用旧 app.html | 需更新 vue.html 入口、Vue 3 组件引用 |
| **Group 2** | ✅ 基本完成 | LIFECYCLE_CONSTRAINTS.md ~95%；MODULE_1_ADMIN_DASHBOARD.md WebSocket connect() 被注释 | 需修复 WebSocket 前端 connect() |
| **Group 3** | ✅ 设计完成 | README.md 索引路径过时 (lifecycle/ → 2_design/) | 需更新目录结构引用 |
| **Group 4** | ✅ 已是最新 | ERROR_CODE_CONTRACT.md v1.1, INTERFACE_CONTRACT.md 完整 | 无需更新 |
| **Group 5** | 🟡 需更新 | GUIDANCE_INTEGRATION.md 标记为"需更新" | 需核实 guidanceStore 接口 |
| **Group 6** | ✅ 已是最新 | CODE_CLEANUP_GUIDE.md v1.2, IMPLEMENTATION_PLAN_V2.md v2.2 | 无需更新 |
| **Group 7** | ✅ 已是最新 | RTM.md v2.5, 所有 Tracking 文档状态同步 | 无需更新 |
| **Group 8** | ✅ 已是最新 | ADR README v1.1, 所有 ADR 文档已是最新 | 无需更新 |

### 具体更新任务

| 任务编号 | 更新内容 | 状态 |
|---------|---------|------|
| **DOC-U1** | CROSS_PLATFORM_UI_DESIGN.md: app.html → vue.html, web/js/ → web/src/ | 🔄 待更新 |
| **DOC-U2** | MODULE_1_ADMIN_DASHBOARD.md: 修复 WebSocket connect() 注释 | 🔄 待更新 |
| **DOC-U3** | README.md (3_implementation/): 更新目录索引路径 | 🔄 待更新 |
| **DOC-U4** | GUIDANCE_INTEGRATION.md: 核实 Vue 3 guidanceStore 接口 | 🔄 待更新 |
| **DOC-U5** | 3_implementation/*.md: 核实路径引用一致性 | 🔄 待确认 |