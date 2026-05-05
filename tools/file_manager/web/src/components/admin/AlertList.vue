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
        <button class="btn-primary" @click="handleAlert(alert)">处理</button>
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
  padding: var(--space-lg, 24px);
  color: var(--color-body-on-dark, #ffffff);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg, 24px);
}

.list-header h3 {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  margin: 0;
  color: var(--color-body-on-dark, #ffffff);
}

.alert-count {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-body-muted, #cccccc);
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm, 12px);
}

.alert-item {
  display: flex;
  align-items: center;
  gap: var(--space-md, 17px);
  padding: var(--space-md, 17px);
  background: var(--color-surface-tile-2, #2a2a2c);
  border-radius: var(--rounded-md, 11px);
  border-left: 4px solid;
  transition: transform 0.1s ease;
}

.alert-item:active {
  transform: scale(0.98);
}

.alert-item.critical { border-left-color: #f85149; }
.alert-item.warning { border-left-color: #d29922; }
.alert-item.normal { border-left-color: #3fb950; }

.alert-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.alert-content {
  flex: 1;
  min-width: 0;
}

.alert-title {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-body-on-dark, #ffffff);
  margin-bottom: 4px;
}

.alert-meta {
  display: flex;
  gap: var(--space-lg, 24px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-body-muted, #cccccc);
}

.btn-primary {
  background: var(--color-primary, #0066cc);
  color: var(--color-on-primary, #ffffff);
  font: var(--text-body, 17px/1.47 -0.374px);
  border-radius: var(--rounded-pill, 9999px);
  padding: 8px 20px;
  border: none;
  cursor: pointer;
  transition: transform 0.1s ease;
  flex-shrink: 0;
}

.btn-primary:active {
  transform: scale(0.95);
}

.no-alerts {
  text-align: center;
  padding: var(--space-xl, 32px);
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-body-muted, #cccccc);
}
</style>