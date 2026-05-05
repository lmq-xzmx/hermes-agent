<template>
  <LifecycleProvider>
  <div class="quota-dashboard">
    <header class="dashboard-header">
      <h1>配额管理</h1>
      <div class="header-actions">
        <button @click="showBatchAdjust = true" class="btn-apple-primary">
          + 批量调整
        </button>
        <button @click="refresh" class="btn-apple-secondary">🔄 刷新</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="dashboard-content">
      <!-- 团队配额列表 -->
      <section class="quota-section">
        <div class="section-header" @click="teamExpanded = !teamExpanded">
          <h2>团队配额</h2>
          <span class="expand-icon">{{ teamExpanded ? '▼' : '▶' }}</span>
        </div>

        <div v-show="teamExpanded" class="section-content">
          <table class="quota-table">
            <thead>
              <tr>
                <th>团队名称</th>
                <th>承诺配额</th>
                <th>已用</th>
                <th>使用率</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="team in teamQuotas" :key="team.id">
                <td>{{ team.name }}</td>
                <td>{{ formatBytes(team.committed_bytes) }}</td>
                <td>{{ formatBytes(team.used_bytes) }}</td>
                <td>
                  <div class="usage-bar">
                    <div
                      class="usage-fill"
                      :class="getUsageClass(team.used_bytes / team.committed_bytes)"
                      :style="{ width: Math.min(100, (team.used_bytes / team.committed_bytes) * 100) + '%' }"
                    ></div>
                  </div>
                  <span class="usage-text">{{ ((team.used_bytes / team.committed_bytes) * 100).toFixed(0) }}%</span>
                </td>
                <td>
                  <span class="status-badge" :class="getStatusClass(team)">
                    {{ getStatusText(team) }}
                  </span>
                </td>
                <td>
                  <button @click="editQuota(team)" class="btn-icon">✏️</button>
                  <button @click="viewTransferHistory(team)" class="btn-icon">📋</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 个人配额列表 -->
      <section class="quota-section">
        <div class="section-header" @click="personalExpanded = !personalExpanded">
          <h2>个人配额</h2>
          <span class="expand-icon">{{ personalExpanded ? '▼' : '▶' }}</span>
        </div>

        <div v-show="personalExpanded" class="section-content">
          <table class="quota-table">
            <thead>
              <tr>
                <th>用户</th>
                <th>配额类型</th>
                <th>承诺配额</th>
                <th>已用</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in personalQuotas" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.quota_type === 'unlimited' ? '无限制' : '有限额' }}</td>
                <td>{{ user.quota_type === 'unlimited' ? '无限制' : formatBytes(user.committed_bytes) }}</td>
                <td>{{ formatBytes(user.used_bytes) }}</td>
                <td>
                  <span class="status-badge" :class="getStatusClass(user)">
                    {{ getStatusText(user) }}
                  </span>
                </td>
                <td>
                  <button @click="editQuota(user)" class="btn-icon">✏️</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- 待处理调配请求 -->
      <section class="quota-section">
        <div class="section-header" @click="transfersExpanded = !transfersExpanded">
          <h2>待处理调配请求</h2>
          <span class="badge" v-if="pendingTransfers.length > 0">{{ pendingTransfers.length }}</span>
          <span class="expand-icon">{{ transfersExpanded ? '▼' : '▶' }}</span>
        </div>

        <div v-show="transfersExpanded" class="section-content">
          <div v-if="pendingTransfers.length === 0" class="empty-state">
            暂无待处理的调配请求
          </div>
          <div v-else class="transfer-list">
            <div v-for="transfer in pendingTransfers" :key="transfer.id" class="transfer-item">
              <div class="transfer-info">
                <span class="transfer-from">{{ transfer.from_space_name }}</span>
                <span class="transfer-arrow">→</span>
                <span class="transfer-to">{{ transfer.to_space_name }}</span>
                <span class="transfer-amount">{{ formatBytes(transfer.transfer_bytes) }}</span>
              </div>
              <div class="transfer-meta">
                <span>申请人: {{ transfer.requested_by }}</span>
                <span>有效期: {{ formatDate(transfer.expires_at) }}</span>
              </div>
              <div class="transfer-actions">
                <button @click="approveTransfer(transfer.id)" class="btn-apple-primary">审批</button>
                <button @click="rejectTransfer(transfer.id)" class="btn-apple-danger">拒绝</button>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- 批量调整弹窗 -->
    <div v-if="showBatchAdjust" class="modal-overlay" @click.self="showBatchAdjust = false">
      <div class="modal">
        <div class="modal-header">
          <h3>批量调整配额</h3>
          <button @click="showBatchAdjust = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择空间</label>
            <select v-model="batchSelect.type" @change="loadSpacesForBatch">
              <option value="team">团队空间</option>
              <option value="personal">个人空间</option>
            </select>
          </div>
          <div class="form-group">
            <label>选择要调整的空间</label>
            <div class="checkbox-list">
              <label v-for="space in spacesForBatch" :key="space.id" class="checkbox-item">
                <input type="checkbox" v-model="batchSelect.spaceIds" :value="space.id" />
                <span>{{ space.name }}</span>
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>新配额</label>
            <div class="input-with-unit">
              <input v-model.number="batchSelect.newQuota" type="number" min="0" />
              <span class="unit">GB</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showBatchAdjust = false" class="btn-apple-secondary">取消</button>
          <button @click="executeBatchAdjust" class="btn-apple-primary">确认调整</button>
        </div>
      </div>
    </div>

    <!-- 编辑配额弹窗 -->
    <div v-if="showEditQuota" class="modal-overlay" @click.self="showEditQuota = false">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑配额 - {{ editingQuota?.name }}</h3>
          <button @click="showEditQuota = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>当前配额</label>
            <div class="quota-display">
              {{ editingQuota ? formatBytes(editingQuota.committed_bytes) : '' }}
            </div>
          </div>
          <div class="form-group">
            <label>新配额</label>
            <div class="input-with-unit">
              <input v-model.number="editQuotaValue" type="number" min="0" />
              <span class="unit">GB</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showEditQuota = false" class="btn-apple-secondary">取消</button>
          <button @click="saveQuotaEdit" class="btn-apple-primary">保存</button>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const store = useAdminStore()
const loading = ref(true)
const teamExpanded = ref(true)
const personalExpanded = ref(true)
const transfersExpanded = ref(true)
const showBatchAdjust = ref(false)
const showEditQuota = ref(false)
const editingQuota = ref(null)
const editQuotaValue = ref(0)

const teamQuotas = ref([])
const personalQuotas = ref([])
const pendingTransfers = ref([])
const spacesForBatch = ref([])

const batchSelect = ref({
  type: 'team',
  spaceIds: [],
  newQuota: 0
})

async function refresh() {
  loading.value = true
  try {
    await Promise.all([
      loadTeamQuotas(),
      loadPersonalQuotas(),
      loadPendingTransfers()
    ])
  } finally {
    loading.value = false
  }
}

async function loadTeamQuotas() {
  // Mock data - in real app would call API
  teamQuotas.value = [
    { id: '1', name: '团队A', committed_bytes: 500 * 1024 * 1024 * 1024, used_bytes: 200 * 1024 * 1024 * 1024 },
    { id: '2', name: '团队B', committed_bytes: 300 * 1024 * 1024 * 1024, used_bytes: 280 * 1024 * 1024 * 1024 },
    { id: '3', name: '团队C', committed_bytes: 200 * 1024 * 1024 * 1024, used_bytes: 150 * 1024 * 1024 * 1024 }
  ]
}

async function loadPersonalQuotas() {
  personalQuotas.value = [
    { id: 'u1', username: 'admin', quota_type: 'unlimited', committed_bytes: 0, used_bytes: 100 * 1024 * 1024 * 1024 },
    { id: 'u2', username: 'lmq', quota_type: 'committed', committed_bytes: 10 * 1024 * 1024 * 1024, used_bytes: 2 * 1024 * 1024 * 1024 }
  ]
}

async function loadPendingTransfers() {
  pendingTransfers.value = [
    {
      id: 't1',
      from_space_name: '团队B',
      to_space_name: '团队A',
      transfer_bytes: 200 * 1024 * 1024 * 1024,
      requested_by: 'lmq',
      expires_at: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
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

function getUsageClass(ratio) {
  if (ratio >= 0.95) return 'critical'
  if (ratio >= 0.8) return 'warning'
  return 'normal'
}

function getStatusClass(item) {
  const ratio = item.used_bytes / item.committed_bytes
  if (item.quota_type === 'unlimited') return 'status-normal'
  if (ratio >= 0.95) return 'status-critical'
  if (ratio >= 0.8) return 'status-warning'
  return 'status-normal'
}

function getStatusText(item) {
  if (item.quota_type === 'unlimited') return '正常'
  const ratio = item.used_bytes / item.committed_bytes
  if (ratio >= 0.95) return '严重'
  if (ratio >= 0.8) return '预警'
  return '正常'
}

function editQuota(quota) {
  editingQuota.value = quota
  editQuotaValue.value = Math.round(quota.committed_bytes / (1024 * 1024 * 1024))
  showEditQuota.value = true
}

async function saveQuotaEdit() {
  if (!editingQuota.value) return
  const newBytes = editQuotaValue.value * 1024 * 1024 * 1024
  // API call to update quota
  editingQuota.value.committed_bytes = newBytes
  showEditQuota.value = false
}

function viewTransferHistory(space) {
  // Navigate to transfer history
}

async function approveTransfer(transferId) {
  // API call to approve
  pendingTransfers.value = pendingTransfers.value.filter(t => t.id !== transferId)
}

async function rejectTransfer(transferId) {
  // API call to reject
  pendingTransfers.value = pendingTransfers.value.filter(t => t.id !== transferId)
}

async function loadSpacesForBatch() {
  spacesForBatch.value = batchSelect.value.type === 'team' ? teamQuotas.value : personalQuotas.value
}

async function executeBatchAdjust() {
  // API call for batch adjustment
  showBatchAdjust.value = false
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
/* === QuotaDashboard - 配额管理页面 === */

.quota-dashboard {
  padding: var(--spacing-lg);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}

.quota-dashboard__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.quota-dashboard__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

.quota-dashboard__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.quota-dashboard__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.quota-section {
  display: flex;
  flex-direction: column;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.quota-section__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  cursor: pointer;
}

.quota-section__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.quota-section__expand-icon {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.quota-section__content {
  padding: 0 var(--spacing-lg) var(--spacing-lg);
}

.quota-table {
  width: 100%;
  border-collapse: collapse;
}

.quota-table th,
.quota-table td {
  padding: var(--spacing-md);
  text-align: left;
  border-bottom: 1px solid var(--color-divider-soft);
}

.quota-table th {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.quota-table td {
  font: var(--text-body);
  color: var(--color-ink);
}

.quota-table__usage {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.usage-bar {
  width: 80px;
  height: var(--spacing-xs);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-xs);
  overflow: hidden;
}

.usage-bar__fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 0.3s;
}

.usage-bar__fill--normal { background: var(--color-success); }
.usage-bar__fill--warning { background: var(--color-warning); }
.usage-bar__fill--critical { background: var(--color-danger); }

.usage-bar__text {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  min-width: 40px;
}

.status-badge {
  display: inline-block;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.status-badge--normal {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.status-badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

.status-badge--critical {
  background: var(--color-danger-subtle);
  color: var(--color-danger-strong);
}

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.transfer-item {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  padding: var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.transfer-item__info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font: var(--text-body);
  color: var(--color-ink);
}

.transfer-item__arrow {
  color: var(--color-ink-muted-48);
}

.transfer-item__amount {
  font: var(--text-body-strong);
  color: var(--color-primary);
}

.transfer-item__meta {
  display: flex;
  gap: var(--spacing-md);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.transfer-item__actions {
  display: flex;
  gap: var(--spacing-sm);
}

.empty-state {
  text-align: center;
  padding: var(--spacing-xl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--color-canvas-parchment);
  border: none;
  border-radius: var(--radius-md);
  font-size: 14px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.btn-icon:hover {
  background: var(--color-canvas);
}

.btn-apple-primary {
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

.btn-apple-primary:active {
  transform: scale(0.95);
}

.btn-apple-secondary {
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

.btn-apple-secondary:active {
  transform: scale(0.95);
}

.btn-apple-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-danger);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.btn-apple-danger:active {
  transform: scale(0.95);
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

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group__label {
  display: block;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--spacing-xxs);
}

.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-select:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-height: 200px;
  overflow-y: auto;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font: var(--text-body);
  color: var(--color-ink);
  cursor: pointer;
}

.quota-display {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.input-with-unit__input {
  width: 120px;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.input-with-unit__input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.input-with-unit__unit {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}
</style>

