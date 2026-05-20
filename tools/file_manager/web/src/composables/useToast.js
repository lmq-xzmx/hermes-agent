/**
 * useToast - 全局 Toast 状态管理
 *
 * 提供全局的 toast 显示机制，所有组件通过此 composable 发送 toast 通知
 */

import { ref } from 'vue'

// 全局单例
const toastVisible = ref(false)
const toastConfig = ref({
  type: 'info',
  title: '',
  message: '',
  closable: true,
  duration: 3000
})

let toastTimer = null

/**
 * 显示 toast 通知
 * @param {Object} options - toast 配置
 * @param {string} options.type - 类型: info/success/error/warning
 * @param {string} options.title - 标题
 * @param {string} options.message - 消息内容
 * @param {number} options.duration - 显示时长 (ms)
 * @param {boolean} options.closable - 是否可关闭
 */
export function useToast() {
  function showToast({ type = 'info', title = '', message, duration = 3000, closable = true }) {
    // 清除之前的定时器
    if (toastTimer) {
      clearTimeout(toastTimer)
      toastTimer = null
    }

    // 设置配置
    toastConfig.value = { type, title, message, duration, closable }
    toastVisible.value = true

    // 自动关闭
    if (duration > 0) {
      toastTimer = setTimeout(() => {
        toastVisible.value = false
      }, duration)
    }
  }

  function hideToast() {
    toastVisible.value = false
    if (toastTimer) {
      clearTimeout(toastTimer)
      toastTimer = null
    }
  }

  // 便捷方法
  function success(message, duration = 3000) {
    showToast({ type: 'success', message, duration })
  }

  function error(message, duration = 4000) {
    showToast({ type: 'error', message, duration })
  }

  function warning(message, duration = 3000) {
    showToast({ type: 'warning', message, duration })
  }

  function info(message, duration = 3000) {
    showToast({ type: 'info', message, duration })
  }

  return {
    // 状态
    toastVisible,
    toastConfig,

    // 方法
    showToast,
    hideToast,

    // 便捷方法
    success,
    error,
    warning,
    info
  }
}

// 便捷调用方式（无需在组件中引入）
export const toast = {
  show: (opts) => useToast().showToast(opts),
  success: (msg) => useToast().success(msg),
  error: (msg) => useToast().error(msg),
  warning: (msg) => useToast().warning(msg),
  info: (msg) => useToast().info(msg)
}

export default useToast