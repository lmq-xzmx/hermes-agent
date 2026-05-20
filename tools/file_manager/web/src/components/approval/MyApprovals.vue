<template>
  <div class="my-approvals">
    <div class="header">
      <h3>我的申请</h3>
      <div class="header-actions">
        <select v-model="statusFilter" class="status-filter">
          <option value="">全部</option>
          <option value="pending">待审批</option>
          <option value="approved">已批准</option>
          <option value="rejected">已拒绝</option>
          <option value="cancelled">已取消</option>
        </select>
        <button class="btn-refresh" @click="refresh" :disabled="loading">
          {{ loading ? '加载中...' : '刷新' }}
        </button>
      </div>
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-if="requests.length === 0 && !loading" class="empty-state">
      暂无申请记录
    </div>

    <div v-else class="request-list">
      <div
        v-for="req in requests"
        :key="req.id"
        class="request-card"
      >
        <div class="request-header">
          <span class="approval-type">{{ getTypeLabel(req.type) }}</span>
          <span class="status-badge" :style="{ backgroundColor: getStatusColor(req.status) }">
            {{ getStatusLabel(req.status) }}
          </span>
        </div>

        <div class="request-info">
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
          <div v-if="req.approval_comment" class="info-row">
            <span class="label">审批意见:</span>
            <span class="value">{{ req.approval_comment }}</span>
          </div>
        </div>

        <div class="card-actions" v-if="req.status === 'pending'">
          <button class="btn-cancel" @click="handleCancel(req.id)">
            取消申请
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useApprovalStore, APPROVAL_TYPES, STATUS_LABELS, STATUS_COLORS } from '@/stores/approvalStore'

const emit = defineEmits(['cancelled', 'error'])

const store = useApprovalStore()

const statusFilter = ref('')
const loading = ref(false)

const requests = computed(() => store.myRequests)
const error = computed(() => store.myRequestsError)

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
  await store.fetchMyRequests(statusFilter.value || null)
  loading.value = false
}

async function handleCancel(requestId) {
  if (!confirm('确定要取消这个申请吗？')) return
  try {
    await store.cancelRequest(requestId)
    emit('cancelled', { requestId })
  } catch (e) {
    emit('error', e.message)
  }
}

// 监听筛选条件变化
watch(statusFilter, () => {
  refresh()
})

onMounted(() => {
  refresh()
})
</script>

