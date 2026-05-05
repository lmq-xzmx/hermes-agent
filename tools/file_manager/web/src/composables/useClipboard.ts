// useClipboard - 剪贴板操作 Composable
import { ref, computed } from 'vue'
import type { ClipboardState } from '@/types/clipboard'

export function useClipboard() {
  const clipboard = ref<ClipboardState>({
    mode: null,
    paths: [],
    timestamp: 0,
  })

  const isEmpty = computed(() => clipboard.value.paths.length === 0)
  const hasContent = computed(() => clipboard.value.paths.length > 0)

  // 复制到剪贴板
  function copy(paths: string[]) {
    clipboard.value = {
      mode: 'copy',
      paths: [...paths],
      timestamp: Date.now(),
    }
    // 同步到系统剪贴板（第一个路径）
    if (paths.length === 1) {
      navigator.clipboard.writeText(paths[0]).catch(() => {})
    }
  }

  // 剪切到剪贴板
  function cut(paths: string[]) {
    clipboard.value = {
      mode: 'cut',
      paths: [...paths],
      timestamp: Date.now(),
    }
    // 同步到系统剪贴板（第一个路径）
    if (paths.length === 1) {
      navigator.clipboard.writeText(paths[0]).catch(() => {})
    }
  }

  // 清空剪贴板
  function clear() {
    clipboard.value = {
      mode: null,
      paths: [],
      timestamp: 0,
    }
  }

  // 获取剪贴板内容（用于粘贴）
  function getClipboard() {
    return clipboard.value
  }

  return {
    clipboard,
    isEmpty,
    hasContent,
    copy,
    cut,
    clear,
    getClipboard,
  }
}