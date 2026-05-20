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
      <button class="btn-apple-primary" @click="retry">重试</button>
    </div>

    <!-- Data Cards - Apple Store Utility Style -->
    <div v-else class="overview-grid">
      <!-- 总用户 -->
      <div class="stat-card tile-light" @click="navigateTo('/admin/users')">
        <div class="stat-icon">
          <Icon name="users" :size="24" colored />
        </div>
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
        <div class="stat-icon">
          <Icon name="folder" :size="24" colored />
        </div>
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
        <div class="stat-icon">
          <Icon name="database" :size="24" colored />
        </div>
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
        <div class="stat-icon">
          <Icon name="warning" :size="24" colored />
        </div>
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
        <div class="stat-icon">
          <Icon name="trending-up" :size="24" colored />
        </div>
        <div class="stat-content">
          <span class="stat-value">+{{ overview?.new_users_7d || 0 }}</span>
          <span class="stat-label">本周新增</span>
        </div>
      </div>

      <!-- 存储池数 -->
      <div class="stat-card tile-light">
        <div class="stat-icon">
          <Icon name="server" :size="24" colored />
        </div>
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
import { Icon } from '@/components/common'

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

