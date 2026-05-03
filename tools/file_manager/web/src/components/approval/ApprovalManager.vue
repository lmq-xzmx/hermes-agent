<template>
  <div class="approval-manager">
    <div class="tabs">
      <button
        :class="{ active: activeTab === 'my' }"
        @click="activeTab = 'my'"
      >
        我的申请
        <span v-if="myPendingCount > 0" class="badge">{{ myPendingCount }}</span>
      </button>
      <button
        v-if="isAdmin"
        :class="{ active: activeTab === 'pending' }"
        @click="activeTab = 'pending'"
      >
        待审批
        <span v-if="pendingCount > 0" class="badge">{{ pendingCount }}</span>
      </button>
      <button
        :class="{ active: activeTab === 'new' }"
        @click="activeTab = 'new'"
      >
        新建申请
      </button>
    </div>

    <div class="tab-content">
      <MyApprovals
        v-if="activeTab === 'my'"
        @cancelled="handleCancelled"
        @error="handleError"
      />

      <PendingApprovals
        v-if="activeTab === 'pending' && isAdmin"
        @processed="handleProcessed"
        @error="handleError"
      />

      <ApprovalRequestForm
        v-if="activeTab === 'new'"
        @submitted="handleSubmitted"
        @error="handleError"
      />
    </div>

    <!-- Toast 通知 -->
    <div v-if="toast" class="toast" :class="toast.type">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useApprovalStore } from '@/stores/approvalStore'
import MyApprovals from './MyApprovals.vue'
import PendingApprovals from './PendingApprovals.vue'
import ApprovalRequestForm from './ApprovalRequestForm.vue'

const store = useApprovalStore()

const activeTab = ref('my')
const toast = ref(null)

// 检查是否是管理员（从 localStorage 获取角色信息）
const isAdmin = computed(() => {
  const userStr = localStorage.getItem('user')
  if (!userStr) return false
  try {
    const user = JSON.parse(userStr)
    return user.role_name === 'admin'
  } catch {
    return false
  }
})

const myPendingCount = computed(() => store.myPendingCount)
const pendingCount = computed(() => store.pendingCount)

function handleCancelled({ requestId }) {
  showToast('申请已取消', 'success')
}

function handleProcessed({ action, requestId }) {
  showToast(`申请已${action === 'approved' ? '批准' : '拒绝'}`, 'success')
}

function handleSubmitted() {
  showToast('申请提交成功', 'success')
  activeTab.value = 'my'
}

function handleError(message) {
  showToast(message, 'error')
}

function showToast(message, type = 'info') {
  toast.value = { message, type }
  setTimeout(() => {
    toast.value = null
  }, 3000)
}

onMounted(() => {
  // 初始加载数据
  store.fetchMyRequests()
  if (isAdmin.value) {
    store.fetchPendingRequests()
  }
})
</script>

<style scoped>
.approval-manager {
  min-height: 100%;
  background: #111827;
  color: #f9fafb;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #374151;
  background: #1f2937;
}

.tabs button {
  flex: 1;
  padding: 12px 16px;
  background: transparent;
  border: none;
  color: #9ca3af;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.tabs button:hover {
  color: #e5e7eb;
  background: #374151;
}

.tabs button.active {
  color: #3b82f6;
  border-bottom: 2px solid #3b82f6;
}

.badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  margin-left: 6px;
  background: #ef4444;
  color: white;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
}

.tab-content {
  min-height: 400px;
}

.toast {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  z-index: 1000;
  animation: slideIn 0.3s ease;
}

.toast.success {
  background: #10b981;
  color: white;
}

.toast.error {
  background: #ef4444;
  color: white;
}

.toast.info {
  background: #3b82f6;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
