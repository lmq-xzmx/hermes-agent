<template>
  <div class="team-view">
    <!-- Toolbar -->
    <div class="toolbar">
      <button class="btn-apple-primary" @click="showCreateTeam">+ 创建团队</button>
      <div class="toolbar-spacer"></div>
      <button class="btn-apple-secondary" @click="loadTeams">刷新</button>
    </div>

    <!-- My Teams section -->
    <div class="view-header">
      <h3 class="section-title">我所在的团队</h3>
    </div>
    <div id="myTeamsSection">
      <div v-if="loading" class="loading">加载中...</div>
      <div v-else-if="myTeams.length === 0" class="empty-state show">
        <div class="empty-state-icon">👥</div>
        <p>您还没有加入任何团队</p>
      </div>
      <div v-else class="team-list">
        <div v-for="team in myTeams" :key="team.team_id" class="team-card">
          <div class="team-card-main">
            <div class="team-info">
              <span class="team-name">{{ team.name }}</span>
              <span v-if="team.description" class="team-desc">{{ team.description }}</span>
            </div>
            <div class="team-stats">
              <div class="stat-item">
                <span class="stat-value">{{ team.member_count || 0 }}</span>
                <span class="stat-label">成员</span>
              </div>
              <div class="stat-item quota-stat">
                <span class="stat-value">{{ formatSize(team.quota_used) }}</span>
                <span class="stat-label">/ {{ formatSize(team.quota_total) }}</span>
              </div>
            </div>
            <div class="quota-bar">
              <div class="quota-fill" :class="getQuotaClass(team.quota_usage)"></div>
            </div>
            <span class="badge" :class="team.status === 'active' ? 'badge-active' : 'badge-inactive'">
              {{ team.status === 'active' ? '活跃' : '未激活' }}
            </span>
          </div>
          <div class="team-card-actions">
            <button class="btn-apple-primary btn-sm" @click="enterTeam(team)">进入</button>
            <button class="btn-apple-secondary btn-sm" @click="showTeamMembers(team)">成员</button>
            <button v-if="team.my_role === 'owner'" class="btn-apple-secondary btn-sm" @click="showTeamCredentials(team)">邀请码</button>
          </div>
        </div>
      </div>
    </div>

    <!-- All teams (admin) -->
    <div v-if="isAdmin" id="allTeamsSection" class="section-gap">
      <div class="view-header">
        <h3 class="section-title">所有团队 (管理)</h3>
      </div>
      <div v-if="allTeams.length === 0" class="empty-state show">
        <p>暂无团队数据</p>
      </div>
      <div v-else class="team-list">
        <div v-for="team in allTeams" :key="team.team_id" class="team-card">
          <div class="team-card-main">
            <div class="team-info">
              <span class="team-name">{{ team.name }}</span>
            </div>
            <div class="team-stats">
              <div class="stat-item">
                <span class="stat-value">{{ team.member_count || 0 }}</span>
                <span class="stat-label">成员</span>
              </div>
              <div class="stat-item quota-stat">
                <span class="stat-value">{{ formatSize(team.quota_used) }}</span>
                <span class="stat-label">/ {{ formatSize(team.quota_total) }}</span>
              </div>
            </div>
            <div class="quota-bar">
              <div class="quota-fill" :class="getQuotaClass(team.quota_usage)"></div>
            </div>
            <span class="team-owner">{{ team.owner_username || '-' }}</span>
          </div>
          <div class="team-card-actions">
            <button class="btn-apple-secondary btn-sm" @click="editTeam(team)">编辑</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Join team -->
    <div class="section-gap">
      <h3 class="section-title">加入团队</h3>
      <div class="join-form">
        <input type="text" v-model="joinToken" placeholder="输入邀请码" class="search-input">
        <button class="btn-apple-primary" @click="joinTeam">加入</button>
      </div>
    </div>

    <!-- Team Credentials Modal -->
    <div v-if="showCredentials" class="modal-overlay" @click.self="showCredentials = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ selectedTeam.name }} - 邀请码</h3>
          <button class="btn-close" @click="showCredentials = false">&times;</button>
        </div>
        <div class="modal-body">
          <button class="btn-apple-primary" style="margin-bottom:16px" @click="createCredential">+ 生成邀请码</button>
          <div v-if="credentials.length === 0" class="empty-state show">
            <p>暂无邀请码</p>
          </div>
          <div v-else class="credential-list">
            <div v-for="cred in credentials" :key="cred.id" class="credential-item">
              <code class="credential-token">{{ cred.token }}</code>
              <span class="badge" :class="cred.used_count >= cred.max_uses ? 'badge-inactive' : 'badge-active'">
                {{ cred.used_count >= cred.max_uses ? '已用完' : '可用' }}
              </span>
              <span class="credential-detail">{{ cred.expires_at ? formatDate(cred.expires_at) : '永不过期' }}</span>
              <span class="credential-detail">{{ cred.used_count }} / {{ cred.max_uses }}</span>
              <button class="btn-apple-danger btn-sm" @click="deleteCredential(cred.id)">删除</button>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-apple-secondary" @click="showCredentials = false">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { api } from '../services/api.js'

const emit = defineEmits(['show-toast', 'navigate'])

const myTeams = ref([])
const allTeams = ref([])
const loading = ref(false)
const joinToken = ref('')
const isAdmin = computed(() => localStorage.getItem('hfm_role') === 'admin')
const showCredentials = ref(false)
const selectedTeam = ref(null)
const credentials = ref([])

onMounted(() => {
  loadTeams()
})

async function loadTeams() {
  loading.value = true
  try {
    const data = await api.getTeams()
    myTeams.value = data.teams || []
    if (isAdmin.value) {
      const allData = await api.getAllTeams()
      allTeams.value = allData.teams || []
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

async function joinTeam() {
  if (!joinToken.value.trim()) {
    emit('show-toast', { type: 'error', title: '错误', message: '请输入邀请码' })
    return
  }

  loading.value = true
  try {
    await api.joinTeam(joinToken.value)
    emit('show-toast', { type: 'success', title: '成功', message: '已加入团队' })
    joinToken.value = ''
    loadTeams()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

async function showCreateTeam() {
  const name = prompt('请输入团队名称:')
  if (!name) return

  const description = prompt('请输入团队描述 (可选):') || ''

  try {
    await api.createTeam(name, description)
    emit('show-toast', { type: 'success', title: '成功', message: '团队创建成功' })
    loadTeams()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function enterTeam(team) {
  emit('navigate', { view: 'spaces', teamId: team.team_id })
}

async function showTeamMembers(team) {
  try {
    const data = await api.getTeamMembers(team.team_id)
    const members = data.members || []
    const memberList = members.map(m => `${m.username} (${m.role})`).join('\n')
    alert(`团队成员 (${members.length}):\n\n${memberList || '暂无成员'}`)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function editTeam(team) {
  const newName = prompt('请输入新的团队名称:', team.name)
  if (!newName || newName === team.name) return

  const newDescription = prompt('请输入新的团队描述:', team.description || '') || ''

  try {
    await api.updateTeam(team.team_id, { name: newName, description: newDescription })
    emit('show-toast', { type: 'success', title: '成功', message: '团队信息已更新' })
    loadTeams()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function showTeamCredentials(team) {
  selectedTeam.value = team
  showCredentials.value = true
  try {
    const data = await api.getTeamCredentials(team.team_id)
    credentials.value = data.credentials || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function createCredential() {
  if (!selectedTeam.value) return
  try {
    await api.createTeamCredential(selectedTeam.value.team_id, { max_uses: 10, expires_at: null })
    emit('show-toast', { type: 'success', title: '成功', message: '邀请码已生成' })
    showTeamCredentials(selectedTeam.value)
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function deleteCredential(credId) {
  if (!confirm('确定要删除这个邀请码吗？')) return
  try {
    await api.deleteTeamCredential(selectedTeam.value.team_id, credId)
    emit('show-toast', { type: 'success', title: '成功', message: '邀请码已删除' })
    showTeamCredentials(selectedTeam.value)
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
.team-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-lg);
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) 0;
  margin-bottom: var(--space-lg);
}

.toolbar-spacer {
  flex: 1;
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
  margin-bottom: var(--space-sm);
}

.section-gap {
  margin-top: var(--space-xl);
}

/* Team List */
.team-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.team-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  padding: var(--space-lg);
}

.team-card-main {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.team-info {
  flex: 1;
  min-width: 150px;
}

.team-name {
  font: var(--text-body-strong);
  color: var(--color-ink);
  display: block;
}

.team-desc {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  display: block;
  margin-top: 4px;
}

.team-stats {
  display: flex;
  gap: var(--space-lg);
}

.stat-item {
  text-align: center;
}

.stat-value {
  font: var(--text-body-strong);
  color: var(--color-ink);
  display: block;
}

.stat-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.quota-stat .stat-label {
  color: var(--color-ink-muted-48);
}

.quota-bar {
  width: 100px;
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

.team-owner {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.team-card-actions {
  display: flex;
  gap: var(--space-xs);
  margin-top: var(--space-md);
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-divider-soft);
}

/* Badge */
.badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: var(--rounded-pill);
  font: var(--text-caption);
  font-weight: 600;
}

.badge-active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge-inactive {
  background: rgba(120, 120, 128, 0.15);
  color: var(--color-ink-muted-48);
}

/* Join Form */
.join-form {
  display: flex;
  gap: var(--space-sm);
  max-width: 400px;
}

.search-input {
  flex: 1;
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--text-body);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-pill);
  padding: 12px 20px;
  height: 44px;
}
.search-input:focus {
  outline: 2px solid var(--color-primary, #0066cc);
  outline-offset: 2px;
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-content {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  width: 90%;
  max-width: 600px;
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

/* Credential List */
.credential-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.credential-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md, 18px);
}

.credential-token {
  font-family: monospace;
  font-size: 14px;
  color: var(--color-ink);
  background: var(--color-canvas);
  padding: 4px 8px;
  border-radius: var(--radius-xs);
}

.credential-detail {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}
</style>
