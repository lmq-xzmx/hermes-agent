<template>
  <div class="admin-overview">
    <!-- Loading State -->
    <div v-if="store.loading" class="loading-state">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="error-state">
      <span class="error-message">{{ store.error }}</span>
      <button class="btn-primary" @click="retry">重试</button>
    </div>

    <!-- Data Cards - Apple Store Utility Style -->
    <div v-else class="overview-grid">
      <!-- 总用户 -->
      <div class="stat-card tile-light" @click="navigateTo('/admin/users')">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_users || 0 }}</span>
          <span class="stat-label">总用户</span>
          <span class="stat-sub" v-if="overview?.active_users_7d">
            {{ overview.active_users_7d }} 活跃(7天)
          </span>
        </div>
      </div>

      <!-- 总团队/空间 -->
      <div class="stat-card tile-light">
        <div class="stat-icon">📁</div>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_spaces || 0 }}</span>
          <span class="stat-label">总空间</span>
          <span class="stat-sub" v-if="overview?.total_teams">
            {{ overview.total_teams }} 团队
          </span>
        </div>
      </div>

      <!-- 存储使用 -->
      <div class="stat-card tile-light" @click="navigateTo('/admin/storage')">
        <div class="stat-icon">💾</div>
        <div class="stat-content">
          <span class="stat-value">{{ formatBytes(overview?.storage?.used_bytes) }}</span>
          <span class="stat-label">已用存储</span>
          <span class="stat-sub" v-if="overview?.storage">
            {{ formatBytes(overview.storage.total_bytes) }} 总计
          </span>
        </div>
        <div v-if="overview?.storage" class="storage-bar">
          <div
            class="storage-bar-fill"
            :style="{ width: (overview.storage.usage_rate * 100) + '%' }"
            :class="{ warning: overview.storage.usage_rate > 0.7, critical: overview.storage.usage_rate > 0.9 }"
          ></div>
        </div>
      </div>

      <!-- 活跃告警 -->
      <div class="stat-card tile-light" :class="{ 'alert-card': criticalAlerts.length > 0 }" @click="navigateTo('/admin/alerts')">
        <div class="stat-icon">⚠️</div>
        <div class="stat-content">
          <span class="stat-value">{{ alerts.length }}</span>
          <span class="stat-label">活跃告警</span>
          <span class="stat-sub critical" v-if="criticalAlerts.length">
            {{ criticalAlerts.length }} 紧急
          </span>
          <span class="stat-sub" v-else>
            {{ warningAlerts.length }} 警告
          </span>
        </div>
      </div>

      <!-- 新增用户趋势 -->
      <div class="stat-card tile-light">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <span class="stat-value">+{{ overview?.new_users_7d || 0 }}</span>
          <span class="stat-label">本周新增</span>
        </div>
      </div>

      <!-- 存储池数 -->
      <div class="stat-card tile-light">
        <div class="stat-icon">🗄️</div>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_pools || 0 }}</span>
          <span class="stat-label">存储池</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAdminStore } from '@/stores/adminStore'

const store = useAdminStore()
const overview = computed(() => store.overview)
const alerts = computed(() => store.alerts)
const criticalAlerts = computed(() => store.criticalAlerts)
const warningAlerts = computed(() => store.warningAlerts)

function formatBytes(bytes) {
  if (!bytes && bytes !== 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function navigateTo(path) {
  window.location.hash = path
}

function retry() {
  store.fetchOverview()
}
</script>

<style scoped>
.admin-overview {
  position: relative;
}

/* Loading & Error States */
.loading-state,
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  gap: var(--space-md, 17px);
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-hairline, #e0e0e0);
  border-top-color: var(--color-primary, #0066cc);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: var(--color-ink-muted-48, #7a7a7a);
  font: var(--text-body, 17px/1.47 -0.374px);
}

/* Grid Layout - 6 columns on desktop */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: var(--space-md, 17px);
}

/* Stat Card - Apple Store Utility Card */
.stat-card {
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  padding: var(--space-lg, 24px);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 12px);
  position: relative;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.stat-card:hover {
  transform: scale(1.02);
}

.stat-card:active {
  transform: scale(0.98);
}

.alert-card {
  border-color: var(--color-primary, #0066cc);
  background: var(--color-primary-faint);
}

.stat-icon {
  font-size: 28px;
  line-height: 1;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-value {
  font: var(--text-display-md, 34px/1.47 -0.374px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  line-height: 1.1;
  letter-spacing: -0.374px;
}

.stat-label {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.stat-sub {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-top: 2px;
}

.stat-sub.critical {
  color: var(--color-primary, #0066cc);
  font-weight: 600;
}

/* Storage Bar */
.storage-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color-hairline, #e0e0e0);
  border-radius: 0 0 var(--rounded-lg, 18px) var(--rounded-lg, 18px);
  overflow: hidden;
}

.storage-bar-fill {
  height: 100%;
  background: var(--color-primary, #0066cc);
  transition: width 0.3s ease;
}

.storage-bar-fill.warning {
  background: #d29922;
}

.storage-bar-fill.critical {
  background: #f85149;
}

/* Responsive */
@media (max-width: 1440px) {
  .overview-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 1068px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 734px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    padding: var(--space-md, 17px);
  }

  .stat-value {
    font-size: 28px;
  }
}
</style>