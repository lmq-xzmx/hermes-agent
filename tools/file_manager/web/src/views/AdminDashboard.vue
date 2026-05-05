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
import { ref, computed, onMounted, onUnmounted, watch, defineAsyncComponent } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

// Lazy load echarts-based components to reduce initial bundle size
const AdminOverview = defineAsyncComponent(() => import('@/components/admin/AdminOverview.vue'))
const StoragePoolChart = defineAsyncComponent(() => import('@/components/admin/StoragePoolChart.vue'))
const UserSpaceSankey = defineAsyncComponent(() => import('@/components/admin/UserSpaceSankey.vue'))
const QuotaHeatmap = defineAsyncComponent(() => import('@/components/admin/QuotaHeatmap.vue'))
const OperationTrends = defineAsyncComponent(() => import('@/components/admin/OperationTrends.vue'))
const AlertList = defineAsyncComponent(() => import('@/components/admin/AlertList.vue'))

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
  background: var(--color-canvas-parchment);
}

/* Dark Header */
.dashboard-header {
  background: var(--color-surface-black);
  color: var(--color-body-on-dark);
  padding: var(--spacing-section);
  padding-bottom: var(--spacing-xxl);
}

.header-content {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dashboard-header h1 {
  font: var(--text-display-md);
  font-weight: 600;
  margin: 0;
}

/* Main Content */
.dashboard-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: var(--space-xl);
}

.overview-section {
  margin-bottom: var(--space-lg);
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}

.alerts-section {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-section);
  color: var(--color-ink-muted-48);
  gap: var(--space-md);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-hairline);
  border-top-color: var(--color-primary);
  border-radius: var(--radius-full);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Select - Apple Design System */
.select-apple {
  background: var(--color-surface-tile-1);
  color: var(--color-body-on-dark);
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  padding: var(--spacing-xs) var(--spacing-sm);
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
    padding: var(--space-lg);
  }

  .header-content {
    flex-direction: column;
    gap: var(--space-md);
    align-items: flex-start;
  }

  .dashboard-content {
    padding: var(--space-md);
  }
}
</style>