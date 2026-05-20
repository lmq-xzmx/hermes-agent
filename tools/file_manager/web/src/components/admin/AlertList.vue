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

