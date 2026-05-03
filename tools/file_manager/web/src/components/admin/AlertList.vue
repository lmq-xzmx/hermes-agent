<template>
  <div class="alert-list">
    <div class="chart-header">
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
        <button class="alert-action" @click="handleAlert(alert)">处理</button>
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
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  padding: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.alert-count {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
}

.alert-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-primary, #0d1117);
  border-radius: 6px;
  border-left: 3px solid;
}

.alert-item.critical { border-left-color: #f85149; }
.alert-item.warning { border-left-color: #d29922; }
.alert-item.normal { border-left-color: #3fb950; }

.alert-icon { font-size: 16px; }

.alert-content { flex: 1; }

.alert-title {
  font-size: 14px;
  margin-bottom: 4px;
}

.alert-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
}

.alert-action {
  padding: 4px 12px;
  background: transparent;
  color: var(--accent, #58a6ff);
  border: 1px solid var(--accent, #58a6ff);
  border-radius: 4px;
  cursor: pointer;
}

.alert-action:hover {
  background: var(--accent, #58a6ff);
  color: white;
}

.no-alerts {
  text-align: center;
  padding: 20px;
  color: var(--text-secondary, #8b949e);
}
</style>