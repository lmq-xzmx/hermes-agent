<template>
  <LifecycleProvider>
  <div class="admin-dashboard">
    <!-- Dark Tile Header -->
    <header class="admin-dashboard__header tile-dark">
      <div class="admin-dashboard__header-content">
        <h1 class="admin-dashboard__header-title">管理控制台</h1>
        <div class="admin-dashboard__header-actions">
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
    <div v-if="loading" class="admin-dashboard__loading">
      <div class="admin-dashboard__spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else class="admin-dashboard__content">
      <!-- Overview Cards - Light Tile -->
      <div class="admin-dashboard__overview">
        <AdminOverview />
      </div>

      <!-- Charts Grid -->
      <div class="admin-dashboard__charts">
        <StoragePoolChart :pools="storagePools" class="admin-dashboard__chart" />
        <UserSpaceSankey :data="userSpaces" class="admin-dashboard__chart" />
        <QuotaHeatmap :data="quotaHeatmap" class="admin-dashboard__chart" />
        <OperationTrends :data="operationTrends" class="admin-dashboard__chart" />
      </div>

      <!-- Alert List - Dark Tile -->
      <div class="admin-dashboard__alerts">
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
/* === Admin Dashboard Styles === */

/* --- Dashboard Header --- */
.admin-dashboard__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  background: var(--color-surface-tile-1);
  border-radius: var(--radius-lg);
  margin-bottom: var(--spacing-lg);
}

.admin-dashboard__header-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.admin-dashboard__header-title {
  font: var(--text-display-md);
  color: var(--color-body-on-dark);
  margin: 0;
}

.admin-dashboard__header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

/* --- Loading State --- */
.admin-dashboard__loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  gap: var(--spacing-md);
  font: var(--text-body);
  color: var(--color-body-muted);
}

.admin-dashboard__spinner {
  width: var(--spacing-lg);
  height: var(--spacing-lg);
  border: 2px solid var(--color-border-on-dark-soft);
  border-top-color: var(--color-primary);
  border-radius: var(--radius-full);
  animation: admin-dashboard__spin 0.8s linear infinite;
}

@keyframes admin-dashboard__spin {
  to { transform: rotate(360deg); }
}

/* --- Dashboard Content --- */
.admin-dashboard__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* --- Overview Section --- */
.admin-dashboard__overview {
  /* AdminOverview component container */
}

/* --- Charts Grid --- */
.admin-dashboard__charts {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-lg);
}

.admin-dashboard__chart {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

/* ECharts dark theme adaptation */
.admin-dashboard__chart :deep(.echarts) {
  background: transparent !important;
}

.admin-dashboard__chart :deep(text) {
  fill: var(--color-body-muted) !important;
}

/* --- Alerts Section --- */
.admin-dashboard__alerts {
  background: var(--color-surface-tile-1);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

/* Alert items use Action Blue highlight */
.admin-dashboard__alerts :deep(.alert-item) {
  border-left: 3px solid var(--color-primary);
  background: var(--color-surface-tile-2);
}
</style>

