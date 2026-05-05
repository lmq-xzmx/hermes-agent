<template>
  <LifecycleProvider>
  <div class="quota-dashboard">
    <header class="dashboard-header">
      <h1>配额管理</h1>
      <div class="header-actions">
        <button @click="showBatchAdjust = true" class="btn btn-primary">
          + 批量调整
        </button>
        <button @click="refresh" class="btn btn-secondary">🔄 刷新</button>
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
                <button @click="approveTransfer(transfer.id)" class="btn btn-success">审批</button>
                <button @click="rejectTransfer(transfer.id)" class="btn btn-danger">拒绝</button>
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
          <button @click="showBatchAdjust = false" class="btn btn-secondary">取消</button>
          <button @click="executeBatchAdjust" class="btn btn-primary">确认调整</button>
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
          <button @click="showEditQuota = false" class="btn btn-secondary">取消</button>
          <button @click="saveQuotaEdit" class="btn btn-primary">保存</button>
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
.quota-dashboard {
  min-height: 100vh;
  background: var(--color-canvas-parchment, #f5f5f7);
  padding: var(--space-section, 80px);
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl, 32px);
  max-width: 1440px;
  margin-left: auto;
  margin-right: auto;
}

.dashboard-header h1 {
  font: var(--text-display-md, 34px/1.47 -0.374px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-sm, 12px);
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg, 24px);
  max-width: 1440px;
  margin: 0 auto;
}

.quota-section {
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
  padding: var(--space-lg, 24px);
  cursor: pointer;
}

.section-header h2 {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.expand-icon {
  color: var(--color-ink-muted-48, #7a7a7a);
  font-size: 12px;
}

.badge {
  background: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
  padding: 2px 10px;
  border-radius: var(--rounded-pill, 9999px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
}

.section-content {
  padding: 0 var(--space-lg, 24px) var(--space-lg, 24px);
}

.quota-table {
  width: 100%;
  border-collapse: collapse;
}

.quota-table th,
.quota-table td {
  padding: var(--space-md, 17px);
  text-align: left;
  border-bottom: 1px solid var(--color-hairline, #e0e0e0);
}

.quota-table th {
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
  color: var(--color-ink-muted-48, #7a7a7a);
}

.quota-table td {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink, #1d1d1f);
}

.usage-bar {
  width: 100px;
  height: 8px;
  background: var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-pill, 9999px);
  display: inline-block;
  vertical-align: middle;
  margin-right: var(--space-xs, 8px);
}

.usage-fill {
  height: 100%;
  border-radius: var(--rounded-pill, 9999px);
  background: var(--color-primary, #0066cc);
}

.usage-fill.warning {
  background: #d29922;
}

.usage-fill.critical {
  background: #f85149;
}

.usage-text {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.status-badge {
  padding: 4px 12px;
  border-radius: var(--rounded-pill, 9999px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
}

.status-normal {
  background: rgba(0, 102, 204, 0.1);
  color: var(--color-primary, #0066cc);
}

.status-warning {
  background: rgba(210, 153, 34, 0.15);
  color: #9e6a03;
}

.status-critical {
  background: rgba(248, 81, 73, 0.15);
  color: #f85149;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--space-xxs, 4px) var(--space-xs, 8px);
  font-size: 16px;
}

.empty-state {
  text-align: center;
  padding: var(--space-xl, 32px);
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 12px);
}

.transfer-item {
  background: var(--color-canvas-parchment, #f5f5f7);
  border-radius: var(--rounded-md, 11px);
  padding: var(--space-md, 17px);
}

.transfer-info {
  display: flex;
  align-items: center;
  gap: var(--space-xs, 8px);
  margin-bottom: var(--space-xs, 8px);
}

.transfer-from, .transfer-to {
  font-weight: 600;
}

.transfer-arrow {
  color: var(--color-ink-muted-48, #7a7a7a);
}

.transfer-amount {
  background: var(--color-canvas, #ffffff);
  padding: 4px 10px;
  border-radius: var(--rounded-pill, 9999px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
}

.transfer-meta {
  display: flex;
  gap: var(--space-md, 17px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-bottom: var(--space-sm, 12px);
}

.transfer-actions {
  display: flex;
  gap: var(--space-xs, 8px);
}

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
  z-index: 1000;
}

.modal {
  background: var(--color-canvas, #ffffff);
  border-radius: var(--rounded-lg, 18px);
  width: 500px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg, 24px);
  border-bottom: 1px solid var(--color-hairline, #e0e0e0);
}

.modal-header h3 {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-ink-muted-48, #7a7a7a);
}

.modal-body {
  padding: var(--space-lg, 24px);
}

.form-group {
  margin-bottom: var(--space-md, 17px);
}

.form-group label {
  display: block;
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-bottom: var(--space-xs, 8px);
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px 14px;
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-sm, 8px);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
}

.input-with-unit {
  display: flex;
}

.input-with-unit input {
  flex: 1;
  border-radius: var(--rounded-sm, 8px) 0 0 var(--rounded-sm, 8px);
}

.input-with-unit .unit {
  padding: 10px 14px;
  background: var(--color-canvas-parchment, #f5f5f7);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-left: none;
  border-radius: 0 var(--rounded-sm, 8px) var(--rounded-sm, 8px) 0;
  color: var(--color-ink-muted-48, #7a7a7a);
}

.checkbox-list {
  max-height: 200px;
  overflow-y: auto;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs, 8px);
  padding: var(--space-xs, 8px);
  cursor: pointer;
}

.checkbox-item:hover {
  background: var(--color-canvas-parchment, #f5f5f7);
}

.quota-display {
  padding: 10px 14px;
  background: var(--color-canvas-parchment, #f5f5f7);
  border-radius: var(--rounded-sm, 8px);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm, 12px);
  padding: var(--space-lg, 24px);
  border-top: 1px solid var(--color-hairline, #e0e0e0);
}

.loading {
  text-align: center;
  padding: var(--space-xl, 32px);
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.btn {
  padding: 10px 20px;
  border-radius: var(--rounded-pill, 9999px);
  cursor: pointer;
  border: none;
  font: var(--text-body, 17px/1.47 -0.374px);
  transition: transform 0.1s ease;
}

.btn:active {
  transform: scale(0.95);
}

.btn-primary {
  background: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
}

.btn-secondary {
  background: var(--color-canvas, #ffffff);
  color: var(--color-ink, #1d1d1f);
  border: 1px solid var(--color-hairline, #e0e0e0);
}

.btn-success {
  background: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
}

.btn-danger {
  background: #f85149;
  color: var(--color-on-primary, #ffffff);
}
</style>
