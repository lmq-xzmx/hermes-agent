<template>
  <div class="space-view">
    <!-- View Header -->
    <div class="view-header">
      <h3 class="section-title">我的空间</h3>
      <div class="header-actions">
        <button class="btn-apple-secondary" @click="showCrossTeamSpaces">跨团队协作</button>
        <button class="btn-apple-primary" @click="showCreateSpaceModal">+ 创建空间</button>
      </div>
    </div>

    <!-- Space list -->
    <div id="spacesList">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="spaces.length === 0" class="empty-state show">
        <div class="empty-state-icon">🚀</div>
        <p>暂无空间</p>
      </div>
      <div v-else class="space-grid">
        <div v-for="space in spaces" :key="space.space_id"
             class="space-card"
             :class="{ selected: selectedSpace?.space_id === space.space_id }"
             @click="selectSpace(space)">
          <div class="space-card-header">
            <span class="space-card-name">{{ space.space_name }}</span>
            <span class="space-type-badge" :class="space.space_type">{{ space.space_type }}</span>
          </div>
          <div class="space-card-meta">
            <span class="meta-item">{{ space.member_count || 0 }} 成员</span>
            <span class="meta-item">{{ formatDate(space.created_at) }}</span>
          </div>
          <div class="space-card-quota" v-if="space.quota_total">
            <div class="quota-bar">
              <div class="quota-fill" :class="getQuotaClass(space.quota_usage)"></div>
            </div>
            <div class="quota-stat">
              <span class="quota-used">{{ formatSize(space.quota_used) }}</span>
              <span class="quota-total">/ {{ formatSize(space.quota_total) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Selected space detail -->
    <div v-if="selectedSpace" id="spaceDetail" class="section-gap">
      <div class="view-header">
        <h3 class="section-title">{{ selectedSpace.space_name }} - 详情</h3>
        <div class="header-actions">
          <button class="btn-apple-secondary btn-sm" @click="showSpaceQuota">配额</button>
          <button class="btn-apple-secondary btn-sm" @click="showSpaceActivity">活动</button>
        </div>
      </div>

      <!-- Space tabs -->
      <div class="tab-bar">
        <button class="tab-btn" :class="{ active: activeTab === 'members' }" @click="activeTab = 'members'">成员</button>
        <button class="tab-btn" :class="{ active: activeTab === 'workflows' }" @click="activeTab = 'workflows'">工作流</button>
        <button class="tab-btn" :class="{ active: activeTab === 'notebooks' }" @click="activeTab = 'notebooks'">笔记本</button>
        <button class="tab-btn" :class="{ active: activeTab === 'settings' }" @click="activeTab = 'settings'">设置</button>
      </div>

      <!-- Members tab -->
      <div v-show="activeTab === 'members'" class="tab-content">
        <div class="member-list">
          <div v-for="member in members" :key="member.user_id" class="member-item">
            <div class="member-info">
              <span class="member-name">{{ member.username }}</span>
              <span class="member-role">{{ member.role }}</span>
            </div>
            <button class="btn-apple-secondary btn-sm" @click="removeMember(member)">移除</button>
          </div>
          <div v-if="members.length === 0" class="empty-state show">
            <p>暂无成员</p>
          </div>
        </div>
        <button class="btn-apple-secondary" style="margin-top:var(--space-md)" @click="showInviteSpaceMember">邀请成员</button>
      </div>

      <!-- Workflows tab -->
      <div v-show="activeTab === 'workflows'" class="tab-content">
        <div style="margin-bottom:var(--space-md)">
          <button class="btn-apple-primary btn-sm" @click="showCreateWorkflow">+ 新建工作流</button>
        </div>
        <div v-if="workflows.length === 0" class="empty-state show">
          <div class="empty-state-icon">⚙️</div>
          <p>暂无工作流</p>
        </div>
        <div v-else class="workflow-list">
          <div v-for="wf in workflows" :key="wf.workflow_id" class="workflow-item" @click="viewWorkflow(wf)">
            <span class="workflow-name">{{ wf.name }}</span>
            <span class="badge" :class="wf.status === 'active' ? 'badge-active' : 'badge-inactive'">{{ wf.status }}</span>
          </div>
        </div>
      </div>

      <!-- Notebooks tab -->
      <div v-show="activeTab === 'notebooks'" class="tab-content">
        <div style="margin-bottom:var(--space-md)">
          <button class="btn-apple-primary btn-sm" @click="showCreateNotebook">+ 新建笔记本</button>
        </div>
        <div v-if="notebooks.length === 0" class="empty-state show">
          <div class="empty-state-icon">📓</div>
          <p>暂无笔记本</p>
        </div>
        <div v-else class="notebook-list">
          <div v-for="nb in notebooks" :key="nb.id" class="notebook-item" @click="viewNotebook(nb)">
            <span class="notebook-name">{{ nb.name }}</span>
            <span class="notebook-date">{{ formatDate(nb.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Settings tab -->
      <div v-show="activeTab === 'settings'" class="tab-content">
        <div class="settings-panel">
          <p style="color:var(--color-ink-muted-48)">空间设置面板</p>
        </div>
      </div>

      <!-- Quota panel -->
      <div v-if="showQuota" id="spaceQuotaPanel" class="quota-panel">
        <div class="quota-card">
          <h4 class="quota-card-title">配额使用</h4>
          <div class="quota-detail-list">
            <div class="quota-detail-item">
              <span class="quota-detail-label">已使用</span>
              <span class="quota-detail-value">{{ formatSize(selectedSpace.quota_used) }}</span>
            </div>
            <div class="quota-detail-item">
              <span class="quota-detail-label">总配额</span>
              <span class="quota-detail-value">{{ formatSize(selectedSpace.quota_total) }}</span>
            </div>
            <div class="quota-detail-item">
              <span class="quota-detail-label">使用率</span>
              <span class="quota-detail-value">{{ ((selectedSpace.quota_usage || 0) * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Activity panel -->
      <div v-if="showActivity" id="spaceActivityPanel" class="activity-panel">
        <div class="activity-card">
          <h4 class="activity-card-title">活动日志</h4>
          <div class="activity-list" id="spaceActivityContent">
            <div v-if="activities.length === 0" class="empty-state show">
              <p>暂无活动记录</p>
            </div>
            <div v-for="act in activities" :key="act.id" class="activity-item">
              <span class="activity-action">{{ act.action }}</span>
              <span class="activity-time">{{ formatDate(act.timestamp) }}</span>
              <div class="activity-path">{{ act.path }}</div>
              <div v-if="act.extra" class="activity-extra">{{ act.extra }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Workflow Detail Modal -->
    <div v-if="selectedWorkflow" class="modal-overlay" @click.self="selectedWorkflow = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedWorkflow.name }}</h3>
          <button class="btn-close" @click="selectedWorkflow = null">&times;</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <span class="info-label">状态</span>
            <span class="badge" :class="selectedWorkflow.status === 'active' ? 'badge-active' : 'badge-inactive'">{{ selectedWorkflow.status }}</span>
          </div>
          <div class="info-row" v-if="selectedWorkflow.description">
            <span class="info-label">描述</span>
            <span>{{ selectedWorkflow.description }}</span>
          </div>
          <div class="info-row" v-if="selectedWorkflow.tags?.length">
            <span class="info-label">标签</span>
            <span>{{ selectedWorkflow.tags.join(', ') }}</span>
          </div>
          <div class="info-row" v-if="selectedWorkflow.steps?.length">
            <span class="info-label">步骤</span>
            <div class="steps-list">
              <div v-for="(step, idx) in selectedWorkflow.steps" :key="idx" class="step-item">
                <span class="step-num">{{ idx + 1 }}</span>
                <span class="step-cmd">{{ step.command }}</span>
                <span v-if="step.confirm_required" class="step-confirm">需确认</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-apple-primary" @click="executeWorkflow(selectedWorkflow.workflow_id)">执行</button>
          <button class="btn-apple-secondary" @click="selectedWorkflow = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- Notebook Detail Modal -->
    <div v-if="selectedNotebook" class="modal-overlay" @click.self="selectedNotebook = null">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedNotebook.name }}</h3>
          <button class="btn-close" @click="selectedNotebook = null">&times;</button>
        </div>
        <div class="modal-body">
          <div class="info-row">
            <span class="info-label">描述</span>
            <span>{{ selectedNotebook.description || '无' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">使用次数</span>
            <span>{{ selectedNotebook.usage_count || 0 }}</span>
          </div>
          <div class="info-row" v-if="selectedNotebook.tags?.length">
            <span class="info-label">标签</span>
            <span>{{ selectedNotebook.tags.join(', ') }}</span>
          </div>
          <div class="notebook-content" v-if="selectedNotebook.content">
            <pre>{{ selectedNotebook.content }}</pre>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-apple-secondary" @click="selectedNotebook = null">关闭</button>
        </div>
      </div>
    </div>

    <!-- Create Workflow Modal -->
    <div v-if="showCreateWorkflowModal" class="modal-overlay" @click.self="showCreateWorkflowModal = false">
      <div class="modal-content" style="max-width:550px">
        <div class="modal-header">
          <h3>新建工作流</h3>
          <button class="btn-close" @click="showCreateWorkflowModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">工作流名称</label>
            <input type="text" v-model="newWorkflow.name" placeholder="如：Git 提交流程" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">描述（可选）</label>
            <input type="text" v-model="newWorkflow.description" placeholder="简要说明用途" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">标签（可选，用逗号分隔）</label>
            <input type="text" v-model="newWorkflow.tagsStr" placeholder="如：git,日常" class="form-input">
          </div>
          <div class="form-group">
            <div class="form-label-row">
              <label class="form-label">步骤</label>
              <button class="btn-apple-secondary btn-sm" @click="addWorkflowStep">+ 添加步骤</button>
            </div>
            <div v-for="(step, idx) in newWorkflow.steps" :key="idx" class="step-item">
              <span class="step-num">{{ idx + 1 }}</span>
              <div class="step-inputs">
                <input type="text" v-model="step.command" placeholder="命令" class="form-input-sm">
                <input type="text" v-model="step.explanation" placeholder="说明（可选）" class="form-input-sm">
                <label class="step-checkbox">
                  <input type="checkbox" v-model="step.confirm_required"> 执行前需确认
                </label>
              </div>
              <button class="btn-apple-danger btn-sm" @click="removeWorkflowStep(idx)">删除</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-apple-primary" @click="createWorkflow">创建</button>
          <button class="btn-apple-secondary" @click="showCreateWorkflowModal = false">取消</button>
        </div>
      </div>
    </div>

    <!-- Create Notebook Modal -->
    <div v-if="showCreateNotebookModal" class="modal-overlay" @click.self="showCreateNotebookModal = false">
      <div class="modal-content" style="max-width:550px">
        <div class="modal-header">
          <h3>新建笔记本</h3>
          <button class="btn-close" @click="showCreateNotebookModal = false">&times;</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">笔记本名称</label>
            <input type="text" v-model="newNotebook.name" placeholder="如：我的笔记" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">描述（可选）</label>
            <input type="text" v-model="newNotebook.description" placeholder="简要说明用途" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">标签（可选，用逗号分隔）</label>
            <input type="text" v-model="newNotebook.tagsStr" placeholder="如：笔记,日常" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">内容</label>
            <textarea v-model="newNotebook.content" placeholder="笔记本内容..." rows="8" class="form-textarea"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-apple-primary" @click="createNotebook">创建</button>
          <button class="btn-apple-secondary" @click="showCreateNotebookModal = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'

const emit = defineEmits(['show-toast'])

const spaces = ref([])
const selectedSpace = ref(null)
const members = ref([])
const workflows = ref([])
const notebooks = ref([])
const activities = ref([])
const loading = ref(false)
const activeTab = ref('members')
const showQuota = ref(false)
const showActivity = ref(false)
const selectedWorkflow = ref(null)
const selectedNotebook = ref(null)
const showCreateWorkflowModal = ref(false)
const showCreateNotebookModal = ref(false)
const newWorkflow = ref({ name: '', description: '', tagsStr: '', steps: [] })
const newNotebook = ref({ name: '', description: '', tagsStr: '', content: '' })

onMounted(() => {
  loadSpaces()
})

async function loadSpaces() {
  loading.value = true
  try {
    const data = await api.getSpaces()
    spaces.value = data.spaces || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

function selectSpace(space) {
  selectedSpace.value = space
  activeTab.value = 'members'
  showQuota.value = false
  showActivity.value = false
  loadSpaceDetail(space.space_id)
}

async function loadSpaceDetail(spaceId) {
  try {
    const [membersData, workflowsData, notebooksData] = await Promise.all([
      api.getSpaceMembers(spaceId),
      api.getSpaceWorkflows(spaceId),
      api.getSpaceNotebooks(spaceId)
    ])
    members.value = membersData.members || []
    workflows.value = workflowsData.workflows || []
    notebooks.value = notebooksData.notebooks || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function showCreateSpaceModal() {
  const name = prompt('请输入空间名称:')
  if (!name) return

  const description = prompt('请输入空间描述（可选）:', '') || ''

  try {
    await api.createSpace(name, description)
    emit('show-toast', { type: 'success', title: '成功', message: '空间创建成功' })
    loadSpaces()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function showCrossTeamSpaces() {
  const token = prompt('请输入跨团队邀请码:')
  if (!token) return
  emit('show-toast', { type: 'info', title: '提示', message: '跨团队协作功能开发中' })
}

function showSpaceQuota() {
  showQuota.value = !showQuota.value
  showActivity.value = false
}

async function showSpaceActivity() {
  showActivity.value = !showActivity.value
  showQuota.value = false
  if (showActivity.value && selectedSpace.value) {
    try {
      const data = await api.getSpaceActivities(selectedSpace.value.space_id)
      activities.value = data.activities || []
    } catch (err) {
      emit('show-toast', { type: 'error', title: '错误', message: err.message })
    }
  }
}

async function showInviteSpaceMember() {
  const username = prompt('请输入要邀请的用户名:')
  if (!username) return

  const role = prompt('请输入角色 (member/admin):', 'member') || 'member'

  try {
    await api.inviteSpaceMember(selectedSpace.value.space_id, username, role)
    emit('show-toast', { type: 'success', title: '成功', message: `已邀请 ${username}` })
    loadSpaceDetail(selectedSpace.value.space_id)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function removeMember(member) {
  if (!confirm(`确定要移除成员 "${member.username}" 吗？`)) return

  try {
    await api.removeSpaceMember(selectedSpace.value.space_id, member.user_id)
    emit('show-toast', { type: 'success', title: '成功', message: `已移除 ${member.username}` })
    loadSpaceDetail(selectedSpace.value.space_id)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function viewWorkflow(wf) {
  try {
    const data = await api.getWorkflow(wf.workflow_id)
    selectedWorkflow.value = data
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function executeWorkflow(workflowId) {
  try {
    await api.executeWorkflow(workflowId)
    emit('show-toast', { type: 'success', title: '成功', message: '工作流已执行' })
    selectedWorkflow.value = null
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function viewNotebook(nb) {
  try {
    const data = await api.getNotebook(nb.id)
    selectedNotebook.value = data
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function showCreateWorkflow() {
  newWorkflow.value = { name: '', description: '', tagsStr: '', steps: [{ command: '', explanation: '', confirm_required: false }] }
  showCreateWorkflowModal.value = true
}

function showCreateNotebook() {
  newNotebook.value = { name: '', description: '', tagsStr: '', content: '' }
  showCreateNotebookModal.value = true
}

function addWorkflowStep() {
  newWorkflow.value.steps.push({ command: '', explanation: '', confirm_required: false })
}

function removeWorkflowStep(idx) {
  newWorkflow.value.steps.splice(idx, 1)
}

async function createWorkflow() {
  if (!newWorkflow.value.name.trim()) {
    emit('show-toast', { type: 'error', title: '请填写', message: '工作流名称不能为空' })
    return
  }
  if (!selectedSpace.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请先选择一个空间' })
    return
  }

  const tags = newWorkflow.value.tagsStr ? newWorkflow.value.tagsStr.split(',').map(t => t.trim()).filter(t => t) : []
  const steps = newWorkflow.value.steps.filter(s => s.command.trim()).map(s => ({
    command: s.command.trim(),
    explanation: s.explanation.trim(),
    confirm_required: s.confirm_required
  }))

  try {
    await api.createWorkflow(selectedSpace.value.space_id, {
      name: newWorkflow.value.name.trim(),
      description: newWorkflow.value.description.trim(),
      is_shared: false,
      tags,
      steps
    })
    emit('show-toast', { type: 'success', title: '成功', message: '工作流已创建' })
    showCreateWorkflowModal.value = false
    loadSpaceDetail(selectedSpace.value.space_id)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function createNotebook() {
  if (!newNotebook.value.name.trim()) {
    emit('show-toast', { type: 'error', title: '请填写', message: '笔记本名称不能为空' })
    return
  }
  if (!selectedSpace.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请先选择一个空间' })
    return
  }

  const tags = newNotebook.value.tagsStr ? newNotebook.value.tagsStr.split(',').map(t => t.trim()).filter(t => t) : []

  try {
    await api.createNotebook(selectedSpace.value.space_id, {
      name: newNotebook.value.name.trim(),
      description: newNotebook.value.description.trim(),
      content: newNotebook.value.content,
      tags
    })
    emit('show-toast', { type: 'success', title: '成功', message: '笔记本已创建' })
    showCreateNotebookModal.value = false
    loadSpaceDetail(selectedSpace.value.space_id)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function getQuotaClass(usage) {
  if (usage > 0.9) return 'danger'
  if (usage > 0.7) return 'warn'
  return 'ok'
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

function formatDate(str) {
  if (!str) return '-'
  const d = new Date(str)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.space-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-lg);
}

/* Typography */
.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-md);
}

.section-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.section-gap {
  margin-top: var(--space-xl);
}

/* Space Grid */
.space-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-md);
  margin-top: var(--space-md);
}

/* Space Card - Apple DESIGN.md store-utility-card */
.space-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: border-color 0.2s, transform 0.1s ease;
}

.space-card:hover {
  border-color: var(--color-primary);
}

.space-card.selected {
  border-color: var(--color-primary);
  border-width: 2px;
  background: var(--color-canvas-parchment);
}

.space-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-sm);
}

.space-card-name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.space-type-badge {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-48);
}

.space-type-badge.team {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.space-type-badge.private {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.space-type-badge.root {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.space-card-meta {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-sm);
}

.meta-item {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.space-card-quota {
  margin-top: var(--space-md);
}

.quota-bar {
  height: 6px;
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.quota-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s;
}

.quota-fill.ok { background: var(--color-success); }
.quota-fill.warn { background: var(--color-warning); }
.quota-fill.danger { background: var(--color-danger); }

.quota-stat {
  display: flex;
  justify-content: space-between;
  margin-top: var(--space-xxs);
}

.quota-used {
  font: var(--text-caption);
  color: var(--color-ink);
}

.quota-total {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* Tab Bar */
.tab-bar {
  display: flex;
  gap: var(--space-xs);
  padding-bottom: var(--space-sm);
  margin-bottom: var(--space-md);
  border-bottom: 1px solid var(--color-hairline);
}

.tab-btn {
  padding: var(--spacing-xxs) var(--spacing-lg);
  border-radius: var(--radius-pill);
  border: none;
  background: transparent;
  color: var(--color-ink-muted-48);
  font: var(--text-body);
  cursor: pointer;
  transition: all 0.15s;
}

.tab-btn:hover {
  background: var(--color-canvas-parchment);
  color: var(--color-ink);
}

.tab-btn.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

/* Member List */
.member-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.member-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.member-name {
  font: var(--text-body);
  color: var(--color-ink);
}

.member-role {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* Workflow and Notebook List */
.workflow-list,
.notebook-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.workflow-item,
.notebook-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.15s;
}

.workflow-item:hover,
.notebook-item:hover {
  background: var(--color-canvas-parchment);
}

.workflow-name,
.notebook-name {
  font: var(--text-body);
  color: var(--color-ink);
}

.notebook-date {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* Badge */
.badge {
  display: inline-block;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption-strong);
}

.badge-active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge-inactive {
  background: var(--color-gray-subtle);
  color: var(--color-ink-muted-48);
}

/* Quota Panel */
.quota-panel {
  margin-top: var(--space-md);
}

.quota-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.quota-card-title {
  font: var(--text-body-strong);
  margin-bottom: var(--space-md);
  color: var(--color-ink);
}

.quota-detail-list {
  display: flex;
  flex-direction: column;
}

.quota-detail-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-divider-soft);
}

.quota-detail-item:last-child {
  border-bottom: none;
}

.quota-detail-label {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.quota-detail-value {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

/* Activity Panel */
.activity-panel {
  margin-top: var(--space-md);
}

.activity-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--space-lg);
}

.activity-card-title {
  font: var(--text-body-strong);
  margin-bottom: var(--space-md);
  color: var(--color-ink);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  max-height: 400px;
  overflow-y: auto;
}

.activity-item {
  padding: var(--space-sm) var(--space-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.activity-action {
  font: var(--text-body);
  font-weight: 600;
  color: var(--color-primary);
}

.activity-time {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-left: var(--space-sm);
}

.activity-path {
  font-family: monospace;
  font-size: 13px;
  color: var(--color-ink-muted-48);
  margin-top: 4px;
}

.activity-extra {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-top: 4px;
}

/* Settings Panel */
.settings-panel {
  padding: var(--space-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* Form Elements */
.form-group {
  margin-bottom: var(--space-md);
}

.form-label {
  display: block;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--space-xxs);
}

.form-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xxs);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-input-sm {
  width: 100%;
  padding: 8px 12px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  resize: vertical;
  box-sizing: border-box;
}

.step-inputs {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.step-checkbox {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  display: flex;
  align-items: center;
  gap: var(--space-xxs);
}

/* Empty State */
.empty-state {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl) var(--space-lg);
}

.empty-state.show {
  display: flex;
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

/* Loading */
.loading {
  text-align: center;
  padding: var(--space-lg);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.modal-header h3 {
  font: var(--text-body-strong);
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-ink-muted-48);
}

.modal-body {
  padding: var(--space-lg);
}

.modal-footer {
  display: flex;
  gap: var(--space-sm);
  justify-content: flex-end;
  padding: var(--space-lg);
  border-top: 1px solid var(--color-divider-soft);
}

/* Info Row */
.info-row {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--color-divider-soft);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  color: var(--color-ink-muted-48);
  min-width: 80px;
}

/* Steps List */
.steps-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  width: 100%;
}

.step-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.step-num {
  width: 24px;
  height: 24px;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.step-cmd {
  flex: 1;
  font-family: monospace;
  font-size: 14px;
  color: var(--color-ink);
}

.step-confirm {
  font: var(--text-caption);
  color: var(--color-warning);
}

/* Notebook Content */
.notebook-content {
  margin-top: var(--space-md);
  padding: var(--space-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
  max-height: 300px;
  overflow: auto;
}

.notebook-content pre {
  white-space: pre-wrap;
  word-break: break-word;
  font: var(--text-body);
  color: var(--color-ink);
}
</style>
