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

