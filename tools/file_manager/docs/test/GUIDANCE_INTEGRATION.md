# 引导系统集成架构文档

> **文档状态**: ✅ 已完善 (2026-05-02 更新)
> **版本**: v1.0
> **日期**: 2026-05-02
> **基于分析**: 自顶向下开发模式 + 架构文档分析

---

## 一、架构现状

### 1.1 双轨制引导系统

系统存在**两套独立的引导系统**，它们之间没有直接集成：

```
┌─────────────────────────────────────────────────────────────────┐
│                    前端引导系统 (Vanilla JS)                      │
├─────────────────────────────────────────────────────────────────┤
│  guidance-trigger-boot.js                                       │
│  ├── 监听 DOM 事件 (file:uploaded, team:joined, etc.)           │
│  ├── 触发 window.guidance (如果存在)                             │
│  ├── 触发 window.__vueGuidance (Pinia store)                    │
│  └── 派发 CustomEvent 'guidance:trigger'                        │
│                                                                  │
│  引导组件:                                                        │
│  ├── WorkflowTour.js (4步引导)                                   │
│  ├── NotebookTour.js (4步引导)                                   │
│  └── Vue: WorkflowTourGuide.vue, NotebookTourGuide.vue           │
└─────────────────────────────────────────────────────────────────┘
                              ↕ (无直接集成)
┌─────────────────────────────────────────────────────────────────┐
│                    后端引导引擎 (Python)                          │
├─────────────────────────────────────────────────────────────────┤
│  guidance_engine.py                                              │
│  ├── GuidanceEvent 枚举定义                                       │
│  ├── EventBus 订阅 (auth.register, auth.login.success, etc.)     │
│  ├── Tour 管理与进度追踪                                          │
│  └── 生命周期约束检查                                             │
│                                                                  │
│  约束引擎:                                                        │
│  └── lifecycle_engine.py (11条规则)                              │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 前端事件流

```
DOM Event                  guidance-trigger-boot.js          Vue Component
──────────────────────────────────────────────────────────────────────────
file:uploaded    ───→    triggerGuidance('FIRST_FILE_UPLOADED')
                               │
                               ├── window.guidance.trigger()
                               ├── window.__vueGuidance.trigger()
                               └── dispatchEvent('guidance:trigger')
                                                                          │
                                                                          ↓
                                                             guidanceStore 监听
                                                             lifecycleStore 监听
```

### 1.3 后端事件流

```
EventBus                       guidance_engine.py              lifecycle_engine.py
──────────────────────────────────────────────────────────────────────────────
auth.register         ───→    _handle_event()
                                    │
                                    ├── _detect_guidance_event()
                                    ├── _build_context()
                                    └── trigger()
                                          │
                                          └── _start_tour()
                                               │
                                               └── 检查约束 (如果配置)
```

---

## 二、事件命名对照

### 2.1 前端 DOM 事件 (guidance-trigger-boot.js)

| DOM Event | 映射到 | 说明 |
|-----------|--------|------|
| `file:uploaded` | FIRST_FILE_UPLOADED | 文件上传成功 |
| `file:shared` | SHARE_FILE | 文件分享 |
| `user:registered` | USER_REGISTERED | 用户注册 |
| `team:joined` | TEAM_JOINED | 加入团队 |
| `team:created` | TEAM_JOINED (isFirstJoin=true) | 创建团队 |
| `member:invited` | MEMBER_INVITED | 邀请成员 |
| `workflow:executed` | WORKFLOW_EXECUTED | 工作流执行 |
| `workflow:created` | WORKFLOW_EXECUTED | 工作流创建 |
| `notebook:created` | FIRST_NOTEBOOK_CREATED | 笔记本创建 |
| `quota:warning` | QUOTA_WARNING | 配额警告 |
| `private:space:requested` | PRIVATE_SPACE_REQUESTED | 私人空间申请 |
| `collaboration:established` | CROSS_TEAM_COLLABORATION | 跨团队协作 |

### 2.2 后端 GuidanceEvent (guidance_engine.py)

| GuidanceEvent | 触发条件 | 说明 |
|---------------|---------|------|
| USER_REGISTER | EventType.AUTH_REGISTER | 用户注册 |
| USER_LOGIN | EventType.AUTH_LOGIN_SUCCESS | 登录成功 |
| TEAM_CREATED | EventType.ADMIN_USER_CREATE | 团队创建 |
| FIRST_FILE_UPLOAD | EventType.FILE_WRITE | 首次文件写入 |
| SPACE_CREATED | - | 空间创建 (未实现) |
| MEMBER_INVITED | - | 成员邀请 (未实现) |
| FILE_UPLOAD_COMPLETE | - | 文件上传完成 (未实现) |
| TOUR_START | - | 引导开始 (内部) |
| TOUR_COMPLETE | - | 引导完成 (内部) |
| TOUR_STEP | - | 引导步骤 (内部) |

### 2.3 不一致问题

**问题**: 前端使用 `FIRST_FILE_UPLOADED` (全大写下划线)，后端使用 `FIRST_FILE_UPLOAD` (无下划线)。

**影响**: 两套系统无法直接通信，前端触发的事件后端收不到。

---

## 三、生命周期约束集成

### 3.1 边缘 Case 约束

| 约束码 | 触发条件 | 日志级别 | 监控状态 |
|--------|---------|---------|----------|
| POOL_TEAMS_MIGRATING | 存储池有团队迁移中 | WARNING | ⚠️ 无监控面板 |
| QUOTA_RESERVED | 并发上传配额预留 | WARNING | ⚠️ 无监控面板 |
| MEMBER_RECENTLY_REMOVED | 24小时内移除的成员 | WARNING | ⚠️ 无监控面板 |
| SPACE_HAS_PENDING_REQUESTS | 有待审核私人空间申请 | WARNING | ⚠️ 无监控面板 |

### 3.2 QUOTA_RESERVED 约束详解

```python
# lifecycle_engine.py line 85-90
self._register_default("QUOTA_RESERVED", ConstraintType.QUOTA,
    lambda ctx: ctx.get("quota_reserved", 0) == 0 or ctx.get("can_override", False),
    "当前有文件正在上传，配额已被临时占用",
    {"label": "刷新状态", "action": "refreshQuota"},
    action="upload_file"
)
```

**问题**: `can_override=True` 可以绕过此约束，可能导致配额超卖。

**建议**: 评估 `can_override` 的使用场景，确保不影响配额准确性。

### 3.3 FileUpload 配额预留机制

**状态**: ✅ 已实现 (2026-05-02)

```python
# engine/models.py - FileUpload 模型
class FileUpload(Base):
    """上传跟踪表 - 记录正在进行的文件上传，用于配额预留计算"""
    __tablename__ = "hfm_file_uploads"

    id = Column(String(36), primary_key=True)
    space_id = Column(String(36), ForeignKey("hfm_spaces.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("hfm_users.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    uploaded_bytes = Column(BigInteger, default=0)
    status = Column(String(16), default="uploading")  # "uploading" | "completed" | "failed" | "cancelled"
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
```

**配额预留查询**:

```python
# lifecycle_engine.py line 360-375
def get_quota_reserved(self, space_id: str, db_factory) -> int:
    from .models import FileUpload
    session = db_factory()
    try:
        total = session.query(FileUpload.file_size).filter(
            FileUpload.space_id == space_id,
            FileUpload.status == "uploading"
        ).all()
        return sum(r[0] for r in total) if total else 0
    finally:
        session.close()
```

**FileUploadService** (`engine/file_upload_service.py`):

| 方法 | 调用时机 |
|------|---------|
| `create_upload()` | 用户开始上传时 |
| `update_progress()` | 上传进行中（可选） |
| `mark_completed()` | 上传成功时 |
| `mark_failed()` | 上传失败时 |
| `cleanup_stale_uploads()` | 清理超时未完成的记录 |

**现状**: FileUpload 模型已实现，`get_quota_reserved()` 方法已完善，配额预留计算已可工作。

**待办**: 前端上传组件需在上传开始时调用 `FileUploadService.create_upload()`，完成后调用 `mark_completed()` 或 `mark_failed()`。

---

## 四、待办事项

### 4.1 高优先级

| ID | 待办 | 影响 | 难度 |
|----|------|------|------|
| G1 | 统一前后端事件命名规范 | 前后端引导系统集成 | 中 |
| G2 | 实现后端 EventBus → 前端 guidanceStore 的推送 | 实时引导触发 | 高 |
| G3 | 边缘 case 约束监控面板 | 可观测性 | 中 |

### 4.2 中优先级

| ID | 待办 | 影响 | 难度 |
|----|------|------|------|
| G4 | 评估 QUOTA_RESERVED can_override 安全性 | 配额准确性 | 高 |
| G5 | FileUpload service 方法暴露 | 配额预留可见性 | 中 |
| G6 | guidanceEngine.js 与后端 guidance_engine.py 集成 | 架构统一 | 高 |

---

## 五、建议的集成方案

### 5.1 方案A: WebSocket 实时推送 (推荐)

```
后端 guidance_engine
       │
       ├── EventBus 事件触发
       │
       └── WebSocket 推送 'guidance:trigger' 到前端
                    │
                    └── 前端 guidanceStore 接收
                              │
                              └── Vue 组件响应
```

**优点**: 实时性强，与 AdminDashboard WebSocket 共用通道
**缺点**: 需要后端 WebSocket 服务支持

### 5.2 方案B: 前端轮询

```
前端 guidanceStore
       │
       ├── 定期调用 GET /api/v1/guidance/pending
       │
       └── 后端返回待触发引导列表
```

**优点**: 简单易实现
**缺点**: 实时性差，有延迟

---

## 六、相关文档

- [LIFECYCLE_CONSTRAINTS.md](./LIFECYCLE_CONSTRAINTS.md) - 生命周期约束
- [NEW_USER_GUIDE.md](./NEW_USER_GUIDE.md) - 新手引导设计
- [MODULE_2_LIFECYCLE_CONSTRAINTS.md](./MODULE_2_LIFECYCLE_CONSTRAINTS.md) - 约束详细设计
