/**
 * useTauri - Tauri 桌面端适配 composable
 *
 * 提供 Tauri 专有功能的封装，包括：
 * - 窗口控制（主窗口/浮窗）
 * - 文件系统操作（openPath）
 * - 系统集成（打开知识库等）
 */

import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/authStore'

export function useTauri() {
  const authStore = useAuthStore()
  const isTauri = ref(false)
  const isFloatingVisible = ref(false)

  onMounted(() => {
    // 检测是否为 Tauri 环境
    isTauri.value = typeof window.__TAURI_INVOKE__ !== 'undefined'
  })

  /**
   * 调用 Tauri 命令
   */
  async function invoke(command, args = {}) {
    if (!isTauri.value) {
      console.warn(`[useTauri] ${command} requires Tauri environment`)
      return null
    }
    try {
      return await window.__TAURI_INVOKE__(command, args)
    } catch (e) {
      console.error(`[useTauri] ${command} failed:`, e)
      throw e
    }
  }

  /**
   * 打开文件所在位置（Finder）
   */
  async function openPath(path) {
    return invoke('open_path_in_finder', { path })
  }

  /**
   * 打开 LLM Wiki 知识库
   */
  async function openLlmWiki() {
    return invoke('open_llm_wiki')
  }

  /**
   * 显示浮窗
   */
  async function showFloatingWindow() {
    await invoke('show_floating_window')
    isFloatingVisible.value = true
  }

  /**
   * 隐藏浮窗
   */
  async function hideFloatingWindow() {
    await invoke('hide_floating_window')
    isFloatingVisible.value = false
  }

  /**
   * 切换浮窗
   */
  async function toggleFloatingWindow() {
    if (isFloatingVisible.value) {
      await hideFloatingWindow()
    } else {
      await showFloatingWindow()
    }
  }

  /**
   * 获取当前平台信息
   */
  function getPlatformInfo() {
    return {
      isTauri: isTauri.value,
      platform: navigator.platform,
      userAgent: navigator.userAgent
    }
  }

  /**
   * 发送桌面通知
   */
  async function sendNotification(title, body) {
    if (isTauri.value) {
      return invoke('send_notification', { title, body })
    } else {
      // Web fallback: 使用浏览器通知
      if ('Notification' in window && Notification.permission === 'granted') {
        new Notification(title, { body })
      }
    }
  }

  return {
    isTauri,
    isFloatingVisible,
    invoke,
    openPath,
    openLlmWiki,
    showFloatingWindow,
    hideFloatingWindow,
    toggleFloatingWindow,
    getPlatformInfo,
    sendNotification
  }
}

export default useTauri