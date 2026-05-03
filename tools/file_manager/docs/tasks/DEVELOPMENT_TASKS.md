# 开发任务分配表 (10人并行)

> **版本**: 2.0
> **更新日期**: 2026-05-03
> **文档来源**: role_permission_design.md, resource_approval_flow.md, quota_management.md
> **团队规模**: 10 人
> **任务模式**: 10项独立任务，并行执行
> **重要更新**: 已核实现有代码基础，任务描述基于实际模型

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

**总体进度**: 10/10 任务全部完成 (100%) 🎉

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

## 六、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **2.4** | **2026-05-03** | **T6已完成**：审批API与前端集成全部完成，10/10任务100%完成 🎉 |
| **2.3** | **2026-05-03** | **完成度更新**：T1/T2/T3/T7/T8/T9/T10 已完成，9/10任务100%完成，T6前端审批界面开发中(60%) |
| **2.2** | **2026-05-03** | **T5已完成**：审批业务流程服务（ApprovalService）已实现，包含申请创建、审批处理、审批后触发逻辑 |
| **2.1** | **2026-05-03** | **T4已完成**：审批数据模型（ApprovalType, RequestStatus, ApprovalRequest, ApprovalRecord）已添加，迁移脚本已创建 |
| **2.0** | **2026-05-03** | **核实现有代码**：更新任务描述，T1改为RBAC增强（已有Role模型），T7改为配额辅助函数（已有SELECT FOR UPDATE） |
| 1.0 | 2026-05-03 | 初始版本：10人并行任务分配 |