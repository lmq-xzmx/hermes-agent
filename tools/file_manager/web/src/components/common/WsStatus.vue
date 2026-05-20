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

