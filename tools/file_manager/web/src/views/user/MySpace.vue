<template>
  <LifecycleProvider>
  <div class="my-space">
    <header class="page-header">
      <h1>我的空间</h1>
      <button @click="showApplyExpand = true" class="btn btn-primary">
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

            <button @click="viewTeamDetail(team)" class="btn btn-secondary btn-small">
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
          <button @click="showApplyExpand = false" class="btn btn-secondary">取消</button>
          <button @click="submitExpandRequest" class="btn btn-primary" :disabled="submitting">
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
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 24px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.space-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.private-space {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

.space-card {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.space-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
  margin-bottom: 12px;
}

.space-meta {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border, #30363d);
}

.quota-label {
  color: var(--text-secondary, #8b949e);
}

.quota-value {
  color: var(--text-primary, #e6edf3);
  font-weight: 500;
}

.usage-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 8px;
}

.progress-bar {
  flex: 1;
  height: 12px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 6px;
  overflow: hidden;
}

.progress-bar.small {
  height: 6px;
}

.progress-fill {
  height: 100%;
  background: #238636;
  border-radius: 6px;
  transition: width 0.3s ease;
}

.progress-fill.warning {
  background: #9e6a03;
}

.progress-fill.critical {
  background: #da3633;
}

.progress-text {
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
  min-width: 50px;
  text-align: right;
}

.warning-banner {
  background: rgba(218, 54, 51, 0.1);
  border: 1px solid rgba(218, 54, 51, 0.3);
  border-radius: 6px;
  padding: 12px;
  color: #da3633;
  font-size: 14px;
}

.team-spaces {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

.team-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.team-card {
  background: var(--bg-tertiary, #21262d);
  border-radius: 8px;
  padding: 16px;
}

.team-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.team-name {
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.team-quota {
  margin-bottom: 12px;
}

.quota-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  padding: 4px 0;
  color: var(--text-secondary, #8b949e);
}

.team-progress {
  margin-bottom: 12px;
}

.team-card .btn-small {
  padding: 6px 12px;
  font-size: 12px;
}

.request-history {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border, #30363d);
}

.history-table th {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  font-weight: 500;
}

.history-table td {
  font-size: 14px;
  color: var(--text-primary, #e6edf3);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-normal {
  background: rgba(35, 134, 54, 0.2);
  color: #238636;
}

.status-warning {
  background: rgba(158, 106, 3, 0.2);
  color: #9e6a03;
}

.status-critical {
  background: rgba(218, 54, 51, 0.2);
  color: #da3633;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  width: 500px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border, #30363d);
}

.modal-header h3 {
  margin: 0;
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary, #8b949e);
}

.modal-body {
  padding: 16px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 8px;
}

.current-quota {
  padding: 12px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  font-weight: 500;
}

.quota-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.quota-option {
  padding: 10px 16px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  cursor: pointer;
  transition: all 0.2s;
}

.quota-option:hover {
  border-color: #238636;
}

.quota-option.selected {
  background: #238636;
  border-color: #238636;
  color: white;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  resize: vertical;
  font-family: inherit;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--border, #30363d);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: #238636;
  color: white;
}

.btn-primary:disabled {
  background: #21262d;
  color: #484f58;
}

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}
</style>
