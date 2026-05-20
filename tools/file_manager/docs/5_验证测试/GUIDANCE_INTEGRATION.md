# 引导系统集成架构文档

> **文档状态**: ✅ 已更新 (2026-05-05)
> **版本**: v1.2
> **日期**: 2026-05-05
> **基于分析**: Vue 3 + Pinia 架构 + Tauri 桌面应用
> **更新说明**: 待办事项更新为完成状态，E2E 测试已完成

---

## 一、架构现状

### 1.1 技术栈

```
┌─────────────────────────────────────────────────────────────────┐
│                    Vue 3 + Pinia 前端                            │
├─────────────────────────────────────────────────────────────────┤
│  guidanceStore.js                                               │
│  ├── 引导事件定义 (GUIDANCE_EVENTS)                              │
│  ├── 引导上下文管理 (context)                                    │
│  ├── 引导弹窗状态 (modalVisible)                                 │
│  ├── Tour 管理 (currentTour, steps)                              │
│  └── localStorage 持久化                                         │
│                                                                  │
│  暴露接口:                                                       │
│  ├── window.__vueGuidance.trigger()                              │
│  ├── window.__vueGuidance.dismiss()                              │
│  ├── window.guidance (别名)                                      │
│  └── window.triggerGuidance() (兼容)                             │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    Tauri 桌面壳 (Rust)                           │
├─────────────────────────────────────────────────────────────────┤
│  WebView 承载 Vue 3 SPA                                          │
│  ├── main.rs: 窗口管理、IPC                                      │
│  └── tauri.conf.json: 权限配置                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
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

---

## 二、事件命名规范

### 2.1 前端事件定义 (guidanceStore.js)

| 事件键 | 值 | 说明 |
|--------|-----|------|
| `USER_REGISTERED` | `'user_registered'` | 用户注册 |
| `TEAM_JOINED` | `'team_joined'` | 加入团队 |
| `FIRST_FILE_UPLOADED` | `'first_file_uploaded'` | 首次文件上传 |
| `MEMBER_INVITED` | `'member_invited'` | 成员邀请 |
| `WORKFLOW_EXECUTED` | `'workflow_executed'` | 工作流执行 |
| `QUOTA_WARNING` | `'quota_warning'` | 配额警告 |
| `PRIVATE_SPACE_PENDING` | `'private_space_pending'` | 私人空间待审核 |
| `CROSS_TEAM_COLLAB` | `'cross_team_collab'` | 跨团队协作 |

### 2.2 引导定义示例

```javascript
const GUIDANCE_DEFINITIONS = {
  [GUIDANCE_EVENTS.USER_REGISTERED]: {
    title: '欢迎使用 Hermes File Manager',
    message: '您已成功注册！首先创建一个团队或加入现有团队开始存储文件。',
    actions: [
      { label: '创建我的团队', action: 'CREATE_TEAM', icon: '👥' },
      { label: '浏览现有团队', action: 'LIST_TEAMS', icon: '🔍' }
    ],
    condition: (ctx) => ctx.teams?.length === 0,
    priority: 100
  },
  // ...
}
```

### 2.3 触发方式

```javascript
// 方式1: 直接调用
window.__vueGuidance.trigger('user_registered', { teams: [] })

// 方式2: 兼容旧API
window.triggerGuidance('user_registered', { teams: [] })

// 方式3: CustomEvent
window.dispatchEvent(new CustomEvent('guidance:trigger', {
  detail: { event: 'user_registered', context: { teams: [] } }
}))
```

---

## 三、后端事件映射

### 3.1 后端 GuidanceEvent (guidance_engine.py)

| GuidanceEvent | 触发条件 | 前端对应 |
|---------------|---------|----------|
| USER_REGISTER | EventType.AUTH_REGISTER | user_registered |
| USER_LOGIN | EventType.AUTH_LOGIN_SUCCESS | - |
| TEAM_CREATED | EventType.ADMIN_USER_CREATE | team_joined |
| FIRST_FILE_UPLOAD | EventType.FILE_WRITE | first_file_uploaded |
| SPACE_CREATED | - | - |
| MEMBER_INVITED | - | member_invited |
| FILE_UPLOAD_COMPLETE | - | - |
| TOUR_START | - | (内部) |
| TOUR_COMPLETE | - | (内部) |
| TOUR_STEP | - | (内部) |

---

## 四、生命周期约束集成

### 4.1 约束类型

| 约束码 | 触发条件 | 日志级别 | 说明 |
|--------|---------|---------|------|
| POOL_TEAMS_MIGRATING | 存储池有团队迁移中 | WARNING | 存储池迁移中禁止删除 |
| QUOTA_RESERVED | 并发上传配额预留 | WARNING | 当前有文件正在上传 |
| MEMBER_RECENTLY_REMOVED | 24小时内移除的成员 | WARNING | 成员移除冷静期 |
| SPACE_HAS_PENDING_REQUESTS | 有待审核私人空间申请 | WARNING | 存在待审核申请 |

### 4.2 配额预留机制

**FileUpload 模型** (`engine/models.py`):

```python
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

**配额预留查询** (`lifecycle_engine.py`):

```python
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

---

## 五、Tour 引导步骤

### 5.1 工作流引导

```javascript
export const WORKFLOW_GUIDE_STEPS = [
  { target: '#workflowTab', content: '点击「工作流」标签', position: 'bottom' },
  { target: '#newWorkflowBtn', content: '点击「+ 新建工作流」', position: 'bottom' },
  { target: '#workflowTemplate', content: '选择「文件归档流程」模板', position: 'right' },
  { target: '#workflowSave', content: '配置步骤并保存', position: 'top' }
]
```

### 5.2 笔记本引导

```javascript
export const NOTEBOOK_GUIDE_STEPS = [
  { target: '#notebookTab', content: '点击「笔记本」标签', position: 'bottom' },
  { target: '#newNotebookBtn', content: '点击「+ 新建笔记本」', position: 'bottom' },
  { target: '#notebookName', content: '输入笔记本名称', position: 'right' },
  { target: '#notebookSave', content: '保存笔记本', position: 'top' }
]
```

---

## 六、Tauri 集成

### 6.1 窗口配置

```json
// tauri.conf.json
{
  "build": {
    "devtools": true
  }
}
```

### 6.2 事件桥接

前端通过 `window.__vueGuidance` 暴露的接口与 Tauri 后端通信。

---

## 七、测试验证

### 7.1 E2E 测试位置

```
web/tests/e2e/
├── contract/          # 接口契约测试
└── *.spec.ts         # Playwright 测试用例
```

### 7.2 验证要点

| 功能 | 验证方式 |
|------|---------|
| 引导事件触发 | E2E: guidance-flow.spec.ts |
| 引导状态持久化 | E2E: 检查 localStorage |
| Tour 步骤展示 | E2E: 验证 DOM 结构 |
| 配额预留 | 单元测试 + 集成测试 |

---

## 八、待办事项

### 8.1 高优先级

| ID | 待办 | 影响 | 状态 | 验证文件 |
|----|------|------|------|----------|
| T1 | E2E 测试覆盖引导流程 | 质量保障 | ~~~E2E 测试覆盖引导流程~~~ ✅ 已完成 | `guidance.spec.js` (923行, 29tests) |
| T2 | 配额预留前后端联调 | 配额准确性 | ~~~配额预留前后端联调~~~ ✅ 已实现 | `lifecycle_engine.py` (get_quota_reserved) |

### 8.2 中优先级

| ID | 待办 | 影响 | 状态 | 验证文件 |
|----|------|------|------|----------|
| T3 | 后端 EventBus → 前端推送 | 实时引导 | ~~~后端 EventBus → 前端推送~~~ ✅ 已实现 | `event_bus.py` |
| T4 | 引导数据统计分析 | 产品优化 | ~~~引导数据统计分析~~~ ✅ 已实现 | guidanceStore.js (recordTrigger/complete/dismiss/action) |

### 8.3 已完成任务

| ID | 待办 | 影响 | 状态 | 验证文件 |
|----|------|------|------|----------|
| T5 | 文件上传触发引导事件 (TC-M3-001) | 引导完整性 | ~~~文件上传触发引导事件验证~~~ ✅ 已完成 | `FileView.vue` |
| T6 | 引导触发点 DOM 绑定 (TC-M3-006) | 引导可用性 | ~~~触发点正确绑定到 DOM~~~ ✅ 已完成 | `useGuidanceTrigger.js` |

---

## 九、相关文档

- [RTM.md](../7_tracking/RTM.md) - 需求追踪矩阵
- [RTM_REQUIREMENTS_TRACEABILITY.md](../7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md) - 需求可追溯性
- [TOP_DOWN_DEVELOPMENT.md](../1_architecture/TOP_DOWN_DEVELOPMENT.md) - 开发方法论