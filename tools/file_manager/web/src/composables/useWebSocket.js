/**
 * useWebSocket - WebSocket 连接管理 composable
 *
 * 用于连接 /ws/admin/analytics 实时推送
 */

import { ref, onUnmounted, computed } from 'vue'

const TOKEN_KEY = 'hfm_token'

export function useWebSocket(url, options = {}) {
  const {
    token = localStorage.getItem(TOKEN_KEY) || '',
    autoReconnect = true,
    reconnectInterval = 5000,
    onMessage = null,
    onConnect = null,
    onDisconnect = null,
  } = options

  const connected = ref(false)
  const error = ref(null)
  let ws = null
  let reconnectTimer = null

  function connect() {
    if (ws && ws.readyState === WebSocket.OPEN) return

    // 从 localStorage 获取最新 token
    const currentToken = localStorage.getItem(TOKEN_KEY) || token
    const wsUrl = currentToken ? `${url}?token=${encodeURIComponent(currentToken)}` : url

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        connected.value = true
        error.value = null
        onConnect?.()
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          onMessage?.(data)
        } catch (e) {
          console.error('[WebSocket] Parse error:', e)
        }
      }

      ws.onerror = (e) => {
        error.value = e
        console.error('[WebSocket] Error:', e)
      }

      ws.onclose = () => {
        connected.value = false
        onDisconnect?.()

        if (autoReconnect) {
          reconnectTimer = setTimeout(connect, reconnectInterval)
        }
      }
    } catch (e) {
      error.value = e
      console.error('[WebSocket] Connection error:', e)
    }
  }

  function disconnect() {
    autoReconnect = false
    if (reconnectTimer) clearTimeout(reconnectTimer)
    if (ws) ws.close()
  }

  function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  function ping() {
    send({ type: 'ping' })
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    error,
    connect,
    disconnect,
    send,
    ping,
  }
}