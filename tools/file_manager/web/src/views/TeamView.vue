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
            <button class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="enterTeam(team)">进入</button>
            <button class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="showTeamMembers(team)">成员</button>
            <button v-if="team.my_role === 'owner'" class="team-view__btn team-view__btn--secondary team-view__btn--sm" @click="showTeamCredentials(team)">邀请码</button>
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

    <!-- All teams (admin) -->
    <div v-if="isAdmin" class="all-teams-section team-view__section-gap">
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

onMounted(() => {
  loadTeams()
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

async function showCreateTeam() {
  const name = prompt('请输入团队名称:')
  if (!name) return

  const description = prompt('请输入团队描述 (可选):') || ''

  try {
    await teamStore.createTeam(name, description)
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
    const members = await teamStore.loadTeamMembers(team.team_id)
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
    await teamStore.updateTeam(team.team_id, { name: newName, description: newDescription })
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
</script>

<style scoped>
.team-quota-panel {
  background: var(--color-surface-secondary);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
}

.team-quota-panel__title {
  font-size: var(--font-size-lg);
  font-weight: 600;
  color: var(--color-ink-primary);
  margin-bottom: 12px;
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

.quota-value {
  color: var(--color-ink-primary);
  font-weight: 500;
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
</style>

