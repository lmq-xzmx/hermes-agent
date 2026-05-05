<template>
  <div class="ws-status" :class="statusClass" @mouseenter="showTooltip = true" @mouseleave="showTooltip = false">
    <span class="status-dot" :class="statusClass"></span>
    <span class="status-text">{{ statusText }}</span>

    <Transition name="tooltip">
      <div v-if="showTooltip && status !== 'connected'" class="status-tooltip">
        <div class="tooltip-row">
          <span class="tooltip-label">最后消息:</span>
          <span class="tooltip-value">{{ lastMessageTime || '-' }}</span>
        </div>
        <div class="tooltip-row">
          <span class="tooltip-label">消息计数:</span>
          <span class="tooltip-value">{{ messageCount }}</span>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  status: {
    type: String,
    default: 'disconnected' // connecting | connected | disconnected | reconnecting
  },
  lastMessageTime: {
    type: String,
    default: ''
  },
  messageCount: {
    type: Number,
    default: 0
  }
})

const showTooltip = ref(false)

const statusClass = computed(() => props.status)

const statusText = computed(() => {
  const map = {
    connecting: '连接中...',
    connected: '已连接',
    disconnected: '未连接',
    reconnecting: '重连中...'
  }
  return map[props.status] || '未知'
})
</script>

<style scoped>
.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  background: var(--color-surface-tile-1);
  cursor: default;
  position: relative;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.connecting {
  background: var(--color-warning);
  animation: pulse 1.5s infinite;
}

.status-dot.connected {
  background: var(--color-success);
}

.status-dot.disconnected {
  background: var(--color-danger);
}

.status-dot.reconnecting {
  background: var(--color-primary);
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-text {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-body-muted);
  letter-spacing: -0.12px;
}

.status-tooltip {
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-sm);
  padding: var(--space-sm);
  min-width: 140px;
  z-index: 100;
}

.tooltip-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  font-family: var(--font-body);
  font-size: 12px;
  padding: 2px 0;
}

.tooltip-label {
  color: var(--color-body-muted);
}

.tooltip-value {
  color: var(--color-body-on-dark);
}

/* Tooltip transition */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: all 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}
</style>