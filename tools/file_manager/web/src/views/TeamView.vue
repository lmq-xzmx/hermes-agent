<template>
  <div class="team-view">
    <!-- Toolbar -->
    <div class="team-view__toolbar">
      <button class="team-view__btn team-view__btn--primary" @click="showCreateTeam">+ 创建团队</button>
      <div class="team-view__spacer"></div>
      <button class="team-view__btn team-view__btn--secondary" @click="loadTeams">刷新</button>
    </div>

    <!-- My Teams section -->
    <div class="team-view__header">
      <h3 class="team-view__title">我所在的团队</h3>
    </div>
    <div id="myTeamsSection">
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
            <button class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="enterTeam(team)">进入</button>
            <button class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="showTeamMembers(team)">成员</button>
            <button v-if="team.my_role === 'owner'" class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="showTeamCredentials(team)">邀请码</button>
          </div>
        </div>
      </div>
    </div>

    <!-- All teams (admin) -->
    <div v-if="isAdmin" id="allTeamsSection" class="team-view__section-gap">
      <div class="team-view__header">
        <h3 class="team-view__title">所有团队 (管理)</h3>
      </div>
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
            <button class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="editTeam(team)">编辑</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Join team -->
    <div class="team-view__section-gap">
      <h3 class="team-view__title">加入团队</h3>
      <div class="team-view__join-form">
        <input type="text" v-model="joinToken" placeholder="输入邀请码" class="team-view__search-input">
        <button class="team-view__btn team-view__btn--primary" @click="joinTeam">加入</button>
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
          <button class="team-view__btn team-view__btn--primary" style="margin-bottom:var(--spacing-md)" @click="createCredential">+ 生成邀请码</button>
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
              <button class="team-view__btn team-view__btn--danger team-view__btn--sm" @click="deleteCredential(cred.id)">删除</button>
            </div>
          </div>
        </div>
        <div class="team-view__modal-footer">
          <button class="team-view__btn team-view__btn--secondary" @click="showCredentials = false">关闭</button>
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
  if (usage > 0.9) return 'team-card__quota-fill--danger'
  if (usage > 0.7) return 'team-card__quota-fill--warn'
  return 'team-card__quota-fill--ok'
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
/* ============================================
   TeamView - Apple Design System
   Based on DESIGN.md Apple Design System specs
   ============================================ */

/* --------------------------------------------
   Layout - View Container
   -------------------------------------------- */
.team-view {
  flex: 1;
  overflow: auto;
  padding: var(--spacing-lg);
}

/* --------------------------------------------
   Toolbar
   -------------------------------------------- */
.team-view__toolbar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) 0;
  margin-bottom: var(--spacing-lg);
}

.team-view__spacer {
  flex: 1;
}

/* --------------------------------------------
   Typography - Headers & Titles
   -------------------------------------------- */
.team-view__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.team-view__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin-bottom: var(--spacing-sm);
}

.team-view__section-gap {
  margin-top: var(--spacing-xl);
}

/* --------------------------------------------
   Buttons - Apple Design System
   -------------------------------------------- */
.team-view__btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font: var(--text-body);
  border: none;
  border-radius: var(--radius-pill);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.team-view__btn:active {
  transform: scale(0.95);
}

.team-view__btn--primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
  padding: var(--spacing-sm) var(--spacing-md);
}

.team-view__btn--primary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.team-view__btn--secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-hairline);
  padding: var(--spacing-sm) var(--spacing-md);
}

.team-view__btn--secondary:hover {
  background: var(--color-canvas-parchment);
}

.team-view__btn--secondary:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.team-view__btn--danger {
  background: transparent;
  color: var(--color-danger);
  border: 1px solid var(--color-hairline);
  padding: var(--spacing-sm) var(--spacing-md);
}

.team-view__btn--danger:hover {
  background: var(--color-danger-subtle);
}

.team-view__btn--sm {
  font: var(--text-caption);
  padding: var(--spacing-xxs) var(--spacing-sm);
}

/* --------------------------------------------
   Team List - Card Grid
   -------------------------------------------- */
.team-view__list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* --------------------------------------------
   Team Card - store-utility-card Style
   -------------------------------------------- */
.team-card {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.team-card__main {
  display: flex;
  align-items: center;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
}

.team-card__info {
  flex: 1;
  min-width: 150px;
}

.team-card__name {
  font: var(--text-body-strong);
  color: var(--color-ink);
  display: block;
}

.team-card__desc {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  display: block;
  margin-top: var(--spacing-xxs);
}

.team-card__stats {
  display: flex;
  gap: var(--spacing-lg);
}

.team-card__stat {
  text-align: center;
}

.team-card__stat-value {
  font: var(--text-body-strong);
  color: var(--color-ink);
  display: block;
}

.team-card__stat-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.team-card__stat--quota .team-card__stat-label {
  color: var(--color-ink-muted-48);
}

.team-card__quota-bar {
  width: 100px;
  height: var(--spacing-xs);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.team-card__quota-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s;
}

.team-card__quota-fill--ok { background: var(--color-success); }
.team-card__quota-fill--warn { background: var(--color-warning); }
.team-card__quota-fill--danger { background: var(--color-danger); }

.team-card__owner {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.team-card__badge {
  display: inline-block;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption-strong);
}

.team-card__badge--active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.team-card__badge--inactive {
  background: var(--color-gray-subtle);
  color: var(--color-ink-muted-48);
}

.team-card__actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-divider-soft);
}

/* --------------------------------------------
   Join Form
   -------------------------------------------- */
.team-view__join-form {
  display: flex;
  gap: var(--spacing-sm);
  max-width: 400px;
}

.team-view__search-input {
  flex: 1;
  background: var(--color-canvas);
  color: var(--color-ink);
  font: var(--text-body);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  height: 44px;
}

.team-view__search-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* --------------------------------------------
   Empty State
   -------------------------------------------- */
.team-view__empty {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl) var(--spacing-lg);
}

.team-view__empty--show {
  display: flex;
}

.team-view__empty-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
  opacity: 0.5;
}

/* --------------------------------------------
   Loading
   -------------------------------------------- */
.team-view__loading {
  text-align: center;
  padding: var(--spacing-lg);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* --------------------------------------------
   Modal - Apple Design System
   -------------------------------------------- */
.team-view__modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal-backdrop);
}

.team-view__modal {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: auto;
}

.team-view__modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.team-view__modal-header h3 {
  font: var(--text-body-strong);
  margin: 0;
}

.team-view__modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-ink-muted-48);
}

.team-view__modal-body {
  padding: var(--spacing-lg);
}

.team-view__modal-footer {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
}

/* --------------------------------------------
   Credential List
   -------------------------------------------- */
.team-view__credential-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.team-view__credential-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-sm);
}

.team-view__credential-token {
  font: var(--text-caption);
  font-family: ui-monospace, "SF Mono", "Cascadia Code", "Fira Code", monospace;
  color: var(--color-ink);
  background: var(--color-canvas);
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
}

.team-view__credential-detail {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}
</style>