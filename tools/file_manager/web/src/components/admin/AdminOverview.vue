<template>
  <div class="admin-overview">
    <!-- Loading State -->
    <div v-if="store.loading" class="loading-overlay">
      <div class="loading-spinner"></div>
      <span>加载中...</span>
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="error-overlay">
      <span class="error-icon">❌</span>
      <span class="error-message">{{ store.error }}</span>
      <button class="retry-btn" @click="retry">重试</button>
    </div>

    <!-- Data Cards -->
    <div v-else class="overview-cards">
      <!-- 总用户 -->
      <div class="stat-card clickable" @click="navigateTo('/admin/users')">
        <span class="stat-icon">👥</span>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_users || 0 }}</span>
          <span class="stat-label">总用户</span>
          <span class="stat-sub" v-if="overview?.active_users_7d">
            {{ overview.active_users_7d }} 活跃(7天)
          </span>
        </div>
      </div>

      <!-- 总团队/空间 -->
      <div class="stat-card">
        <span class="stat-icon">📁</span>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_spaces || 0 }}</span>
          <span class="stat-label">总空间</span>
          <span class="stat-sub" v-if="overview?.total_teams">
            {{ overview.total_teams }} 团队
          </span>
        </div>
      </div>

      <!-- 存储使用 -->
      <div class="stat-card clickable" @click="navigateTo('/admin/storage')">
        <span class="stat-icon">💾</span>
        <div class="stat-content">
          <span class="stat-value">{{ formatBytes(overview?.storage?.used_bytes) }}</span>
          <span class="stat-label">已用存储</span>
          <span class="stat-sub" v-if="overview?.storage">
            {{ formatBytes(overview.storage.total_bytes) }} 总计
          </span>
        </div>
        <!-- 存储使用率进度条 -->
        <div v-if="overview?.storage" class="storage-bar">
          <div
            class="storage-bar-fill"
            :style="{ width: (overview.storage.usage_rate * 100) + '%' }"
            :class="{ warning: overview.storage.usage_rate > 0.7, critical: overview.storage.usage_rate > 0.9 }"
          ></div>
        </div>
      </div>

      <!-- 活跃告警 -->
      <div class="stat-card clickable" :class="{ 'alert': criticalAlerts.length > 0 }" @click="navigateTo('/admin/alerts')">
        <span class="stat-icon">⚠️</span>
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
      <div class="stat-card">
        <span class="stat-icon">📈</span>
        <div class="stat-content">
          <span class="stat-value">+{{ overview?.new_users_7d || 0 }}</span>
          <span class="stat-label">本周新增</span>
        </div>
      </div>

      <!-- 存储池数 -->
      <div class="stat-card">
        <span class="stat-icon">🗄️</span>
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
  margin-bottom: 16px;
  position: relative;
}

.loading-overlay,
.error-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  gap: 12px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border, #30363d);
  border-top-color: var(--accent-primary, #238636);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-message {
  color: var(--text-secondary, #8b949e);
}

.retry-btn {
  padding: 8px 16px;
  background: var(--accent-primary, #238636);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  transition: all 0.2s;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  background: var(--bg-tertiary, #21262d);
  transform: translateY(-2px);
}

.stat-card.alert {
  border: 1px solid #f85149;
  background: rgba(248, 81, 73, 0.1);
}

.stat-icon {
  font-size: 24px;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  display: block;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  display: block;
}

.stat-sub {
  font-size: 11px;
  color: var(--text-secondary, #8b949e);
  display: block;
  margin-top: 2px;
}

.stat-sub.critical {
  color: #f85149;
}

.storage-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--bg-tertiary, #30363d);
  border-radius: 0 0 8px 8px;
  overflow: hidden;
}

.storage-bar-fill {
  height: 100%;
  background: var(--accent-primary, #238636);
  transition: width 0.3s ease;
}

.storage-bar-fill.warning {
  background: #d29922;
}

.storage-bar-fill.critical {
  background: #f85149;
}
</style>