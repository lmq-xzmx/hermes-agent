<template>
  <div class="admin-overview">
    <div class="overview-cards">
      <div class="stat-card">
        <span class="stat-icon">👥</span>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_users || 0 }}</span>
          <span class="stat-label">总用户</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">📁</span>
        <div class="stat-content">
          <span class="stat-value">{{ overview?.total_spaces || 0 }}</span>
          <span class="stat-label">总空间</span>
        </div>
      </div>
      <div class="stat-card">
        <span class="stat-icon">💾</span>
        <div class="stat-content">
          <span class="stat-value">{{ formatBytes(overview?.storage?.used_bytes) }}</span>
          <span class="stat-label">已用存储</span>
        </div>
      </div>
      <div class="stat-card" :class="{ 'alert': criticalAlerts.length > 0 }">
        <span class="stat-icon">⚠️</span>
        <div class="stat-content">
          <span class="stat-value">{{ alerts.length }}</span>
          <span class="stat-label">活跃告警</span>
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

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}
</script>

<style scoped>
.admin-overview {
  margin-bottom: 16px;
}

.overview-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-card.alert {
  border: 1px solid #f85149;
  background: rgba(248, 81, 73, 0.1);
}

.stat-icon {
  font-size: 24px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  display: block;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
}
</style>