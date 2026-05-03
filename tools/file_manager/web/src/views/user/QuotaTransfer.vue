<template>
  <LifecycleProvider>
  <div class="quota-transfer">
    <header class="page-header">
      <h1>配额调配</h1>
      <button @click="showTransferRequest = true" class="btn btn-primary">
        发起调配请求
      </button>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="transfer-content">
      <!-- 当前空间配额 -->
      <section class="current-space">
        <h2>当前空间</h2>
        <div class="space-select">
          <select v-model="selectedSpaceId" @change="loadSpaceQuota">
            <option value="">选择空间</option>
            <option v-for="space in userSpaces" :key="space.id" :value="space.id">
              {{ space.name }}
            </option>
          </select>
        </div>

        <div v-if="currentSpace" class="quota-overview">
          <div class="quota-stat">
            <span class="stat-label">承诺配额</span>
            <span class="stat-value">{{ formatBytes(currentSpace.committed_bytes) }}</span>
          </div>
          <div class="quota-stat">
            <span class="stat-label">已用</span>
            <span class="stat-value">{{ formatBytes(currentSpace.used_bytes) }}</span>
          </div>
          <div class="quota-stat">
            <span class="stat-label">可用</span>
            <span class="stat-value available">{{ formatBytes(currentSpace.available_bytes) }}</span>
          </div>
        </div>
      </section>

      <!-- 发起调配请求 -->
      <section v-if="showTransferRequest" class="transfer-request-section">
        <h2>发起调配请求</h2>

        <div class="form-grid">
          <div class="form-group">
            <label>目标空间 <span class="required">*</span></label>
            <select v-model="transferRequest.target_space_id">
              <option value="">选择目标空间</option>
              <option
                v-for="space in availableTargetSpaces"
                :key="space.id"
                :value="space.id"
              >
                {{ space.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>调配配额 <span class="required">*</span></label>
            <div class="input-with-unit">
              <input
                v-model.number="transferRequest.transfer_quota_gb"
                type="number"
                min="1"
                :max="maxTransferQuota"
              />
              <span class="unit">GB</span>
            </div>
            <span class="helper-text">
              最大可调配: {{ formatBytes(maxTransferQuota) }}
            </span>
          </div>

          <div class="form-group">
            <label>调配原因 <span class="required">*</span></label>
            <textarea
              v-model="transferRequest.reason"
              placeholder="请输入调配原因..."
              rows="3"
            ></textarea>
          </div>

          <div class="form-group">
            <label>有效期</label>
            <select v-model="transferRequest.duration_days">
              <option :value="7">7 天</option>
              <option :value="14">14 天</option>
              <option :value="30">30 天</option>
            </select>
          </div>
        </div>

        <div class="form-actions">
          <button @click="cancelTransfer" class="btn btn-secondary">取消</button>
          <button @click="submitTransfer" class="btn btn-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </section>

      <!-- 调配历史 -->
      <section class="transfer-history">
        <h2>调配历史</h2>

        <div v-if="transferHistory.length === 0" class="empty-state">
          暂无调配记录
        </div>

        <table v-else class="history-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>类型</th>
              <th>空间</th>
              <th>配额</th>
              <th>状态</th>
              <th>有效期至</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in transferHistory" :key="record.id">
              <td>{{ formatDate(record.created_at) }}</td>
              <td>
                <span :class="['type-badge', record.direction]">
                  {{ record.direction === 'out' ? '调配出' : '收到' }}
                </span>
              </td>
              <td>{{ record.space_name }}</td>
              <td>{{ formatBytes(record.transfer_bytes) }}</td>
              <td>
                <span :class="['status-badge', record.status]">
                  {{ getStatusText(record.status) }}
                </span>
              </td>
              <td>{{ record.expires_at ? formatDate(record.expires_at) : '-' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <!-- 确认弹窗 -->
    <div v-if="showConfirmDialog" class="modal-overlay" @click.self="showConfirmDialog = false">
      <div class="modal">
        <div class="modal-header">
          <h3>确认调配</h3>
          <button @click="showConfirmDialog = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <p>确定要发起以下调配请求吗？</p>
          <div class="confirm-details">
            <div class="detail-row">
              <span>从:</span>
              <span>{{ currentSpace?.name }}</span>
            </div>
            <div class="detail-row">
              <span>到:</span>
              <span>{{ getTargetSpaceName() }}</span>
            </div>
            <div class="detail-row">
              <span>配额:</span>
              <span>{{ transferRequest.transfer_quota_gb }} GB</span>
            </div>
            <div class="detail-row">
              <span>有效期:</span>
              <span>{{ transferRequest.duration_days }} 天</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showConfirmDialog = false" class="btn btn-secondary">取消</button>
          <button @click="confirmTransfer" class="btn btn-primary">确认</button>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const loading = ref(true)
const submitting = ref(false)
const showTransferRequest = ref(false)
const showConfirmDialog = ref(false)

const selectedSpaceId = ref('')
const userSpaces = ref([])
const currentSpace = ref(null)
const transferHistory = ref([])

const transferRequest = ref({
  target_space_id: '',
  transfer_quota_gb: 10,
  reason: '',
  duration_days: 7
})

const availableTargetSpaces = computed(() => {
  return userSpaces.value.filter(s => s.id !== selectedSpaceId.value)
})

const maxTransferQuota = computed(() => {
  if (!currentSpace.value) return 0
  return currentSpace.value.available_bytes
})

async function loadUserSpaces() {
  userSpaces.value = [
    {
      id: 's1',
      name: '团队A',
      committed_bytes: 500 * 1024 * 1024 * 1024,
      used_bytes: 200 * 1024 * 1024 * 1024,
      available_bytes: 300 * 1024 * 1024 * 1024
    },
    {
      id: 's2',
      name: '团队B',
      committed_bytes: 300 * 1024 * 1024 * 1024,
      used_bytes: 280 * 1024 * 1024 * 1024,
      available_bytes: 20 * 1024 * 1024 * 1024
    },
    {
      id: 's3',
      name: '团队C',
      committed_bytes: 200 * 1024 * 1024 * 1024,
      used_bytes: 50 * 1024 * 1024 * 1024,
      available_bytes: 150 * 1024 * 1024 * 1024
    }
  ]
}

function loadSpaceQuota() {
  if (!selectedSpaceId.value) {
    currentSpace.value = null
    return
  }
  currentSpace.value = userSpaces.value.find(s => s.id === selectedSpaceId.value)
}

async function loadTransferHistory() {
  transferHistory.value = [
    {
      id: 't1',
      direction: 'out',
      space_name: '团队A',
      transfer_bytes: 200 * 1024 * 1024 * 1024,
      status: 'expired',
      created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
      expires_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000)
    },
    {
      id: 't2',
      direction: 'in',
      space_name: '团队C',
      transfer_bytes: 100 * 1024 * 1024 * 1024,
      status: 'expired',
      created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000),
      expires_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000)
    },
    {
      id: 't3',
      direction: 'in',
      space_name: '团队B',
      transfer_bytes: 50 * 1024 * 1024 * 1024,
      status: 'approved',
      created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000),
      expires_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000)
    }
  ]
}

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

function getStatusText(status) {
  const statusMap = {
    pending: '待审批',
    approved: '已通过',
    rejected: '已拒绝',
    expired: '已过期',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

function getTargetSpaceName() {
  const target = userSpaces.value.find(s => s.id === transferRequest.value.target_space_id)
  return target?.name || ''
}

function cancelTransfer() {
  showTransferRequest.value = false
  transferRequest.value = {
    target_space_id: '',
    transfer_quota_gb: 10,
    reason: '',
    duration_days: 7
  }
}

function submitTransfer() {
  if (!transferRequest.value.target_space_id) {
    alert('请选择目标空间')
    return
  }
  if (!transferRequest.value.reason) {
    alert('请输入调配原因')
    return
  }
  showConfirmDialog.value = true
}

async function confirmTransfer() {
  showConfirmDialog.value = false
  submitting.value = true

  try {
    // API call to submit transfer request
    await new Promise(resolve => setTimeout(resolve, 500))

    transferHistory.value.unshift({
      id: 't' + Date.now(),
      direction: 'out',
      space_name: getTargetSpaceName(),
      transfer_bytes: transferRequest.value.transfer_quota_gb * 1024 * 1024 * 1024,
      status: 'pending',
      created_at: new Date(),
      expires_at: new Date(Date.now() + transferRequest.value.duration_days * 24 * 60 * 60 * 1000)
    })

    cancelTransfer()
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  await loadUserSpaces()
  await loadTransferHistory()
  loading.value = false
})
</script>

<style scoped>
.quota-transfer {
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

.transfer-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

section {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

section h2 {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
  margin: 0 0 16px 0;
}

.space-select select {
  width: 100%;
  padding: 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  font-size: 14px;
}

.quota-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 16px;
}

.quota-stat {
  background: var(--bg-tertiary, #21262d);
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.stat-value.available {
  color: #238636;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
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

.required {
  color: #da3633;
}

.form-group select,
.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
  font-size: 14px;
}

.form-group textarea {
  resize: vertical;
}

.input-with-unit {
  display: flex;
}

.input-with-unit input {
  flex: 1;
  border-radius: 6px 0 0 6px;
}

.input-with-unit .unit {
  padding: 10px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-left: none;
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary, #8b949e);
}

.helper-text {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-top: 4px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
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

.type-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.type-badge.out {
  background: rgba(218, 54, 51, 0.2);
  color: #da3633;
}

.type-badge.in {
  background: rgba(35, 134, 54, 0.2);
  color: #238636;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.pending {
  background: rgba(158, 106, 3, 0.2);
  color: #9e6a03;
}

.status-badge.approved {
  background: rgba(35, 134, 54, 0.2);
  color: #238636;
}

.status-badge.rejected,
.status-badge.expired {
  background: rgba(218, 54, 51, 0.2);
  color: #da3633;
}

.status-badge.cancelled {
  background: var(--bg-tertiary, #21262d);
  color: var(--text-secondary, #8b949e);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
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
  width: 450px;
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

.modal-body p {
  color: var(--text-secondary, #8b949e);
  margin: 0 0 16px 0;
}

.confirm-details {
  background: var(--bg-tertiary, #21262d);
  border-radius: 6px;
  padding: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border, #30363d);
}

.detail-row:last-child {
  border-bottom: none;
}

.detail-row span:first-child {
  color: var(--text-secondary, #8b949e);
}

.detail-row span:last-child {
  color: var(--text-primary, #e6edf3);
  font-weight: 500;
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
  padding: 10px 20px;
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
