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
import { useAuthStore } from '@/stores/authStore'
import MyApprovals from './MyApprovals.vue'
import PendingApprovals from './PendingApprovals.vue'
import ApprovalRequestForm from './ApprovalRequestForm.vue'

const store = useApprovalStore()
const authStore = useAuthStore()

const activeTab = ref('my')
const toast = ref(null)

// 检查是否是管理员（统一使用 authStore）
const isAdmin = computed(() => authStore.userRole === 'admin')

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

