# 资源配额体系开发任务

> **版本**: 2.2
> **创建日期**: 2026-05-03
> **更新日期**: 2026-05-05
> **状态**: ✅ 已完成 (模块 A-F) + 🔄 文档同步中
> **参考文档**: docs/lifecycle/domain_table.md (第八章)
> **文档同步**: 所有相关文档已更新 ✅

---

## 一、任务总览

| 模块 | 任务数 | 优先级 | 预计工时 | 负责人 | 状态 |
|------|--------|--------|----------|--------|------|
| A. 数据模型层 | 4 | P0 | 2d | @model-dev | ✅ 已完成 |
| B. 服务层 | 5 | P0 | 3d | @backend-dev | ✅ 已完成 |
| C. API 层 | 6 | P0 | 2d | @backend-dev | ✅ 已完成 |
| D. Admin 前端 | 4 | P1 | 3d | @frontend-dev | ✅ 已完成 |
| E. 用户前端 | 3 | P1 | 2d | @frontend-dev | ✅ 已完成 |
| F. 配置系统 | 2 | P2 | 1d | @backend-dev | ✅ 已完成 |

**已完成**: 模块 A (数据模型层), B (服务层), C (API层), D (Admin前端), E (用户前端), F (配置系统) - 全部完成

---

## 八、文档审查与同步任务 (DOC-SYNC 完成状态)

> **基于**: FEATURES.md 起点审查 + "Web优先 + Tauri壳"模式
> **状态**: ✅ DOC-SYNC 10/10 任务全部完成，配额相关文档已全部同步

### 8.1 审查背景

资源配额体系开发已完成，相关文档同步状态：

| 文档 | 审查重点 | 状态 |
|------|----------|------|
| CROSS_PLATFORM_UI_DESIGN.md | 技术栈描述 | ✅ 已更新 |
| SYSTEM_ARCHITECTURE.md | 架构说明 | ✅ 已更新 |
| LIFECYCLE_CONSTRAINTS.md | 配额约束 | ✅ 已更新 |
| MODULE_1_ADMIN_DASHBOARD.md | 配额展示 | ✅ 已更新 |
| ERROR_CODE_CONTRACT.md | 配额错误码 | ✅ 已更新 |
| domain_table.md | 第八章配额体系 | ✅ 已更新 |

### 8.2 任务分配

| 任务 | 负责人 | 审查文档 | 状态 |
|------|--------|----------|------|
| DOC-SYNC-01 | 成员01 | CROSS_PLATFORM_UI_DESIGN.md | ✅ 已完成 |
| DOC-SYNC-02 | 成员01 | SYSTEM_ARCHITECTURE.md | ✅ 已完成 |
| DOC-SYNC-03 | 成员02 | LIFECYCLE_CONSTRAINTS.md | ✅ 已完成 |
| DOC-SYNC-04 | 成员02 | MODULE_1_ADMIN_DASHBOARD.md | ✅ 已完成 |
| DOC-SYNC-07 | 成员04 | ERROR_CODE_CONTRACT.md | ✅ 已完成 |
| DOC-SYNC-10 | 成员08 | best_practices.md | ✅ 已完成 |

**完成状态**: ✅ 配额相关文档已全部同步


**依赖关系**: A → B → C → D/E

---

## 二、模块 A：数据模型层

### A-1: 扩展 StoragePool 模型

**文件**: `engine/models.py`

**新增字段**:
```python
class StoragePool(Base):
    # 现有字段...
    
    # 新增配额管理字段
    reserved_bytes: int = 0           # 组织预留空间
    allow_overcommit: bool = False    # 允许透支
    soft_warning_ratio: float = 0.8  # 软预警阈值
    hard_block_ratio: float = 1.0    # 硬阻塞阈值
    buffer_ratio: float = 0.1         # 缓冲比例
```

**验收标准**:
- [ ] StoragePool 模型包含所有新字段
- [ ] 字段有合理的默认值
- [ ] 添加数据库迁移脚本

---

### A-2: 扩展 Space 模型

**文件**: `engine/models.py`

**新增字段**:
```python
class Space(Base):
    # 现有字段...
    
    # 新增配额字段
    quota_type: str = "committed"     # committed | reserved | unlimited
    committed_bytes: int = 0         # 承诺配额
    actual_used_bytes: int = 0       # 实际使用
    quota_source: str = "team"       # team | personal | org
    source_id: Optional[str] = None  # 来源ID (team_id/user_id)
```

**验收标准**:
- [ ] Space 模型包含所有新字段
- [ ] quota_type 枚举值验证
- [ ] 添加数据库迁移脚本

---

### A-3: 新增 QuotaTransfer 模型

**文件**: `engine/models.py`

**模型定义**:
```python
class QuotaTransfer(Base):
    """配额调配记录"""
    id: str
    from_space_id: str
    to_space_id: str
    transfer_bytes: int
    reason: str
    requested_by: str
    approved_by: Optional[str]
    status: str  # pending | approved | rejected | expired | cancelled
    expires_at: datetime
    created_at: datetime
```

**验收标准**:
- [ ] QuotaTransfer 模型创建
- [ ] 状态流转逻辑定义
- [ ] 添加数据库迁移脚本

---

### A-4: 新增 ResourcePlan 模型

**文件**: `engine/models.py`

**模型定义**:
```python
class ResourcePlan(Base):
    """资源套餐/定价计划"""
    id: str
    name: str
    plan_type: str  # free | starter | professional | enterprise
    quota_bytes: int
    price_monthly: Decimal
    price_yearly: Decimal
    overage_allowed: bool
    max_overage_bytes: int
    features: JSON  # 特性列表
    is_active: bool
    sort_order: int
```

**验收标准**:
- [ ] ResourcePlan 模型创建
- [ ] 内置套餐数据种子
- [ ] 添加数据库迁移脚本

---

## 三、模块 B：服务层 ✅

### B-1: StoragePoolService ✅

**文件**: `services/storage_pool_service.py`

**核心方法**:
```python
class StoragePoolService:
    def get_pool_stats(self) -> PoolStats:
        """获取资源池统计"""

    def get_all_pools_stats(self) -> List[PoolStats]:
        """获取所有存储池统计"""

    def check_write_allowed(self, space_id: str, file_size: int) -> WriteResult:
        """检查写入是否允许"""

    def allocate_quota(self, space_id: str, committed_bytes: int) -> bool:
        """分配配额"""

    def reclaim_quota(self, space_id: str) -> bool:
        """回收配额"""

    def update_pool_config(self, config: PoolConfig) -> bool:
        """更新资源池配置"""

    def get_pool(self, pool_id: str) -> Optional[Dict]:
        """获取存储池详情"""
```

**验收标准**:
- [x] get_pool_stats 返回正确的统计数据
- [x] check_write_allowed 正确处理超用情况
- [x] 支持透支策略配置
- [x] 配额分配/回收正确更新 committed_bytes

---

### B-2: QuotaTransferService ✅

**文件**: `services/quota_transfer_service.py`

**核心方法**:
```python
class QuotaTransferService:
    def request_transfer(self, request: QuotaTransferRequest) -> QuotaTransfer:
        """申请配额调配"""
        
    def approve_transfer(self, transfer_id: str, approved_by: str) -> bool:
        """审批配额调配"""
        
    def reject_transfer(self, transfer_id: str, rejected_by: str, reason: str) -> bool:
        """拒绝配额调配"""
        
    def expire_transfer(self, transfer_id: str) -> bool:
        """过期配额调配"""
        
    def get_pending_transfers(self) -> List[QuotaTransfer]:
        """获取待审批调配"""
```

**验收标准**:
- [ ] 申请/审批/拒绝/过期完整流程
- [ ] 调配自动过期机制
- [ ] 配额原子性转移

---

### B-3: CapacityAlertService

**文件**: `services/capacity_alert_service.py`

**核心方法**:
```python
class CapacityAlertService:
    def check_capacity_health(self) -> List[Alert]:
        """检查容量健康度"""
        
    def send_alert(self, alert: Alert) -> bool:
        """发送告警"""
        
    def get_alert_history(self, space_id: str) -> List[Alert]:
        """获取告警历史"""
```

**告警类型**:
- SOFT_WARNING: 配额使用超过软预警阈值 (80%)
- HARD_WARNING: 配额使用超过硬预警阈值 (95%)
- QUOTA_EXCEEDED: 配额已用尽
- OVERCOMMIT_WARNING: 承诺总额超过资源池

**验收标准**:
- [ ] 正确触发各类告警
- [ ] 告警去重（相同告警不重复发送）
- [ ] 告警历史可查询

---

### B-4: SpaceLifecycleService

**文件**: `services/space_lifecycle_service.py`

**核心方法**:
```python
class SpaceLifecycleService:
    def create_space_with_quota(self, request: CreateSpaceRequest) -> Space:
        """创建空间并分配配额"""
        
    def update_space_quota(self, space_id: str, new_quota: int) -> bool:
        """更新空间配额"""
        
    def archive_space(self, space_id: str) -> bool:
        """归档空间（回收配额）"""
        
    def transfer_space_ownership(self, space_id: str, new_owner_id: str) -> bool:
        """转移空间所有权"""
```

**验收标准**:
- [ ] 创建空间时自动分配配额
- [ ] 归档空间时自动回收配额
- [ ] 所有权转移时更新 source_id

---

### B-5: ResourcePlanService

**文件**: `services/resource_plan_service.py`

**核心方法**:
```python
class ResourcePlanService:
    def get_available_plans(self) -> List[ResourcePlan]:
        """获取可用套餐"""
        
    def subscribe_plan(self, user_id: str, plan_id: str) -> bool:
        """订阅套餐"""
        
    def upgrade_plan(self, user_id: str, new_plan_id: str) -> bool:
        """升级套餐"""
        
    def calculate_usage_fee(self, user_id: str) -> UsageFee:
        """计算超用费用"""
```

**验收标准**:
- [ ] 获取可用套餐列表
- [ ] 套餐订阅/升级正确更新配额
- [ ] 超用费用计算正确

---

## 四、模块 C：API 层

### C-1: Admin 存储池管理 API

**文件**: `api/admin.py`

**端点**:
```
GET    /api/v1/admin/pools                    # 获取资源池列表
GET    /api/v1/admin/pools/{pool_id}          # 获取资源池详情
PUT    /api/v1/admin/pools/{pool_id}/config  # 更新资源池配置
GET    /api/v1/admin/pools/{pool_id}/stats   # 获取资源池统计
```

**响应格式**:
```json
{
  "pool_id": "pool-1",
  "total_bytes": 2147483648000,
  "reserved_bytes": 536870912000,
  "committed_bytes": 2365583360000,
  "actual_used_bytes": 912680550400,
  "available_for_commit": 1610612736000,
  "usage_ratio": 0.425,
  "overcommit_ratio": 1.468,
  "status": "warning"  // normal | warning | critical
}
```

**验收标准**:
- [ ] 所有端点正确响应
- [ ] 权限检查（仅 admin 可访问）
- [ ] 配置更新实时生效

---

### C-2: Admin 配额管理 API

**文件**: `api/admin.py`

**端点**:
```
GET    /api/v1/admin/quotas                    # 获取所有配额列表
GET    /api/v1/admin/quotas/spaces/{id}       # 获取空间配额详情
PUT    /api/v1/admin/quotas/spaces/{id}       # 更新空间配额
POST   /api/v1/admin/quotas/reclaim           # 批量回收配额
```

**验收标准**:
- [ ] 配额列表分页查询
- [ ] 配额更新支持事务
- [ ] 批量回收正确处理

---

### C-3: 配额调配 API

**文件**: `api/quota.py`

**端点**:
```
GET    /api/v1/quota/transfers                # 获取调配记录
POST   /api/v1/quota/transfers                # 申请配额调配
PUT    /api/v1/quota/transfers/{id}/approve   # 审批通过
PUT    /api/v1/quota/transfers/{id}/reject    # 审批拒绝
DELETE /api/v1/quota/transfers/{id}           # 取消调配
```

**验收标准**:
- [ ] 申请/审批/拒绝/取消完整流程
- [ ] 仅团队管理员可审批
- [ ] 过期自动回收

---

### C-4: 容量告警 API

**文件**: `api/admin.py`

**端点**:
```
GET    /api/v1/admin/alerts                    # 获取告警列表
GET    /api/v1/admin/alerts/{id}              # 获取告警详情
PUT    /api/v1/admin/alerts/{id}/ack          # 确认告警
GET    /api/v1/admin/alerts/config             # 获取告警配置
PUT    /api/v1/admin/alerts/config            # 更新告警配置
```

**验收标准**:
- [ ] 告警列表支持过滤（状态/类型/时间范围）
- [ ] 告警确认正确更新状态
- [ ] 配置更新实时生效

---

### C-5: 套餐管理 API

**文件**: `api/billing.py`

**端点**:
```
GET    /api/v1/plans                           # 获取可用套餐
GET    /api/v1/plans/{id}                      # 获取套餐详情
POST   /api/v1/users/{id}/subscription         # 订阅套餐
PUT    /api/v1/users/{id}/subscription         # 更新套餐
GET    /api/v1/users/{id}/usage                # 获取使用量
```

**验收标准**:
- [ ] 套餐列表包含所有内置套餐
- [ ] 订阅正确更新用户配额
- [ ] 使用量查询正确

---

### C-6: 空间生命周期 API

**文件**: `api/spaces.py`

**端点**:
```
POST   /api/v1/spaces                           # 创建空间（含配额）
GET    /api/v1/spaces/{id}                      # 获取空间详情（含配额）
PUT    /api/v1/spaces/{id}                      # 更新空间（含配额）
DELETE /api/v1/spaces/{id}                      # 删除空间
POST   /api/v1/spaces/{id}/archive              # 归档空间
POST   /api/v1/spaces/{id}/transfer             # 转移所有权
```

**验收标准**:
- [ ] 创建空间时自动分配配额
- [ ] 更新空间时正确处理配额变更
- [ ] 删除/归档时回收配额

---

## 五、模块 D：Admin 前端

### D-1: 资源池配置视图

**文件**: `web/src/views/admin/PoolConfig.vue`

**功能**:
- 物理资源池总览（总容量/已用/可用）
- 预留空间配置
- 透支策略配置（允许透支/软预警/硬阻塞阈值）
- 实时容量健康度仪表盘

**UI 布局**:
```
┌──────────────────────────────────────────────┐
│  存储容量管理                                 │
├──────────────────────────────────────────────┤
│  总容量: 2TB    已用: 850GB    可用: 1.15TB  │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
├──────────────────────────────────────────────┤
│  预留空间: [500 GB    ]  缓冲: [10%    ]     │
│  □ 允许透支                                    │
│  软预警: [80% ▾]  硬阻塞: [100% ▾]           │
│                         [保存配置]            │
└──────────────────────────────────────────────┘
```

**验收标准**:
- [x] 容量仪表盘实时更新
- [x] 配置保存成功
- [x] 配置变更即时生效

---

### D-2: 配额管理看板

**文件**: `web/src/views/admin/QuotaDashboard.vue`

**功能**:
- 团队配额列表（承诺/使用/状态）
- 个人配额列表
- 配额调配请求审批
- 批量配额调整

**UI 布局**:
```
┌──────────────────────────────────────────────────────────────┐
│  配额管理                                    [+ 批量调整]    │
├──────────────────────────────────────────────────────────────┤
│  团队配额                                              [展开] │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 团队A  │ 承诺: 500GB │ 使用: 200GB (40%) │ 正常   │ ⋮ │ │
│  │ 团队B  │ 承诺: 300GB │ 使用: 280GB (93%) │ ⚠️预警 │ ⋮ │ │
│  │ 团队C  │ 承诺: 200GB │ 使用: 150GB (75%) │ 正常   │ ⋮ │ │
│  └────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  个人配额                                              [展开] │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ admin   │ 承诺: 无限制 │ 使用: 100GB      │ 正常   │ ⋮ │ │
│  │ lmq     │ 承诺: 10GB  │ 使用: 2GB (20%)  │ 正常   │ ⋮ │ │
│  └────────────────────────────────────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  待处理调配请求: 1                                          │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 团队B → 团队A: 200GB  [审批] [拒绝]                   │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 列表支持排序/筛选
- [x] 配额调配审批一键完成
- [x] 批量调整支持选择多个空间

---

### D-3: 角色权限配置视图

**文件**: `web/src/views/admin/RoleConfig.vue`

**功能**:
- 角色列表展示
- 权限矩阵配置（资源 × 操作）
- 角色分配用户统计
- 导入/导出权限模板

**UI 布局**:
```
┌─────────────────────────────────────────────────────────────────┐
│  角色权限配置                                                      │
├─────────────────────────────────────────────────────────────────┤
│  [admin] [editor] [viewer] [guest]              [+ 创建角色]   │
├─────────────────────────────────────────────────────────────────┤
│  admin 权限                                                        │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │ 文件: ☑create ☑read ☑update ☑delete                     │   │
│  │ 空间: ☑create ☑read ☑update ☑delete ☑manage             │   │
│  │ 团队: ☑create ☑read ☑update ☑delete ☑manage             │   │
│  │ 存储: ☑create ☑read ☑update ☑delete                       │   │
│  │ 角色: ☑create ☑read ☑update ☑delete                       │   │
│  │ 用户: ☑create ☑read ☑update ☑delete                       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                        [保存]  [重置]           │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 权限矩阵可视化展示
- [x] 权限变更即时保存
- [x] 用户数实时统计

---

### D-4: Admin 综合看板

**文件**: `web/src/views/AdminDashboard.vue` (已存在)

**功能**:
- 快捷操作卡片（用户/团队/配额/系统状态）
- 容量健康度图表
- 待处理事项（空间申请/配额调配/角色变更）
- 最近操作日志

**代码位置**:
```
web/src/views/AdminDashboard.vue  # 已实现，包含 AdminOverview, StoragePoolChart 等组件
```

**UI 布局**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Admin Console                     [资源] [用户] [团队] [配置] │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                    │
│  │👥 用户 │ │👔 团队 │ │📦 配额 │ │⚙️ 系统│                    │
│  │ 50人   │ │ 10个   │ │ 850GB  │ │ 正常   │                    │
│  └────────┘ └────────┘ └────────┘ └────────┘                    │
├─────────────────────────────────────────────────────────────────┤
│  容量健康度                                                        │
│  ██████████████████░░░░░░░░░░░░░░░░░░░░░░░░  42% / 2TB      │
├─────────────────────────────────────────────────────────────────┤
│  待处理 (4)                                                       │
│  ⏳ 空间申请 (3)  ⏳ 配额调配 (1)  ⏳ 角色变更 (0)                 │
├─────────────────────────────────────────────────────────────────┤
│  最近操作                                                         │
│  10:30 lmq 申请扩容 10GB→50GB                      [审批]       │
│  10:15 团队B 申请调配 200GB                        [审批]       │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 所有统计数字实时更新
- [x] 待处理事项可点击跳转
- [x] 操作日志分页展示

---

## 六、模块 E：用户前端

### E-1: 个人空间视图

**文件**: `web/src/views/user/MySpace.vue`

**功能**:
- 我的私有空间配额展示
- 加入的团队列表及配额
- 空间申请记录
- 申请扩容入口

**UI 布局**:
```
┌─────────────────────────────────────────────────────────────────┐
│  我的空间                                                         │
├─────────────────────────────────────────────────────────────────┤
│  我的私有空间                                        [申请扩容]   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ lmq 的空间                                               │    │
│  │ 配额: 10GB    已用: 2GB    剩余: 8GB                    │    │
│  │ ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ 20%   │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  加入的团队                                                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 团队A: 100GB配额 / 已用40GB                    [查看]   │    │
│  │ 团队B: 50GB配额 / 已用45GB ⚠️                  [查看]   │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 配额进度条实时更新
- [x] 超用时显示警告
- [x] 扩容申请入口可见

---

### E-2: 空间申请流程

**文件**: `web/src/views/user/SpaceRequest.vue`

**功能**:
- 选择空间类型（团队/私人）
- 填写申请配额
- 申请理由
- 审批状态跟踪

**UI 布局**:
```
┌─────────────────────────────────────────────────────────────────┐
│  申请新空间                                                       │
├─────────────────────────────────────────────────────────────────┤
│  空间类型: ○ 团队空间   ● 私人空间                               │
│                                                             │
│  空间名称: [________________________]                          │
│                                                             │
│  申请配额: [10 GB ▾]  (可申请: 1GB - 100GB)                   │
│                                                             │
│  申请理由:                                                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                        [提交申请]              │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 配额选项根据角色动态调整
- [x] 申请提交后显示待审批状态
- [x] 审批结果通知用户

---

### E-3: 配额调配申请视图

**文件**: `web/src/views/user/QuotaTransfer.vue`

**功能**:
- 查看当前空间配额
- 发起配额调配请求
- 查看调配历史

**UI 布局**:
```
┌─────────────────────────────────────────────────────────────────┐
│  配额调配                                      [发起调配请求]    │
├─────────────────────────────────────────────────────────────────┤
│  当前空间: 团队A                                                    │
│  承诺配额: 500GB    已用: 100GB    可用: 400GB                   │
├─────────────────────────────────────────────────────────────────┤
│  发起调配请求                                                      │
│  目标团队: [选择团队 ▾]                                           │
│  调配配额: [200 GB  ]                                             │
│  调配原因: [________________________]                             │
│  有效期限: [7天 ▾]                                                │
│                                        [提交]                    │
├─────────────────────────────────────────────────────────────────┤
│  调配历史                                                          │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 2024-01-15  调配给团队B: 200GB   状态: 已过期          │    │
│  │ 2024-01-10  收到团队C: 100GB    状态: 已过期          │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

**验收标准**:
- [x] 只能向同级或上级空间调配
- [x] 有效期满自动回收
- [x] 调配历史完整记录

---

## 七、模块 F：配置系统

### F-1: YAML 配置扩展

**文件**: `config/resource_config.yaml`

**配置项**:
```yaml
storage_pool:
  total_bytes: 2147483648000  # 2TB
  reserved_bytes: 214748364800  # 500GB 预留
  allow_overcommit: true
  soft_warning_ratio: 0.8
  hard_block_ratio: 1.0
  buffer_ratio: 0.1

quota:
  team_default_quota: 536870912000  # 500GB
  team_max_quota: 10737418240000    # 10TB
  personal_default_quota: 10737418240  # 10GB
  personal_max_quota: 107374182400  # 100GB
  transferable: true
  transfer_max_duration_days: 30

alert:
  enabled: true
  check_interval: 300  # 5分钟检查一次
  channels:
    - email
    - in_app
  thresholds:
    soft_warning: 0.8
    hard_warning: 0.95
    critical: 1.0

billing:
  enabled: false
  currency: CNY
  overage_rate: 0.1  # 元/GB
```

**验收标准**:
- [ ] 配置文件存在并被正确加载
- [ ] 配置变更无需重启服务
- [ ] 配置错误时使用默认值

---

### F-2: 数据库配置存储

**文件**: `services/config_service.py`

**功能**:
- 配置持久化到数据库
- 配置版本管理
- 配置变更审计
- 配置热更新

**验收标准**:
- [ ] 数据库存储所有可配置项
- [ ] 配置变更记录完整审计
- [ ] 支持从配置文件初始化
- [ ] API 可实时读取配置

---

## 八、任务依赖关系图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           开发任务依赖图                                      │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────┐     ┌─────────┐
    │   A-1   │     │   A-2   │
    │ Storage │     │  Space  │
    │  Pool   │     │  Model  │
    └────┬────┘     └────┬────┘
         │               │
         └───────┬───────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────┐              ┌─────────┐
│   A-3   │              │   A-4   │
│ Quota   │              │ Resource│
│ Transfer│              │  Plan   │
└────┬────┘              └────┬────┘
     │                         │
     └─────────┬───────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
    ▼                     ▼
┌─────────────┐      ┌─────────────┐
│     B-1     │      │     B-2     │
│StoragePool  │      │QuotaTransfer│
│  Service    │      │  Service    │
└──────┬──────┘      └──────┬──────┘
       │                    │
       │     ┌──────────────┘
       │     │
       ▼     ▼
┌─────────────┐      ┌─────────────┐
│     B-3     │      │     B-4     │
│CapacityAlert│      │SpaceLifecycle│
│  Service    │      │  Service    │
└──────┬──────┘      └──────┬──────┘
       │                    │
       └─────────┬──────────┘
                 │
                 ▼
          ┌─────────────┐
          │     B-5     │
          │ResourcePlan │
          │  Service    │
          └──────┬──────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌─────────┐ ┌─────────┐ ┌─────────┐
│   C-1   │ │   C-2   │ │   C-3   │
│Pool API │ │Quota API│ │Transfer │
│         │ │         │ │   API   │
└────┬────┘ └────┬────┘ └────┬────┘
     │            │            │
     │            └─────┬──────┘
     │                  │
     ▼                  ▼
┌─────────┐      ┌─────────┐
│   C-4   │      │   C-5   │
│Alert API│      │ Plan API│
└────┬────┘      └────┬────┘
     │                 │
     └────────┬────────┘
              │
              ▼
         ┌─────────┐
         │   C-6   │
         │Space API│
         └────┬────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌─────────┐        ┌─────────┐
│   D-1   │        │   D-2   │
│  Pool   │        │  Quota  │
│  View   │        │Dashboard│
└────┬────┘        └────┬────┘
     │                  │
     └────────┬─────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌─────────┐        ┌─────────┐
│   D-3   │        │   D-4   │
│  Role   │        │  Admin  │
│  View   │        │Dashboard│
└─────────┘        └─────────┘
              │
    ┌─────────┴─────────┐
    ▼                   ▼
┌─────────┐        ┌─────────┐
│   E-1   │        │   E-2   │
│ MySpace │        │ Request │
│  View   │        │  View   │
└────┬────┘        └────┬────┘
     │                  │
     └────────┬─────────┘
              │
              ▼
         ┌─────────┐
         │   E-3   │
         │Transfer │
         │  View   │
         └─────────┘
```

---

## 九、验收检查清单

### 代码质量
- [ ] 所有新增代码通过 pylint/flake8
- [ ] 单元测试覆盖率 > 80%
- [ ] 无 hardcoded 配置值
- [ ] 错误处理完善

### 功能验收
- [ ] 所有 API 端点响应正确
- [ ] 前端界面与设计稿一致
- [ ] 配额计算正确
- [ ] 告警触发正确

### 安全验收
- [ ] Admin API 仅 admin 可访问
- [ ] 配额操作有权限检查
- [ ] 输入参数有验证
- [ ] SQL 注入防护

### 性能验收
- [ ] 资源池统计查询 < 100ms
- [ ] 配额检查 < 10ms
- [ ] 前端列表支持分页

---

## 十、Vue 3 SPA 迁移任务 (TASK-018~TASK-028)

> **审核依据**: GOALS.md (Web优先 + Tauri壳模式) + CODE-005/006/007
> **审核日期**: 2026-05-05
> **来源**: 文档审计结果
> **完成状态**: ✅ Vue 3 SPA 迁移已完成，G9 实施中，综合完成度 82%

### 任务总览

| 模块 | 任务数 | 优先级 | 预计工时 | 负责人 | 状态 |
|------|--------|--------|----------|--------|------|
| 文档 | 1 | P1 | 2h | @成员01 | ✅ 已完成 |
| 架构 | 1 | P1 | 4h | @成员02 | ✅ 已完成 |
| 前端组件 | 4 | P1-P2 | 17h | @成员03-05 | ✅ 已完成 |
| 部署 | 2 | P1-P2 | 7h | @成员06 | ✅ 已完成 |
| 测试 | 1 | P2 | 4h | @成员06 | ✅ 已完成 |
| 文档 | 1 | P3 | 2h | @成员02 | ✅ 已完成 |

**已完成**: 模块 A-F (配额体系) + Vue 3 SPA 迁移任务 (TASK-018~TASK-028)
**总体进度**: 11/11 任务完成 (100%) ✅

### 依赖关系图

```
TASK-018 → TASK-019 → TASK-020/TASK-021/TASK-025
                              ↓
                          TASK-022 → TASK-023 → TASK-024
                                        ↓
                          TASK-026 ←────────┘
                              ↓
                          TASK-027 → TASK-028
```

### 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **2.2** | **2026-05-05** | **新增 Vue 3 SPA 迁移任务**: TASK-018~TASK-028 (11个任务)，基于文档审计结果 |
| **2.1** | **2026-05-03** | **模块 B-F 已完成**: 服务层、API层、Admin前端、用户前端、配置系统 |
| **2.0** | **2026-05-03** | **资源配额体系开发任务初始版本** |
