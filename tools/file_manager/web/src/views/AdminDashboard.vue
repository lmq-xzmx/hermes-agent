<template>
  <LifecycleProvider>
  <div class="admin-dashboard">
    <header class="dashboard-header">
      <h1>管理控制台</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn btn-secondary">🔄 刷新</button>
        <select v-model="refreshInterval" @change="setupAutoRefresh">
          <option :value="0">手动刷新</option>
          <option :value="30000">30秒</option>
          <option :value="60000">1分钟</option>
          <option :value="300000">5分钟</option>
        </select>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="dashboard-grid">
      <AdminOverview class="overview-section" />

      <StoragePoolChart :pools="storagePools" class="chart-section" />

      <UserSpaceSankey :data="userSpaces" class="chart-section" />

      <QuotaHeatmap :data="quotaHeatmap" class="chart-section" />

      <OperationTrends :data="operationTrends" class="chart-section" />

      <AlertList :alerts="alerts" class="chart-section" />
    </div>
  </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import AdminOverview from '@/components/admin/AdminOverview.vue'
import StoragePoolChart from '@/components/admin/StoragePoolChart.vue'
import UserSpaceSankey from '@/components/admin/UserSpaceSankey.vue'
import QuotaHeatmap from '@/components/admin/QuotaHeatmap.vue'
import OperationTrends from '@/components/admin/OperationTrends.vue'
import AlertList from '@/components/admin/AlertList.vue'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const store = useAdminStore()
const refreshInterval = ref(60000)
let refreshTimer = null

const loading = computed(() => store.loading)
const storagePools = computed(() => store.storagePools)
const userSpaces = computed(() => store.userSpaces)
const quotaHeatmap = computed(() => store.quotaHeatmap)
const operationTrends = computed(() => store.operationTrends)
const alerts = computed(() => store.alerts)

// WebSocket 通过 store.enableWebSocket() 管理（在 onMounted 中调用）

async function refresh() {
  await store.fetchAll()
}

function setupAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer)
  if (refreshInterval.value > 0) {
    refreshTimer = setInterval(() => store.fetchAll(), refreshInterval.value)
  }
}

onMounted(async () => {
  await store.fetchAll()
  setupAutoRefresh()
  // 启用 WebSocket 实时更新
  const token = localStorage.getItem('hfm_token')
  if (token) {
    store.enableWebSocket(token)
  }
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
  store.disableWebSocket()
})
</script>

<style scoped>
.admin-dashboard {
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

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 16px;
}

.overview-section {
  grid-column: span 12;
}

.chart-section {
  grid-column: span 6;
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
}

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}

select {
  padding: 8px 12px;
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
}
</style>