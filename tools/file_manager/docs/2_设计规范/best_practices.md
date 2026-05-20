# 最佳实践领域管理表 (Best Practices Registry)

> **版本**: v5.6
> **更新日期**: 2026-05-06
> **状态**: **新增 FE-022 前端 LIFECYCLE 操作预检规范**
> ~~v5.5
> **更新日期**: 2026-05-06
> ~~v5.0
> **更新日期**: 2026-05-06
> ~~v4.0
> **更新日期**: 2026-05-05
> ~~v2.0
> **更新日期**: 2026-05-04
> ~~v1.0
> **更新日期**: 2026-05-03
> **项目**: Hermes File Manager
> **状态**: 维护中

---

## 零、术语统一

| 术语 | 统一表述 | 说明 |
|------|---------|------|
| SSOT (Single Source of Truth) | **SSOT (Single Source of Truth)** | 行业标准术语 |
| 前端构建产物 | **web/dist/** | 唯一构建输出目录 |
| 架构模式 | **"Web优先 + Tauri 壳"模式** | 中文标准名称 |
| Vue 入口 | **vue.html / floating-vue.html** | Tauri 窗口入口 |
| 平台适配器 | **platformAdapter.js** | Tauri/Web 统一接口 |

---

## 一、目的与范围

本文档记录和维护项目开发过程中产生的所有**最佳实践（Best Practices）**，涵盖：
- 架构设计模式
- 代码规范与技巧
- 数据库设计规范
- API 设计规范
- 前端开发规范 (Vue 3 SPA)
- 测试最佳实践
- 运维与部署规范

---

## 二、分类索引

| 分类 | 说明 | 最佳实践数量 |
|------|------|-------------|
| **ARCH** | 架构设计 | 3 |
| **CODE** | 代码规范 | 13 |
| **DB** | 数据库设计 | 3 |
| **API** | API 设计 | 3 |
| **FE** | 前端开发 (Vue 3 SPA) | 22 |
| **TEST** | 测试规范 | 3 |
| **OPS** | 运维部署 | 3 |
| **KNOWLEDGE** | 知识库管理 | 2 |
| **FILE** | 文件操作 | 1 |

---

## 三、最佳实践详情

### ARCH-001: 层级清晰的模块划分

| 属性 | 内容 |
|------|------|
| **编号** | ARCH-001 |
| **分类** | 架构设计 (ARCH) |
| **标题** | 层级清晰的模块划分 |
| **描述** | 按职责划分模块，避免循环依赖，保持单向依赖 |
| **适用场景** | 新模块创建、代码重构 |
| **示例** | engine/ (核心业务) → services/ (业务编排) → api/ (接口层) → web/ (前端) |

**正确示例**:
```
engine/models.py      # 数据模型，不依赖其他模块
services/            # 业务逻辑，依赖 models
api/                 # 接口层，依赖 services
web/                 # 前端，依赖 api
```

**错误示例**:
```
# 循环依赖
services/user_service.py → api/auth.py → services/user_service.py
```

**Benefits**: 易于测试、替换、扩展

---

### ARCH-002: 配置与代码分离

| 属性 | 内容 |
|------|------|
| **编号** | ARCH-002 |
| **分类** | 架构设计 (ARCH) |
| **标题** | 配置与代码分离 |
| **描述** | 业务配置通过配置文件管理，不硬编码在代码中 |
| **适用场景** | 功能开关、阈值配置、环境差异化配置 |

**示例**:
```python
# ❌ 硬编码
THRESHOLD_WARNING = 0.8

# ✅ 配置文件
config = get_config()
THRESHOLD_WARNING = config.get("quota_warning_threshold", 0.8)
```

**Benefits**: 运行时可调整，无需修改代码

---

### ARCH-003: 生命周期约束前置检查

| 属性 | 内容 |
|------|------|
| **编号** | ARCH-003 |
| **分类** | 架构设计 (ARCH) |
| **标题** | 生命周期操作前置约束检查 |
| **描述** | 在执行操作前进行前置条件检查，提前发现问题 |
| **适用场景** | 文件上传、空间删除、团队解散等高风险操作 |

**示例**:
```python
LIFECYCLE_CONSTRAINTS = {
    "delete_pool": (
        lambda ctx: no_teams_using_pool(ctx["pool_id"]),
        "该存储池仍有团队使用，无法删除",
        "查看占用的团队"
    ),
}
```

**Benefits**: 减少数据库回滚，保护数据一致性

---

### CODE-001: 使用枚举定义常量

| 属性 | 内容 |
|------|------|
| **编号** | CODE-001 |
| **分类** | 代码规范 (CODE) |
| **标题** | 使用枚举定义状态常量 |
| **描述** | 避免字符串硬编码，使用枚举提高可读性和类型安全 |
| **适用场景** | 状态定义、类型标识、配置键名 |

**示例**:
```python
# ❌ 字符串硬编码
status = "pending"
if status == "pending": ...

# ✅ 枚举定义
class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

status = RequestStatus.PENDING
if status == RequestStatus.PENDING: ...
```

**Benefits**: IDE自动补全、类型检查、避免拼写错误

---

### CODE-002: 统一错误处理模式

| 属性 | 内容 |
|------|------|
| **编号** | CODE-002 |
| **分类** | 代码规范 (CODE) |
| **标题** | 统一的自定义异常和错误码 |
| **描述** | 业务异常使用自定义异常类，错误码统一管理 |
| **适用场景** | API 错误处理、服务层异常抛出 |

**示例**:
```python
# 自定义异常
class QuotaExceeded(Exception):
    def __init__(self, space_id, required, available):
        self.space_id = space_id
        self.required = required
        self.available = available
        super().__init__(f"配额不足: 需要 {required}, 可用 {available}")

# 统一错误码
class ErrorCode:
    QUOTA_EXCEEDED = "E1001"
    FILE_NOT_FOUND = "E1002"
```

**Benefits**: 错误可追踪、便于日志分析、客户端可处理

---

### CODE-003: 使用上下文对象传递请求信息

| 属性 | 内容 |
|------|------|
| **编号** | CODE-003 |
| **分类** | 代码规范 (CODE) |
| **标题** | 使用上下文对象而非多参数传递 |
| **描述** | 相关参数封装为上下文对象，减少函数签名复杂度 |
| **适用场景** | 服务层方法、多层调用场景 |

**示例**:
```python
# ❌ 多参数
def check_quota(space_id, user_id, file_size, session):
    ...

# ✅ 上下文对象
class LifecycleContext:
    def __init__(self, space_id, user_id, file_size, session):
        self.space_id = space_id
        self.user_id = user_id
        self.file_size = file_size
        self.session = session

def check_quota(ctx: LifecycleContext):
    ...
```

**Benefits**: 参数分组清晰、易于扩展、便于日志记录

---

### CODE-004: 日志级别规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-004 |
| **分类** | 代码规范 (CODE) |
| **标题** | 正确的日志级别使用 |
| **描述** | DEBUG/INFO/WARNING/ERROR 各司其职，避免日志污染 |
| **适用场景** | 所有日志记录场景 |

**规范**:
| 级别 | 使用场景 | 示例 |
|------|---------|------|
| DEBUG | 开发调试信息 | `logger.debug(f"查询条件: {params}")` |
| INFO | 正常业务流程 | `logger.info(f"用户 {user_id} 登录成功")` |
| WARNING | 异常但不阻塞 | `logger.warning("配额使用率超过 80%")` |
| ERROR | 错误需处理 | `logger.error(f"数据库连接失败: {e}")` |


---

### CODE-005: 消除重复代码与文件合并

| 属性 | 内容 |
|------|------|
| **编号** | CODE-005 |
| **分类** | 代码规范 (CODE) |
| **标题** | 消除重复代码与文件合并原则 |
| **描述** | 相同功能只保留一个实现，避免维护两份代码导致的不一致问题 |
| **适用场景** | 代码审查、重构、文件整理 |

**问题示例**:
```
# 冗余文件示例
StoragePoolView.vue + StoragePool.vue  → 保留一个
TeamView.vue       + Team.vue        → 保留一个
lifecycle_engine.py + lifecycle.py    → 保留一个
permission_checker.py + permission.py → 保留一个
```

**判断标准**:
| 情况 | 操作 |
|------|------|
| 两个文件内容完全相同 | 删除其中一个 |
| 一个文件是另一个的子集 | 合并到更完整的文件 |
| 两个文件有重叠功能 | 合并并重构提取公共部分 |
| 较旧的文件有独特功能 | 保留较新/更完整的，迁移独特功能 |

**合并步骤**:
```
1. 对比两个文件内容差异
2. 确定保留的目标文件（更完整/更规范）
3. 将独特功能迁移到目标文件
4. 更新所有引用
5. 删除冗余文件
6. 验证功能不受影响
```

** Benefits**: 减少维护成本、避免不一致、提升代码可读性

---

### CODE-006: 文件命名一致性规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-006 |
| **分类** | 代码规范 (CODE) |
| **标题** | 前后端文件命名一致性规范 |
| **描述** | 相同功能的文件在前后端应遵循一致的命名模式 |
| **适用场景** | 新建文件、代码审查 |

**命名模式**:
| 层级 | 前端 (Vue) | 后端 (Python) |
|------|-----------|---------------|
| 页面/View | `XxxView.vue` | `xxx_service.py` |
| 组件/Component | `Xxx.vue` | - |
| 模型/Model | `useXxxStore.js` (Pinia) | `models.py` |
| 工具/Util | `xxxUtil.js` | `xxx_utils.py` |

**命名原则**:
```
# ✅ 推荐：清晰的层级命名
views/TeamView.vue        # 页面
components/TeamCard.vue   # 组件
stores/teamStore.js      # 状态

# ❌ 避免：冗余/重复命名
views/TeamView.vue
views/Team.vue           # TeamView 已包含 Team，无需重复

services/team_service.py
services/team.py         # team_service.py 已说明是服务，无需简化
```

** Benefits**: 易导航、易理解、易维护

---

### CODE-007: 模块职责单一原则

| 属性 | 内容 |
|------|------|
| **编号** | CODE-007 |
| **分类** | 代码规范 (CODE) |
| **标题** | 模块职责单一原则 (SRP) |
| **描述** | 每个模块只负责一项职责，避免职责混杂导致的耦合 |
| **适用场景** | 模块设计、代码审查、重构 |

**职责判定**:
| 模块类型 | 职责 | 示例 |
|---------|------|------|
| `*View.vue` | 页面展示和用户交互 | 渲染模板、绑定事件 |
| `*Service.py` | 业务逻辑处理 | 计算、验证、编排 |
| `*Store.js` | 状态管理 | 响应式状态、持久化 |
| `*Adapter.js` | 协议转换 | platformAdapter |

**常见问题**:
```
# ❌ 职责混杂
TeamView.vue:
  - 包含业务逻辑 (应该放在 store)
  - 直接调用 API (应该通过 store)
  - 复杂计算 (应该提取为 utils)

# ✅ 职责分离
TeamView.vue      # 只管展示和交互
useTeamStore.js   # 状态管理
teamService.js    # API 调用
teamUtils.js      # 工具函数
```

** Benefits**: 可测试性、可复用性、可维护性

---

### CODE-008: 备份文件禁止规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-008 |
| **分类** | 代码规范 (CODE) |
| **标题** | 代码库中禁止保留备份文件 |
| **描述** | 禁止在代码库中保留 `*_backup/`、`*_old/`、`*-副本/`、`*-copy/` 等备份目录或文件，使用 Git 版本控制管理历史 |
| **适用场景** | 代码审查、CI/CD、文件清理 |

**禁止模式**:
```
# ❌ 代码库中禁止的备份文件/目录
lifecycle_old/                    # 包含 _old 后缀
lifecycle_backup/                # 包含 _backup 后缀
lifecycle - 副本/                 # 包含 - 副本 后缀
lifecycle - 副本 (2)/             # 包含 - 副本 (n) 后缀
models_20260503backup/           # 包含日期 + backup

FileView-Backup.vue              # 包含 -Backup 后缀
TeamView-Backup.vue              # 包含 -Backup 后缀
SpaceView_old.vue                # 包含 _old 后缀

api_backup.py                    # 包含 _backup 后缀
schemas - 副本.py                 # 包含 - 副本 后缀
```

**正确做法**:
```
✅ 使用 Git 管理历史
   git commit -m "重构: 合并 lifecycle 模块"
   # 之前的版本通过 git log / git diff 查看

✅ 如果必须临时保存工作进度
   git stash push -m "WIP: lifecycle 重构"
   # 或使用 git branch 创建临时分支

✅ 如果必须保留旧版本参考
   # 在代码注释中引用 Git commit hash
   # 不要在代码库中创建物理备份文件
```

**清理步骤**:
```bash
# 1. 查找所有备份文件/目录
find . -type d \( -name "*_old*" -o -name "*_backup*" -o -name "*副本*" -o -name "*copy*" \) 2>/dev/null

# 2. 确认无有效引用后删除
rm -rf lifecycle_old/ models_backup/ api_backup/

# 3. 验证删除后功能正常
pnpm run dev  # 前端验证
pytest        # 后端验证

# 4. 提交变更
git add -A
git commit -m "chore: 删除冗余备份文件和目录"
```

**CI/CD 检测**:
```yaml
# .github/workflows/check-no-backup.yml
name: Check No Backup Files

on:
  pull_request:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for backup files
        run: |
          BACKUP_FILES=$(find . -type d \( -name "*_old*" -o -name "*_backup*" -o -name "*副本*" \) 2>/dev/null | head -20)
          if [ -n "$BACKUP_FILES" ]; then
            echo "❌ 发现备份文件/目录，请删除后重试："
            echo "$BACKUP_FILES"
            exit 1
          fi
          echo "✅ 无备份文件"
```

** Benefits**:
- 代码库保持干净，无冗余文件
- 历史通过 Git 管理，而非物理备份
- 避免混淆（哪个是正式版本？）
- 便于自动化检查和 CI/CD 验证

---

### CODE-009: 页面/组件冗余检测与整合

| 属性 | 内容 |
|------|------|
| **编号** | CODE-009 |
| **分类** | 代码规范 (CODE) |
| **标题** | 页面与组件冗余检测及整合规范 |
| **描述** | 当两个页面或组件功能重叠时，应合并为一个，避免维护多份相似代码 |
| **适用场景** | 代码审查、重构、UI 整理 |

**冗余类型判断矩阵**:

| 情况 | 判定 | 操作 |
|------|------|------|
| 两个页面渲染相同内容 | 功能重复 | ✅ 合并 |
| 两个组件结构相同但命名不同 | 组件重复 | ✅ 合并 |
| 子目录页面与根目录页面同名 | 冗余层级 | ✅ 提升或合并 |
| `XxxView.vue` + `Xxx.vue` | 命名冗余 | ✅ 保留 `XxxView.vue` |
| `views/admin/Xxx.vue` + `views/Xxx.vue` | 路径冗余 | ✅ 合并到一处 |

**典型冗余模式**:

```
# ❌ 前端冗余模式
views/FileView.vue              # 主文件
views/file/FileView.vue         # 子目录重复
    → 合并到 views/FileView.vue

views/TeamView.vue             # 主文件
views/team/Team.vue            # team 子目录中的重复
    → 合并到 views/TeamView.vue

components/AdminPanel.vue      # 主文件
views/admin/AdminPanel.vue     # admin 子目录中的重复
    → 合并到 components/AdminPanel.vue

# ❌ 后端冗余模式
services/team_service.py       # 主文件
services/team.py              # 重复的简化命名
    → 删除 team.py，保留 team_service.py

services/space_service.py      # 主文件
services/spaces.py            # 重复的复数形式
    → 删除 spaces.py，保留 space_service.py
```

**整合决策树**:

```
发现问题文件 A 和文件 B 功能相似
        │
        ▼
┌───────────────────┐
│ 内容完全相同？     │
└───────────────────┘
        │
   是 → ✅ 删除 B，保留 A（更规范/更完整）
        │
   否 → ┌───────────────────┐
        │ 功能有重叠？       │
        └───────────────────┘
                │
           是 → ┌───────────────────┐
                │ 重叠部分可提取？  │
                └───────────────────┘
                    │
               是 → ✅ 重构提取公共组件 → 合并
                    │
               否 → ┌───────────────────┐
                    │ 哪个更完整/规范？│
                    └───────────────────┘
                        │
                   → ✅ 保留更完整的，迁移独特功能到它 → 删除另一个
```

**审计命令**:

```bash
# 1. 查找同名但在不同目录的 Vue 文件
find views/ -name "*.vue" | while read f; do
  basename "$f" .vue | sort | uniq -d | while read name; do
    find views/ -name "${name}.vue" -o -name "${name,,}.vue" 2>/dev/null
  done
done

# 2. 查找 views/ 和 views/sub/ 中同名的页面
find views/ -maxdepth 2 -name "*.vue" | sort

# 3. 查找 services/ 中可能重复的文件
ls services/*.py | sed 's/_service//g' | sed 's/.py//g' | sort | uniq -d
```

**CI/CD 检测**:

```yaml
# 检测同名文件出现在不同子目录
- name: Check for redundant Vue files
  run: |
    # 查找 views/ 下所有 .vue 文件，按文件名分组
    for f in $(find views/ -name "*.vue"); do
      name=$(basename "$f" .vue | tr '[:upper:]' '[:lower:]')
      echo "$name: $f"
    done | sort | uniq -d -w 1
    # 如果有输出，说明存在同名文件在不同目录
```

---

### CODE-010: 视图层级结构规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-010 |
| **分类** | 代码规范 (CODE) |
| **标题** | 视图层级结构扁平化原则 |
| **描述** | 同一功能域的视图应扁平组织，避免深层嵌套子目录导致导航困难 |
| **适用场景** | 项目初始化、目录结构审查 |

**目录结构规范**:

| 结构 | 推荐 | 说明 |
|------|------|------|
| 扁平结构 | `views/XxxView.vue` | ✅ 推荐，同级目录便于查找 |
| 子目录结构 | `views/sub/Xxx.vue` | ⚠️ 仅当子视图数量≥5 时使用 |
| 混合结构 | `views/admin/` | ⚠️ 仅用于大型管理后台的模块分离 |

**推荐目录结构**:

```
web/src/views/
├── LoginView.vue          # 登录
├── FileView.vue          # 文件管理
├── TeamView.vue          # 团队管理
├── SpaceView.vue         # 空间管理
├── StoragePoolView.vue   # 存储池
├── TrashView.vue         # 回收站
├── KnowledgeView.vue     # 知识库
├── FloatingWindow.vue    # 浮窗
├── MainLayout.vue        # 布局
├── Sidebar.vue          # 侧边栏
└── admin/               # 仅当管理后台模块≥5个时使用
    ├── PoolConfig.vue    # 池配置
    ├── QuotaDashboard.vue # 配额看板
    └── RoleConfig.vue    # 角色配置
```

**命名冲突检测**:

```bash
# 查找 views/ 下是否有子目录中的文件与根目录同名
for dir in views/*/; do
  sub_name=$(basename "$dir")
  if [ -f "views/${sub_name}View.vue" ] && [ -f "${dir}${sub_name}View.vue" ]; then
    echo "冲突: views/${sub_name}View.vue <-> ${dir}${sub_name}View.vue"
  fi
done
```

---

### DB-001: 使用 UUID 作为主键

| 属性 | 内容 |
|------|------|
| **编号** | DB-001 |
| **分类** | 数据库设计 (DB) |
| **标题** | 使用 UUID 作为主键避免 ID 泄露 |
| **描述** | 对外暴露的 ID 使用 UUID，内部自增 ID 不暴露 |
| **适用场景** | 所有实体表的主键设计 |

**示例**:
```python
# ✅ UUID 主键
id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

# 避免自增 ID 对外暴露
# ❌ id = Column(Integer, primary_key=True, autoincrement=True)
```

**Benefits**: 避免 ID 顺序预测、便于分布式部署、无法枚举

---

### DB-002: 统一时间戳字段

| 属性 | 内容 |
|------|------|
| **编号** | DB-002 |
| **分类** | 数据库设计 (DB) |
| **标题** | 统一的时间戳字段规范 |
| **描述** | 所有实体表包含 created_at、updated_at 字段 |
| **适用场景** | 所有业务表 |

**示例**:
```python
created_at = Column(DateTime, default=datetime.utcnow)
updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**Benefits**: 数据追踪、审计支持、缓存失效依据

---

### DB-003: 使用唯一索引防止重复数据

| 属性 | 内容 |
|------|------|
| **编号** | DB-003 |
| **分类** | 数据库设计 (DB) |
| **标题** | 关键字段添加唯一索引 |
| **描述** | 防止并发写入产生重复数据，应用层检查 + 数据库约束双重保险 |
| **适用场景** | 用户-空间关联、邀请记录等 |

**示例**:
```python
__table_args__ = (
    Index("ix_hfm_space_members_unique", "space_id", "user_id", unique=True),
)
```

**Benefits**: 数据一致性保证、并发安全、异常明确

---

### API-001: RESTful API 设计规范

| 属性 | 内容 |
|------|------|
| **编号** | API-001 |
| **分类** | API 设计 (API) |
| **标题** | RESTful API 命名与结构规范 |
| **描述** | 资源命名用复数名词，HTTP 方法表达操作语义 |
| **适用场景** | 新 API 设计 |

**规范**:
| 方法 | 用途 | 示例 |
|------|------|------|
| GET | 查询 | `GET /api/v1/users` |
| POST | 创建 | `POST /api/v1/users` |
| PUT | 全量更新 | `PUT /api/v1/users/{id}` |
| PATCH | 部分更新 | `PATCH /api/v1/users/{id}` |
| DELETE | 删除 | `DELETE /api/v1/users/{id}` |

---

### API-002: 统一的响应格式

| 属性 | 内容 |
|------|------|
| **编号** | API-002 |
| **分类** | API 设计 (API) |
| **标题** | 统一的 API 响应格式 |
| **描述** | 成功/失败响应格式统一，便于前端处理 |
| **适用场景** | 所有 API 接口 |

**响应格式**:
```json
// 成功响应
{
    "data": { ... },
    "code": 200
}

// 错误响应
{
    "detail": "错误描述",
    "code": 400
}
```

---

### API-003: 分页查询规范

| 属性 | 内容 |
|------|------|
| **编号** | API-003 |
| **分类** | API 设计 (API) |
| **标题** | 分页查询统一模式 |
| **描述** | 使用 limit/offset 或 cursor 方式实现分页 |
| **适用场景** | 列表查询接口 |

**示例**:
```python
GET /api/v1/users?limit=20&offset=0
{
    "items": [...],
    "total": 100,
    "limit": 20,
    "offset": 0
}
```

---

### FE-001: 组件单向数据流

| 属性 | 内容 |
|------|------|
| **编号** | FE-001 |
| **分类** | 前端开发 (FE) |
| **标题** | 组件单向数据流原则 |
| **描述** | Props 向下传递，事件向上冒泡，避免双向绑定 |
| **适用场景** | Vue/React 组件开发 |

**示例**:
```javascript
// Parent → Child (props)
<UserCard :user="currentUser" @select="handleSelect" />

// Child → Parent (emit)
emit('select', userId)
```

---

### FE-002: 前端错误边界处理

| 属性 | 内容 |
|------|------|
| **编号** | FE-002 |
| **分类** | 前端开发 (FE) |
| **标题** | 前端统一错误处理 |
| **描述** | 捕获 API 错误，转换为用户友好的提示 |
| **适用场景** | 所有 API 调用 |

**示例**:
```javascript
async function api(endpoint, options) {
    try {
        const res = await fetch(API_BASE + endpoint, options);
        if (!res.ok) throw await res.json();
        return await res.json();
    } catch (err) {
        showErrorToast(err.detail || '操作失败');
        throw err;
    }
}
```

---



---

### FE-004: Vue 3 Composition API 规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-004 |
| **分类** | 前端开发 (FE) |
| **标题** | Vue 3 Composition API 组件规范 |
| **描述** | 使用 Composition API (script setup) 编写 Vue 组件，确保响应式数据正确管理 |
| **适用场景** | 所有 Vue 3 组件开发 |

**规范**:
```javascript
// ✅ 推荐：使用 script setup
<script setup>
import { ref, computed, onMounted } from 'vue'

// 响应式状态
const count = ref(0)
const doubled = computed(() => count.value * 2)

// 生命周期
onMounted(() => {
  console.log('mounted')
})

// 方法
function increment() {
  count.value++
}
</script>

// ❌ 避免：Options API
export default {
  data() { return { count: 0 } },
  methods: { increment() { this.count++ } }
}
```

** Benefits**: 更好的类型推断、代码复用、逻辑分组

---

### FE-005: Pinia 状态管理规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-005 |
| **分类** | 前端开发 (FE) |
| **标题** | Pinia Store 设计与使用规范 |
| **描述** | 使用 Pinia 进行全局状态管理，遵循单一职责和模块化原则 |
| **适用场景** | 跨组件共享状态管理 |

**规范**:
```javascript
// stores/auth.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const token = ref(null)
  
  // Getters
  const isAuthenticated = computed(() => !!token.value)
  
  // Actions
  async function login(credentials) {
    const response = await api.login(credentials)
    token.value = response.token
    user.value = response.user
  }
  
  function logout() {
    token.value = null
    user.value = null
  }
  
  return { user, token, isAuthenticated, login, logout }
})

// ❌ 避免：在组件内修改 store 状态
// store.count++

// ✅ 推荐：通过 action 修改
// store.increment()
```

** Benefits**: 更好的调试支持、TypeScript 支持、模块化

---

### FE-006: PlatformAdapter 平台适配器模式

| 属性 | 内容 |
|------|------|
| **编号** | FE-006 |
| **分类** | 前端开发 (FE) |
| **标题** | Web/Tauri 平台能力统一抽象 |
| **描述** | 通过 platformAdapter.js 统一抽象平台能力，Web 端和 Tauri 端共用同一套代码 |
| **适用场景** | 需要调用原生能力的场景（窗口管理、文件系统、系统托盘） |

**架构**:
```javascript
// platformAdapter.js
const platform = {
  api: {
    isTauri: __TAURI_MODE__ === 'tauri',
    base: __API_BASE__,
    openPath: (path) => {
      if (platform.api.isTauri) {
        return tauri.invoke('open_path_in_finder', { path })
      }
      // Web fallback
      window.open(`file://${path}`)
    }
  }
}

// ✅ 组件中使用
import { platform } from '@/platformAdapter.js'

async function openFile(path) {
  try {
    await platform.api.openPath(path)
  } catch (err) {
    console.error('Failed to open path:', err)
  }
}
```

** Benefits**: Web/Tauri 代码共用、渐进增强、无缝降级

---

### FE-007: 构建时配置注入

| 属性 | 内容 |
|------|------|
| **编号** | FE-007 |
| **分类** | 前端开发 (FE) |
| **标题** | Vite 构建时环境变量注入 |
| **描述** | 通过 vite.config.js define 在构建时注入配置，避免运行时检测 |
| **适用场景** | API_BASE、WS_BASE、TAURI_MODE 等构建时确定的配置 |

**实现**:
```javascript
// vite.config.js
define: {
  __API_BASE__: JSON.stringify(process.env.VITE_API_BASE || '/api/v1'),
  __WS_BASE__: JSON.stringify(process.env.VITE_WS_BASE || 'ws://localhost:8080'),
  __TAURI_MODE__: JSON.stringify(process.env.NODE_ENV === 'production' ? 'tauri' : 'web'),
}
```

** Benefits**: 运行时零检测开销、生产构建更小、配置错误提前发现

---

### FE-008: 代码分割与按需加载

| 属性 | 内容 |
|------|------|
| **编号** | FE-008 |
| **分类** | 前端开发 (FE) |
| **标题** | Vite manualChunks 优化 bundle 大小 |
| **描述** | 通过 manualChunks 将大库（echarts、marked）独立分割，减小主 chunk 体积 |
| **适用场景** | 生产构建优化 |

**配置**:
```javascript
// vite.config.js
build: {
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
```

** 分割结果**:
```
vue-vendor:  ~107 KB ✅ (vue + vue-router + pinia)
echarts:    ~1,119 KB (echarts 库本身较大)
marked:      ~42 KB ✅
vue:        ~120 KB ✅ (主应用代码)
```

** Benefits**: 首屏加载更快、并行下载、缓存效率更高

---

### FE-009: 组件单向数据流

| 属性 | 内容 |
|------|------|
| **编号** | FE-009 |
| **分类** | 前端开发 (FE) |
| **标题** | Vue 组件 Props/Emit 规范 |
| **描述** | 父组件通过 props 向下传递数据，子组件通过 emit 向上传递事件 |
| **适用场景** | 所有 Vue 组件通信 |

**规范**:
```vue
<!-- Parent -->
<template>
  <ChildComponent 
    :items="items" 
    :loading="loading"
    @select="handleSelect"
    @delete="handleDelete"
  />
</template>

<!-- Child -->
<script setup>
const props = defineProps({
  items: { type: Array, required: true },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['select', 'delete'])

function onItemClick(item) {
  emit('select', item)
}
</script>

<!-- ❌ 避免：直接修改 props -->
<!-- props.items.push(newItem) -->

<!-- ✅ 推荐：emit 事件让父组件修改 -->
</script>
```

** Benefits**: 数据流可追踪、组件更易测试、避免意外修改

---

### FE-010: 前端 API 服务层封装

| 属性 | 内容 |
|------|------|
| **编号** | FE-010 |
| **分类** | 前端开发 (FE) |
| **标题** | 统一 API 服务封装 |
| **描述** | 通过 api.js 封装所有后端 API 调用，统一错误处理和响应格式 |
| **适用场景** | 所有前后端通信 |

**规范**:
```javascript
// services/api.js
const api = {
  async get(endpoint, params) {
    const res = await fetch(`${API_BASE}${endpoint}?${new URLSearchParams(params)}`)
    if (!res.ok) throw await res.json()
    return res.json()
  },
  
  async post(endpoint, data) {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    if (!res.ok) throw await res.json()
    return res.json()
  },
  
  // 文件上传
  async uploadFile(spaceId, file, path) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', path)
    const res = await fetch(`${API_BASE}/spaces/${spaceId}/files/upload`, {
      method: 'POST',
      body: formData
    })
    if (!res.ok) throw await res.json()
    return res.json()
  }
}

export { api }
```

** Benefits**: 统一错误处理、类型安全、易于维护

---

### FE-011: SSOT 单一构建源原则

| 属性 | 内容 |
|------|------|
| **编号** | FE-011 |
| **分类** | 前端开发 (FE) |
| **标题** | SSOT 单一构建源原则 |
| **描述** | web/dist 是唯一构建产物，前端只构建一次，Web 和 Tauri 共用同一套构建结果 |
| **适用场景** | "Web优先 + Tauri壳"模式的前端构建 |
| **G1-G11映射** | G3 (SSOT), G4 (一次构建) |

**原则**:
```
web/dist/
├── vue.html              # Vue SPA 主入口
├── floating-vue.html     # 浮窗入口
└── assets/              # 构建产物
    ├── vue-*.js
    ├── vue-vendor-*.js
    └── ...
```

**Tauri 配置**:
```json
// tauri.conf.json
{
  "bundle": {
    "resources": {
      "../web/dist": ""
    }
  }
}
```

**Benefits**:
- 前端只构建一次，Web 和 Tauri 共用
- 构建产物单一来源，易于追踪
- 支持 Web 独立部署到 Vercel/Netlify

---

### FE-012: Tauri 窗口入口配置规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-012 |
| **分类** | 前端开发 (FE) |
| **标题** | Tauri 窗口入口配置规范 |
| **描述** | Tauri 主窗口和浮窗使用独立的 Vue 入口文件，遵循窗口 URL 标准化 |
| **适用场景** | Tauri 多窗口配置 |
| **G1-G11映射** | G8 (窗口 URL 标准化) |

**窗口配置**:
```json
// tauri.conf.json
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

**入口文件对应**:
| 窗口 | 入口文件 | 用途 |
|------|---------|------|
| main | vue.html | 主窗口，产品交付层 |
| floating | floating-vue.html | 浮窗入口，alwaysOnTop |

**Benefits**: 窗口职责清晰，入口文件一一对应，URL 标准化

---

### FE-013: 事件委托模式（替代 window 暴露）

| 属性 | 内容 |
|------|------|
| **编号** | FE-013 |
| **分类** | 前端开发 (FE) |
| **标题** | 事件委托模式替代 window 函数暴露 |
| **描述** | 使用 `document.addEventListener` + `data-*` 属性实现事件委托，避免直接在 window 上暴露函数 |
| **适用场景** | Vue/HTML 中的 onclick、onchange 等事件处理 |
| **G1-G11映射** | G1 (壳层最小化)、window 暴露清理 |

**旧模式（已废弃）**:
```javascript
// ❌ 禁止：window 暴露函数
window.deletePool = function(poolId) {
  // 删除存储池
};
```

```html
<!-- ❌ 禁止：onclick 直接调用 window 函数 -->
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
    case 'refresh': refreshPool(poolId); break;
    case 'create': createPool(); break;
  }
});
```

```html
<!-- ✅ 推荐：data-* 属性 -->
<button data-pool-action="delete" data-pool-id="123">删除</button>
<button data-pool-action="refresh" data-pool-id="123">刷新</button>
<button data-pool-action="create">新建存储池</button>
```

** Benefits**:
- 避免全局命名空间污染
- 事件监听器只绑定一次，性能更好
- 符合渐进增强原则
- 便于 Vue 组件和原生 HTML 共存

---

### FE-014: Rust Tauri 壳最低维护规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-014 |
| **分类** | 前端开发 (FE) - Tauri 集成 |
| **标题** | Rust Tauri 壳最低维护原则 |
| **描述** | Rust 代码 ≤200 行，仅做窗口管理和系统能力调用，不承载任何业务逻辑 |
| **适用场景** | Tauri 桌面应用开发 |
| **G1-G11映射** | G1 (Tauri 最低维护量) |

**Rust 代码行数目标**:
```
目标: ≤ 200 行
当前: 200 行 ✅
```

**Rust 应做**:
```rust
// ✅ 窗口管理
#[tauri::command]
fn toggle_window(label: &str) -> Result<(), String> { /* ... */ }

// ✅ 系统托盘
fn setup_tray(app: &App) -> Result<(), Box<dyn Error>> { /* ... */ }

// ✅ 原生能力封装
#[tauri::command]
fn open_path_in_finder(path: &str) -> Result<(), String> { /* ... */ }
```

**Rust 不应做**:
```rust
// ❌ 禁止：业务逻辑
async fn process_file(file_id: &str) -> Result<File, Error> {
    // 这是后端 API 的职责，不应在 Tauri 壳中
    let file = db.query_file(file_id).await?;
    // ...
}
```

** Benefits**:
- 前端主导产品交付，业务逻辑在 Web 层
- Rust 仅处理原生能力，无需业务理解
- 便于前端开发者独立迭代
- 降低 Tauri 维护成本

---

### FE-015: Tauri IPC 通信规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-015 |
| **分类** | 前端开发 (FE) - Tauri 集成 |
| **标题** | Tauri IPC Commands/Events 通信规范 |
| **描述** | 前端通过 invoke 调用 Rust Commands，Rust 通过 emit 推送事件到前端 |
| **适用场景** | Vue 3 与 Tauri Rust 之间的双向通信 |
| **G1-G11映射** | G1 (IPC 机制) |

**Commands (前端 → Rust)**:

```rust
// Rust 端：定义 Command
#[tauri::command]
fn get_system_status() -> Result<SystemStatus, String> {
    Ok(SystemStatus {
        version: "1.0".to_string(),
        uptime: 12345,
    })
}

#[tauri::command]
fn open_path_in_finder(path: String) -> Result<(), String> {
    #[cfg(target_os = "macos")]
    std::process::Command::new("open")
        .arg(&path)
        .spawn()
        .map_err(|e| e.to_string())?;
    Ok(())
}
```

```javascript
// Vue 3 端：调用 Command
import { invoke } from '@tauri-apps/api/tauri';

async function getStatus() {
  try {
    const status = await invoke('get_system_status');
    console.log('System status:', status);
  } catch (err) {
    console.error('Failed to get status:', err);
  }
}
```

**Events (Rust → 前端)**:

```rust
// Rust 端：推送事件
app.emit("file-upload-progress", ProgressPayload {
    file_id: file_id.clone(),
    percent: (downloaded as f64 / total as f64 * 100.0) as u32,
}).map_err(|e| e.to_string())?;
```

```javascript
// Vue 3 端：监听事件
import { listen } from '@tauri-apps/api/event';

onMounted(() => {
  const unlisten = listen('file-upload-progress', (event) => {
    console.log('Upload progress:', event.payload);
    updateProgressBar(event.payload.percent);
  });

  onUnmounted(() => {
    unlisten.then(fn => fn());
  });
});
```

** Benefits**:
- 职责清晰：Commands 用于请求/响应，Events 用于异步推送
- 解耦：前端不直接依赖 Rust 实现
- 统一接口：便于 Web 模式下的 Mock

---

### WM-001: 跨端复用模式 (Cross-Platform Reuse)

| 属性 | 内容 |
|------|------|
| **编号** | WM-001 |
| **分类** | 工作模式 (WM) |
| **标题** | 跨端复用 - 一套代码覆盖桌面、移动、Web 三端 |
| **描述** | 在 "Web优先 + Tauri壳" 模式下，Web 源码同时服务于 Web 浏览器、Tauri 桌面应用、移动端 WebView |
| **适用场景** | 多平台产品交付 |
| **G1-G11映射** | G2 (Web 主导产品交付), G4 (一次构建) |

**复用架构**:
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        web/src/ (同一套源码)                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ Vue 3 SPA                                                          │   │
│  │ - views/ (页面组件)                                                │   │
│  │ - components/ (公共组件)                                            │   │
│  │ - composables/ (逻辑复用)                                          │   │
│  │ - stores/ (状态管理)                                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              ↓ 构建                                         │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐              │
│  │ Web 浏览器    │     │ Tauri 桌面   │     │ 移动端 WebView│              │
│  │ (Vite Dev)   │     │ (Bundle)    │     │ (Cordova等)  │              │
│  └──────────────┘     └──────────────┘     └──────────────┘              │
```

**平台差异处理**:
```javascript
// platformAdapter.js - 统一抽象
const platform = {
  // Tauri 桌面端
  desktop: {
    openPath: (path) => invoke('open_path_in_finder', { path }),
    toggleWindow: (label) => invoke('toggle_window', { label }),
  },
  
  // 移动端 WebView
  mobile: {
    openPath: (path) => cordova.exec('FileOpener.open', path),
    getDeviceInfo: () => cordova.exec('Device.info'),
  },
  
  // Web 浏览器（降级实现）
  web: {
    openPath: (path) => window.open(`file://${path}`),
    getDeviceInfo: () => ({ platform: 'web' }),
  }
};
```

**Benefits**:
- 前端只维护一套代码，降低维护成本
- 产品功能在各平台高度一致
- 便于统一测试和 CI/CD

---

### WM-002: 组件共享模式 (Component Sharing)

| 属性 | 内容 |
|------|------|
| **分类** | 工作模式 (WM) |
| **标题** | 组件共享 - Web、Tauri、移动端共享 UI 组件库 |
| **描述** | 所有 UI 组件放在 `web/src/components/` 目录，不做平台差异化，Tauri 仅做窗口包装 |
| **适用场景** | 需要跨平台保持 UI 一致性 |
| **G1-G11映射** | G2 (Web 主导交付), G3 (SSOT) |

**共享组件原则**:
| 原则 | 说明 |
|------|------|
| **平台无关** | 组件不直接调用 `window.__TAURI__`，通过 platformAdapter |
| **响应式设计** | 组件使用弹性布局，适配不同屏幕尺寸 |
| **单一职责** | 每个组件只负责 UI，不处理平台差异 |
| **Props 注入** | 平台差异通过 props 传入，组件内部不做判断 |

**示例**:
```vue
<!-- FileContextMenu.vue - 跨平台共享组件 -->
<script setup>
const props = defineProps({
  canPaste: Boolean,
  targetFile: Object,
})

const emit = defineEmits(['open', 'copy', 'cut', 'paste', 'delete'])

// 组件内部不做平台判断，只发出事件
function onDelete() {
  emit('delete', props.targetFile)
}
</script>

<!-- Tauri 桌面使用 -->
<FileContextMenu :can-paste="true" @delete="handleDelete" />

<!-- Web 浏览器使用 -->
<FileContextMenu :can-paste="clipboard.length > 0" @delete="handleDelete" />
```

**Benefits**:
- UI 高度一致，用户体验统一
- 组件可在任何平台复用
- 便于设计系统统一管理

---

### IPC-001: Commands/Events IPC 通信规范

| 属性 | 内容 |
|------|------|
| **编号** | IPC-001 |
| **分类** | IPC 通信 (IPC) |
| **标题** | Tauri Commands/Events IPC 机制 |
| **描述** | 前端通过 `invoke()` 调用 Rust Commands，Rust 通过 `emit()` 推送 Events 到前端 |
| **适用场景** | Vue 3 与 Tauri Rust 之间的双向通信 |
| **G1-G11映射** | G1 (IPC 机制) |

**IPC 机制对比**:

| 机制 | 方向 | 用途 | 示例 |
|------|------|------|------|
| **Commands/invoke** | 前端 → Rust | 请求-响应模式 | `invoke('show_window', { label: 'main' })` |
| **Events/listen** | Rust → 前端 | 异步推送模式 | `app.emit('file-changed', payload)` |

**Commands 规范**:
```rust
// Rust: 定义 Command（仅限窗口管理、系统能力）
#[tauri::command]
fn show_floating_window() -> Result<(), String> {
    // 窗口管理 - 这是 Tauri 应该做的
    app.get_window("floating").ok_or("Window not found")?.show()?;
    Ok(())
}

#[tauri::command]
fn hide_floating_window() -> Result<(), String> {
    app.get_window("floating").ok_or("Window not found")?.hide()?;
    Ok(())
}
```

```javascript
// Vue 3: 调用 Command
import { invoke } from '@tauri-apps/api/tauri';

async function showFloatingWindow() {
  try {
    await invoke('show_floating_window');
  } catch (err) {
    console.error('Failed to show floating window:', err);
  }
}
```

**Events 规范**:
```rust
// Rust: 推送事件（异步通知）
app.emit("tray-icon-clicked", { label: "floating" })
    .map_err(|e| e.to_string())?;
```

```javascript
// Vue 3: 监听事件
import { listen } from '@tauri-apps/api/event';

onMounted(() => {
  const unlisten = listen('tray-icon-clicked', (event) => {
    console.log('Tray icon clicked:', event.payload);
    // 处理托盘图标点击事件
  });

  onUnmounted(() => {
    unlisten.then(fn => fn());
  });
});
```

**Web 降级处理**:
```javascript
// Vue 3: Web 模式下 Events 不存在，使用 Mock
function listen(event, callback) {
  if (typeof window.__TAURI__ === 'undefined') {
    // Web 降级：不需要监听系统事件
    return Promise.resolve({ unsubscribe: () => {} });
  }
  return window.__TAURI__.event.listen(event, callback);
}
```

**Benefits**:
- 职责清晰：Commands 用于请求响应，Events 用于异步通知
- 解耦：前端不直接依赖 Rust 实现细节
- 统一接口：便于 Web 模式下的 Mock 和测试

---

### FE-003: 本地状态持久化规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-003 |
| **分类** | 前端开发 (FE) |
| **标题** | 用户偏好本地存储 |
| **描述** | 用户引导状态等偏好使用 localStorage 持久化 |
| **适用场景** | 引导状态、主题选择、折叠状态 |

**示例**:
```javascript
// 存储
localStorage.setItem(STORAGE_KEY, JSON.stringify([...dismissedEvents]));

// 读取
const dismissed = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
```

---

### TEST-001: TDD 红绿测试循环

| 属性 | 内容 |
|------|------|
| **编号** | TEST-001 |
| **分类** | 测试规范 (TEST) |
| **标题** | TDD 红绿重构循环 |
| **描述** | 先写失败测试 (Red)，再实现功能让测试通过 (Green)，最后重构 (Refactor) |
| **适用场景** | 新功能开发、复杂逻辑实现 |

**流程**:
```
Red（红）: 写一个失败测试，明确期望行为
    ↓
Green（绿）: 写最简单代码让测试通过
    ↓
Refactor（重构）: 优化代码，保持测试通过
    ↓
Repeat（重复）: 下一个功能
```

---

### TEST-002: 测试金字塔

| 属性 | 内容 |
|------|------|
| **编号** | TEST-002 |
| **分类** | 测试规范 (TEST) |
| **标题** | 合理的测试层级分布 |
| **描述** | 底层单元测试多、顶层 E2E 测试少，形成金字塔 |
| **适用场景** | 测试策略规划 |

**金字塔**:
```
        ┌─────────┐
        │   E2E   │  ← 少量，验证关键路径
       ┌┴─────────┴┐
       │  集成测试 │  ← 中量，验证模块协作
      ┌┴───────────┴┐
      │   单元测试  │  ← 大量，快速反馈
     ┌┴─────────────┴┐
```

---

### TEST-003: 契约测试自动化

| 属性 | 内容 |
|------|------|
| **编号** | TEST-003 |
| **分类** | 测试规范 (TEST) |
| **标题** | 前后端接口契约测试 |
| **描述** | 使用 Schemathesis 等工具基于 OpenAPI Schema 自动生成测试用例 |
| **适用场景** | API 变更检测、版本兼容性 |

**工具**: Schemathesis, Pact

---

### OPS-001: 环境配置分离

| 属性 | 内容 |
|------|------|
| **编号** | OPS-001 |
| **分类** | 运维部署 (OPS) |
| **标题** | 开发/测试/生产环境配置分离 |
| **描述** | 通过环境变量或配置文件管理不同环境参数 |
| **适用场景** | 部署配置 |

**示例**:
```python
config = {
    "dev": {"debug": True, "log_level": "DEBUG"},
    "test": {"debug": False, "log_level": "INFO"},
    "prod": {"debug": False, "log_level": "WARNING"}
}[ENV]
```

---

### OPS-002: 前后端独立部署

| 属性 | 内容 |
|------|------|
| **编号** | OPS-002 |
| **分类** | 运维部署 (OPS) |
| **标题** | 前端静态资源与后端 API 解耦 |
| **描述** | 前端通过 Vite Dev Server 开发，生产环境可独立部署到 CDN |
| **适用场景** | 前端构建与部署 |

**优势**:
- 前后端可独立迭代
- 前端可部署到 CDN 加速
- 后端 API 更简洁

---

### OPS-003: CSP 内容安全策略配置

| 属性 | 内容 |
|------|------|
| **编号** | OPS-003 |
| **分类** | 运维部署 (OPS) |
| **标题** | CSP 内容安全策略最小权限配置 |
| **描述** | Tauri 应用的 CSP 应遵循最小权限原则，移除不必要的 unsafe-eval |
| **适用场景** | Tauri 桌面应用安全配置 |

**验证方法**:
```bash
# 移除 unsafe-eval 后运行构建
cargo tauri build 2>&1 | grep -i error
```

**CSP 最佳实践**:
```json
{
  "csp": "default-src 'self' 'unsafe-inline' blob: data:; " +
         "connect-src 'self' http://localhost:8080 https://localhost:* ws://localhost:* wss://localhost:*; " +
         "script-src 'self' 'unsafe-inline' blob:; " +
         "style-src 'self' 'unsafe-inline' 'unsafe-hashed-attributes' blob: data: asset: https://localhost:*; " +
         "img-src 'self' data: blob: asset: https://localhost:*; " +
         "font-src 'self' data: blob: asset: https://localhost:*; " +
         "frame-src 'self' blob: asset:; worker-src 'self' blob:;"
}
```

**注意事项**:
- `unsafe-inline` 用于内联 CSS（Vite 生产构建需要）
- `unsafe-eval` **不需要** - Vite 生产构建不使用 eval
- 定期审查 CSP 配置，移除任何不必要的权限

**验证结果** (2026-05-04):
- ✅ 移除 `unsafe-eval` 后构建成功
- ✅ 应用启动正常，无 CSP 错误

---

## 四、贡献指南

### 添加新最佳实践

当发现新的最佳实践时，按以下格式添加：

```markdown
### XXX-NNN: 标题

| 属性 | 内容 |
|------|------|
| **编号** | XXX-NNN |
| **分类** | 分类名 (XXX) |
| **标题** | 最佳实践标题 |
| **描述** | 详细描述 |
| **适用场景** | 使用场景说明 |
| **示例** | 代码示例或架构图 |
```

### 更新现有最佳实践

- 添加版本历史记录
- 保持格式一致
- 添加相关最佳实践的交叉引用

---

## 五、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **v4.0** | **2026-05-05** | **CODE-008 备份文件禁止规范**: 禁止代码库中保留 `*_backup/`、`*_old/`、`*-副本/` 备份目录；使用 Git 版本控制管理历史；新增 CI/CD 检测 |
| **v3.2** | **2026-05-05** | **Vue 3 + Tauri 集成规范**: 新增 FE-013 事件委托模式 (window暴露清理)、FE-014 Rust壳最低维护规范 (G1)、FE-015 Tauri IPC通信规范 |
| **v3.1** | **2026-05-05** | **对齐GOALS.md v3.0**: 新增 FE-011 SSOT单一构建源原则 (G3/G4)、FE-012 Tauri窗口入口配置规范 (G8) |
| v3.0 | 2026-05-05 | **Vue 3 SPA 技术要求**: FE-004~FE-010 添加 Vue 3 Composition API、Pinia、PlatformAdapter、构建注入等规范；术语表增加 Vue 入口和平台适配器 |
| v2.0 | 2026-05-04 | 术语已对齐，FE-001~FE-003 前端规范完善 |
| 1.0 | 2026-05-03 | 初始版本：最佳实践领域管理表 |
---

## 九、Vue 3 前端开发最佳实践

> **分类**: FE (前端开发)
> **版本**: v3.0
> **更新日期**: 2026-05-05

### FE-004: Vue 3 Composition API 规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-004 |
| **分类** | 前端开发 (FE) |
| **标题** | Vue 3 Composition API 组件规范 |
| **描述** | 使用 `<script setup>` 语法，组合式函数封装逻辑，TypeScript 类型支持 |
| **适用场景** | Vue 3 组件开发 |

**规范**:
```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFileStore } from '@/stores/fileStore'

// 状态
const fileStore = useFileStore()
const files = computed(() => fileStore.files)

// 方法
async function handleUpload(file: File) {
  await fileStore.uploadFile(file)
}

// 生命周期
onMounted(() => {
  fileStore.loadFiles('/')
})
</script>
```

**Composables 规范**:
```javascript
// composables/useContextMenu.js
export function useContextMenu() {
  const visible = ref(false)
  const position = ref({ x: 0, y: 0 })
  
  function show(e: MouseEvent) {
    position.value = { x: e.clientX, y: e.clientY }
    visible.value = true
  }
  
  function hide() {
    visible.value = false
  }
  
  return { visible, position, show, hide }
}
```

---

### FE-005: Pinia Store 规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-005 |
| **分类** | 前端开发 (FE) |
| **标题** | Pinia 状态管理规范 |
| **描述** | 按领域拆分 Store，使用 `defineStore` + Composition API 风格 |
| **适用场景** | Vue 3 状态管理 |

**Store 规范**:
```javascript
// stores/fileStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useFileStore = defineStore('file', () => {
  // 状态
  const files = ref([])
  const selectedPaths = ref(new Set())
  const currentPath = ref('/')
  const loading = ref(false)
  
  // 计算属性
  const fileCount = computed(() => files.value.length)
  const selectedCount = computed(() => selectedPaths.value.size)
  
  // actions
  async function loadFiles(path: string) {
    loading.value = true
    try {
      const res = await api.get(`/files?path=${encodeURIComponent(path)}`)
      files.value = res.data
      currentPath.value = path
    } finally {
      loading.value = false
    }
  }
  
  async function uploadFile(file: File) {
    // 实现...
  }
  
  function toggleSelect(path: string) {
    if (selectedPaths.value.has(path)) {
      selectedPaths.value.delete(path)
    } else {
      selectedPaths.value.add(path)
    }
  }
  
  return {
    files, selectedPaths, currentPath, loading,
    fileCount, selectedCount,
    loadFiles, uploadFile, toggleSelect
  }
})
```

**Store 分割原则**:
| Store | 职责 | 状态 |
|-------|------|------|
| `useAuthStore` | 用户认证、会话、登录状态 | ✅ |
| `useFileStore` | 文件列表、选中、上传、删除 | ✅ |
| `useTeamStore` | 团队列表、成员管理 | ✅ |
| `useSpaceStore` | 空间列表、配额管理 | ✅ |
| `useGuidanceStore` | 用户引导状态 | ✅ |

---

### FE-006: Platform Adapter 模式

| 属性 | 内容 |
|------|------|
| **编号** | FE-006 |
| **分类** | 前端开发 (FE) |
| **标题** | Tauri/Web 平台抽象模式 |
| **描述** | 通过统一接口抽象 Tauri 和 Web 的差异，实现一套代码跨端运行 |
| **适用场景** | Tauri 桌面应用 + Web 混合开发 |

**实现规范**:
```javascript
// platform/index.js
const API_BASE = typeof __API_BASE__ !== 'undefined' ? __API_BASE__ : '/api/v1';
const WS_BASE = typeof __WS_BASE__ !== 'undefined' ? __WS_BASE__ : 'ws://localhost:8080';
const TAURI_MODE = typeof __TAURI_MODE__ !== 'undefined' ? __TAURI_MODE__ : 'web';

function tauriInvoke(command, args) {
  if (typeof tauri !== 'undefined' && typeof tauri.invoke === 'function') {
    return tauri.invoke(command, args);
  }
  throw new Error('Tauri command "' + command + '" not available in ' + TAURI_MODE + ' mode');
}

function tauriListen(eventName, callback) {
  if (window.__TAURI__ && window.__TAURI__.event) {
    return window.__TAURI__.event.listen(eventName, callback);
  }
  console.warn('Tauri event "' + eventName + '" not available');
  return Promise.resolve({ unsubscribe: () => {} });
}

export const platform = {
  api: {
    base: API_BASE,
    wsBase: WS_BASE,
    isTauri: TAURI_MODE === 'tauri',
    mode: TAURI_MODE,
    getSystemStatus: () => tauriInvoke('get_system_status'),
    openPath: (path) => tauriInvoke('open_path_in_finder', { path }),
    toggleWindow: (label) => tauriInvoke('toggle_window', { label }),
  },
  invoke: tauriInvoke,
  listen: tauriListen,
};
```

**使用方式**:
```vue
<script setup>
import platform from '@/platform'

async function openInFinder(path) {
  if (platform.api.isTauri) {
    await platform.api.openPath(path)
  } else {
    // Web fallback
    window.open('file://' + path)
  }
}
</script>
```

---

### FE-007: 契约测试规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-007 |
| **分类** | 前端开发 (FE) |
| **标题** | API 契约测试规范 |
| **描述** | 前后端接口契约测试，确保 API 兼容性 |
| **适用场景** | API 开发与集成 |

**测试规范**:
```javascript
// tests/contract/api.test.js
describe('API Contract Tests', () => {
  it('GET /files - should return file list', async () => {
    const res = await api.get('/files?path=/')
    expect(res.status).toBe(200)
    expect(res.data).toHaveProperty('files')
    expect(Array.isArray(res.data.files)).toBe(true)
  })
  
  it('POST /files/upload - should accept multipart/form-data', async () => {
    const formData = new FormData()
    formData.append('file', new Blob(['test'], { type: 'text/plain' }), 'test.txt')
    const res = await api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    expect(res.status).toBe(200)
  })
})
```

---

### FE-008: 路由懒加载规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-008 |
| **分类** | 前端开发 (FE) |
| **标题** | Vue Router 懒加载规范 |
| **描述** | 非首屏组件使用路由懒加载，优化首屏加载时间 |
| **适用场景** | Vue Router 配置 |

**规范**:
```javascript
// router/index.js
const routes = [
  {
    path: '/',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/files',
    component: () => import('@/views/FileView.vue')
  },
  {
    path: '/teams',
    component: () => import('@/views/TeamView.vue')
  },
]
```

---

## 十、"Web优先 + Tauri壳"模式技术要求

> **分类**: ARCH
> **版本**: v3.0
> **更新日期**: 2026-05-05

### ARCH-004: Web优先 + Tauri壳模式规范

| 属性 | 内容 |
|------|------|
| **编号** | ARCH-004 |
| **分类** | 架构设计 (ARCH) |
| **标题** | "Web优先 + Tauri壳"模式技术要求 |
| **描述** | 定义 Web 优先模式下的前端技术栈、架构原则、构建流程 |
| **适用场景** | Hermes File Manager 架构设计 |

**核心原则**:
| 原则 | 描述 | 对应目标 |
|------|------|---------|
| **SSOT** | web/dist 是唯一构建产物 | G3 |
| **跨端复用** | 一套 Vue 代码跑在 Web 和 Tauri | G2 |
| **契约先行** | API 接口先定义后实现 | G5 |
| **Rust 最小化** | Rust ≤ 200 行，仅做窗口管理 | G1 |

**层级架构**:
```
┌─────────────────────────────────────────────────────────────┐
│                    产品交付层 (Web/Vue)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Vue 3 SPA - UI渲染、业务逻辑、状态管理                │ │
│  │  - views/ (页面组件)                                  │ │
│  │  - stores/ (Pinia 状态)                               │ │
│  │  - composables/ (逻辑复用)                            │ │
│  │  - services/ (API 封装)                               │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Platform Adapter 层                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  platform/index.js - 统一抽象 Tauri/Web 差异          │ │
│  │  - platform.api (API_BASE, isTauri)                  │ │
│  │  - platform.invoke (调用 Rust 命令)                    │ │
│  │  - platform.listen (监听 Tauri 事件)                   │ │
│  └────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Tauri 壳层 (Rust)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Rust ≤ 200 行 - 仅窗口管理、系统托盘、文件系统         │ │
│  │  - main.rs (入口)                                     │ │
│  │  - tauri.conf.json (配置)                             │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**技术栈要求**:
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.x | 前端框架 |
| Pinia | 2.x | 状态管理 |
| Vue Router | 4.x | 路由管理 |
| TypeScript | 5.x | 类型安全 |
| Vite | 5.x | 构建工具 |
| Vitest | 1.x | 单元测试 |

**构建流程**:
```
1. pnpm run dev    # Vite 开发服务器
2. pnpm run build  # 构建到 web/dist/ (SSOT)
3. cargo tauri build # Tauri 打包（Rust ≤ 200行）
```

**验证清单**:
- [ ] Vue 3 Composition API 组件
- [ ] Pinia Store 按领域拆分
- [ ] Platform Adapter 统一抽象
- [ ] web/dist 是唯一构建产物
- [ ] Rust 代码 ≤ 200 行
- [ ] 契约测试 100% 覆盖

---

### CODE-005: DRY (Don't Repeat Yourself) 原则

| 属性 | 内容 |
|------|------|
| **编号** | CODE-005 |
| **分类** | 代码规范 (CODE) |
| **标题** | DRY 原则 - 代码去重与功能整合 |
| **描述** | 相同功能及页面必须整合为一个，避免重复代码和冗余 UI 元素 |
| **适用场景** | 代码审查、重构、新功能开发 |
| **问题示例** | 截图显示：两个 `文件` 导航重复、多个独立 Sidebar 冗余 |

**常见冗余问题**:
| 冗余类型 | 问题描述 | 解决方案 |
|----------|----------|----------|
| **导航重复** | 多个视图各自维护独立的文件导航 | 使用统一的 AppSidebar 组件 |
| **列表重复** | FileView、TeamView、SpaceView 各自实现类似的列表布局 | 提取公共 ListCard/ListView 组件 |
| **卡片重复** | 多个页面使用结构相同但独立的卡片组件 | 统一 Card 组件库 |
| **布局重复** | 每个视图都有独立的侧边栏实例 | 使用 Vue Router + Layout 布局组件 |

**识别方法**:
```bash
# 检测重复的组件名称
grep -r "Sidebar\|FileList\|TeamList" web/src/views/

# 检测重复的函数/方法
grep -rn "function.*List\|function.*Grid" web/src/

# 检测相似的 JSX/HTML 结构
# 使用 esbenw/prettier-eslint 格式化后人工比对
```

**整合步骤**:
```
1. 识别：找出所有重复的功能模块
2. 抽象：提取共同部分作为共享组件
3. 迁移：将业务逻辑移至 composables/stores
4. 替换：在各视图中原地替换为共享组件
5. 验证：确保功能完全等价
```

** Benefits**: 减少维护成本、保持一致性、降低 bug 概率

---

#### CODE-005-1: 功能合并决策规则（核心）

| 判定条件 | 处理方式 | 操作者 |
|----------|----------|--------|
| **功能完全一样** | **直接触发合并** | 开发者自行执行 |
| **功能有差异** | **提交审核** | 提 Issue/MR，由 Maintainer 决策 |

**决策流程**:
```
发现疑似重复代码
        ↓
    功能是否完全一样？
    ↓yes             ↓no
直接合并         提交审核
    ↓                   ↓
开发者执行       Maintainer 决策
```

**直接合并判定标准**:
| 检查项 | 标准 |
|--------|------|
| 函数签名 | 100% 相同 |
| 功能逻辑 | 100% 相同 |
| 依赖关系 | 可兼容 |

---

### CODE-006: 界面一致性原则

| 属性 | 内容 |
|------|------|
| **编号** | CODE-006 |
| **分类** | 代码规范 (CODE) |
| **标题** | 界面一致性 - 消除冗余 UI 元素 |
| **描述** | 同一应用内相同功能的 UI 元素必须唯一，避免多个功能相似但独立的 UI |
| **适用场景** | UI 审查、页面重构、设计系统实施 |

**冗余 UI 类型与解决方案**:
| 冗余类型 | 问题 | 解决方案 |
|----------|------|----------|
| **重复导航** | 左侧 Sidebar + 各视图内嵌导航 | 使用 Layout 布局组件 + Vue Router |
| **重复面包屑** | 每个视图独立的面包屑导航 | 统一 Breadcrumb 组件 |
| **重复操作栏** | 每个列表视图都有独立的工具栏 | 提取 Toolbar 组件 |
| **重复空状态** | 多个视图独立实现空状态 | 统一 EmptyState 组件 |

**导航统一规范**:
```
┌─────────────────────────────────────────────────────────────┐
│  AppLayout                                                │
│  ┌─────────┬───────────────────────────────────────────┐ │
│  │ Sidebar │  RouterView (动态视图)                     │ │
│  │         │  ┌─────────────────────────────────────┐ │ │
│  │ - 文件   │  │ FileView / TeamView / SpaceView     │ │ │
│  │ - 团队   │  │                                     │ │ │
│  │ - 存储池 │  │ 无需内嵌导航，Layout 已提供统一导航  │ │ │
│  │ - 知识库 │  │                                     │ │ │
│  │ - 回收站 │  │                                     │ │ │
│  └─────────┴───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

** Benefits**: 用户体验一致、减少认知负担、便于维护

---

### FE-016: 前端页面结构规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-016 |
| **分类** | 前端开发 (FE) |
| **标题** | 前端页面结构规范 - 统一布局与组件层次 |
| **描述** | Vue 3 SPA 必须使用统一的布局组件，禁止在视图内部实现可复用的导航/布局元素 |
| **适用场景** | Vue 3 组件开发、页面结构审查 |

**正确结构**:
```vue
<!-- AppLayout.vue - 全局布局组件 -->
<template>
  <div class="app-layout">
    <AppSidebar :nav-items="navItems" />
    <main class="app-content">
      <AppHeader />
      <RouterView />  <!-- 视图只负责内容，不包含布局 -->
    </main>
  </div>
</template>
```

```vue
<!-- FileView.vue - 视图组件，只负责内容 -->
<template>
  <div class="file-view">
    <FileToolbar @upload="handleUpload" />
    <FileGrid :files="files" @select="handleSelect" />
    <FilePreview />
  </div>
</template>
```

**错误结构（需重构）**:
```vue
<!-- FileView.vue - 错误：包含了自己的 Sidebar -->
<template>
  <div class="file-view">
    <FileSidebar />  <!-- ❌ 错误：每个视图不应有自己的 Sidebar -->
    <div class="file-content">
      ...
    </div>
  </div>
</template>
```

**布局层级**:
```
AppLayout (全局布局)
├── AppHeader (顶部栏)
├── AppSidebar (侧边导航) ← 全局唯一
└── RouterView (动态视图)
    ├── FileView
    ├── TeamView
    ├── SpaceView
    └── ...
```

** Benefits**: 布局统一、视图职责清晰、便于维护

---

### FE-017: 导航菜单统一规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-017 |
| **分类** | 前端开发 (FE) |
| **标题** | 导航菜单统一 - 单一来源原则 |
| **描述** | 应用导航必须从单一来源（Pinia store 或配置文件）生成，禁止在多个组件中独立定义 |
| **适用场景** | 导航菜单开发、侧边栏实现 |

**正确实现**:
```javascript
// stores/navigation.js - 导航配置单一来源
export const useNavigationStore = defineStore('navigation', () => {
  const navItems = ref([
    { id: 'files', label: '文件', icon: 'folder', route: '/files' },
    { id: 'teams', label: '团队', icon: 'users', route: '/teams' },
    { id: 'storage', label: '存储池', icon: 'database', route: '/storage' },
    { id: 'knowledge', label: '知识库', icon: 'book', route: '/knowledge' },
    { id: 'trash', label: '回收站', icon: 'trash', route: '/trash' },
  ])

  return { navItems }
})
```

```vue
<!-- AppSidebar.vue - 全局侧边栏 -->
<script setup>
import { useNavigationStore } from '@/stores/navigation'

const navStore = useNavigationStore()
</script>

<template>
  <nav class="app-sidebar">
    <NavItem 
      v-for="item in navStore.navItems" 
      :key="item.id"
      :label="item.label"
      :icon="item.icon"
      :to="item.route"
    />
  </nav>
</template>
```

**错误实现（需重构）**:
```vue
<!-- FileView.vue - 错误：在视图内定义导航 -->
<template>
  <div class="file-view">
    <nav class="file-nav">  <!-- ❌ 错误：重复的导航 -->
      <button>文件</button>
      <button>团队</button>
      <button>存储池</button>
    </nav>
    ...
  </div>
</template>
```

** Benefits**: 导航一致性、易于维护、便于动态控制

---

### REFACTOR-001: 冗余代码重构规范

| 属性 | 内容 |
|------|------|
| **编号** | REFACTOR-001 |
| **分类** | 重构规范 (REFACTOR) |
| **标题** | 冗余代码识别与重构流程 |
| **描述** | 系统性识别和消除代码冗余的标准流程 |
| **适用场景** | 代码审查、技术债务清理 |

**识别检查清单**:
```
代码冗余检查:
□ 是否存在重复的函数/方法？
□ 是否存在相似的组件结构？
□ 是否存在重复的样式定义？
□ 是否存在重复的业务逻辑？

UI 冗余检查:
□ 是否存在重复的导航元素？
□ 是否存在相似的页面布局？
□ 是否存在功能重叠的按钮/操作？
□ 是否存在多个实现相同功能的视图？

架构冗余检查:
□ 是否存在职责不清的模块？
□ 是否存在不合理的抽象层次？
□ 是否存在循环依赖？
```

**重构优先级**:
| 优先级 | 类型 | 影响 | 重构方式 |
|--------|------|------|----------|
| P0 | 功能冗余 | 高 | 合并功能，保留一个实现 |
| P1 | UI 冗余 | 中 | 提取共享组件，统一布局 |
| P2 | 代码重复 | 低 | 提取函数/类，统一样式 |

**重构验证**:
```bash
# 重构前后必须验证
1. 功能测试通过
2. 视觉回归通过
3. 单元测试通过
4. 无新增 lint 警告
```

** Benefits**: 降低维护成本、提升代码质量、减少潜在 bug

---

## 十一、代码冗余管理最佳实践

> **分类**: CODE (代码规范)
> **版本**: v3.0
> **更新日期**: 2026-05-05

### CODE-005: DRY 原则（Don't Repeat Yourself）

| 属性 | 内容 |
|------|------|
| **编号** | CODE-005 |
| **分类** | 代码规范 (CODE) |
| **标题** | DRY - 不要重复自己 |
| **描述** | 相同逻辑只实现一次，避免复制粘贴导致的维护问题 |
| **适用场景** | 所有代码编写场景 |

**规范**:
```javascript
// ❌ 重复代码 - 维护多份
function formatFileSizeKB(size) {
  return (size / 1024).toFixed(2) + ' KB';
}
function formatFileSizeMB(size) {
  return (size / 1024 / 1024).toFixed(2) + ' MB';
}

// ✅ DRY - 单一实现，参数化
function formatFileSize(size, unit = 'KB') {
  const units = { KB: 1024, MB: 1024 * 1024, GB: 1024 * 1024 * 1024 };
  const divisor = units[unit] || 1024;
  return (size / divisor).toFixed(2) + ' ' + unit;
}
```

**检测方法**:
| 方法 | 工具 | 说明 |
|------|------|------|
| ESLint | `no-duplicate` | 检测重复代码块 |
| SonarQube | Duplicate Code | 检测重复代码片段 |
| GitHub Copilot | AI 辅助 | 识别相似代码模式 |

---

### CODE-006: 服务/组件粒度设计

| 属性 | 内容 |
|------|------|
| **编号** | CODE-006 |
| **分类** | 代码规范 (CODE) |
| **标题** | 合理的服务与组件粒度 |
| **描述** | 服务和组件应该具有合理的粒度，避免过度拆分或过度耦合 |
| **适用场景** | 服务设计、组件设计 |

**粒度规范**:
```javascript
// ❌ 粒度过细 - 每个小功能一个文件
utils/formatDate.js
utils/formatTime.js
utils/formatDateTime.js
utils/formatFileSize.js

// ✅ 粒度合理 - 按职责分组
utils/formatters.js      // 所有格式化相关
utils/validators.js      // 所有验证相关
```

**粒度检测**:
| 问题 | 检测标准 | 解决方案 |
|------|---------|---------|
| 文件过大 | >500 行/文件 | 拆分职责 |
| 函数过长 | >100 行/函数 | 提取子函数 |
| 依赖过深 | >5 层调用 | 扁平化设计 |
| 职责扩散 | 单模块处理多领域 | 分离模块 |

---

### CODE-007: 前端组件整合规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-007 |
| **分类** | 代码规范 (CODE) |
| **标题** | Vue 组件整合最佳实践 |
| **描述** | 识别并整合冗余的 Vue 组件，减少重复代码 |
| **适用场景** | Vue 3 组件开发 |

**整合检查表**:
```javascript
// 检查点 1: 相似组件识别
// 问题: TeamCardA.vue 和 TeamCardB.vue 结构相似度 > 80%
// 解决方案: 提取公共 TeamCard.vue，通过 props 差异化

// 检查点 2: 重复逻辑提取
// 问题: FileList.vue 和 SpaceList.vue 都有相似的多选逻辑
// 解决方案: 提取 useSelection composable

// 检查点 3: API 调用统一
// 问题: 多个组件直接调用 api.getUsers()
// 解决方案: 统一通过 userStore 调用
```

**组件合并示例**:
```vue
<!-- ❌ 冗余: TeamCardA.vue, TeamCardB.vue, TeamCardC.vue -->
<!-- ✅ 整合: TeamCard.vue with props -->

<template>
  <div class="team-card" :class="size">
    <img :src="team.avatar" :alt="team.name" />
    <span>{{ team.name }}</span>
    <span v-if="showMemberCount">{{ team.memberCount }} 成员</span>
  </div>
</template>

<script setup>
defineProps({
  team: { type: Object, required: true },
  size: { type: String, default: 'medium' },  // small, medium, large
  showMemberCount: { type: Boolean, default: false }
})
</script>
```

---

### CODE-008: 后端服务整合规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-008 |
| **分类** | 代码规范 (CODE) |
| **标题** | Python 服务整合最佳实践 |
| **描述** | 识别并整合冗余的 Python 服务，减少重复逻辑 |
| **适用场景** | FastAPI 服务开发 |

**整合检查表**:
```python
# 检查点 1: 相似业务逻辑
# 问题: user_service.py 的 create_user 和 team_service.py 的 create_team 都有相似的验证逻辑
# 解决方案: 提取统一的 validators.py

# 检查点 2: 重复数据模型
# 问题: 多处定义相似的 TeamSchema
# 解决方案: 统一在 models.py 或 schemas/team.py

# 检查点 3: 重复 API 端点
# 问题: /api/teams 和 /api/v1/teams 都存在
# 解决方案: 统一使用 /api/v1/teams
```

**服务合并示例**:
```python
# ❌ 冗余: user_service.py, team_service.py, space_service.py 都有相似的 CRUD 方法
# ✅ 整合: 提取 base_service.py

# base_service.py
class BaseService:
    def get_by_id(self, model, id: str):
        return self.db.query(model).filter(model.id == id).first()
    
    def list_all(self, model, limit=100, offset=0):
        return self.db.query(model).limit(limit).offset(offset).all()

# user_service.py
class UserService(BaseService):
    def __init__(self):
        super().__init__(User)
    
    def create_user(self, data):
        # User 特定逻辑
        pass

# team_service.py  
class TeamService(BaseService):
    def __init__(self):
        super().__init__(Team)
    
    def create_team(self, data):
        # Team 特定逻辑
        pass
```

---

### CODE-009: 代码审查冗余检测清单

| 属性 | 内容 |
|------|------|
| **编号** | CODE-009 |
| **分类** | 代码规范 (CODE) |
| **标题** | Code Review 冗余检测标准 |
| **描述** | 在代码审查时检测冗余的标准检查清单 |
| **适用场景** | GitHub PR Review, 人工审查 |

**前端审查清单**:
```
[ ] 是否有相似的 Vue 组件？（结构相似度 > 70%）
[ ] 是否有重复的 composable 逻辑？（相同的 useXXX 实现多份）
[ ] 是否有冗余的 API 服务封装？（可直接调用的重复封装）
[ ] 组件 props 是否过于复杂？（> 7 个 props）
[ ] 是否有 Copy-Paste 的代码？

组件层级检查:
[ ] 是否有粒度过小的组件？（< 20 行）
[ ] 是否有粒度过大的组件？（> 500 行）
[ ] 组件依赖是否过深？（> 3 层）
```

**后端审查清单**:
```
[ ] 是否有相似的 Service 类？（业务逻辑重复）
[ ] 是否有重复的工具函数？（utils/ 中功能重叠）
[ ] 是否有相似的数据模型？（多个文件定义相似 Schema）
[ ] 是否有重复的验证逻辑？（各 endpoint 重复的验证代码）
[ ] API 端点是否冗余？（同一资源多个端点）

服务层级检查:
[ ] 单个文件是否过大？（> 500 行）
[ ] 单个函数是否过长？（> 100 行）
[ ] 服务间依赖是否过深？（> 5 层调用链）
[ ] 是否有不必要的继承层次？
```

---

## 十二、SOLID 原则与代码质量

> **分类**: ARCH (架构设计)
> **版本**: v3.0
> **更新日期**: 2026-05-05

### ARCH-005: SOLID 原则实践

| 属性 | 内容 |
|------|------|
| **编号** | ARCH-005 |
| **分类** | 架构设计 (ARCH) |
| **标题** | SOLID 原则应用 |
| **描述** | 单一职责、开闭原则、里氏替换、接口隔离、依赖倒置 |
| **适用场景** | 架构设计、代码重构 |

**SOLID 原则对照表**:
| 原则 | 缩写 | 描述 | Vue 示例 | Python 示例 |
|------|------|------|---------|-------------|
| 单一职责 | SRP | 一个类/组件只做一件事 | `FileCard` 只负责文件卡片渲染 | `UserService` 只处理用户逻辑 |
| 开闭原则 | OCP | 对扩展开放，对修改关闭 | 通过 slot/emit 扩展 | 通过继承/组合扩展 |
| 里氏替换 | LSP | 子类可替换父类 | - | Service 可替换 BaseService |
| 接口隔离 | ISP | 接口要小而专 | Props 只接收必要的 | 函数参数要具体 |
| 依赖倒置 | DIP | 依赖抽象而非具体 | Store 依赖接口 | Service 依赖 Repository 接口 |

**实践示例**:
```javascript
// ❌ 违反 SRP - 组件同时处理渲染和业务
const FileList = {
  template: '<div>{{ files.map(f => f.name).join(", ") }}</div>',
  async mounted() {
    this.files = await api.getFiles()  // 业务逻辑混入
    this.notify()  // 副作用
  }
}

// ✅ 遵循 SRP - 分离关注点
const FileList = {
  template: '<div>{{ files.map(f => f.name).join(", ") }}</div>',
  props: { files: Array }
}

// composable 处理业务
const useFileList = () => {
  const files = ref([])
  const loadFiles = async () => { files.value = await api.getFiles() }
  return { files, loadFiles }
}
```

```python
# ❌ 违反 DIP - 直接依赖具体实现
class UserService:
    def __init__(self):
        self.db = MySQLDatabase()  # 具体依赖
        
# ✅ 遵循 DIP - 依赖抽象
class UserService:
    def __init__(self, db: Database):  # 抽象接口
        self.db = db
```

---

### FE-018: Space 配额前端管理规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-018 |
| **分类** | 前端开发 (FE) |
| **标题** | Space 配额前端管理规范 |
| **描述** | Space 配额展示、配额条渲染、预警阈值处理的前端规范 |
| **适用场景** | SpaceView.vue、SpaceCard.vue 等空间相关组件 |

**配额条设计规范**:
```vue
<!-- ✅ 正确：使用 CSS 变量和 BEM 命名 -->
<div class="quota-bar">
  <div
    class="quota-bar__fill"
    :class="getQuotaClass(space.quota_usage)"
  ></div>
</div>

<script setup>
function getQuotaClass(usage) {
  if (usage > 0.9) return 'quota-bar__fill--danger'
  if (usage > 0.7) return 'quota-bar__fill--warn'
  return 'quota-bar__fill--ok'
}
</script>

<style scoped>
.quota-bar {
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  height: var(--spacing-xxs);
  overflow: hidden;
}

.quota-bar__fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s ease;
}

.quota-bar__fill--ok { background: var(--color-success); }
.quota-bar__fill--warn { background: var(--color-warning); }
.quota-bar__fill--danger { background: var(--color-danger); }
</style>
```

**配额阈值规范**:
| 使用率 | 等级 | CSS 类 | 动作 |
|--------|------|--------|------|
| < 70% | 正常 | `quota-bar__fill--ok` | 无 |
| 70-90% | 警告 | `quota-bar__fill--warn` | 发送通知 |
| > 90% | 危急 | `quota-bar__fill--danger` | 阻止上传 + 通知 |

** Benefits**: 配额状态清晰可见，用户体验一致

---

### FE-019: Space 邀请凭证生命周期管理

| 属性 | 内容 |
|------|------|
| **编号** | FE-019 |
| **分类** | 前端开发 (FE) |
| **标题** | Space 邀请凭证生命周期前端规范 |
| **描述** | 邀请码生成、使用、过期/撤销状态的前端处理规范 |
| **适用场景** | SpaceView.vue 成员管理、邀请功能 |

**邀请凭证状态流转**:
```
创建凭证 (created)
    │
    ├── 有效 (active) ──→ 已使用 (used) ──→ 满额 (exhausted)
    │
    └── 过期 (expired) / 撤销 (revoked)
```

**前端状态处理**:
```javascript
// ✅ 正确：凭证状态判断
function getCredentialStatus(cred) {
  if (!cred.is_active) return 'revoked'
  if (cred.expires_at && new Date(cred.expires_at) < new Date()) return 'expired'
  if (cred.max_uses && cred.used_count >= cred.max_uses) return 'exhausted'
  return 'active'
}

// ❌ 错误：硬编码状态判断
if (cred.status === 'active' && !cred.is_expired) { ... }
```

**邀请链接展示**:
```vue
<!-- ✅ 正确：显示完整邀请信息 -->
<div class="invite-info">
  <span class="invite-info__code">{{ credential.token }}</span>
  <span class="invite-info__status" :class="`invite-info__status--${status}`">
    {{ statusText }}
  </span>
  <span v-if="credential.expires_at" class="invite-info__expires">
    有效期至: {{ formatDate(credential.expires_at) }}
  </span>
</div>
```

** Benefits**: 凭证状态清晰，错误处理一致

---

### CODE-011: Space/Team 统一命名规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-011 |
| **分类** | 代码规范 (CODE) |
| **标题** | Space 与 Team 概念统一规范 |
| **描述** | 明确 Space 作为核心实体，Team 仅为历史兼容别名，避免概念混淆 |
| **适用场景** | 所有涉及空间/团队的文件命名、变量命名、文档描述 |

**概念澄清**:
| 旧概念 | 新概念 | 说明 |
|--------|--------|------|
| Team (团队) | Space (空间) | Space 是核心实体，Team 是 space_type="team" 的别名 |
| 团队成员 | SpaceMember | 通过 SpaceMember 关联 User 和 Space |
| 团队空间 | Space (space_type="team") | 多人协作空间 |
| 私人空间 | Space (space_type="private") | 个人专属空间，需审批创建 |

**命名规范**:
```
# ✅ 推荐：使用 Space 相关命名
SpaceService          # 服务层
SpaceView.vue         # 前端视图
space_type            # 空间类型字段
space_member_count    # 成员计数

# ❌ 避免：混合使用 Team/Space
TeamService + SpaceService  # 概念混淆
team_view + space_view      # 职责不清
```

**数据库字段规范**:
```python
# ✅ 正确：Space 为核心
class Space(Base):
    space_type = Column(String(16))  # "root" | "team" | "private"
    owner_id = Column(String(36))    # 所有者

# ❌ 错误：保留独立的 Team 概念
class Team(Base):
    name = Column(String(64))
    space_id = Column(String(36))  # Team 和 Space 分离
```

** Benefits**: 概念统一，减少认知负担，避免维护两套相似代码

---

### CODE-012: 枚举定义规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-012 |
| **分类** | 代码规范 (CODE) |
| **标题** | 状态枚举与字符串字面量规范 |
| **描述** | 前后端共用枚举必须在 engine/models.py 中定义，使用 PyEnum 或常量对象，禁止字符串散落代码中 |
| **适用场景** | 用户角色、团队状态、空间类型、邀请码状态等 |
| **相关领域** | RBAC, TENANT, LIFECYCLE |

**规范**:

```python
# ✅ 正确：在 engine/models.py 定义枚举
class TeamStatus(PyEnum):
    """团队状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ARCHIVED = "archived"


class TeamMemberRole(PyEnum):
    """团队成员角色枚举"""
    OWNER = "owner"
    MEMBER = "member"
    VIEWER = "viewer"
```

**前端常量对齐**:

```javascript
// constants/team.js
export const TEAM_STATUS = {
  ACTIVE: 'active',
  INACTIVE: 'inactive',
  PENDING: 'pending',
  ARCHIVED: 'archived'
}

// ❌ 错误：散落的字符串
const status = team.status === 'active' ? '活跃' : '未激活'
```

** Benefits**: 前后端状态一致、易于维护和扩展、类型安全

---

### CODE-013: 账号类型与权限层级规范

| 属性 | 内容 |
|------|------|
| **编号** | CODE-013 |
| **分类** | 代码规范 (CODE) |
| **标题** | 系统账号类型与空间成员角色双层权限模型 |
| **描述** | 系统使用两层权限模型：系统账号类型(Role.account_type)决定全局权限，空间成员角色(SpaceMember.role)决定资源访问权限 |
| **适用场景** | RBAC 权限设计、Admin 功能判断 |
| **相关领域** | AUTH, RBAC, TENANT |

**双层权限模型**:

```
┌─────────────────────────────────────────────────────────────────┐
│ Layer 1: 系统账号类型 (Role.account_type)                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ admin (priority=100) - 系统管理员，拥有全部管理功能          │ │
│ │ member (priority=50)  - 普通成员，按空间权限访问资源          │ │
│ │ guest  (priority=1)   - 访客，仅有最小权限                   │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓ 用户登录后
┌─────────────────────────────────────────────────────────────────┐
│ Layer 2: 空间成员角色 (SpaceMember.role)                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ owner - 空间所有者，可管理成员、设置配额、生成邀请码          │ │
│ │ member - 普通成员，可读写文件                                 │ │
│ │ viewer - 只读成员，仅能查看文件                               │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**权限判断逻辑**:

| 判断场景 | 判断依据 | 示例 |
|---------|---------|------|
| 能否访问管理后台 | `Role.account_type === 'admin'` | AdminDashboard 可见性 |
| 能否管理某团队 | `SpaceMember.role === 'owner'` AND `该用户是此团队成员` | 编辑团队、生成邀请码 |
| 能否查看某空间文件 | `SpaceMember.status === 'active'` | FileView 文件列表 |
| 能否上传文件到空间 | `SpaceMember.role in ['owner', 'member']` AND `quota充足` | 上传按钮可见性 |

**前端 Admin 判断（必须通过 Store）**:

```javascript
// ✅ 正确
const authStore = useAuthStore()
const isAdmin = computed(() => authStore.user?.role === 'admin')

// ❌ 错误
const isAdmin = localStorage.getItem('hfm_role') === 'admin'
```

** Benefits**: 清晰的权限分层、便于审计和追踪、符合最小权限原则

---

### FE-020: 存储池视图规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-020 |
| **分类** | 前端开发 (FE) |
| **标题** | 存储池视图组件规范 |
| **描述** | StoragePoolView.vue 组件结构、BEM 命名、设计 token、状态管理规范 |
| **适用场景** | StoragePoolView.vue 组件开发 |

**组件结构规范**:
```vue
<!-- ✅ 正确：BEM 命名 + 设计 token -->
<template>
  <div class="storage-pool-view">
    <header class="storage-pool-view__header">
      <h2 class="storage-pool-view__title">存储池</h2>
      <ButtonPrimary @click="showCreatePool">+ 创建存储池</ButtonPrimary>
    </header>

    <main class="storage-pool-view__content">
      <div class="storage-pool-view__grid">
        <article v-for="pool in pools" :key="pool.pool_id" class="pool-card">
          <!-- Card Header -->
          <header class="pool-card__header">
            <div class="pool-card__info">
              <h3 class="pool-card__name">{{ pool.name }}</h3>
            </div>
            <span class="pool-card__badge" :class="pool.status === 'active' ? 'pool-card__badge--active' : 'pool-card__badge--inactive'">
              {{ pool.status === 'active' ? '活跃' : '停用' }}
            </span>
          </header>

          <!-- Stats -->
          <dl class="pool-card__stats">
            <div class="pool-card__stat-row">
              <dt class="pool-card__stat-label">类型</dt>
              <dd class="pool-card__stat-value">{{ pool.type }}</dd>
            </div>
            <!-- ... -->
          </dl>

          <!-- Actions -->
          <footer class="pool-card__actions">
            <ButtonSecondary size="sm" @click="editPool(pool)">编辑</ButtonSecondary>
            <ButtonPearl size="sm" @click="confirmDeletePool(pool)">删除</ButtonPearl>
          </footer>
        </article>
      </div>
    </main>
  </div>
</template>
```

**BEM 命名对照表**:
| 块 (Block) | 元素 (Element) | 修饰符 (Modifier) | 说明 |
|------------|---------------|------------------|------|
| `storage-pool-view` | `__header` | | 视图容器 |
| `storage-pool-view` | `__content` | | 内容区 |
| `storage-pool-view` | `__grid` | | 卡片网格 |
| `storage-pool-view` | `__loading` | | 加载状态 |
| `storage-pool-view` | `__empty` | | 空状态 |
| `pool-card` | `__header` | | 卡片头部 |
| `pool-card` | `__badge` | `--active`, `--inactive` | 状态徽章 |
| `pool-card` | `__stats` | | 统计信息 |
| `pool-card` | `__stat-row` | | 统计行 |
| `pool-card` | `__stat-label` | | 统计标签 |
| `pool-card` | `__stat-value` | | 统计值 |
| `pool-card` | `__progress` | | 进度条 |
| `pool-card` | `__progress-fill` | `--ok`, `--warn`, `--danger` | 进度填充 |
| `pool-card` | `__actions` | | 操作按钮 |
| `details-panel` | `__header` | | 详情面板头部 |
| `modal-overlay` | `__card` | | 模态框卡片 |

**设计 token 使用**:
```css
/* ✅ 正确：使用 CSS 变量 */
.storage-pool-view {
  padding: var(--spacing-lg);
  background: var(--color-canvas-parchment);
}

.pool-card {
  padding: var(--spacing-lg);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.pool-card__badge--active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

/* ❌ 错误：硬编码值 */
.storage-pool-view {
  padding: 24px;
  background: #F5F5F7;
}
```

**配额进度条规范**:
```javascript
function getQuotaClass(usage) {
  if (usage > 0.9) return 'pool-card__progress-fill--danger'
  if (usage > 0.7) return 'pool-card__progress-fill--warn'
  return 'pool-card__progress-fill--ok'
}
```

| 使用率 | 等级 | CSS 类 | 颜色 token |
|--------|------|--------|-----------|
| < 70% | 正常 | `pool-card__progress-fill--ok` | `var(--color-primary)` |
| 70-90% | 警告 | `pool-card__progress-fill--warn` | `var(--color-warning)` |
| > 90% | 危急 | `pool-card__progress-fill--danger` | `var(--color-danger)` |

**Pinia Store 规范**:
```javascript
// stores/poolStore.js
export const usePoolStore = defineStore('pool', () => {
  const pools = ref([])
  const loading = ref(false)

  async function loadPools() {
    loading.value = true
    try {
      const data = await api.getPools()
      pools.value = data.pools || []
    } finally {
      loading.value = false
    }
  }

  async function createPool(name, type, size) {
    const pool = await api.createPool({ name, type, size })
    pools.value.push(pool)
    return pool
  }

  async function deletePool(poolId) {
    await api.deletePool(poolId)
    pools.value = pools.value.filter(p => p.pool_id !== poolId)
  }

  return { pools, loading, loadPools, createPool, deletePool }
})
```

**约束展示规范**:
```javascript
// 删除前检查生命周期约束
async function deletePool(poolId) {
  try {
    await api.deletePool(poolId)
    showToast({ type: 'success', title: '成功', message: '存储池已删除' })
    await loadPools()
  } catch (err) {
    if (err.code === 'STORAGE_POOL_IN_USE') {
      showToast({
        type: 'error',
        title: '无法删除',
        message: '该存储池仍有团队使用，请先迁移或删除团队'
      })
    }
  }
}
```

**存储池操作权限规范 (SPOOL Permission)**:

| 操作 | admin | editor | viewer | guest |
|------|-------|--------|--------|-------|
| 查看列表 | ✅ | ✅ | ✅ | ❌ |
| 查看详情 | ✅ | ✅ | ✅ | ❌ |
| 创建存储池 | ✅ | ❌ | ❌ | ❌ |
| 编辑存储池 | ✅ | ❌ | ❌ | ❌ |
| 删除存储池 | ✅ | ❌ | ❌ | ❌ |
| 清理存储池 | ✅ | ❌ | ❌ | ❌ |

**前端权限检查规范**:
```javascript
// ✅ 正确：使用 authStore 判断权限
import { useAuthStore } from '../stores/authStore.js'

const authStore = useAuthStore()
const isAdmin = computed(() => authStore.userRole === 'admin')

// 模板中条件渲染
<ButtonPrimary v-if="isAdmin" @click="showCreatePool">+ 创建存储池</ButtonPrimary>

// ❌ 错误：直接使用字符串判断
const isAdmin = localStorage.getItem('hfm_role') === 'admin'
```

**后端权限检查规范**:
```python
# ✅ 正确：检查 user.role.name
if user.role and user.role.name == "admin":
    # 允许操作
    pass

# ❌ 错误：缺少角色检查
if user.is_authenticated:
    # 任何登录用户都能操作
    pass
```

** Benefits**: 存储池视图统一规范，BEM 命名清晰，设计 token 一致，状态管理规范，权限控制完善

---

## 十三、KNOWLEDGE 知识库管理

### KNOWLEDGE-001: 知识库同步权限规范

| 属性 | 内容 |
|------|------|
| **编号** | KNOWLEDGE-001 |
| **分类** | 知识库管理 (KNOWLEDGE) |
| **标题** | 知识库同步操作权限规范 |
| **描述** | 知识库同步操作的权限检查和访问控制规范 |
| **适用场景** | llm_wiki 知识库同步功能 |

**账号类型体系**:

| 账号类型 | 说明 | 优先级 |
|----------|------|--------|
| admin | 系统管理员，拥有所有权限 | 100 |
| editor | 编辑者，可读写文件 | 50 |
| viewer | 查看者，仅读权限 | 10 |
| guest | 访客，最小权限 | 1 |

**功能可见性矩阵**:

| 账号类型 | 检查状态 | 同步设置 | 同步文件 | 搜索知识库 |
|----------|---------|---------|---------|-----------|
| admin | ✅ | ✅ | ✅ | ✅ |
| editor | ✅ | ✅ | ✅ | ✅ |
| viewer | ✅ | ❌ | ❌ | ✅ |
| guest | ✅ | ❌ | ❌ | ✅ |

**权限检查实现**:
```python
# ✅ 正确：基于角色的权限检查
async def sync_to_knowledge(source_path: str, project: str, user_id: str):
    user = await get_user(user_id)
    if user.role.priority < 50:  # editor 以下不能同步
        raise PermissionDenied("需要编辑者权限才能同步文档")

# ✅ 正确：检查 llm_wiki 服务状态
    if not await llm_wiki_is_running():
        raise ServiceUnavailable("llm_wiki 服务未启动")

# ❌ 错误：缺少权限检查
async def sync_to_knowledge(source_path: str, project: str, user_id: str):
    # 直接同步，无权限验证
    await llm_wiki_client.sync(source_path, project)
```

**Benefits**: 防止未授权用户同步文档，保护数据安全

---

### KNOWLEDGE-002: 知识库同步模式规范

| 属性 | 内容 |
|------|------|
| **编号** | KNOWLEDGE-002 |
| **分类** | 知识库管理 (KNOWLEDGE) |
| **标题** | 知识库同步模式选择规范 |
| **描述** | manual/interval/webhook 三种同步模式的选择和使用规范 |
| **适用场景** | llm_wiki 知识库同步设置 |

**同步模式对比**:
| 模式 | 说明 | 适用场景 | 配置项 |
|------|------|---------|--------|
| manual | 手动触发，单次同步 | 偶尔同步、不频繁更新 | 无需定时配置 |
| interval | 定时同步，固定间隔 | 定期更新、内容变化可预期 | `sync_interval` (分钟) |
| webhook | 外部触发，CI/CD 集成 | 自动构建、内容更新后立即同步 | webhook URL |

**模式配置示例**:
```python
# ✅ 正确：模式配置存储
SYNC_MODES = {
    "manual": {"type": "manual", "description": "手动同步"},
    "interval": {"type": "interval", "interval_minutes": 30},
    "webhook": {"type": "webhook", "url": "https://ci.example.com/webhook"}
}

# ❌ 错误：硬编码模式判断
if mode == "interval":
    schedule.every(30).minutes.do(sync)
```

**Webhook 触发格式**:
```yaml
# GitLab CI/CD 示例
sync_wiki:
  script:
    - curl -X POST https://api.example.com/knowledge/webhook \
      -H "Content-Type: application/json" \
      -d '{"project": "default", "source": "docs/", "token": "xxx"}'
```

**Benefits**: 灵活适应不同使用场景，支持自动化工作流

---

## 十四、FILE 文件操作管理

### FILE-001: 回收站操作权限规范

| 属性 | 内容 |
|------|------|
| **编号** | FILE-001 |
| **分类** | 文件操作 (FILE) |
| **标题** | 回收站操作权限与生命周期规范 |
| **描述** | 回收站（软删除）操作的权限检查、生命周期管理和安全删除规范 |
| **适用场景** | TrashService、文件删除/恢复功能、/trash 页面 |
| **关联规范** | ARCH-003 (生命周期约束前置检查) |

**回收站操作分类**:
| 操作 | 方法 | 说明 |
|------|------|------|
| 移入回收站 | `move_to_trash()` | 软删除，设置 deleted_at 时间戳 |
| 查看回收站 | `list_trash()` | 列出指定空间内已删除文件 |
| 恢复文件 | `restore_from_trash()` | 从回收站恢复文件 |
| 永久删除 | `permanent_delete()` | 物理删除，不可恢复 |
| 清空回收站 | `empty_trash()` | 清空指定空间所有回收站内容 |
| 自动清理 | `purge_expired()` | 清理超过保留期的文件 |

**权限矩阵** (v2.0 更新):

| 操作 \ 账号类型 | admin (系统) | owner (空间) | member (空间) | viewer (空间) |
|----------------|--------------|-------------|--------------|--------------|
| `list_trash` | ✓ | ✓ | ✓ | ✓ |
| `restore` | ✓ (任意) | ✓ (任意) | ✓ (仅自己的文件) | ✗ |
| `permanent_delete` | ✓ (任意) | ✓ (任意) | ✗ | ✗ |
| `empty_trash` | ✓ (任意) | ✓ (任意) | ✗ | ✗ |
| `auto_purge` | ✓ (调度) | - | - | - |

**说明**:
- `admin` (系统级角色): 拥有全部权限，可以操作任何空间的回收站
- `owner` (空间级角色): 空间所有者，可以操作空间内任何回收站内容
- `member` (空间级角色): 只能恢复自己删除的文件，不能永久删除
- `viewer` (空间级角色): 只能查看回收站，不能进行任何操作

**权限检查实现**:
```python
# ✅ 正确：操作前检查空间成员身份
async def restore_from_trash(space_id: str, item_id: str, user_id: str):
    # 1. 检查用户是否是空间成员
    if not await is_space_member(space_id, user_id):
        raise TrashAccessDenied("只有空间成员才能操作回收站")

    # 2. 检查文件所有权（如果是成员，只能操作自己的文件）
    item = await get_trash_item(item_id)
    if item.owner_id != user_id and not await is_space_owner(space_id, user_id):
        raise TrashAccessDenied("只能恢复自己删除的文件")

    # 3. 检查文件是否过期
    if is_item_expired(item):
        raise TrashExpired("该文件已超过保留期，无法恢复")

    # 4. 执行恢复
    await do_restore(item)

# ❌ 错误：缺少权限检查
async def restore_from_trash(space_id: str, item_id: str, user_id: str):
    item = await get_trash_item(item_id)
    await do_restore(item)
```

**生命周期约束 (ARCH-003)**:
```python
# ✅ 正确：删除前检查生命周期约束
LIFECYCLE_CONSTRAINTS = {
    "permanent_delete": (
        lambda ctx: ctx["item"].deleted_at is not None,
        "只有已进入回收站的文件才能永久删除",
        "请先将文件移入回收站"
    ),
    "empty_trash": (
        lambda ctx: ctx["space_id"] is not None,
        "必须指定空间ID",
        "请选择要清空的空间"
    ),
}

async def permanent_delete(space_id: str, item_id: str, user_id: str):
    ctx = {"space_id": space_id, "item_id": item_id, "user_id": user_id}

    # 前置条件检查
    for check_fn, error_msg, hint in LIFECYCLE_CONSTRAINTS["permanent_delete"]:
        if not check_fn(ctx):
            raise LifecycleConstraintViolation(error_msg, hint)

    await do_permanent_delete(item_id)
```

**回收站保留期配置**:
```python
# ✅ 正确：保留期可配置
DEFAULT_RETENTION_DAYS = 30  # 默认30天

@dataclass
class TrashConfig:
    retention_days: int = DEFAULT_RETENTION_DAYS
    max_trash_size_per_space: int = 1024 * 1024 * 1024  # 1GB
    auto_purge_interval_hours: int = 24

# ❌ 错误：硬编码保留期
if days_elapsed > 30:  # 硬编码
    await purge(item)
```

**安全删除检查清单**:
```
回收站操作前必须确认：
□ 用户是否是空间成员？
□ 用户是否有权限操作该文件（自己 vs 他人）？
□ 文件是否在保留期内？
□ 操作是否满足生命周期约束（ARCH-003）？
□ 是否需要二次确认（permanent_delete/empty_trash）？
```

**Benefits**: 防止未授权访问回收站、保护用户数据安全、符合 ARCH-003 生命周期约束规范

---

### FE-021: 前端权限控制规范 (基于角色的 UI 可见性)

| 属性 | 内容 |
|------|------|
| **编号** | FE-021 |
| **分类** | 前端开发 (FE) |
| **标题** | 前端权限控制 - 基于角色的 UI 可见性规范 |
| **描述** | 前端应根据用户角色控制 UI 元素的可见性，而不是仅依赖后端返回 403 错误 |
| **适用场景** | 所有 Vue 组件中需要权限控制的操作按钮/菜单/面板 |

**权限控制原则**:

| 原则 | 说明 |
|------|------|
| **可见即可操作** | 用户看到的元素都应该可以操作，避免 UI 权限和 API 权限不一致 |
| **防御性设计** | 前端做第一层过滤，后端做第二层验证 |
| **优雅降级** | 无权限时隐藏而非禁用（除非有明确提示） |

**角色优先级体系**:

```javascript
// utils/permissions.js
const ROLE_PRIORITY = {
  'admin': 100,    // 系统管理员
  'editor': 50,     // 编辑者
  'viewer': 10,     // 查看者
  'guest': 1,       // 访客
  'member': 50      // 成员 (editor 别名)
}
```

**前端角色判断**:

```javascript
// stores/authStore.js
const userRole = computed(() => user.value?.role || 'member')
const isAdmin = computed(() => userRole.value === 'admin')
const isOwner = computed(() => memberRole.value === 'owner')

// 使用权限工具 utils/permissions.js
import { hasPermission, isAdmin, isEditor } from '@/utils/permissions'

const canSync = computed(() => isEditor(authStore.userRole))
```

**KnowledgeView.vue 权限控制示例**:

```vue
<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'
import { isEditor } from '@/utils/permissions'

const authStore = useAuthStore()

// 编辑者+ 权限才能同步文件
const canSyncKnowledge = computed(() => isEditor(authStore.userRole))
</script>

<template>
  <div class="knowledge-view">
    <!-- 同步设置按钮: 仅 editor+ 可见 -->
    <button v-if="canSyncKnowledge" @click="showSyncSettings">
      同步设置
    </button>

    <!-- 同步到知识库区块: 仅 editor+ 可见 -->
    <section v-if="canSyncKnowledge" class="knowledge-view__section">
      ...
    </section>
  </div>
</template>
```

**路由守卫权限控制**:

```javascript
// router/index.js
const ROLE_PRIORITY = {
  'admin': 100,
  'editor': 50,
  'viewer': 10,
  'guest': 1
}

router.beforeEach(async (to, from, next) => {
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

**SpaceView.vue 权限控制示例**:

```vue
<template>
  <div class="space-view">
    <!-- Header: 创建空间按钮仅 admin 可见 -->
    <header class="space-view__header">
      <h3 class="space-view__title">我的空间</h3>
      <div class="space-view__actions">
        <button v-if="isAdmin" class="btn-apple-secondary" @click="showCrossTeamSpaces">
          跨团队协作
        </button>
        <button v-if="canCreateSpace" class="btn-apple-primary" @click="showCreateSpaceModal">
          + 创建空间
        </button>
      </div>
    </header>

    <!-- Members tab: 邀请/移除按钮仅 owner 或 admin 可见 -->
    <div v-show="activeTab === 'members'" class="tab-content">
      <div class="member-list">
        <div v-for="member in members" :key="member.user_id" class="member-item">
          <div class="member-item__info">
            <span class="member-item__name">{{ member.username }}</span>
            <span class="member-item__role">{{ member.role }}</span>
          </div>
          <!-- 移除按钮: 非 owner 自己，且有权限 -->
          <button
            v-if="canRemoveMember && member.role !== 'owner'"
            class="btn-apple-secondary btn-sm"
            @click="removeMember(member)"
          >
            移除
          </button>
        </div>
      </div>
      <!-- 邀请成员按钮: owner 或 admin -->
      <button v-if="canInviteMember" class="btn-apple-secondary space-view__mt" @click="showInviteSpaceMember">
        邀请成员
      </button>
    </div>

    <!-- Settings tab: 仅 owner 或 admin 可见 -->
    <div v-show="activeTab === 'settings'" class="tab-content">
      <div v-if="canEditSettings" class="settings-panel">
        <!-- 设置面板内容 -->
      </div>
      <div v-else class="space-view__empty">
        <p>您没有权限修改空间设置</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/authStore'

const authStore = useAuthStore()

// 权限计算属性
const isAdmin = computed(() => authStore.userRole === 'admin')
const isOwner = computed(() => authStore.currentMember?.role === 'owner')

const canCreateSpace = computed(() => isAdmin.value)
const canInviteMember = computed(() => isAdmin.value || isOwner.value)
const canRemoveMember = computed(() => isAdmin.value || isOwner.value)
const canDeleteSpace = computed(() => isAdmin.value || isOwner.value)
const canEditSettings = computed(() => isAdmin.value || isOwner.value)
</script>
```

**权限矩阵表**:

| 操作 | admin | owner | member | guest |
|------|-------|-------|--------|-------|
| 查看空间列表 | ✅ | ✅ | ✅ | ❌ |
| 创建 Space | ✅ | ❌ | ❌ | ❌ |
| 删除 Space | ✅ | ✅ (自己) | ❌ | ❌ |
| 邀请成员 | ✅ | ✅ | ❌ | ❌ |
| 移除成员 | ✅ | ✅ (非 owner) | ❌ | ❌ |
| 修改配额 | ✅ | ❌ | ❌ | ❌ |
| 查看活动 | ✅ | ✅ | ✅ | ❌ |
| 创建工作流 | ✅ | ✅ | ✅ | ❌ |
| 执行工作流 | ✅ | ✅ | ✅ | ❌ |

**API 权限 vs UI 权限对比**:

| 层面 | 职责 | 失败处理 |
|------|------|---------|
| **UI 层 (FE-021)** | 根据角色隐藏/显示元素 | 无操作入口 |
| **API 层** | 验证请求合法性 | 返回 403 + 错误信息 |
| **Service 层** | 执行业务逻辑校验 | 抛出业务异常 |

**常见错误示例**:

```vue
<!-- ❌ 错误：前端不做权限过滤，仅依赖后端返回 403 -->
<button @click="deleteSpace">删除</button>

<!-- ✅ 正确：前端根据角色隐藏无权限的按钮 -->
<button v-if="canDeleteSpace" @click="deleteSpace">删除</button>

<!-- ❌ 错误：禁用按钮但仍显示 -->
<button :disabled="!canDeleteSpace" @click="deleteSpace">删除</button>

<!-- ✅ 正确：无权限时隐藏而非禁用 -->
<button v-if="canDeleteSpace" @click="deleteSpace">删除</button>
```

**Benefits**:
- 用户体验：看不到无权限的操作，避免困惑
- 安全性：前端 + 后端双重验证
- 性能：减少无效请求

---

### FE-022: 前端 LIFECYCLE 操作预检规范

| 属性 | 内容 |
|------|------|
| **编号** | FE-022 |
| **分类** | 前端开发 (FE) |
| **标题** | 前端生命周期操作预检规范 |
| **描述** | 前端在进行生命周期操作前，应先调用验证接口进行预检，避免无效请求，提升用户体验 |
| **适用场景** | 加入团队、上传文件、创建空间、删除资源等需要前置条件验证的操作 |
| **相关领域** | LIFECYCLE, TENANT |

**预检原则**:

| 操作 | 预检接口 | 预检内容 | 预检失败处理 |
|------|---------|---------|------------|
| `join_team` | `GET /teams/{teamId}/validate-invite?code=XXX` | 邀请码有效性 | 提示用户邀请码无效/已过期 |
| `upload_file` | 前端计算 | 配额是否充足 | 提示配额不足，引导清理 |
| `create_space` | `GET /pools/available` | 是否有可用存储池 | 提示联系管理员 |
| `delete_space` | 前端计算 | 空间是否还有成员 | 提示先移除成员 |

**join_team 预检流程**:

```
用户输入邀请码
       ↓
调用 validateInviteCode 预检
       ↓
   ┌──┴──┐
   │     │
 成功   失败 → 显示友好错误信息
   │        (邀请码无效/已过期/次数用完)
   ↓
调用 joinTeam API
       ↓
   ┌──┴──┐
   │     │
 成功   失败 → 显示错误信息
   ↓
刷新团队列表
```

**join_team 预检示例**:

```javascript
// ✅ 正确：先预检邀请码再加入
async function joinTeamWithValidation(token) {
  loading.value = true
  try {
    // 1. 预检邀请码
    await api.validateInviteCode(token)
  } catch (err) {
    // 预检失败，显示友好错误
    showToast({
      type: 'error',
      title: '无法加入团队',
      message: err.message || '邀请码无效或已过期'
    })
    return
  }

  // 2. 预检通过，执行加入
  try {
    await api.joinTeam(token)
    showToast({ type: 'success', title: '成功', message: '已加入团队' })
    joinToken.value = ''
    loadTeams()
  } catch (err) {
    showToast({ type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

// ❌ 错误：直接调用加入 API（用户体验差）
async function joinTeam(token) {
  await api.joinTeam(token)  // 可能因邀请码无效直接失败
}
```

**Benefits**:
- 减少无效 API 请求
- 提供更好的用户体验（提前知道结果）
- 符合 LIFECYCLE 约束规范
- 减少服务器负载

---

## 十五、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| **v5.6** | **2026-05-06** | **新增 FE-022 前端 LIFECYCLE 操作预检规范** |
| **v5.5** | **2026-05-06** | **新增 CODE-012 枚举定义规范、CODE-013 账号类型与权限层级双层权限模型** |
| **v5.4** | **2026-05-06** | **新增 FE-021 前端权限控制规范 (基于角色的 UI 可见性)** |
| **v5.3** | **2026-05-06** | **新增 FE-020 存储池视图规范 (BEM 命名 + 设计 token + 状态管理)** |
| **v5.2** | **2026-05-06** | **新增 FILE-001 回收站操作权限规范，与 ARCH-003 生命周期约束联动** |
| **v5.1** | **2026-05-06** | **新增 KNOWLEDGE-001 知识库同步权限规范、KNOWLEDGE-002 知识库同步模式规范** |
| **v5.0** | **2026-05-06** | **新增 FE-018 Space配额前端规范、FE-019 Space邀请凭证规范、CODE-011 Space/Team统一命名规范** |
| v4.0 | 2026-05-05 | CODE-008 备份文件禁止规范：禁止代码库中保留 `*_backup/`、`*_old/` 备份目录 |
| v3.2 | 2026-05-05 | Vue 3 + Tauri 集成规范：FE-013 事件委托模式、FE-014 Rust壳最低维护、FE-015 Tauri IPC |
| v3.1 | 2026-05-05 | 对齐GOALS.md v3.0：FE-011 SSOT、FE-012 Tauri窗口入口 |
| v3.0 | 2026-05-05 | Vue 3 SPA 技术要求：FE-004~FE-010 Composition API、Pinia、PlatformAdapter |
| v2.0 | 2026-05-04 | 术语对齐，FE-001~FE-003 前端规范完善 |
| v1.0 | 2026-05-03 | 初始版本：最佳实践领域管理表 |
