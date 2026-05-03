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
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.dashboard-header h1 {
  font-size: 24px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.dashboard-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.quota-section {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  cursor: pointer;
}

.section-header h2 {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.expand-icon {
  color: var(--text-secondary, #8b949e);
  font-size: 12px;
}

.badge {
  background: #da3633;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
}

.section-content {
  padding: 0 16px 16px;
}

.quota-table {
  width: 100%;
  border-collapse: collapse;
}

.quota-table th,
.quota-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid var(--border, #30363d);
}

.quota-table th {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  font-weight: 500;
}

.quota-table td {
  font-size: 14px;
  color: var(--text-primary, #e6edf3);
}

.usage-bar {
  width: 100px;
  height: 8px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 4px;
  display: inline-block;
  vertical-align: middle;
  margin-right: 8px;
}

.usage-fill {
  height: 100%;
  border-radius: 4px;
  background: #238636;
}

.usage-fill.warning {
  background: #9e6a03;
}

.usage-fill.critical {
  background: #da3633;
}

.usage-text {
  font-size: 12px;
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

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  font-size: 14px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
}

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transfer-item {
  background: var(--bg-tertiary, #21262d);
  border-radius: 6px;
  padding: 16px;
}

.transfer-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.transfer-from, .transfer-to {
  font-weight: 500;
}

.transfer-arrow {
  color: var(--text-secondary, #8b949e);
}

.transfer-amount {
  background: var(--bg-secondary, #161b22);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.transfer-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 12px;
}

.transfer-actions {
  display: flex;
  gap: 8px;
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

.form-group select,
.form-group input {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
}

.input-with-unit {
  display: flex;
}

.input-with-unit input {
  flex: 1;
  border-radius: 6px 0 0 6px;
}

.input-with-unit .unit {
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-left: none;
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary, #8b949e);
}

.checkbox-list {
  max-height: 200px;
  overflow-y: auto;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  cursor: pointer;
}

.checkbox-item:hover {
  background: var(--bg-tertiary, #21262d);
}

.quota-display {
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
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

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}

.btn-success {
  background: #238636;
  color: white;
}

.btn-danger {
  background: #da3633;
  color: white;
}
</style>
