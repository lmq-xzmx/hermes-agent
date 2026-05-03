<template>
  <div class="pending-approvals">
    <div class="header">
      <h3>待审批列表</h3>
      <button class="btn-refresh" @click="refresh" :disabled="loading">
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="requests.length === 0 && !loading" class="empty-state">
      暂无待审批的申请
    </div>

    <div v-else class="request-list">
      <div
        v-for="req in requests"
        :key="req.id"
        class="request-card"
        :class="{ selected: selectedId === req.id }"
        @click="selectRequest(req)"
      >
        <div class="request-header">
          <span class="approval-type">{{ getTypeLabel(req.type) }}</span>
          <span class="status-badge" :style="{ backgroundColor: getStatusColor(req.status) }">
            {{ getStatusLabel(req.status) }}
          </span>
        </div>

        <div class="request-info">
          <div class="info-row">
            <span class="label">申请人:</span>
            <span class="value">{{ req.applicant_name || req.applicant_id }}</span>
          </div>
          <div class="info-row" v-if="req.target_id">
            <span class="label">目标ID:</span>
            <span class="value">{{ req.target_id }}</span>
          </div>
          <div class="info-row" v-if="req.reason">
            <span class="label">理由:</span>
            <span class="value">{{ req.reason }}</span>
          </div>
          <div class="info-row">
            <span class="label">申请时间:</span>
            <span class="value">{{ formatDate(req.created_at) }}</span>
          </div>
        </div>

        <!-- 审批操作 (仅在选中时显示) -->
        <div v-if="selectedId === req.id" class="action-panel">
          <div class="comment-input">
            <textarea
              v-model="comment"
              placeholder="审批意见（可选）"
              rows="2"
            ></textarea>
          </div>
          <div class="action-buttons">
            <button class="btn-approve" @click.stop="handleApprove(req.id)">
              批准
            </button>
            <button class="btn-reject" @click.stop="handleReject(req.id)">
              拒绝
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApprovalStore, APPROVAL_TYPES, STATUS_LABELS, STATUS_COLORS } from '@/stores/approvalStore'

const props = defineProps({
  autoRefresh: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['processed', 'error'])

const store = useApprovalStore()

const selectedId = ref(null)
const comment = ref('')
const loading = ref(false)

const requests = computed(() => store.pendingRequests)
const error = computed(() => store.pendingError)

function getTypeLabel(type) {
  return APPROVAL_TYPES[type] || type
}

function getStatusLabel(status) {
  return STATUS_LABELS[status] || status
}

function getStatusColor(status) {
  return STATUS_COLORS[status] || '#6b7280'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

async function refresh() {
  loading.value = true
  await store.fetchPendingRequests()
  loading.value = false
}

function selectRequest(req) {
  selectedId.value = selectedId.value === req.id ? null : req.id
  comment.value = ''
}

async function handleApprove(requestId) {
  try {
    await store.decideRequest(requestId, 'approved', comment.value)
    selectedId.value = null
    comment.value = ''
    emit('processed', { action: 'approved', requestId })
  } catch (e) {
    emit('error', e.message)
  }
}

async function handleReject(requestId) {
  try {
    await store.decideRequest(requestId, 'rejected', comment.value)
    selectedId.value = null
    comment.value = ''
    emit('processed', { action: 'rejected', requestId })
  } catch (e) {
    emit('error', e.message)
  }
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
.pending-approvals {
  padding: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header h3 {
  margin: 0;
  font-size: 18px;
}

.btn-refresh {
  padding: 6px 12px;
  background: #374151;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 4px;
  margin-bottom: 16px;
}

.empty-state {
  padding: 32px;
  text-align: center;
  color: #6b7280;
}

.request-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.request-card {
  border: 1px solid #374151;
  border-radius: 8px;
  padding: 12px;
  background: #1f2937;
  cursor: pointer;
  transition: all 0.2s;
}

.request-card:hover {
  border-color: #4b5563;
}

.request-card.selected {
  border-color: #3b82f6;
}

.request-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.approval-type {
  font-weight: 600;
  color: #f9fafb;
}

.status-badge {
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  color: white;
}

.request-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-row {
  display: flex;
  gap: 8px;
  font-size: 14px;
}

.info-row .label {
  color: #9ca3af;
  min-width: 70px;
}

.info-row .value {
  color: #e5e7eb;
}

.action-panel {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #374151;
}

.comment-input textarea {
  width: 100%;
  padding: 8px;
  background: #111827;
  border: 1px solid #374151;
  border-radius: 4px;
  color: #e5e7eb;
  resize: vertical;
  margin-bottom: 8px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.btn-approve, .btn-reject {
  flex: 1;
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-approve {
  background: #10b981;
  color: white;
}

.btn-approve:hover {
  background: #059669;
}

.btn-reject {
  background: #ef4444;
  color: white;
}

.btn-reject:hover {
  background: #dc2626;
}
</style>
