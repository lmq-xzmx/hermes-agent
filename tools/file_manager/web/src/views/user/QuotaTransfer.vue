<template>
  <LifecycleProvider>
  <div class="quota-transfer">
    <header class="quota-transfer__header">
      <h1 class="quota-transfer__title">配额调配</h1>
      <button @click="showTransferRequest = true" class="button-primary">
        发起调配请求
      </button>
    </header>

    <div v-if="loading" class="quota-transfer__loading">加载中...</div>

    <div v-else class="quota-transfer__content">
      <!-- 当前空间配额 -->
      <section class="quota-transfer__section">
        <h2 class="quota-transfer__section-title">当前空间</h2>
        <div class="space-select">
          <select v-model="selectedSpaceId" @change="loadSpaceQuota" class="select-input">
            <option value="">选择空间</option>
            <option v-for="space in userSpaces" :key="space.id" :value="space.id">
              {{ space.name }}
            </option>
          </select>
        </div>

        <div v-if="currentSpace" class="quota-overview">
          <div class="quota-stat">
            <span class="quota-stat__label">承诺配额</span>
            <span class="quota-stat__value">{{ formatBytes(currentSpace.committed_bytes) }}</span>
          </div>
          <div class="quota-stat">
            <span class="quota-stat__label">已用</span>
            <span class="quota-stat__value">{{ formatBytes(currentSpace.used_bytes) }}</span>
          </div>
          <div class="quota-stat">
            <span class="quota-stat__label">可用</span>
            <span class="quota-stat__value quota-stat__value--available">{{ formatBytes(currentSpace.available_bytes) }}</span>
          </div>
        </div>
      </section>

      <!-- 发起调配请求 -->
      <section v-if="showTransferRequest" class="quota-transfer__section">
        <h2 class="quota-transfer__section-title">发起调配请求</h2>

        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">目标空间 <span class="required">*</span></label>
            <select v-model="transferRequest.target_space_id" class="select-input">
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
            <label class="form-label">调配配额 <span class="required">*</span></label>
            <div class="input-with-unit">
              <input
                v-model.number="transferRequest.transfer_quota_gb"
                type="number"
                min="1"
                :max="maxTransferQuota"
                class="form-input form-input--number"
              />
              <span class="unit">GB</span>
            </div>
            <span class="form-hint">
              最大可调配: {{ formatBytes(maxTransferQuota) }}
            </span>
          </div>

          <div class="form-group form-group--full">
            <label class="form-label">调配原因 <span class="required">*</span></label>
            <textarea
              v-model="transferRequest.reason"
              placeholder="请输入调配原因..."
              rows="3"
              class="form-textarea"
            ></textarea>
          </div>

          <div class="form-group">
            <label class="form-label">有效期</label>
            <select v-model="transferRequest.duration_days" class="select-input">
              <option :value="7">7 天</option>
              <option :value="14">14 天</option>
              <option :value="30">30 天</option>
            </select>
          </div>
        </div>

        <div class="form-actions">
          <button @click="cancelTransfer" class="button-secondary">取消</button>
          <button @click="submitTransfer" class="button-primary" :disabled="submitting">
            {{ submitting ? '提交中...' : '提交' }}
          </button>
        </div>
      </section>

      <!-- 调配历史 -->
      <section class="quota-transfer__section">
        <h2 class="quota-transfer__section-title">调配历史</h2>

        <div v-if="transferHistory.length === 0" class="empty-state">
          暂无调配记录
        </div>

        <table v-else class="data-table">
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
                <span :class="['badge', record.direction === 'out' ? 'badge--warning' : 'badge--success']">
                  {{ record.direction === 'out' ? '调配出' : '收到' }}
                </span>
              </td>
              <td>{{ record.space_name }}</td>
              <td>{{ formatBytes(record.transfer_bytes) }}</td>
              <td>
                <span :class="['badge', getStatusBadgeClass(record.status)]">
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
        <div class="modal__header">
          <h3 class="modal__title">确认调配</h3>
          <button @click="showConfirmDialog = false" class="modal__close">×</button>
        </div>
        <div class="modal__body">
          <p class="confirm-message">确定要发起以下调配请求吗？</p>
          <div class="confirm-details">
            <div class="detail-row">
              <span class="detail-row__label">从:</span>
              <span class="detail-row__value">{{ currentSpace?.name }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-row__label">到:</span>
              <span class="detail-row__value">{{ getTargetSpaceName() }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-row__label">配额:</span>
              <span class="detail-row__value">{{ transferRequest.transfer_quota_gb }} GB</span>
            </div>
            <div class="detail-row">
              <span class="detail-row__label">有效期:</span>
              <span class="detail-row__value">{{ transferRequest.duration_days }} 天</span>
            </div>
          </div>
        </div>
        <div class="modal__footer">
          <button @click="showConfirmDialog = false" class="button-secondary">取消</button>
          <button @click="confirmTransfer" class="button-primary">确认</button>
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
    { id: 's1', name: '团队A', committed_bytes: 500 * 1024 * 1024 * 1024, used_bytes: 200 * 1024 * 1024 * 1024, available_bytes: 300 * 1024 * 1024 * 1024 },
    { id: 's2', name: '团队B', committed_bytes: 300 * 1024 * 1024 * 1024, used_bytes: 280 * 1024 * 1024 * 1024, available_bytes: 20 * 1024 * 1024 * 1024 },
    { id: 's3', name: '团队C', committed_bytes: 200 * 1024 * 1024 * 1024, used_bytes: 50 * 1024 * 1024 * 1024, available_bytes: 150 * 1024 * 1024 * 1024 }
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
    { id: 't1', direction: 'out', space_name: '团队A', transfer_bytes: 200 * 1024 * 1024 * 1024, status: 'expired', created_at: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000), expires_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000) },
    { id: 't2', direction: 'in', space_name: '团队C', transfer_bytes: 100 * 1024 * 1024 * 1024, status: 'expired', created_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000), expires_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000) },
    { id: 't3', direction: 'in', space_name: '团队B', transfer_bytes: 50 * 1024 * 1024 * 1024, status: 'approved', created_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000), expires_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000) }
  ]
}

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024 * 1024) return (bytes / (1024 * 1024 * 1024 * 1024)).toFixed(2) + ' TB'
  if (bytes >= 1024 * 1024 * 1024) return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

function formatDate(date) {
  return new Date(date).toLocaleDateString('zh-CN')
}

function getStatusText(status) {
  const statusMap = { pending: '待审批', approved: '已通过', rejected: '已拒绝', expired: '已过期', cancelled: '已取消' }
  return statusMap[status] || status
}

function getStatusBadgeClass(status) {
  if (status === 'approved') return 'badge--success'
  if (status === 'rejected' || status === 'expired') return 'badge--danger'
  return 'badge--warning'
}

function getTargetSpaceName() {
  const target = userSpaces.value.find(s => s.id === transferRequest.value.target_space_id)
  return target?.name || ''
}

function cancelTransfer() {
  showTransferRequest.value = false
  transferRequest.value = { target_space_id: '', transfer_quota_gb: 10, reason: '', duration_days: 7 }
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
/* === QuotaTransfer - 配额调配页面 === */

.quota-transfer {
  padding: var(--spacing-lg);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}

/* === Header === */
.quota-transfer__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.quota-transfer__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

/* === Loading === */
.quota-transfer__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* === Content === */
.quota-transfer__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

/* === Section === */
.quota-transfer__section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.quota-transfer__section-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

/* === Empty State === */
.empty-state {
  padding: var(--spacing-xl);
  text-align: center;
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* === Space Select === */
.space-select {
  max-width: 300px;
}

.select-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  cursor: pointer;
  box-sizing: border-box;
}

.select-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* === Quota Overview === */
.quota-overview {
  display: flex;
  gap: var(--spacing-xl);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.quota-stat {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.quota-stat__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.quota-stat__value {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.quota-stat__value--available {
  color: var(--color-success);
}

/* === Form Grid === */
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-group--full {
  grid-column: 1 / -1;
}

.form-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.required {
  color: var(--color-danger);
}

.form-input {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-input--number {
  width: 120px;
}

.form-textarea {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  resize: vertical;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-hint {
  font: var(--text-fine-print);
  color: var(--color-ink-muted-48);
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.unit {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* === Form Actions === */
.form-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

/* === Data Table === */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-divider-soft);
}

.data-table th {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  font: var(--text-body);
  color: var(--color-ink);
}

/* === Badge === */
.badge {
  display: inline-block;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.badge--success {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

.badge--danger {
  background: var(--color-danger-subtle);
  color: var(--color-danger-strong);
}

/* === Modal === */
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
  z-index: var(--z-modal-backdrop);
}

.modal {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.modal__title {
  font: var(--text-body-strong);
  margin: 0;
}

.modal__close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
}

.modal__body {
  padding: var(--spacing-lg);
}

.modal__footer {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
}

.confirm-message {
  font: var(--text-body);
  color: var(--color-ink);
  margin: 0 0 var(--spacing-md) 0;
}

.confirm-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: var(--spacing-md);
}

.detail-row__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.detail-row__value {
  font: var(--text-body);
  color: var(--color-ink);
  text-align: right;
}

/* === Buttons === */
.button-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.button-primary:active {
  transform: scale(0.95);
}

.button-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, background 0.15s ease;
}

.button-secondary:active {
  transform: scale(0.95);
}
</style>