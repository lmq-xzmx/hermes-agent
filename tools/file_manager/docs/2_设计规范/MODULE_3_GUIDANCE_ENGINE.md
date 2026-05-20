# 模块三：用户引导引擎 - 详细设计

> **实现状态**: ✅ ~80%
>
> 状态说明: 核心引擎已实现，前端引导 UI 已完成，引导与服务集成待完善
>
> **架构更新 (2026-05-06)**: 前端已迁移至 Vue 3 SPA，使用 vue.html 入口，GuidanceModal 已重构为 Vue SFC

---

## 架构说明

### 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Vue 3 SPA)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              guidanceStore (Pinia)                       │   │
│  │  - showGuidance: boolean                               │   │
│  │  - guidanceConfig: GuidanceConfig                      │   │
│  │  - guidanceStats: Map<event, Progress>                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │              GuidanceModal.vue                            │   │
│  │  - 单个/多个 actions                                     │   │
│  │  - "不再显示" 复选框                                     │   │
│  │  - ESC 键关闭                                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │              useGuidance (Composable)                    │   │
│  │  - trigger(event, context)                             │   │
│  │  - onUserRegistered(), onTeamJoined()                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                        Backend (Python)                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 GuidanceEngine                           │   │
│  │  - Event-driven trigger via EventBus                    │   │
│  │  - Constraint-aware (LifecycleEngine integration)       │   │
│  │  - Tour management with step tracking                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────▼─────────────────────────────┐   │
│  │                 GuidanceEvent (Enum)                      │   │
│  │  - USER_REGISTER, USER_LOGIN                            │   │
│  │  - TEAM_CREATED, SPACE_CREATED, MEMBER_INVITED         │   │
│  │  - FIRST_FILE_UPLOAD, FILE_UPLOAD_COMPLETE             │   │
│  │  - TOUR_START, TOUR_COMPLETE, TOUR_STEP                 │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. 核心数据结构

### 1.1 GuidanceEvent 枚举

```python
class GuidanceEvent(str, Enum):
    """Guidance trigger events."""
    # Auth events
    USER_REGISTER = "guidance.user_register"
    USER_LOGIN = "guidance.user_login"

    # Space/Team events
    TEAM_CREATED = "guidance.team_created"
    SPACE_CREATED = "guidance.space_created"
    MEMBER_INVITED = "guidance.member_invited"

    # File operations
    FIRST_FILE_UPLOAD = "guidance.first_file_upload"
    FILE_UPLOAD_COMPLETE = "guidance.file_upload_complete"

    # Tour events
    TOUR_START = "guidance.tour_start"
    TOUR_COMPLETE = "guidance.tour_complete"
    TOUR_STEP = "guidance.tour_step"
```

### 1.2 引导步骤

```python
@dataclass
class GuidanceStep:
    """引导步骤定义"""
    id: str                           # 步骤唯一标识
    title: str                        # 步骤标题
    content: str                      # 引导内容（支持 HTML）
    target_selector: str              # 目标元素 CSS 选择器
    position: str                     # 弹出位置: top/bottom/left/right
    button_text: str                   # 按钮文本
    button_action: str                # 按钮回调函数名

@dataclass
class GuidanceTour:
    """引导流程"""
    id: str                           # 流程唯一标识
    name: str                         # 流程名称
    description: str                  # 流程描述
    steps: List[GuidanceStep]         # 步骤列表
    trigger_event: GuidanceEvent      # 触发事件
    conditions: Dict[str, Any]        # 触发条件

@dataclass
class GuidanceContext:
    """引导上下文"""
    user_id: str
    event: GuidanceEvent
    data: Dict[str, Any]
```

---

## 2. 引导引擎 (Python)

### 2.1 核心类

```python
# engine/guidance_engine.py

class GuidanceEngine:
    """用户引导引擎"""

    def __init__(self, event_bus=None, lifecycle_engine=None):
        self._event_bus = event_bus
        self._lifecycle = lifecycle_engine
        self._tours: Dict[GuidanceEvent, List[GuidanceTour]] = {}
        self._user_progress: Dict[str, Dict[str, int]] = {}  # user_id -> tour_id -> step

    def register_tour(self, tour: GuidanceTour):
        """注册引导流程"""
        if tour.trigger_event not in self._tours:
            self._tours[tour.trigger_event] = []
        self._tours[tour.trigger_event].append(tour)

    def trigger(self, event: GuidanceEvent, context: GuidanceContext):
        """触发引导"""
        tours = self._tours.get(event, [])
        for tour in tours:
            if tour.check_conditions(context.data):
                # 检查生命周期约束
                if self._lifecycle:
                    constraint = self._lifecycle.check("show_guidance", context.data)
                    if constraint:
                        logger.debug(f"Constraint {constraint.code} prevents guidance")
                        continue
                self._start_tour(tour, context)

    def _start_tour(self, tour: GuidanceTour, context: GuidanceContext):
        """开始引导流程"""
        # 发送引导开始事件到前端
        if self._event_bus:
            self._event_bus.publish(
                Event(type=f"guidance:start:{tour.id}", data={
                    "tour": tour.to_dict(),
                    "user_id": context.user_id
                })
            )

    def get_user_progress(self, user_id: str, tour_id: str) -> int:
        """获取用户引导进度"""
        return self._user_progress.get(user_id, {}).get(tour_id, 0)

    def advance_step(self, user_id: str, tour_id: str):
        """推进引导步骤"""
        if user_id not in self._user_progress:
            self._user_progress[user_id] = {}
        self._user_progress[user_id][tour_id] = \
            self._user_progress[user_id].get(tour_id, 0) + 1
```

### 2.2 默认引导流程

```python
# 注册默认引导
DEFAULT_TOURS = [
    GuidanceTour(
        id="create_team_tour",
        name="创建团队引导",
        description="引导新用户创建第一个团队",
        trigger_event=GuidanceEvent.USER_REGISTER,
        conditions={"no_teams": True},
        steps=[
            GuidanceStep(
                id="step_1",
                title="创建团队",
                content="点击下方按钮创建您的第一个团队",
                target_selector="#create-team-btn",
                position="top",
                button_text="下一步",
                button_action="next_step"
            ),
            # ... more steps
        ]
    ),
    GuidanceTour(
        id="upload_file_tour",
        name="上传文件引导",
        description="引导用户完成首次文件上传",
        trigger_event=GuidanceEvent.FIRST_FILE_UPLOAD,
        conditions={},
        steps=[...]
    )
]
```

---

## 3. 前端实现

### 3.1 guidanceStore (Pinia)

```javascript
// web/src/stores/guidanceStore.js

export const useGuidanceStore = defineStore('guidance', () => {
  const showGuidance = ref(false)
  const guidanceConfig = ref(null)
  const guidanceStats = ref(new Map())  // event -> { triggered, completed, dismissed }

  function trigger(event, context = {}) {
    // 发送到后端获取引导配置
    api.getGuidance(event, context).then(config => {
      if (config) {
        guidanceConfig.value = config
        showGuidance.value = true
        updateStats(event, 'triggered')
      }
    })
  }

  function close() {
    showGuidance.value = false
    guidanceConfig.value = null
  }

  function dismiss(tourId) {
    // 记录用户跳过
    localStorage.setItem(`guidance_dismissed_${tourId}`, Date.now().toString())
    close()
    updateStats(getCurrentEvent(), 'dismissed')
  }

  function complete() {
    updateStats(getCurrentEvent(), 'completed')
    close()
  }

  return {
    showGuidance,
    guidanceConfig,
    guidanceStats,
    trigger,
    close,
    dismiss,
    complete
  }
})
```

### 3.2 useGuidance Composable

```javascript
// web/src/composables/useGuidance.js

export function useGuidance() {
  const guidanceStore = useGuidanceStore()

  // 用户注册引导
  function onUserRegistered(userId, teams) {
    if (teams.length === 0) {
      guidanceStore.trigger('user_registered', { userId, teams })
    }
  }

  // 加入团队引导
  function onTeamJoined(teamId, teamName) {
    guidanceStore.trigger('team_joined', { teamId, teamName })
  }

  // 首次上传引导
  function onFirstFileUploaded(fileId, fileName, spaceId) {
    guidanceStore.trigger('first_file_uploaded', {
      fileId,
      fileName,
      spaceId,
      uploadCount: 1
    })
  }

  return {
    trigger: guidanceStore.trigger,
    onUserRegistered,
    onTeamJoined,
    onFirstFileUploaded,
    close: guidanceStore.close,
    dismiss: guidanceStore.dismiss,
    complete: guidanceStore.complete
  }
}
```

### 3.3 GuidanceModal.vue

```vue
<template>
  <Teleport to="body">
    <div v-if="showGuidance" class="guidance-modal" @keydown.esc="handleDismiss">
      <div class="guidance-overlay" @click="handleDismiss"></div>
      <div class="guidance-dialog" :class="`guidance-dialog--${position}`">
        <div class="guidance-header">
          <h3 class="guidance-title">{{ config.title }}</h3>
          <button class="guidance-close" @click="handleDismiss">×</button>
        </div>
        <div class="guidance-body" v-html="config.content"></div>
        <div class="guidance-footer">
          <button
            v-for="action in config.actions"
            :key="action.label"
            class="guidance-action"
            :class="{ 'guidance-action--primary': action.primary }"
            @click="handleAction(action)"
          >
            {{ action.label }}
          </button>
        </div>
        <div class="guidance-checkbox">
          <input type="checkbox" id="dont-show" v-model="dontShowAgain" />
          <label for="dont-show">不再显示</label>
        </div>
      </div>
    </div>
  </Teleport>
</template>
```

---

## 4. 生命周期集成

引导引擎与生命周期约束引擎集成：

```python
def trigger(self, event: GuidanceEvent, context: GuidanceContext):
    tours = self._tours.get(event, [])
    for tour in tours:
        if tour.check_conditions(context.data):
            # 在显示引导前检查操作约束
            if self._lifecycle:
                constraint = self._lifecycle.check("show_guidance", context.data)
                if constraint:
                    logger.debug(f"Constraint {constraint.code} prevents guidance: {tour.id}")
                    continue
            self._start_tour(tour, context)
```

---

## 5. 缺失功能与改进建议

### 5.1 待实现功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 后端 GuidanceService | ❌ 缺失 | 需要独立的引导服务类 |
| CRUD API 端点 | ❌ 缺失 | `/api/v1/guidance/*` 未实现 |
| 引导模板管理 | ❌ 缺失 | 动态配置引导流程 |
| 用户引导统计 | ⚠️ 部分 | 仅前端记录，后端未持久化 |

### 5.2 改进建议

**1. 添加后端 GuidanceService**

```python
class GuidanceService:
    """引导服务 - 提供 REST API"""

    def __init__(self, guidance_engine: GuidanceEngine):
        self._engine = guidance_engine

    async def get_guidance(self, event: str, context: dict) -> Optional[dict]:
        """获取引导配置"""
        # 检查用户是否已跳过
        user_id = context.get("user_id")
        if self._is_dismissed(user_id, event):
            return None
        return self._engine.get_tour_for_event(event, context)

    async def record_progress(self, user_id: str, tour_id: str, step: int):
        """记录引导进度"""
        # 持久化到数据库

    async def dismiss_tour(self, user_id: str, tour_id: str):
        """跳过引导"""
        # 写入 localStorage/数据库
```

**2. 添加 API 端点**

```python
# /api/v1/guidance/{event}
@router.get("/{event}")
async def get_guidance(
    event: str,
    context: dict,
    current_user: User = Depends(get_current_user)
):
    """获取引导配置"""
    return await guidance_service.get_guidance(event, {
        "user_id": current_user.id,
        **context
    })

# /api/v1/guidance/{tour_id}/progress
@router.post("/{tour_id}/progress")
async def record_progress(
    tour_id: str,
    step: int,
    current_user: User = Depends(get_current_user)
):
    """记录引导进度"""
    await guidance_service.record_progress(current_user.id, tour_id, step)

# /api/v1/guidance/{tour_id}/dismiss
@router.post("/{tour_id}/dismiss")
async def dismiss_tour(
    tour_id: str,
    current_user: User = Depends(get_current_user)
):
    """跳过引导"""
    await guidance_service.dismiss_tour(current_user.id, tour_id)
```

**3. 引导模板配置化**

```yaml
# config/guidance_tours.yaml
tours:
  create_team:
    name: 创建团队引导
    trigger_event: user_registered
    conditions:
      no_teams: true
    steps:
      - id: step_1
        title: 创建团队
        content: 点击按钮创建团队
        target: "#create-team-btn"
        position: bottom

  first_upload:
    name: 首次上传引导
    trigger_event: first_file_upload
    conditions: {}
    steps:
      - id: step_1
        title: 上传文件
        content: 选择文件上传
        target: "#upload-area"
        position: right
```

---

## 6. 相关文档

- [INTERFACE_CONTRACT.md](../4_api/INTERFACE_CONTRACT.md) - Guidance 事件契约
- [lifecycle_config.yaml](../4_api/lifecycle_config.yaml) - 约束规则配置
- [useGuidance.js](../../web/src/composables/useGuidance.js) ✅ 已实现
- [guidanceStore.js](../../web/src/stores/guidanceStore.js) ✅ 已实现
- [GuidanceModal.vue](../../web/src/components/common/GuidanceModal.vue) ✅ 已实现
- [guidance_engine.py](../../engine/guidance_engine.py) ✅ 已实现

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-05-06 | 初始版本，文档化现有实现，识别缺失功能 |
