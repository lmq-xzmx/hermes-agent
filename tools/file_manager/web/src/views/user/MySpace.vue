<template>
  <LifecycleProvider>
  <div class="my-space">
    <header class="page-header">
      <h1>我的空间</h1>
      <button @click="showApplyExpand = true" class="btn-apple-primary">
        申请扩容
      </button>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="space-content">
      <!-- 我的私有空间 -->
      <section class="private-space">
        <div class="section-header">
          <h2>我的私有空间</h2>
        </div>

        <div class="space-card">
          <div class="space-info">
            <div class="space-name">{{ currentUser.username }} 的空间</div>
            <div class="space-meta">
              <span class="quota-label">配额</span>
              <span class="quota-value">{{ formatBytes(mySpace.committed_bytes) }}</span>
            </div>
            <div class="space-meta">
              <span class="quota-label">已用</span>
              <span class="quota-value">{{ formatBytes(mySpace.used_bytes) }}</span>
            </div>
            <div class="space-meta">
              <span class="quota-label">剩余</span>
              <span class="quota-value">{{ formatBytes(mySpace.available_bytes) }}</span>
            </div>
          </div>

          <div class="usage-progress">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :class="getUsageClass(mySpace.used_bytes / mySpace.committed_bytes)"
                :style="{ width: Math.min(100, (mySpace.used_bytes / mySpace.committed_bytes) * 100) + '%' }"
              ></div>
            </div>
            <div class="progress-text">
              {{ ((mySpace.used_bytes / mySpace.committed_bytes) * 100).toFixed(1) }}%
            </div>
          </div>

          <div v-if="mySpace.used_bytes > mySpace.committed_bytes * 0.9" class="warning-banner">
            ⚠️ 空间使用率超过 90%，请及时清理或申请扩容
          </div>
        </div>
      </section>

      <!-- 加入的团队 -->
      <section class="team-spaces">
        <div class="section-header">
          <h2>加入的团队</h2>
        </div>

        <div v-if="teamSpaces.length === 0" class="empty-state">
          暂未加入任何团队
        </div>

        <div v-else class="team-list">
          <div v-for="team in teamSpaces" :key="team.id" class="team-card">
            <div class="team-header">
              <span class="team-name">{{ team.name }}</span>
              <span class="status-badge" :class="getStatusClass(team)">
                {{ getStatusText(team) }}
              </span>
            </div>

            <div class="team-quota">
              <div class="quota-row">
                <span>配额</span>
                <span>{{ formatBytes(team.committed_bytes) }}</span>
              </div>
              <div class="quota-row">
                <span>已用</span>
                <span>{{ formatBytes(team.used_bytes) }}</span>
              </div>
            </div>

            <div class="team-progress">
              <div class="progress-bar small">
                <div
                  class="progress-fill"
                  :class="getUsageClass(team.used_bytes / team.committed_bytes)"
                  :style="{ width: Math.min(100, (team.used_bytes / team.committed_bytes) * 100) + '%' }"
                ></div>
              </div>
            </div>

            <button @click="viewTeamDetail(team)" class="btn-apple-secondary btn-sm">
              查看详情
            </button>
          </div>
        </div>
      </section>

      <!-- 申请记录 -->
      <section class="request-history">
        <div class="section-header">
          <h2>申请记录</h2>
        </div>

        <div v-if="requestHistory.length === 0" class="empty-state">
          暂无申请记录
        </div>

        <table v-else class="history-table">
          <thead>
            <tr>
              <th>申请类型</th>
              <th>申请内容</th>
              <th>状态</th>
              <th>申请时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="req in requestHistory" :key="req.id">
              <td>{{ req.type }}</td>
              <td>{{ req.content }}</td>
              <td>
                <span class="status-badge" :class="getRequestStatusClass(req.status)">
                  {{ req.status_text }}
                </span>
              </td>
              <td>{{ formatDate(req.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- 申请扩容弹窗 -->
    <div v-if="showApplyExpand" class="modal-overlay" @click.self="showApplyExpand = false">
      <div class="modal">
        <div class="modal-header">
          <h3>申请扩容</h3>
          <button @click="showApplyExpand = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>当前配额</label>
            <div class="current-quota">
              {{ formatBytes(mySpace.committed_bytes) }}
            </div>
          </div>
          <div class="form-group">
            <label>申请扩容至</label>
            <div class="quota-options">
              <button
                v-for="option in quotaOptions"
                :key="option.value"
                :class="['quota-option', { selected: expandRequest.newQuota === option.value }]"
                @click="expandRequest.newQuota = option.value"
              >
                {{ option.label }}
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>申请理由</label>
            <textarea
              v-model="expandRequest.reason"
              placeholder="请输入申请扩容的理由..."
              rows="4"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showApplyExpand = false" class="btn-apple-secondary">取消</button>
          <button @click="submitExpandRequest" class="btn-apple-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交申请' }}
          </button>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const loading = ref(true)
const submitting = ref(false)
const showApplyExpand = ref(false)

const currentUser = ref({
  username: 'current_user',
  id: 'u1'
})

const mySpace = ref({
  committed_bytes: 10 * 1024 * 1024 * 1024,
  used_bytes: 2 * 1024 * 1024 * 1024,
  available_bytes: 8 * 1024 * 1024 * 1024
})

const teamSpaces = ref([
  {
    id: 't1',
    name: '团队A',
    committed_bytes: 100 * 1024 * 1024 * 1024,
    used_bytes: 40 * 1024 * 1024 * 1024,
    status: 'normal'
  },
  {
    id: 't2',
    name: '团队B',
    committed_bytes: 50 * 1024 * 1024 * 1024,
    used_bytes: 45 * 1024 * 1024 * 1024,
    status: 'warning'
  }
])

const requestHistory = ref([
  {
    id: 'r1',
    type: '扩容申请',
    content: '申请从 10GB 扩容至 20GB',
    status: 'pending',
    status_text: '待审批',
    created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000)
  }
])

const quotaOptions = [
  { label: '20 GB', value: 20 * 1024 * 1024 * 1024 },
  { label: '50 GB', value: 50 * 1024 * 1024 * 1024 },
  { label: '100 GB', value: 100 * 1024 * 1024 * 1024 },
  { label: '200 GB', value: 200 * 1024 * 1024 * 1024 },
  { label: '500 GB', value: 500 * 1024 * 1024 * 1024 }
]

const expandRequest = ref({
  newQuota: 20 * 1024 * 1024 * 1024,
  reason: ''
})

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024 * 1024)).toFixed(2) + ' TB'
  }
  if (bytes >= 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('zh-CN')
}

function getUsageClass(ratio) {
  if (ratio >= 0.95) return 'critical'
  if (ratio >= 0.8) return 'warning'
  return 'normal'
}

function getStatusClass(team) {
  const ratio = team.used_bytes / team.committed_bytes
  if (ratio >= 0.95) return 'status-critical'
  if (ratio >= 0.8) return 'status-warning'
  return 'status-normal'
}

function getStatusText(team) {
  const ratio = team.used_bytes / team.committed_bytes
  if (ratio >= 0.95) return '严重'
  if (ratio >= 0.8) return '预警'
  return '正常'
}

function getRequestStatusClass(status) {
  if (status === 'approved') return 'status-normal'
  if (status === 'rejected') return 'status-critical'
  return 'status-warning'
}

function viewTeamDetail(team) {
  // Navigate to team detail page
}

async function submitExpandRequest() {
  submitting.value = true
  try {
    // API call to submit expansion request
    await new Promise(resolve => setTimeout(resolve, 500))
    requestHistory.value.unshift({
      id: 'r' + Date.now(),
      type: '扩容申请',
      content: `申请从 ${formatBytes(mySpace.value.committed_bytes)} 扩容至 ${formatBytes(expandRequest.value.newQuota)}`,
      status: 'pending',
      status_text: '待审批',
      created_at: new Date()
    })
    showApplyExpand.value = false
    expandRequest.value = { newQuota: 20 * 1024 * 1024 * 1024, reason: '' }
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  // Load user space data
  await new Promise(resolve => setTimeout(resolve, 300))
  loading.value = false
})
</script>

<style scoped>
.my-space {
  padding: var(--spacing-lg);
  background: var(--color-surface-tile-1);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.page-header h1 {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0;
  letter-spacing: -0.374px;
}

.space-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.section-header {
  margin-bottom: var(--space-md);
}

.section-header h2 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0;
  letter-spacing: -0.374px;
}

.private-space {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.space-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.space-name {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin-bottom: var(--space-md);
}

.space-meta {
  display: flex;
  justify-content: space-between;
  padding: var(--space-xs) 0;
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.quota-label {
  color: var(--color-body-muted);
}

.quota-value {
  color: var(--color-body-on-dark);
  font-weight: 400;
}

.usage-progress {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-sm);
}

.progress-bar {
  flex: 1;
  height: 12px;
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-bar.small {
  height: 6px;
}

.progress-fill {
  height: 100%;
  background: var(--color-success);
  border-radius: var(--radius-full);
  transition: width 0.3s ease;
}

.progress-fill.warning {
  background: var(--color-warning);
}

.progress-fill.critical {
  background: var(--color-danger);
}

.progress-text {
  font-size: 14px;
  color: var(--color-body-muted);
  min-width: 50px;
  text-align: right;
}

.warning-banner {
  background: var(--color-danger-subtle);
  border: 1px solid var(--color-danger-hover);
  border-radius: var(--radius-md, 18px);
  padding: var(--space-md);
  color: var(--color-danger);
  font-size: 14px;
}

.team-spaces {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.team-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-md);
}

.team-card {
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-md);
  padding: var(--spacing-md);
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.team-name {
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.team-quota {
  margin-bottom: var(--space-sm);
}

.quota-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  padding: var(--space-xxs) 0;
  color: var(--color-body-muted);
}

.team-progress {
  margin-bottom: var(--space-sm);
}

.team-card .btn-small {
  padding: 6px 14px;
  font-size: 14px;
}

.request-history {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: var(--space-sm);
  text-align: left;
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.history-table th {
  font-size: 12px;
  color: var(--color-body-muted);
  font-weight: 600;
}

.history-table td {
  font-size: 14px;
  color: var(--color-body-on-dark);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-body-muted);
}

.status-badge {
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 12px;
}

.status-normal {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.status-warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning);
}

.status-critical {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

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
  z-index: var(--z-modal);
}

.modal {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  width: 500px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.modal-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-body-muted);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md, 18px);
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--color-surface-tile-1);
}

.btn-close:active {
  transform: scale(0.95);
}

.modal-body {
  padding: var(--space-md);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--color-body-muted);
  margin-bottom: var(--space-xs);
}

.current-quota {
  padding: var(--space-sm);
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-md, 18px);
  color: var(--color-body-on-dark);
  font-weight: 400;
}

.quota-options {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.quota-option {
  padding: 10px 16px;
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md, 18px);
  color: var(--color-body-on-dark);
  cursor: pointer;
  transition: all 0.2s;
}

.quota-option:hover {
  border-color: var(--color-primary);
}

.quota-option.selected {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-on-primary);
}

.form-group textarea {
  width: 100%;
  padding: var(--space-sm);
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md, 18px);
  color: var(--color-body-on-dark);
  resize: vertical;
  font-family: var(--font-family-text);
  font-size: 17px;
  line-height: 1.47;
  letter-spacing: -0.374px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-top: 1px solid var(--color-border-on-dark-soft);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--color-body-muted);
}

.btn {
  padding: 11px 22px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  border: none;
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  transition: var(--transition-active);
}

</style>
