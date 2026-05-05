<template>
  <Teleport to="body">
    <div v-if="visible" class="debug-panel" :class="{ minimized }">
      <div class="debug-header" @click="toggleMinimize">
        <span class="debug-title">调试面板</span>
        <div class="debug-controls">
          <button class="debug-btn" @click.stop="clearLogs" title="清除日志">🗑️</button>
          <button class="debug-btn" @click.stop="toggleMinimize" title="最小化">
            {{ minimized ? '➕' : '➖' }}
          </button>
          <button class="debug-btn" @click.stop="close" title="关闭">✕</button>
        </div>
      </div>

      <div v-if="!minimized" class="debug-content">
        <div class="debug-section">
          <div class="debug-section-header">系统信息</div>
          <div class="debug-row">
            <span class="debug-label">版本:</span>
            <span class="debug-value">{{ systemInfo.version }}</span>
          </div>
          <div class="debug-row">
            <span class="debug-label">构建:</span>
            <span class="debug-value">{{ systemInfo.buildType }}</span>
          </div>
          <div class="debug-row">
            <span class="debug-label">模式:</span>
            <span class="debug-value">{{ systemInfo.mode }}</span>
          </div>
          <div class="debug-row">
            <span class="debug-label">时间:</span>
            <span class="debug-value">{{ systemInfo.buildTime }}</span>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-header">认证状态</div>
          <div class="debug-row">
            <span class="debug-label">Token:</span>
            <span class="debug-value" :class="authInfo.hasToken ? 'success' : 'error'">
              {{ authInfo.hasToken ? '✓ 存在' : '✗ 不存在' }}
            </span>
          </div>
          <div class="debug-row">
            <span class="debug-label">用户:</span>
            <span class="debug-value">{{ authInfo.username || '-' }}</span>
          </div>
          <div class="debug-row">
            <span class="debug-label">角色:</span>
            <span class="debug-value">{{ authInfo.role || '-' }}</span>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-header">API 状态</div>
          <div class="debug-row">
            <span class="debug-label">后端:</span>
            <span class="debug-value" :class="apiStatus.backend ? 'success' : 'error'">
              {{ apiStatus.backend ? '✓ 在线' : '✗ 离线' }}
            </span>
          </div>
          <div class="debug-row">
            <span class="debug-label">WS:</span>
            <span class="debug-value" :class="apiStatus.ws ? 'success' : 'error'">
              {{ apiStatus.ws ? '✓ 已连接' : '✗ 未连接' }}
            </span>
          </div>
        </div>

        <div class="debug-section">
          <div class="debug-section-header">日志 ({{ logs.length }})</div>
          <div class="debug-logs">
            <div
              v-for="(log, i) in logs"
              :key="i"
              class="debug-log"
              :class="{ error: log.isError }"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-msg">{{ log.msg }}</span>
            </div>
            <div v-if="logs.length === 0" class="debug-empty">
              暂无日志
            </div>
          </div>
        </div>
      </div>

      <div class="debug-footer">
        <span class="debug-version">v{{ systemInfo.version }} · {{ systemInfo.mode }}</span>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['close'])

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

function toggleMinimize() {
  minimized.value = !minimized.value
}

function close() {
  visible.value = false
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

  // Auth info
  const token = localStorage.getItem('hfm_token')
  authInfo.hasToken = !!token
  authInfo.username = localStorage.getItem('hfm_username') || '-'
  authInfo.role = localStorage.getItem('hfm_role') || '-'

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

defineExpose({
  show,
  close,
  addLog,
  updateInfo
})
</script>

.debug-panel {
  position: fixed;
  bottom: var(--space-lg);
  right: var(--space-lg);
  width: 360px;
  max-height: 60vh;
  background: var(--color-surface-tile-1);
  border: 1px solid var(--color-border-on-dark-soft);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  z-index: 9999;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.debug-panel.minimized {
  max-height: none;
}

.debug-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-surface-tile-2);
  border-bottom: 1px solid var(--color-border-on-dark-soft);
  cursor: pointer;
  height: 36px;
}

.debug-title {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: -0.224px;
  color: var(--color-body-on-dark);
}

.debug-controls {
  display: flex;
  gap: var(--space-xxs);
}

.debug-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 12px;
  padding: 4px 6px;
  border-radius: var(--radius-xs);
  opacity: 0.7;
  color: var(--color-body-muted);
}

.debug-btn:hover {
  opacity: 1;
  background: var(--color-surface-tile-3);
}

.debug-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-sm);
  background: var(--color-surface-tile-1);
}

.debug-section {
  margin-bottom: var(--space-md);
}

.debug-section:last-child {
  margin-bottom: 0;
}

.debug-section-header {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: -0.224px;
  color: var(--color-body-muted);
  margin-bottom: var(--space-xs);
  padding-bottom: var(--space-xxs);
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.debug-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-xxs) 0;
  font-family: var(--font-body);
  font-size: 13px;
}

.debug-label {
  color: var(--color-body-muted);
}

.debug-value {
  color: var(--color-body-on-dark);
}

.debug-value.success {
  color: var(--color-success);
}

.debug-value.error {
  color: var(--color-danger);
}

.debug-logs {
  max-height: 200px;
  overflow-y: auto;
  font-family: 'SF Mono', 'Monaco', monospace;
  font-size: 12px;
  scrollbar-width: thin;
  scrollbar-color: var(--color-surface-tile-3) transparent;
}

.debug-logs::-webkit-scrollbar {
  width: 6px;
}

.debug-logs::-webkit-scrollbar-track {
  background: transparent;
}

.debug-logs::-webkit-scrollbar-thumb {
  background: var(--color-surface-tile-3);
  border-radius: 3px;
}

.debug-log {
  padding: var(--space-xxs) 0;
  border-bottom: 1px solid var(--color-border-on-dark-subtle);
  display: flex;
  gap: var(--space-xs);
}

.debug-log.error {
  color: var(--color-danger);
}

.log-time {
  color: var(--color-body-muted);
  flex-shrink: 0;
  font-size: 11px;
}

.log-msg {
  word-break: break-all;
  color: var(--color-body-on-dark);
}

.debug-empty {
  color: var(--color-body-muted);
  font-family: var(--font-body);
  font-size: 12px;
  text-align: center;
  padding: var(--space-md);
}

.debug-footer {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-3);
  border-top: 1px solid var(--color-border-on-dark-soft);
}

.debug-version {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-body-muted);
  letter-spacing: -0.08px;
}
</style>
