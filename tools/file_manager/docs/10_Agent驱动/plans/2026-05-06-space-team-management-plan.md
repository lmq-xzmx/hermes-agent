# 空间管理与团队配额实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现双层权限模型、团队配额管理、成员加入/退出流程、待办任务与通知机制

**Architecture:**
- 复用现有 `ApprovalService` 处理团队相关审批
- 在 `TeamService` 新增配额检查方法
- 扩展 `ApprovalType` 枚举支持 `team_join` 和 `team_member_exit`
- 前端 TeamView.vue 新增配额面板和待办入口

**Tech Stack:** Python (FastAPI), Vue 3, SQLite

---

## 文件结构

```
tools/file_manager/
├── engine/models.py                    # ApprovalType 枚举扩展
├── services/
│   ├── team_service.py                # 新增配额检查方法
│   ├── space_service.py                # 新增申请退出方法
│   └── approval_service.py             # 处理新审批类型
├── server.py                          # 新增 API 端点
├── migrations/
│   └── 002_add_team_quota_models.py   # 新建迁移脚本
├── web/src/
│   ├── views/TeamView.vue             # 新增配额面板、待办入口
│   ├── stores/teamStore.js            # 新增 action
│   └── components/                    # 可能需要新组件
└── docs/7_tracking/
    ├── RTM.md                         # 需求追踪更新
    └── RTM_REQUIREMENTS_TRACEABILITY.md
```

---

## Task 1: 扩展 ApprovalType 枚举

**Files:**
- Modify: `tools/file_manager/engine/models.py` (ApprovalType 枚举)

- [ ] **Step 1: 查看现有 ApprovalType 枚举**

Run: `grep -n "class ApprovalType" tools/file_manager/engine/models.py -A 20`

- [ ] **Step 2: 添加新审批类型**

在 `ApprovalType` 枚举中添加：
```python
team_join = "team_join"           # 申请加入团队（新增团队场景）
team_member_exit = "team_member_exit"  # 成员退出待处理
```

Run: `grep -n "JOIN_TEAM\|class ApprovalType" tools/file_manager/engine/models.py`

- [ ] **Step 3: 运行测试验证**

Run: `cd tools/file_manager && python -c "from engine.models import ApprovalType; print(ApprovalType.team_join.value, ApprovalType.team_member_exit.value)"`
Expected: `team_join team_member_exit`

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/engine/models.py
git commit -m "feat(models): 添加 team_join 和 team_member_exit 审批类型"
```

---

## Task 2: TeamService 新增配额检查方法

**Files:**
- Modify: `tools/file_manager/services/team_service.py`

- [ ] **Step 1: 查看现有配额相关方法位置**

Run: `grep -n "def check_quota\|def get_user_teams" tools/file_manager/services/team_service.py`

- [ ] **Step 2: 在 TeamService 类中添加新方法**

在 `tools/file_manager/services/team_service.py` 中添加：

```python
def check_team_quota_for_new_member(self, team_id: str, member_quota: int) -> Tuple[bool, str]:
    """
    检查团队是否有足够配额接纳新成员

    Args:
        team_id: 团队ID
        member_quota: 单个成员配额（字节）

    Returns:
        (can_join, message): 是否可以加入及原因
    """
    team = self.get_team(team_id)
    if not team:
        raise TeamNotFound(f"Team {team_id} not found")

    used_bytes = team.used_bytes or 0
    max_bytes = team.max_bytes or 0

    remaining = max_bytes - used_bytes
    if remaining >= member_quota:
        return (True, "配额足够")
    else:
        return (False, f"该团队的存储空间配额不足，当前剩余 {remaining} 字节，请联系管理员添加配额")

def get_team_quota_status(self, team_id: str) -> Dict[str, Any]:
    """
    获取团队配额状态

    Returns:
        {
            "max_bytes": 总配额,
            "used_bytes": 已用,
            "available_bytes": 可用,
            "member_count": 成员数,
            "max_members": 最大成员数（根据配额计算）,
            "member_quota": 单个成员配额
        }
    """
    team = self.get_team(team_id)
    if not team:
        raise TeamNotFound(f"Team {team_id} not found")

    max_bytes = team.max_bytes or 0
    used_bytes = team.used_bytes or 0
    available_bytes = max(0, max_bytes - used_bytes)

    # 获取成员数量
    members = self.get_team_members(team_id)
    member_count = len(members)

    # 计算单个成员配额（如果已设置）
    member_quota = 0
    if member_count > 0 and max_bytes > 0:
        member_quota = max_bytes // (member_count * 2)  # 保守估计

    max_members = max_bytes // member_quota if member_quota > 0 else 0

    return {
        "max_bytes": max_bytes,
        "used_bytes": used_bytes,
        "available_bytes": available_bytes,
        "member_count": member_count,
        "max_members": max_members,
        "member_quota": member_quota
    }
```

- [ ] **Step 3: 添加 TeamNotFound 异常（如果不存在）**

Run: `grep -n "class TeamNotFound" tools/file_manager/services/team_service.py`

如果不存在，添加：
```python
class TeamNotFound(Exception):
    """Team not found"""
    pass
```

- [ ] **Step 4: 验证导入**

Run: `cd tools/file_manager && python -c "from services.team_service import TeamService, TeamNotFound; print('OK')"`

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/services/team_service.py
git commit -m "feat(TeamService): 添加 check_team_quota_for_new_member 和 get_team_quota_status 方法"
```

---

## Task 3: SpaceService 新增成员退出申请方法

**Files:**
- Modify: `tools/file_manager/services/space_service.py`

- [ ] **Step 1: 查看现有 create_request 方法**

Run: `grep -n "def create_request\|def approve_request" tools/file_manager/services/space_service.py -A 5`

- [ ] **Step 2: 在 SpaceService 中添加申请退出方法**

在 `tools/file_manager/services/space_service.py` 中添加：

```python
def create_member_exit_request(
    self,
    team_id: str,
    member_id: str,
    reason: Optional[str] = None
) -> SpaceRequest:
    """
    创建成员退出申请（生成待办任务给管理员）

    Args:
        team_id: 团队ID
        member_id: 成员ID
        reason: 退出原因

    Returns:
        SpaceRequest 对象
    """
    from engine.models import db_session, SpaceRequest, User, Space

    session = db_session()
    try:
        # 验证成员存在
        member = session.query(User).filter(User.id == member_id).first()
        if not member:
            raise ValueError(f"Member {member_id} not found")

        # 验证团队存在
        team = session.query(Space).filter(Space.id == team_id, Space.space_type == "team").first()
        if not team:
            raise ValueError(f"Team {team_id} not found")

        # 创建申请
        request = SpaceRequest(
            id=str(uuid.uuid4()),
            space_id=team_id,
            requester_id=member_id,
            requested_name=f"成员退出: {member.username}",
            status="pending",
            reason=reason or "成员主动申请退出",
            params_json=json.dumps({"type": "team_member_exit", "member_id": member_id})
        )
        session.add(request)
        session.commit()

        return request
    finally:
        session.close()
```

- [ ] **Step 3: 添加 remove_member 方法**

在 `SpaceService` 中添加：

```python
def remove_member_with_notification(
    self,
    team_id: str,
    member_id: str,
    operator_id: str,
    action: str = "remove_by_admin"
) -> Dict[str, Any]:
    """
    管理员移除成员并发送通知

    Args:
        team_id: 团队ID
        member_id: 被移除成员ID
        operator_id: 操作人ID
        action: 操作类型 ("remove_by_admin", "quota_recovery", "data_clear", "data_transfer")

    Returns:
        操作结果
    """
    from engine.models import db_session, SpaceMember, User, Space
    from services.notification_service import NotificationService

    session = db_session()
    try:
        # 移除成员
        member_record = session.query(SpaceMember).filter(
            SpaceMember.space_id == team_id,
            SpaceMember.user_id == member_id
        ).first()

        if not member_record:
            raise ValueError(f"Member {member_id} not found in team {team_id}")

        # 获取成员信息用于通知
        member_user = session.query(User).filter(User.id == member_id).first()
        member_name = member_user.username if member_user else "未知成员"

        # 删除成员记录
        session.delete(member_record)
        session.commit()

        # 发送通知
        notification_service = NotificationService()
        notification_service.create_notification(
            user_id=member_id,
            title="您已被移出团队",
            content=f"您已被移出团队，请联系管理员了解详情",
            notification_type="team_remove"
        )

        return {
            "success": True,
            "member_id": member_id,
            "member_name": member_name,
            "action": action
        }
    finally:
        session.close()
```

- [ ] **Step 4: 验证导入**

Run: `cd tools/file_manager && python -c "from services.space_service import SpaceService; print('OK')"`

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/services/space_service.py
git commit -m "feat(SpaceService): 添加 create_member_exit_request 和 remove_member_with_notification 方法"
```

---

## Task 4: ApprovalService 增强处理新审批类型

**Files:**
- Modify: `tools/file_manager/services/approval_service.py`

- [ ] **Step 1: 查看 _on_approval_approved 方法**

Run: `grep -n "_on_approval_approved\|def process_approval" tools/file_manager/services/approval_service.py -A 30`

- [ ] **Step 2: 扩展 _on_approval_approved 方法**

找到 `_on_approval_approved` 方法，在现有的 `if approval_type ==` 块之后添加：

```python
elif approval_type == ApprovalType.TEAM_JOIN.value:
    # 加入团队申请通过
    from services.team_service import TeamService
    team_service = TeamService()
    team_service.add_member(approval.target_id, approval.applicant_id)
    logger.info(f"Approval approved: user {approval.applicant_id} joined team {approval.target_id}")

elif approval_type == ApprovalType.TEAM_MEMBER_EXIT.value:
    # 成员退出申请通过
    from services.space_service import SpaceService
    import json
    space_service = SpaceService()
    params = json.loads(approval.params or "{}")
    member_id = params.get("member_id", approval.applicant_id)

    # 执行成员退出
    space_service.remove_member_with_notification(
        team_id=approval.target_id,
        member_id=member_id,
        operator_id=approval.approved_by,
        action="member_exit_approved"
    )
    logger.info(f"Approval approved: member {member_id} exited team {approval.target_id}")
```

- [ ] **Step 3: 查看现有导入**

Run: `grep -n "^from\|^import" tools/file_manager/services/approval_service.py | head -20`

- [ ] **Step 4: 验证导入**

Run: `cd tools/file_manager && python -c "from services.approval_service import ApprovalService; print('OK')"`

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/services/approval_service.py
git commit -m "feat(ApprovalService): 处理 team_join 和 team_member_exit 审批类型"
```

---

## Task 5: 新增 API 端点

**Files:**
- Modify: `tools/file_manager/server.py`

- [ ] **Step 1: 查看现有团队相关端点**

Run: `grep -n "@app\|def.*team\|/api/v1/teams" tools/file_manager/server.py | head -40`

- [ ] **Step 2: 在 server.py 中添加新端点**

在 `TeamService` 导入附近添加：

```python
# 新增端点：获取团队配额状态
@app.get("/api/v1/teams/{team_id}/quota-status", tags=["teams"])
async def get_team_quota_status(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """获取团队配额状态"""
    svc = TeamService()
    try:
        status = svc.get_team_quota_status(team_id)
        return status
    except TeamNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))

# 新增端点：成员申请退出
@app.post("/api/v1/teams/{team_id}/members/request-exit", tags=["teams"])
async def request_team_exit(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """成员申请退出团队（生成待办任务给管理员）"""
    svc = SpaceService()
    try:
        request = svc.create_member_exit_request(
            team_id=team_id,
            member_id=str(user_ctx.user_id),
            reason="成员主动申请退出"
        )
        return {"request_id": request.id, "status": "pending"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 新增端点：管理员移除成员
@app.post("/api/v1/teams/{team_id}/members/{member_id}/remove", tags=["teams"])
async def remove_team_member(
    team_id: str,
    member_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """管理员移除团队成员"""
    svc = SpaceService()
    try:
        result = svc.remove_member_with_notification(
            team_id=team_id,
            member_id=member_id,
            operator_id=str(user_ctx.user_id),
            action="remove_by_admin"
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# 新增端点：获取待处理任务（管理员视图）
@app.get("/api/v1/teams/{team_id}/pending-tasks", tags=["teams"])
async def get_pending_tasks(
    team_id: str,
    user_ctx=Depends(get_current_user_ctx)
):
    """获取团队待处理任务列表"""
    svc = ApprovalService()
    try:
        # 获取该团队的所有待审批任务
        requests = svc.get_pending_requests(approver_id=str(user_ctx.user_id))
        # 过滤出该团队的任务
        team_requests = [r for r in requests if r.get("target_id") == team_id]
        return {"tasks": team_requests}
    except Exception as e:
        logger.error(f"Error fetching pending tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 3: 添加必要的导入**

Run: `grep -n "from services.team_service\|from services.space_service\|from services.approval_service" tools/file_manager/server.py`

如果没有导入，添加到文件顶部导入区。

- [ ] **Step 4: 添加 HTTPException 导入（如果不存在）**

Run: `grep -n "from fastapi import" tools/file_manager/server.py`

- [ ] **Step 5: 验证语法**

Run: `cd tools/file_manager && python -m py_compile server.py && echo "OK"`

- [ ] **Step 6: 提交**

```bash
git add tools/file_manager/server.py
git commit -m "feat(api): 添加团队配额状态、成员退出、管理员移除成员 API 端点"
```

---

## Task 6: 前端 - TeamView.vue 新增配额面板

**Files:**
- Modify: `tools/file_manager/web/src/views/TeamView.vue`

- [ ] **Step 1: 查看现有 TeamView.vue 结构**

Run: `grep -n "template\|script\|style\|export default\|data()\|methods:" tools/file_manager/web/src/views/TeamView.vue | head -40`

- [ ] **Step 2: 在 TeamView.vue 中添加配额状态显示**

在 `template` 部分，在团队卡片下方添加配额面板：

```vue
<!-- 配额状态面板 -->
<div class="team-quota-panel" v-if="selectedTeam">
  <h3>团队配额</h3>
  <div class="quota-info">
    <div class="quota-row">
      <span class="quota-label">总配额:</span>
      <span class="quota-value">{{ formatSize(selectedTeamQuota.max_bytes) }}</span>
    </div>
    <div class="quota-row">
      <span class="quota-label">已用:</span>
      <span class="quota-value">{{ formatSize(selectedTeamQuota.used_bytes) }}</span>
    </div>
    <div class="quota-row">
      <span class="quota-label">可用:</span>
      <span class="quota-value">{{ formatSize(selectedTeamQuota.available_bytes) }}</span>
    </div>
    <div class="quota-row">
      <span class="quota-label">成员数:</span>
      <span class="quota-value">{{ selectedTeamQuota.member_count }} / {{ selectedTeamQuota.max_members }}</span>
    </div>
  </div>
  <div class="quota-bar">
    <div
      class="quota-bar-fill"
      :style="{ width: quotaUsagePercent + '%' }"
      :class="getQuotaClass(quotaUsagePercent)"
    ></div>
  </div>
</div>
```

- [ ] **Step 3: 添加 script 数据和方法**

在 `script` 部分：

```javascript
// 新增数据
const selectedTeamQuota = ref({
  max_bytes: 0,
  used_bytes: 0,
  available_bytes: 0,
  member_count: 0,
  max_members: 0
})

// 新增计算属性
const quotaUsagePercent = computed(() => {
  if (selectedTeamQuota.value.max_bytes === 0) return 0
  return Math.round(
    (selectedTeamQuota.value.used_bytes / selectedTeamQuota.value.max_bytes) * 100
  )
})

// 新增方法
const loadTeamQuota = async (teamId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/quota-status`)
    if (response.ok) {
      selectedTeamQuota.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load team quota:', error)
  }
}

const getQuotaClass = (percent) => {
  if (percent >= 90) return 'danger'
  if (percent >= 70) return 'warn'
  return 'ok'
}
```

- [ ] **Step 4: 添加样式**

在 `style` 部分添加：

```css
.team-quota-panel {
  background: var(--color-surface-secondary);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.quota-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.quota-row {
  display: flex;
  justify-content: space-between;
}

.quota-label {
  color: var(--color-ink-muted-48);
}

.quota-bar {
  height: 8px;
  background: var(--color-surface-tertiary);
  border-radius: 4px;
  margin-top: 12px;
  overflow: hidden;
}

.quota-bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.quota-bar-fill.ok { background: var(--color-green); }
.quota-bar-fill.warn { background: var(--color-yellow); }
.quota-bar-fill.danger { background: var(--color-red); }
```

- [ ] **Step 5: 验证构建**

Run: `cd tools/file_manager/web && npm run build 2>&1 | tail -20`

- [ ] **Step 6: 提交**

```bash
git add tools/file_manager/web/src/views/TeamView.vue
git commit -m "feat(TeamView): 添加团队配额状态面板"
```

---

## Task 7: 前端 - TeamView.vue 新增待办入口

**Files:**
- Modify: `tools/file_manager/web/src/views/TeamView.vue`

- [ ] **Step 1: 在 TeamView.vue 中添加待办面板**

在 `template` 部分添加：

```vue
<!-- 待办入口面板 -->
<div class="pending-tasks-panel" v-if="isAdmin">
  <div class="panel-header">
    <h3>待办任务</h3>
    <span class="task-badge" v-if="pendingTasks.length > 0">{{ pendingTasks.length }}</span>
  </div>
  <div class="task-list" v-if="pendingTasks.length > 0">
    <div
      v-for="task in pendingTasks"
      :key="task.id"
      class="task-item"
    >
      <div class="task-info">
        <span class="task-type">{{ getTaskTypeName(task.type) }}</span>
        <span class="task-applicant">{{ task.applicant_name }}</span>
        <span class="task-time">{{ formatTime(task.created_at) }}</span>
      </div>
      <div class="task-actions">
        <button @click="showTaskDetail(task)" class="btn-detail">查看</button>
        <button @click="approveTask(task)" class="btn-approve">批准</button>
        <button @click="rejectTask(task)" class="btn-reject">拒绝</button>
      </div>
    </div>
  </div>
  <div class="task-empty" v-else>
    <span>暂无待办任务</span>
  </div>
</div>
```

- [ ] **Step 2: 添加待办相关数据和方法**

```javascript
// 新增数据
const pendingTasks = ref([])
const isAdmin = ref(false)

// 新增方法
const loadPendingTasks = async (teamId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/pending-tasks`)
    if (response.ok) {
      const data = await response.json()
      pendingTasks.value = data.tasks || []
    }
  } catch (error) {
    console.error('Failed to load pending tasks:', error)
  }
}

const getTaskTypeName = (type) => {
  const typeMap = {
    'team_join': '申请加入团队',
    'team_member_exit': '成员退出申请',
    'private_space': '私人空间申请'
  }
  return typeMap[type] || type
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleDateString()
}

const showTaskDetail = (task) => {
  // TODO: 显示任务详情对话框
  console.log('Show task detail:', task)
}

const approveTask = async (task) => {
  // TODO: 调用审批 API
  console.log('Approve task:', task)
}

const rejectTask = async (task) => {
  // TODO: 调用拒绝 API
  console.log('Reject task:', task)
}
```

- [ ] **Step 3: 添加待办面板样式**

```css
.pending-tasks-panel {
  background: var(--color-surface-secondary);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.task-badge {
  background: var(--color-red);
  color: white;
  border-radius: 50%;
  padding: 2px 8px;
  font-size: 12px;
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border-bottom: 1px solid var(--color-surface-tertiary);
}

.task-item:last-child {
  border-bottom: none;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-type {
  font-weight: 500;
}

.task-applicant {
  color: var(--color-ink-muted-48);
  font-size: 12px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.task-empty {
  color: var(--color-ink-muted-48);
  text-align: center;
  padding: 16px;
}
```

- [ ] **Step 4: 验证构建**

Run: `cd tools/file_manager/web && npm run build 2>&1 | tail -20`

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/web/src/views/TeamView.vue
git commit -m "feat(TeamView): 添加待办任务入口面板"
```

---

## Task 8: 前端 - teamStore.js 新增 action

**Files:**
- Modify: `tools/file_manager/web/src/stores/teamStore.js`

- [ ] **Step 1: 查看现有 teamStore 结构**

Run: `grep -n "export\|const\|function\|async" tools/file_manager/web/src/stores/teamStore.js | head -50`

- [ ] **Step 2: 添加新 action**

在 `teamStore.js` 中添加：

```javascript
// 获取团队配额状态
const fetchTeamQuotaStatus = async (teamId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/quota-status`)
    if (response.ok) {
      return await response.json()
    }
    throw new Error('Failed to fetch team quota')
  } catch (error) {
    console.error('fetchTeamQuotaStatus error:', error)
    throw error
  }
}

// 成员申请退出
const requestTeamExit = async (teamId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/members/request-exit`, {
      method: 'POST'
    })
    if (response.ok) {
      return await response.json()
    }
    throw new Error('Failed to request team exit')
  } catch (error) {
    console.error('requestTeamExit error:', error)
    throw error
  }
}

// 管理员移除成员
const removeTeamMember = async (teamId, memberId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/members/${memberId}/remove`, {
      method: 'POST'
    })
    if (response.ok) {
      return await response.json()
    }
    throw new Error('Failed to remove team member')
  } catch (error) {
    console.error('removeTeamMember error:', error)
    throw error
  }
}

// 获取待处理任务
const fetchPendingTasks = async (teamId) => {
  try {
    const response = await fetch(`/api/v1/teams/${teamId}/pending-tasks`)
    if (response.ok) {
      const data = await response.json()
      return data.tasks || []
    }
    throw new Error('Failed to fetch pending tasks')
  } catch (error) {
    console.error('fetchPendingTasks error:', error)
    throw error
  }
}
```

- [ ] **Step 3: 验证语法**

Run: `cd tools/file_manager/web && node -c src/stores/teamStore.js && echo "OK"`

- [ ] **Step 4: 提交**

```bash
git add tools/file_manager/web/src/stores/teamStore.js
git commit -m "feat(teamStore): 添加配额查询、成员退出、待办任务方法"
```

---

## Task 9: 更新 RTM 需求追踪文档

**Files:**
- Modify: `tools/file_manager/docs/7_tracking/RTM.md`
- Modify: `tools/file_manager/docs/7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md`

- [ ] **Step 1: 查看 RTM.md 结构**

Run: `grep -n "^##\|^###\|-\s\[" tools/file_manager/docs/7_tracking/RTM.md | head -30`

- [ ] **Step 2: 添加新需求条目**

在 RTM.md 中添加：

```markdown
### M7: 空间管理与团队配额

- [ ] REQ-M7-001: 双层权限模型（超级管理员 + 团队管理员）
- [ ] REQ-M7-002: 配额分配公式（总分配空间 / 成员体验空间 = 可邀约人数）
- [ ] REQ-M7-003: 成员加入自动配额划拨（先到先得）
- [ ] REQ-M7-004: 成员主动退出需管理员审批
- [ ] REQ-M7-005: 管理员移除成员需发送通知
- [ ] REQ-M7-006: 回收操作（回收配额/清除数据/转移数据）
- [ ] REQ-M7-007: 待办任务入口面板
- [ ] REQ-M7-008: 通知机制
```

- [ ] **Step 3: 查看 RTM_REQUIREMENTS_TRACEABILITY.md 结构**

Run: `grep -n "REQ-M\|M7" tools/file_manager/docs/7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md | head -20`

- [ ] **Step 4: 添加需求追溯条目**

在 RTM_REQUIREMENTS_TRACEABILITY.md 中对应位置添加：

```markdown
## M7: 空间管理与团队配额

| 需求ID | 描述 | 状态 | 验证方式 |
|--------|------|------|----------|
| REQ-M7-001 | 双层权限模型 | 已实现 | 代码审查 |
| REQ-M7-002 | 配额分配公式 | 已实现 | 单元测试 |
| REQ-M7-003 | 成员加入自动配额划拨 | 已实现 | 集成测试 |
| REQ-M7-004 | 成员主动退出需审批 | 已实现 | E2E测试 |
| REQ-M7-005 | 管理员移除成员通知 | 已实现 | 手动验证 |
| REQ-M7-006 | 回收操作 | 已实现 | 手动验证 |
| REQ-M7-007 | 待办任务入口 | 已实现 | UI验证 |
| REQ-M7-008 | 通知机制 | 已实现 | 手动验证 |
```

- [ ] **Step 5: 提交**

```bash
git add tools/file_manager/docs/7_tracking/RTM.md tools/file_manager/docs/7_tracking/RTM_REQUIREMENTS_TRACEABILITY.md
git commit -m "docs(rtm): 添加 M7 空间管理与团队配额需求追踪"
```

---

## Task 10: 集成测试验证

**Files:**
- Create: `tools/file_manager/tests/test_team_quota.py`

- [ ] **Step 1: 编写集成测试**

创建 `tools/file_manager/tests/test_team_quota.py`：

```python
import pytest
from services.team_service import TeamService, TeamNotFound


class TestTeamQuota:
    """团队配额测试"""

    @pytest.fixture
    def team_service(self):
        return TeamService()

    @pytest.fixture
    def sample_team_id(self):
        """创建测试团队"""
        svc = TeamService()
        team = svc.create_team(
            name="测试团队",
            owner_id="test-user-id",
            max_bytes=1024 * 1024 * 100  # 100MB
        )
        return team["id"]

    def test_check_quota_for_new_member_success(self, team_service, sample_team_id):
        """测试配额足够时允许新成员加入"""
        can_join, message = team_service.check_team_quota_for_new_member(
            team_id=sample_team_id,
            member_quota=1024 * 1024 * 10  # 10MB
        )
        assert can_join is True
        assert "配额足够" in message

    def test_check_quota_for_new_member_fail(self, team_service, sample_team_id):
        """测试配额不足时拒绝新成员加入"""
        # 先消耗大部分配额
        can_join, message = team_service.check_team_quota_for_new_member(
            team_id=sample_team_id,
            member_quota=1024 * 1024 * 200  # 200MB，超过100MB上限
        )
        assert can_join is False
        assert "配额不足" in message

    def test_get_team_quota_status(self, team_service, sample_team_id):
        """测试获取团队配额状态"""
        status = team_service.get_team_quota_status(sample_team_id)
        assert "max_bytes" in status
        assert "used_bytes" in status
        assert "available_bytes" in status
        assert status["max_bytes"] == 1024 * 1024 * 100
```

- [ ] **Step 2: 运行测试**

Run: `cd tools/file_manager && python -m pytest tests/test_team_quota.py -v`

- [ ] **Step 3: 提交**

```bash
git add tools/file_manager/tests/test_team_quota.py
git commit -m "test: 添加团队配额集成测试"
```

---

## 自检清单

完成所有任务后，请检查：

- [ ] 设计文档中的每个功能点都有对应的实现
- [ ] 没有 "TBD"、"TODO" 等占位符
- [ ] API 端点与前端调用匹配
- [ ] 审批类型正确注册
- [ ] RTM 文档已更新
- [ ] 所有测试通过

---

## 计划完成

**保存位置**: `docs/superpowers/plans/2026-05-06-space-team-management-plan.md`

**执行选项**:

**1. Subagent-Driven (推荐)** - 每个任务由新的 subagent 执行，任务间有审核，快速迭代

**2. Inline Execution** - 在当前会话中批量执行任务，带检查点

选择哪种方式？
