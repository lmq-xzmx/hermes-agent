<template>
  <div class="alert-list">
    <div class="list-header">
      <h3>告警列表</h3>
      <span class="alert-count">{{ alerts.length }} 条告警</span>
    </div>
    <div class="alert-items">
      <div v-for="alert in alerts" :key="alert.id" :class="['alert-item', alert.level]">
        <div class="alert-icon">
          {{ alert.level === 'critical' ? '🔴' : alert.level === 'warning' ? '🟡' : '🟢' }}
        </div>
        <div class="alert-content">
          <div class="alert-title">{{ alert.message }}</div>
          <div class="alert-meta">
            <span>{{ alert.resource_name }}</span>
            <span>{{ formatTime(alert.created_at) }}</span>
          </div>
        </div>
        <button class="btn-apple-primary btn-sm" @click="handleAlert(alert)">处理</button>
      </div>
      <div v-if="alerts.length === 0" class="no-alerts">
        暂无告警
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  alerts: { type: Array, default: () => [] }
})

function formatTime(isoString) {
  if (!isoString) return ''
  const d = new Date(isoString)
  return d.toLocaleString('zh-CN')
}

function handleAlert(alert) {
  console.log('Handle alert:', alert)
}
</script>

<style scoped>
.alert-list {
  padding: var(--space-lg);
  color: var(--color-body-on-dark);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.list-header h3 {
  font: var(--text-body-strong);
  font-weight: 600;
  margin: 0;
  color: var(--color-body-on-dark);
}

.alert-count {
  font: var(--text-caption);
  color: var(--color-body-muted);
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.alert-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-surface-tile-2);
  border-radius: var(--rounded-md);
  border-left: 4px solid;
  transition: transform 0.1s ease;
}

.alert-item:active {
  transform: scale(0.98);
}

.alert-item.critical { border-left-color: var(--color-danger); }
.alert-item.warning { border-left-color: var(--color-warning); }
.alert-item.normal { border-left-color: var(--color-success); }

.alert-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font: var(--text-body);
  color: var(--color-body-on-dark);
  margin-bottom: 4px;
}

.alert-meta {
  display: flex;
  gap: var(--space-lg);
  font: var(--text-caption);
  color: var(--color-body-muted);
}

.no-alerts {
  text-align: center;
  padding: var(--space-xl);
  font: var(--text-body);
  color: var(--color-body-muted);
}
</style>