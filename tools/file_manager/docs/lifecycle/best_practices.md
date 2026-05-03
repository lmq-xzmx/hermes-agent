# 最佳实践领域管理表 (Best Practices Registry)

> **版本**: 1.0
> **更新日期**: 2026-05-03
> **项目**: Hermes File Manager
> **状态**: 维护中

---

## 一、目的与范围

本文档记录和维护项目开发过程中产生的所有**最佳实践（Best Practices）**，涵盖：
- 架构设计模式
- 代码规范与技巧
- 数据库设计规范
- API 设计规范
- 前端开发规范
- 测试最佳实践
- 运维与部署规范

---

## 二、分类索引

| 分类 | 说明 | 最佳实践数量 |
|------|------|-------------|
| **ARCH** | 架构设计 | 3 |
| **CODE** | 代码规范 | 4 |
| **DB** | 数据库设计 | 3 |
| **API** | API 设计 | 3 |
| **FE** | 前端开发 | 3 |
| **TEST** | 测试规范 | 3 |
| **OPS** | 运维部署 | 2 |

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
| 1.0 | 2026-05-03 | 初始版本：最佳实践领域管理表 |