<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="debug-panel"
      :class="{ 'debug-panel--minimized': minimized }"
    >
      <!-- Header -->
      <header class="debug-panel__header" @click="toggleMinimize">
        <h2 class="debug-panel__title">调试面板</h2>
        <div class="debug-panel__controls">
          <button
            class="debug-panel__btn"
            type="button"
            title="清除日志"
            @click.stop="clearLogs"
          >
            <Icon name="trash" :size="14" class="debug-panel__btn-icon" />
          </button>
          <button
            class="debug-panel__btn"
            type="button"
            :title="minimized ? '展开' : '最小化'"
            @click.stop="toggleMinimize"
          >
            <Icon :name="minimized ? 'plus' : 'minus'" :size="14" class="debug-panel__btn-icon" />
          </button>
          <button
            class="debug-panel__btn debug-panel__btn--close"
            type="button"
            title="关闭"
            @click.stop="close"
          >
            <Icon name="close" :size="14" class="debug-panel__btn-icon" />
          </button>
        </div>
      </header>

      <!-- Content -->
      <div v-if="!minimized" class="debug-panel__content">
        <!-- System Info Section -->
        <section class="debug-panel__section">
          <h3 class="debug-panel__section-header">系统信息</h3>
          <dl class="debug-panel__list">
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">版本</dt>
              <dd class="debug-panel__value">{{ systemInfo.version }}</dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">构建</dt>
              <dd class="debug-panel__value">{{ systemInfo.buildType }}</dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">模式</dt>
              <dd class="debug-panel__value">{{ systemInfo.mode }}</dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">时间</dt>
              <dd class="debug-panel__value">{{ systemInfo.buildTime }}</dd>
            </div>
          </dl>
        </section>

        <!-- Auth Status Section -->
        <section class="debug-panel__section">
          <h3 class="debug-panel__section-header">认证状态</h3>
          <dl class="debug-panel__list">
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">Token</dt>
              <dd
                class="debug-panel__value debug-panel__value--status"
                :class="authInfo.hasToken ? 'debug-panel__value--success' : 'debug-panel__value--error'"
              >
                {{ authInfo.hasToken ? '✓ 存在' : '✗ 不存在' }}
              </dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">用户</dt>
              <dd class="debug-panel__value">{{ authInfo.username || '-' }}</dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">角色</dt>
              <dd class="debug-panel__value">{{ authInfo.role || '-' }}</dd>
            </div>
          </dl>
        </section>

        <!-- API Status Section -->
        <section class="debug-panel__section">
          <h3 class="debug-panel__section-header">API 状态</h3>
          <dl class="debug-panel__list">
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">后端</dt>
              <dd
                class="debug-panel__value debug-panel__value--status"
                :class="apiStatus.backend ? 'debug-panel__value--success' : 'debug-panel__value--error'"
              >
                {{ apiStatus.backend ? '✓ 在线' : '✗ 离线' }}
              </dd>
            </div>
            <div class="debug-panel__list-item">
              <dt class="debug-panel__label">WS</dt>
              <dd
                class="debug-panel__value debug-panel__value--status"
                :class="apiStatus.ws ? 'debug-panel__value--success' : 'debug-panel__value--error'"
              >
                {{ apiStatus.ws ? '✓ 已连接' : '✗ 未连接' }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- Logs Section -->
        <section class="debug-panel__section debug-panel__section--logs">
          <h3 class="debug-panel__section-header">
            日志
            <span class="debug-panel__badge">{{ logs.length }}</span>
          </h3>
          <div class="debug-panel__logs">
            <div
              v-for="(log, i) in logs"
              :key="i"
              class="debug-panel__log"
              :class="{ 'debug-panel__log--error': log.isError }"
            >
              <time class="debug-panel__log-time">{{ log.time }}</time>
              <span class="debug-panel__log-msg">{{ log.msg }}</span>
            </div>
            <div v-if="logs.length === 0" class="debug-panel__empty">
              暂无日志
            </div>
          </div>
        </section>
      </div>

      <!-- Footer -->
      <footer class="debug-panel__footer">
        <span class="debug-panel__version">v{{ systemInfo.version }} · {{ systemInfo.mode }}</span>
      </footer>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { Icon } from '@/components/common'
import { useAuthStore } from '@/stores/authStore'

// ============================================
// Emits
// ============================================
const emit = defineEmits(['close'])

// ============================================
// State
// ============================================
const visible = ref(false)
const minimized = ref(false)
const logs = ref([])

const systemInfo = reactive({
  version: '1.0.0',
  buildType: 'Release',
  mode: 'web',
  buildTime: '-'
})

const authInfo = reactive({
  hasToken: false,
  username: '-',
  role: '-'
})

const apiStatus = reactive({
  backend: false,
  ws: false
})

// ============================================
// Methods
// ============================================
function toggleMinimize() {
  minimized.value = !minimized.value
}

function close() {
  visible.value = false
  emit('close')
}

function clearLogs() {
  logs.value = []
}

function show() {
  visible.value = true
  updateInfo()
}

function updateInfo() {
  // System info
  systemInfo.version = window.__VERSION__ || '1.0.0'
  systemInfo.buildType = window.__BUILD_TYPE__ || 'Debug'
  systemInfo.mode = window.__TAURI_MODE__ || 'web'
  systemInfo.buildTime = window.__BUILD_TIME__ || new Date().toLocaleString()

  // Auth info (use authStore for consistent role info)
  const authStore = useAuthStore()
  const token = localStorage.getItem('hfm_token')
  authInfo.hasToken = !!token
  authInfo.username = authStore.user?.username || localStorage.getItem('hfm_username') || '-'
  authInfo.role = authStore.userRole

  // Check backend
  checkBackend()
}

async function checkBackend() {
  try {
    const res = await fetch('/api/v1/health', {
      method: 'GET',
      signal: AbortSignal.timeout(3000)
    })
    apiStatus.backend = res.ok
  } catch {
    apiStatus.backend = false
  }
}

function addLog(msg, isError = false) {
  const time = new Date().toLocaleTimeString()
  logs.value.push({ msg, isError, time })

  // Keep only last 50 logs
  if (logs.value.length > 50) {
    logs.value = logs.value.slice(-50)
  }
}

function handleKeydown(e) {
  // Ctrl+Shift+D to toggle debug panel
  if (e.ctrlKey && e.shiftKey && e.key === 'D') {
    e.preventDefault()
    visible.value = !visible.value
    if (visible.value) updateInfo()
  }
  // Escape to close
  if (e.key === 'Escape' && visible.value) {
    close()
  }
}

// ============================================
// Lifecycle
// ============================================
onMounted(() => {
  document.addEventListener('keydown', handleKeydown)

  // Listen for custom debug events
  window.addEventListener('debug:log', (e) => {
    addLog(e.detail?.msg || String(e.detail), e.detail?.isError)
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// ============================================
// Expose
// ============================================
defineExpose({
  show,
  close,
  addLog,
  updateInfo
})
</script>

