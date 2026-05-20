<template>
  <div class="team-view">
    <!-- Toolbar -->
    <div class="team-view__toolbar">
      <button class="btn-apple-primary" @click="showCreateTeam">+ 创建团队</button>
      <div class="team-view__toolbar-spacer"></div>
      <button class="btn-apple-secondary" @click="loadTeams">刷新</button>
    </div>

    <!-- My Teams section -->
    <div class="team-view__section">
      <h3 class="team-view__title">我所在的团队</h3>
      <div class="my-teams-section">
        <div v-if="loading" class="team-view__loading">加载中...</div>
        <div v-else-if="myTeams.length === 0" class="team-view__empty show">
          <div class="team-view__empty-icon">👥</div>
          <p>您还没有加入任何团队</p>
        </div>
        <div v-else class="team-view__list">
          <div v-for="team in myTeams" :key="team.team_id" class="team-card">
            <div class="team-card__main">
              <div class="team-card__info">
                <span class="team-card__name">{{ team.name }}</span>
                <span v-if="team.description" class="team-card__desc">{{ team.description }}</span>
              </div>
              <div class="team-card__stats">
                <div class="team-card__stat">
                  <span class="team-card__stat-value">{{ team.member_count || 0 }}</span>
                  <span class="team-card__stat-label">成员</span>
                </div>
                <div class="team-card__stat team-card__stat--quota">
                  <span class="team-card__stat-value">{{ formatSize(team.quota_used) }}</span>
                  <span class="team-card__stat-label">/ {{ formatSize(team.quota_total) }}</span>
                </div>
              </div>
              <div class="team-card__quota-bar">
                <div class="team-card__quota-fill" :class="getQuotaClass(team.quota_usage)"></div>
              </div>
              <span class="team-card__badge" :class="team.status === 'active' ? 'team-card__badge--active' : 'team-card__badge--inactive'">
                {{ team.status === 'active' ? '活跃' : '未激活' }}
              </span>
            </div>
            <div class="team-card__actions">
              <button class="btn-apple-secondary btn-apple-sm" @click="enterTeam(team)">进入</button>
              <button class="btn-apple-secondary btn-apple-sm" @click="showTeamMembers(team)">成员</button>
              <button v-if="team.my_role === 'owner'" class="btn-apple-secondary btn-apple-sm" @click="showTeamCredentials(team)">邀请码</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 配额状态面板 -->
    <div class="team-quota-panel" v-if="selectedTeamForQuota">
      <h3 class="team-quota-panel__title">团队配额</h3>
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
          :class="getQuotaClassForPanel(quotaUsagePercent)"
        ></div>
      </div>
    </div>

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

    <!-- All teams (admin) -->
    <div v-if="isAdmin" class="all-teams-section team-view__section-gap">
      <h3 class="team-view__title">所有团队 (管理)</h3>
      <div v-if="allTeams.length === 0" class="team-view__empty show">
        <p>暂无团队数据</p>
      </div>
      <div v-else class="team-view__list">
        <div v-for="team in allTeams" :key="team.team_id" class="team-card">
          <div class="team-card__main">
            <div class="team-card__info">
              <span class="team-card__name">{{ team.name }}</span>
            </div>
            <div class="team-card__stats">
              <div class="team-card__stat">
                <span class="team-card__stat-value">{{ team.member_count || 0 }}</span>
                <span class="team-card__stat-label">成员</span>
              </div>
              <div class="team-card__stat team-card__stat--quota">
                <span class="team-card__stat-value">{{ formatSize(team.quota_used) }}</span>
                <span class="team-card__stat-label">/ {{ formatSize(team.quota_total) }}</span>
              </div>
            </div>
            <div class="team-card__quota-bar">
              <div class="team-card__quota-fill" :class="getQuotaClass(team.quota_usage)"></div>
            </div>
            <span class="team-card__owner">{{ team.owner_username || '-' }}</span>
          </div>
          <div class="team-card__actions">
            <button class="btn-apple-secondary btn-apple-sm" @click="editTeam(team)">编辑</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Join team -->
    <div class="team-view__section-gap">
      <h3 class="team-view__title">加入团队</h3>
      <div class="team-view__join-form">
        <input type="text" v-model="joinToken" placeholder="输入邀请码" class="team-view__search-input">
        <button class="btn-apple-primary" @click="joinTeam">加入</button>
      </div>
    </div>

    <!-- Team Credentials Modal -->
    <div v-if="showCredentials" class="team-view__modal-overlay" @click.self="showCredentials = false">
      <div class="team-view__modal">
        <div class="team-view__modal-header">
          <h3>{{ selectedTeam.name }} - 邀请码</h3>
          <button class="team-view__modal-close" @click="showCredentials = false">&times;</button>
        </div>
        <div class="team-view__modal-body">
          <button class="btn-apple-secondary" style="margin-bottom:var(--spacing-md)" @click="createCredential">+ 生成邀请码</button>
          <div v-if="credentials.length === 0" class="team-view__empty show">
            <p>暂无邀请码</p>
          </div>
          <div v-else class="team-view__credential-list">
            <div v-for="cred in credentials" :key="cred.id" class="team-view__credential-item">
              <code class="team-view__credential-token">{{ cred.token }}</code>
              <span class="team-card__badge" :class="cred.used_count >= cred.max_uses ? 'team-card__badge--inactive' : 'team-card__badge--active'">
                {{ cred.used_count >= cred.max_uses ? '已用完' : '可用' }}
              </span>
              <span class="team-view__credential-detail">{{ cred.expires_at ? formatDate(cred.expires_at) : '永不过期' }}</span>
              <span class="team-view__credential-detail">{{ cred.used_count }} / {{ cred.max_uses }}</span>
              <button class="btn-apple-danger btn-apple-sm" @click="deleteCredential(cred.id)">删除</button>
            </div>
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="btn-apple-secondary" @click="showCredentials = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- Create Team Modal -->
    <div v-if="showCreateTeamModal" class="team-view__modal-overlay" @click.self="showCreateTeamModal = false">
      <div class="team-view__modal">
        <div class="team-view__modal-header">
          <h3>创建团队</h3>
          <button class="team-view__modal-close" @click="showCreateTeamModal = false">&times;</button>
        </div>
        <div class="team-view__modal-body">
          <div class="form-group">
            <label class="form-label">团队名称</label>
            <input type="text" v-model="newTeam.name" placeholder="如：产品研发团队" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">存储池</label>
            <select v-model="newTeam.storagePoolId" class="form-select">
              <option value="">使用默认存储池</option>
              <option v-for="pool in storagePools" :key="pool.id" :value="pool.id">{{ pool.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">描述（可选）</label>
            <input type="text" v-model="newTeam.description" placeholder="简要说明团队用途" class="form-input">
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="btn-apple-primary" @click="confirmCreateTeam" :disabled="!newTeam.name">创建</button>
          <button class="btn-apple-secondary" @click="showCreateTeamModal = false">取消</button>
        </div>
      </div>
    </div>

    <!-- Team Members Modal -->
    <div v-if="showMembersModal" class="team-view__modal-overlay" @click.self="showMembersModal = false">
      <div class="team-view__modal">
        <div class="team-view__modal-header">
          <h3>{{ selectedTeam?.name }} - 成员列表</h3>
          <button class="team-view__modal-close" @click="showMembersModal = false">&times;</button>
        </div>
        <div class="team-view__modal-body">
          <div v-if="teamMembers.length === 0" class="team-view__empty show">
            <p>暂无成员</p>
          </div>
          <div v-else class="member-list-modal">
            <div v-for="member in teamMembers" :key="member.user_id" class="member-item-modal">
              <div class="member-info">
                <span class="member-name">{{ member.username }}</span>
                <span class="member-role-badge" :class="member.role">{{ member.role }}</span>
              </div>
              <button v-if="canRemoveMember(member)" class="btn-apple-danger btn-sm" @click="removeTeamMember(member)">移除</button>
            </div>
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="btn-apple-secondary" @click="showMembersModal = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- Edit Team Modal -->
    <div v-if="showEditTeamModal" class="team-view__modal-overlay" @click.self="showEditTeamModal = false">
      <div class="team-view__modal">
        <div class="team-view__modal-header">
          <h3>编辑团队</h3>
          <button class="team-view__modal-close" @click="showEditTeamModal = false">&times;</button>
        </div>
        <div class="team-view__modal-body">
          <div class="form-group">
            <label class="form-label">团队名称</label>
            <input type="text" v-model="editTeamData.name" class="form-input">
          </div>
          <div class="form-group">
            <label class="form-label">描述</label>
            <input type="text" v-model="editTeamData.description" class="form-input">
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="btn-apple-primary" @click="confirmEditTeam">保存</button>
          <button class="btn-apple-secondary" @click="showEditTeamModal = false">取消</button>
        </div>
      </div>
    </div>

    <!-- Task Detail Modal -->
    <div v-if="showTaskDetailModal" class="team-view__modal-overlay" @click.self="showTaskDetailModal = false">
      <div class="team-view__modal">
        <div class="team-view__modal-header">
          <h3>任务详情</h3>
          <button class="team-view__modal-close" @click="showTaskDetailModal = false">&times;</button>
        </div>
        <div class="team-view__modal-body">
          <div class="task-detail">
            <div class="task-detail-row">
              <span class="task-detail-label">任务类型</span>
              <span class="task-detail-value">{{ getTaskTypeName(selectedTask?.type) }}</span>
            </div>
            <div class="task-detail-row">
              <span class="task-detail-label">申请人</span>
              <span class="task-detail-value">{{ selectedTask?.applicant_name }}</span>
            </div>
            <div class="task-detail-row">
              <span class="task-detail-label">申请时间</span>
              <span class="task-detail-value">{{ formatTime(selectedTask?.created_at) }}</span>
            </div>
            <div class="task-detail-row" v-if="selectedTask?.reason">
              <span class="task-detail-label">原因</span>
              <span class="task-detail-value">{{ selectedTask.reason }}</span>
            </div>
            <div class="task-detail-row">
              <span class="task-detail-label">状态</span>
              <span class="task-detail-value status-badge" :class="selectedTask?.status">{{ selectedTask?.status }}</span>
            </div>
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="btn-apple-primary" @click="approveTask(selectedTask)">批准</button>
          <button class="btn-apple-danger" @click="rejectTask(selectedTask)">拒绝</button>
          <button class="btn-apple-secondary" @click="showTaskDetailModal = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/authStore.js'
import { useTeamStore } from '../stores/teamStore.js'

const emit = defineEmits(['show-toast', 'navigate'])

const authStore = useAuthStore()
const teamStore = useTeamStore()

// Admin判断必须通过 authStore（符合 FE-016）
const isAdmin = computed(() => authStore.isAdmin)

// 配额使用百分比
const quotaUsagePercent = computed(() => {
  if (selectedTeamQuota.value.max_bytes === 0) return 0
  return Math.round(
    (selectedTeamQuota.value.used_bytes / selectedTeamQuota.value.max_bytes) * 100
  )
})

const myTeams = ref([])
const allTeams = ref([])
const loading = ref(false)
const joinToken = ref('')
const showCredentials = ref(false)
const showCreateTeamModal = ref(false)
const showMembersModal = ref(false)
const showEditTeamModal = ref(false)
const showTaskDetailModal = ref(false)
const selectedTeam = ref(null)
const selectedTeamForQuota = ref(null)
const selectedTeamQuota = ref({
  max_bytes: 0,
  used_bytes: 0,
  available_bytes: 0,
  member_count: 0,
  max_members: 0
})
const credentials = ref([])
const pendingTasks = ref([])
const teamMembers = ref([])
const newTeam = ref({ name: '', description: '', storagePoolId: '' })
const storagePools = ref([])
const editTeamData = ref({ name: '', description: '' })
const selectedTask = ref(null)

onMounted(() => {
  loadTeams()
  if (isAdmin.value) {
    loadPendingTasks()
  }
})

async function loadTeams() {
  loading.value = true
  try {
    await teamStore.loadTeams()
    myTeams.value = teamStore.myTeams || []
    if (isAdmin.value) {
      await teamStore.loadAllTeams()
      allTeams.value = teamStore.allTeams || []
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

// 使用 teamStore.joinTeamWithValidation（符合 FE-022 先预检再加入）
async function joinTeam() {
  if (!joinToken.value.trim()) {
    emit('show-toast', { type: 'error', title: '错误', message: '请输入邀请码' })
    return
  }

  loading.value = true
  try {
    // 先预检邀请码，有效则自动加入（符合 FE-022）
    await teamStore.joinTeamWithValidation(joinToken.value)
    emit('show-toast', { type: 'success', title: '成功', message: '已加入团队' })
    joinToken.value = ''
    loadTeams()
  } catch (err) {
    // 预检失败会抛出明确错误信息
    emit('show-toast', { type: 'error', title: '无法加入', message: err.message })
  } finally {
    loading.value = false
  }
}

function showCreateTeam() {
  newTeam.value = { name: '', description: '', storagePoolId: '' }
  loadStoragePoolsForTeam()
  showCreateTeamModal.value = true
}

async function loadStoragePoolsForTeam() {
  try {
    const data = await api.getStoragePools()
    storagePools.value = data.pools || []
  } catch (err) {
    console.warn('Failed to load storage pools:', err)
  }
}

async function confirmCreateTeam() {
  if (!newTeam.value.name) return

  try {
    await teamStore.createTeam(
      newTeam.value.name,
      newTeam.value.description,
      newTeam.value.storagePoolId || null
    )
    emit('show-toast', { type: 'success', title: '成功', message: '团队创建成功' })
    showCreateTeamModal.value = false
    loadTeams()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function enterTeam(team) {
  emit('navigate', { view: 'spaces', teamId: team.team_id })
}

async function showTeamMembers(team) {
  selectedTeam.value = team
  showMembersModal.value = true
  try {
    const members = await teamStore.loadTeamMembers(team.team_id)
    teamMembers.value = members || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function canRemoveMember(member) {
  return member.role !== 'owner' && selectedTeam.value?.my_role === 'owner'
}

async function removeTeamMember(member) {
  if (!confirm(`确定要移除成员 "${member.username}" 吗？`)) return
  try {
    await teamStore.removeTeamMember(selectedTeam.value.team_id, member.user_id)
    emit('show-toast', { type: 'success', title: '成功', message: `已移除 ${member.username}` })
    showTeamMembers(selectedTeam.value)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function editTeam(team) {
  selectedTeam.value = team
  editTeamData.value = { name: team.name, description: team.description || '' }
  showEditTeamModal.value = true
}

async function confirmEditTeam() {
  if (!editTeamData.value.name) return

  try {
    await teamStore.updateTeam(selectedTeam.value.team_id, {
      name: editTeamData.value.name,
      description: editTeamData.value.description
    })
    emit('show-toast', { type: 'success', title: '成功', message: '团队信息已更新' })
    showEditTeamModal.value = false
    loadTeams()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function showTeamCredentials(team) {
  selectedTeam.value = team
  showCredentials.value = true
  try {
    const data = await teamStore.getTeamCredentials(team.team_id)
    credentials.value = data.credentials || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function createCredential() {
  if (!selectedTeam.value) return
  try {
    await teamStore.createInviteCode(selectedTeam.value.team_id)
    emit('show-toast', { type: 'success', title: '成功', message: '邀请码已生成' })
    showTeamCredentials(selectedTeam.value)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function deleteCredential(credId) {
  if (!confirm('确定要删除这个邀请码吗？')) return
  try {
    await teamStore.deleteTeamCredential(selectedTeam.value.team_id, credId)
    emit('show-toast', { type: 'success', title: '成功', message: '邀请码已删除' })
    showTeamCredentials(selectedTeam.value)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function getQuotaClass(usage) {
  if (usage > 0.9) return 'team-card__quota-fill--danger'
  if (usage > 0.7) return 'team-card__quota-fill--warn'
  return 'team-card__quota-fill--ok'
}

function getQuotaClassForPanel(percent) {
  if (percent >= 90) return 'danger'
  if (percent >= 70) return 'warn'
  return 'ok'
}

async function loadTeamQuota(team) {
  selectedTeamForQuota.value = team
  try {
    const data = await teamStore.fetchTeamQuotaStatus(team.team_id)
    selectedTeamQuota.value = data
  } catch (err) {
    console.error('Failed to load team quota:', err)
  }
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

async function loadPendingTasks() {
  try {
    const tasks = await teamStore.fetchPendingTasks()
    pendingTasks.value = tasks || []
  } catch (err) {
    console.error('Failed to load pending tasks:', err)
  }
}

function getTaskTypeName(type) {
  const typeMap = {
    'team_join': '申请加入团队',
    'team_member_exit': '成员退出申请',
    'private_space': '私人空间申请'
  }
  return typeMap[type] || type
}

function formatTime(time) {
  if (!time) return ''
  const date = new Date(time)
  return date.toLocaleDateString()
}

function showTaskDetail(task) {
  selectedTask.value = task
  showTaskDetailModal.value = true
}

async function approveTask(task) {
  if (!task) return
  try {
    await teamStore.processApproval(task.id, 'approved')
    emit('show-toast', { type: 'success', title: '已批准', message: '申请已批准' })
    showTaskDetailModal.value = false
    loadPendingTasks()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function rejectTask(task) {
  if (!task) return
  try {
    await teamStore.processApproval(task.id, 'rejected')
    emit('show-toast', { type: 'success', title: '已拒绝', message: '申请已拒绝' })
    showTaskDetailModal.value = false
    loadPendingTasks()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}
</script>

<style scoped>
/* ============================================
   TeamView - Apple Design System
   Layout: max-width constrained, centered content
   ============================================ */

/* === Layout === */
.team-view {
  /* Layout */
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: auto;
  padding: var(--spacing-lg);
  box-sizing: border-box;

  /* Visual */
  background: transparent;
}

/* === Toolbar === */
.team-view__toolbar {
  /* Layout */
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-lg);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;

  /* Box Sizing */
  box-sizing: border-box;
}

/* === Header === */
.team-view__header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-lg);

  /* Visual - Card styling per DESIGN.md */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;

  /* Box Sizing */
  box-sizing: border-box;
}

/* === My Teams Section === */
.my-teams-section {
  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);

  /* Box Model */
  margin-bottom: var(--spacing-xl);
}

/* === All Teams Section === */
.all-teams-section {
  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);

  /* Box Model */
  margin-bottom: var(--spacing-xl);
}

/* === Join Team Section === */
.team-view__join-form {
  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);

  /* Box Model */
  margin-top: var(--spacing-lg);
}

/* === Element: team-view__title === */
.team-view__title {
  font: var(--text-tagline);
  color: var(--color-ink);
  margin: 0 0 var(--spacing-md);
}

/* === Element: team-view__toolbar-spacer === */
.team-view__toolbar-spacer {
  flex: 1;
}

.team-quota-panel {
  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Box Model */
  padding: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.team-quota-panel__title {
  /* Typography */
  font: var(--text-body-strong);
  color: var(--color-ink);

  /* Box Model */
  margin-bottom: var(--spacing-md);
}

.quota-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.quota-row {
  display: flex;
  justify-content: space-between;
}

.quota-label {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.quota-value {
  /* Typography */
  font: var(--text-body);
  font-weight: 600;
  color: var(--color-ink);
}

.quota-bar {
  /* Box Model */
  height: var(--spacing-xxs);
  margin-top: var(--spacing-md);

  /* Visual */
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.quota-bar-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s ease;
}

.quota-bar-fill.ok { background: var(--color-success); }
.quota-bar-fill.warn { background: var(--color-warning); }
.quota-bar-fill.danger { background: var(--color-danger); }

.pending-tasks-panel {
  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Box Model */
  padding: var(--spacing-lg);
  margin-top: var(--spacing-lg);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

.task-badge {
  /* Visual */
  background: var(--color-danger);
  color: var(--color-body-on-dark);
  border-radius: var(--radius-full);

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-sm);

  /* Typography */
  font: var(--text-caption);
}

.task-item {
  display: flex;
  justify-content: space-between;
  align-items: center;

  /* Box Model */
  padding: var(--spacing-sm);
  margin-bottom: var(--spacing-xs);

  /* Visual */
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.task-item:last-child {
  margin-bottom: 0;
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.task-type {
  /* Typography */
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.task-applicant {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.task-actions {
  display: flex;
  gap: var(--spacing-xs);
}

.task-empty {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  text-align: center;
  padding: var(--spacing-lg);
}

/* === Task Detail Modal === */
.task-detail {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.task-detail-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.task-detail-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.task-detail-value {
  font: var(--text-body);
  color: var(--color-ink);
  text-align: right;
}

.task-detail-value.status-badge {
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.task-detail-value.status-badge.pending {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.task-detail-value.status-badge.approved {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.task-detail-value.status-badge.rejected {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

/* === Member List Modal === */
.member-list-modal {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.member-item-modal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.member-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.member-name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.member-role-badge {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
}

.member-role-badge.owner {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.member-role-badge.admin {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.member-role-badge.member {
  background: var(--color-gray-subtle);
  color: var(--color-ink-muted-48);
}

/* === Form Elements === */
.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font: var(--text-caption-strong);
  color: var(--color-ink);
  margin-bottom: var(--spacing-xxs);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm);
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

/* === Modal Styles === */
.team-view__modal-overlay {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-overlay);
  z-index: 1000;
}

.team-view__modal {
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.team-view__modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.team-view__modal-header h3 {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.team-view__modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  font-size: 24px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.team-view__modal-close:hover {
  background: var(--color-surface-pearl);
}

.team-view__modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-lg);
}

.team-view__modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-hairline);
}

.team-view__empty {
  text-align: center;
  padding: var(--spacing-lg);
  color: var(--color-ink-muted-48);
}

.team-view__empty p {
  margin: 0;
  font: var(--text-body);
}

/* === Button Variants === */
.btn-apple-sm {
  padding: 6px 14px;
  min-height: auto;
  font: var(--text-caption);
}

.btn-detail {
  padding: 4px 10px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-sm);
  font: var(--text-caption);
  color: var(--color-ink);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-detail:hover {
  background: var(--color-surface-pearl);
}

.btn-approve {
  padding: 4px 10px;
  background: var(--color-success);
  border: none;
  border-radius: var(--radius-sm);
  font: var(--text-caption);
  color: var(--color-body-on-dark);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-approve:hover {
  background: #2db84d;
}

.btn-reject {
  padding: 4px 10px;
  background: var(--color-danger);
  border: none;
  border-radius: var(--radius-sm);
  font: var(--text-caption);
  color: var(--color-body-on-dark);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-reject:hover {
  background: #e6352b;
}
</style>

