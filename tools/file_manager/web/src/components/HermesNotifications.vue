<template>
  <div class="hermes-notifications">
    <!-- Notification Bell -->
    <button class="notification-bell" @click="togglePanel" :class="{ 'has-unread': unreadCount > 0 }">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M10 2C7.79 2 6 3.79 6 6V9.59L4.41 11.18C3.52 12.07 3 13.21 3 14.4V15.5C3 16.33 3.67 17 4.5 17H15.5C16.33 17 17 16.33 17 15.5V14.4C17 13.21 16.48 12.07 15.59 11.18L14 9.59V6C14 3.79 12.21 2 10 2Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M8 17V18C8 18.5523 8.44772 19 9 19H11C11.5523 19 12 18.5523 12 18V17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
    </button>

    <!-- Notification Panel -->
    <Transition name="panel">
      <div v-if="isOpen" class="notification-panel">
        <div class="panel-header">
          <h3>通知</h3>
          <div class="panel-actions">
            <button v-if="notifications.length > 0" class="mark-all-btn" @click="markAllAsRead">
              全部已读
            </button>
            <button class="close-btn" @click="togglePanel">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div class="panel-content">
          <!-- Empty State -->
          <div v-if="notifications.length === 0" class="empty-state">
            <span class="empty-icon">🔔</span>
            <p>暂无通知</p>
          </div>

          <!-- Notification List -->
          <div v-else class="notification-list">
            <div
              v-for="notification in notifications"
              :key="notification.id"
              class="notification-item"
              :class="{ 'is-read': notification.is_read, [`type-${notification.type}`]: true }"
              @click="handleNotificationClick(notification)"
            >
              <div class="notification-icon">
                {{ getNotificationIcon(notification.type) }}
              </div>
              <div class="notification-content">
                <div class="notification-title">{{ notification.title }}</div>
                <div class="notification-message">{{ notification.message }}</div>
                <div class="notification-time">{{ formatTime(notification.created_at) }}</div>
              </div>
              <div v-if="!notification.is_read" class="unread-dot"></div>
            </div>
          </div>
        </div>

        <!-- Hermes Tasks Section -->
        <div v-if="hermesTasks.length > 0" class="hermes-tasks-section">
          <div class="section-header">
            <span class="section-icon">🤖</span>
            <span>Hermes 任务</span>
          </div>
          <div class="task-list">
            <div
              v-for="task in hermesTasks"
              :key="task.id"
              class="task-item"
              :class="`status-${task.status}`"
            >
              <div class="task-info">
                <div class="task-command">{{ task.command }}</div>
                <div class="task-status">{{ getTaskStatusText(task.status) }}</div>
              </div>
              <div class="task-time">{{ formatTime(task.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>

  <!-- Click Outside Handler -->
  <div v-if="isOpen" class="backdrop" @click="togglePanel"></div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// Props
const props = defineProps({
  userId: {
    type: String,
    required: true
  }
})

// State
const isOpen = ref(false)
const notifications = ref([])
const hermesTasks = ref([])
const ws = ref(null)

// Computed
const unreadCount = computed(() => {
  return notifications.value.filter(n => !n.is_read).length
})

// Methods
function togglePanel() {
  isOpen.value = !isOpen.value
  if (isOpen.value && notifications.value.length === 0) {
    loadNotifications()
    loadHermesTasks()
  }
}

async function loadNotifications() {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/v1/notifications?unread_only=false&limit=50', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      notifications.value = data.notifications || []
    }
  } catch (error) {
    console.error('Failed to load notifications:', error)
  }
}

async function loadHermesTasks() {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/v1/hermes/tasks?limit=10', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      hermesTasks.value = data.tasks || []
    }
  } catch (error) {
    console.error('Failed to load Hermes tasks:', error)
  }
}

async function markAsRead(notificationId) {
  try {
    const token = localStorage.getItem('access_token')
    await fetch(`/api/v1/notifications/${notificationId}/read`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    const notification = notifications.value.find(n => n.id === notificationId)
    if (notification) {
      notification.is_read = true
    }
  } catch (error) {
    console.error('Failed to mark as read:', error)
  }
}

async function markAllAsRead() {
  try {
    const token = localStorage.getItem('access_token')
    await fetch('/api/v1/notifications/read-all', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('Failed to mark all as read:', error)
  }
}

function handleNotificationClick(notification) {
  if (!notification.is_read) {
    markAsRead(notification.id)
  }
  if (notification.link) {
    window.location.href = notification.link
  }
}

function getNotificationIcon(type) {
  const iconMap = {
    'quota_warning': '⚠️',
    'task_complete': '✅',
    'approval': '📋',
    'share': '📤',
    'system': 'ℹ️',
    'hermes_task': '🤖'
  }
  return iconMap[type] || 'ℹ️'
}

function getTaskStatusText(status) {
  const statusMap = {
    'pending': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleDateString('zh-CN')
}

// WebSocket for real-time updates
function connectWebSocket() {
  const token = localStorage.getItem('access_token')
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/hermes/${props.userId}?token=${token}`

  ws.value = new WebSocket(wsUrl)

  ws.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.event === 'task_update') {
      // Update Hermes task status
      const taskIndex = hermesTasks.value.findIndex(t => t.id === data.data.task_id)
      if (taskIndex !== -1) {
        hermesTasks.value[taskIndex] = { ...hermesTasks.value[taskIndex], ...data.data }
      } else {
        hermesTasks.value.unshift(data.data)
      }
    } else if (data.event === 'notification') {
      notifications.value.unshift(data.data)
    }
  }

  ws.value.onclose = () => {
    // Reconnect after 5 seconds
    setTimeout(connectWebSocket, 5000)
  }
}

// Lifecycle
onMounted(() => {
  loadNotifications()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
/* ============================================
   Hermes Notifications - Apple Design System
   ============================================ */

.hermes-notifications {
  position: relative;
}

/* Notification Bell */
.notification-bell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-body);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.notification-bell:hover {
  background: var(--color-fill-secondary);
}

.notification-bell.has-unread {
  color: var(--color-primary);
}

.notification-badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  background: var(--color-danger);
  color: white;
  font-size: 10px;
  font-weight: 600;
  line-height: 16px;
  text-align: center;
  border-radius: var(--radius-pill);
}

/* Backdrop */
.backdrop {
  position: fixed;
  inset: 0;
  z-index: var(--z-dropdown);
}

/* Notification Panel */
.notification-panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 360px;
  max-height: 480px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  z-index: calc(var(--z-dropdown) + 1);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-border);
}

.panel-header h3 {
  font: var(--text-body);
  font-weight: 600;
  margin: 0;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.mark-all-btn {
  background: transparent;
  border: none;
  color: var(--color-primary);
  font-size: 12px;
  cursor: pointer;
}

.mark-all-btn:hover {
  text-decoration: underline;
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  color: var(--color-body-secondary);
  cursor: pointer;
  border-radius: var(--radius-sm);
}

.close-btn:hover {
  background: var(--color-fill-secondary);
}

/* Panel Content */
.panel-content {
  max-height: 320px;
  overflow-y: auto;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  color: var(--color-body-secondary);
}

.empty-icon {
  font-size: 32px;
  margin-bottom: var(--spacing-sm);
}

/* Notification List */
.notification-list {
  padding: var(--spacing-sm);
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.notification-item:hover {
  background: var(--color-fill-secondary);
}

.notification-item.is-read {
  opacity: 0.6;
}

.notification-icon {
  flex-shrink: 0;
  font-size: 20px;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-body);
  margin-bottom: 2px;
}

.notification-message {
  font-size: 12px;
  color: var(--color-body-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notification-time {
  font-size: 11px;
  color: var(--color-body-tertiary);
  margin-top: 4px;
}

.unread-dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 50%;
  margin-top: 4px;
}

/* Hermes Tasks Section */
.hermes-tasks-section {
  border-top: 1px solid var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-body);
  background: var(--color-fill-secondary);
}

.section-icon {
  font-size: 16px;
}

.task-list {
  padding: var(--spacing-sm);
}

.task-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--radius-md);
}

.task-item:hover {
  background: var(--color-fill-secondary);
}

.task-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.task-command {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-body);
}

.task-status {
  font-size: 11px;
  color: var(--color-body-secondary);
}

.task-item.status-pending .task-status {
  color: var(--color-warning);
}

.task-item.status-running .task-status {
  color: var(--color-primary);
}

.task-item.status-completed .task-status {
  color: var(--color-success);
}

.task-item.status-failed .task-status {
  color: var(--color-danger);
}

.task-time {
  font-size: 11px;
  color: var(--color-body-tertiary);
}

/* Transition Animations */
.panel-enter-active,
.panel-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.panel-enter-from,
.panel-leave-to {
  transform: translateY(-10px);
  opacity: 0;
}
</style>
