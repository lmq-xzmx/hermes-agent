<template>
  <LifecycleProvider>
  <div class="admin-dashboard">
    <!-- Dark Tile Header -->
    <header class="dashboard-header tile-dark">
      <div class="header-content">
        <h1>管理控制台</h1>
        <div class="header-actions">
          <button @click="refresh" class="btn-dark-utility">🔄 刷新</button>
          <select v-model="refreshInterval" @change="setupAutoRefresh" class="select-apple">
            <option :value="0">手动刷新</option>
            <option :value="30000">30秒</option>
            <option :value="60000">1分钟</option>
            <option :value="300000">5分钟</option>
          </select>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <div v-if="loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else class="dashboard-content">
      <!-- Overview Cards - Light Tile -->
      <div class="overview-section">
        <AdminOverview />
      </div>

      <!-- Charts Grid -->
      <div class="charts-grid">
        <StoragePoolChart :pools="storagePools" class="card-utility" />
        <UserSpaceSankey :data="userSpaces" class="card-utility" />
        <QuotaHeatmap :data="quotaHeatmap" class="card-utility" />
        <OperationTrends :data="operationTrends" class="card-utility" />
      </div>

      <!-- Alert List - Dark Tile -->
      <div class="alerts-section tile-dark">
        <AlertList :alerts="alerts" />
      </div>
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
  min-height: 100vh;
  background: var(--color-canvas-parchment, #f5f5f7);
}

/* Dark Header */
.dashboard-header {
  background: var(--color-surface-black, #000000);
  color: var(--color-body-on-dark, #ffffff);
  padding: var(--space-section, 80px);
  padding-bottom: 48px;
}

.header-content {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font: var(--text-display-md, 34px/1.47 -0.374px);
  font-weight: 600;
  margin: 0;
}

/* Main Content */
.dashboard-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-xl, 32px);
}

.overview-section {
  margin-bottom: var(--space-lg, 24px);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg, 24px);
  margin-bottom: var(--space-lg, 24px);
}

.alerts-section {
  border-radius: var(--rounded-lg, 18px);
  overflow: hidden;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px;
  color: var(--color-ink-muted-48, #7a7a7a);
  gap: var(--space-md, 17px);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-hairline, #e0e0e0);
  border-top-color: var(--color-primary, #0066cc);
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Select */
.select-apple {
  background: var(--color-surface-tile-1, #272729);
  color: var(--color-body-on-dark, #ffffff);
  font: var(--text-body, 17px/1.47 -0.374px);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--radius-md, 18px);
  padding: 8px 12px;
  cursor: pointer;
}

/* Responsive */
@media (max-width: 1068px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 734px) {
  .dashboard-header {
    padding: var(--space-lg, 24px);
  }

  .header-content {
    flex-direction: column;
    gap: var(--space-md, 17px);
    align-items: flex-start;
  }

  .dashboard-content {
    padding: var(--space-md, 17px);
  }
}
</style>