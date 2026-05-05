/**
 * WebSocket 服务 - Admin Analytics 实时推送
 */
import { ref } from 'vue'

// WebSocket 连接状态
export const wsConnected = ref(false)
export const wsError = ref(null)

let ws = null
let reconnectTimer = null
let reconnectAttempts = 0
const MAX_RECONNECT_ATTEMPTS = 5
const RECONNECT_DELAY = 3000

// 消息处理器
const handlers = new Map()

/**
 * 连接到 Admin Analytics WebSocket
 * @param {string} token - 认证 token
 * @param {Function} onMessage - 消息回调
 */
export function connectAdminAnalytics(token, onMessage) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    return
  }

  const wsUrl = `${getWsBase()}/ws/admin/analytics?token=${token}`

  try {
    ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('[WebSocket] Admin analytics connected')
      wsConnected.value = true
      wsError.value = null
      reconnectAttempts = 0

      // 注册消息处理器
      if (onMessage) {
        handlers.set('analytics', onMessage)
      }

      // 发送 ping 保持连接
      startPing()
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // 处理不同类型的消息
        if (data.type === 'analytics_update') {
          const handler = handlers.get('analytics')
          if (handler) handler(data.data)
        } else if (data.type === 'pong') {
          // 心跳响应
        }
      } catch (e) {
        console.warn('[WebSocket] Failed to parse message:', e)
      }
    }

    ws.onerror = (error) => {
      console.error('[WebSocket] Error:', error)
      wsError.value = '连接错误'
      wsConnected.value = false
    }

    ws.onclose = (event) => {
      console.log('[WebSocket] Disconnected:', event.code, event.reason)
      wsConnected.value = false
      ws = null

      // 自动重连
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        scheduleReconnect(token, onMessage)
      }
    }
  } catch (e) {
    console.error('[WebSocket] Connection failed:', e)
    wsError.value = e.message
  }
}

/**
 * 断开 WebSocket 连接
 */
export function disconnectAdminAnalytics() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (ws) {
    ws.close(1000, 'User disconnect')
    ws = null
  }

  wsConnected.value = false
  handlers.clear()
  reconnectAttempts = 0
}

/**
 * 发送消息到服务器
 */
export function sendWsMessage(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message))
  }
}

// 私有函数

function getWsBase() {
  // TASK-006: 使用构建时注入的 WebSocket 基础 URL
  // __WS_BASE__ 由 vite.config.js 在构建时定义
  return __WS_BASE__
}

let pingTimer = null

function startPing() {
  if (pingTimer) clearInterval(pingTimer)

  pingTimer = setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'ping' }))
    }
  }, 30000) // 每 30 秒 ping 一次
}

function scheduleReconnect(token, onMessage) {
  reconnectAttempts++
  console.log(`[WebSocket] Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttempts})`)

  reconnectTimer = setTimeout(() => {
    connectAdminAnalytics(token, onMessage)
  }, RECONNECT_DELAY)
}
