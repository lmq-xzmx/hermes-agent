/**
 * useFileManagerShortcuts.js - 文件管理器快捷键集成
 *
 * 文件管理器场景下的快捷键使用示例
 */

import { ref, computed } from 'vue'
import { useKeyboardShortcuts } from './useKeyboardShortcuts.js'

export function useFileManagerShortcuts(options = {}) {
  const {
    selectedFiles = ref([]),
    currentPath = ref(''),
    onFileAction = null,  // 文件操作回调
  } = options

  const isMac = computed(() => navigator.platform.toUpperCase().indexOf('MAC') >= 0)
  const modKey = computed(() => isMac.value ? '⌘' : 'Ctrl')

  // 文件操作
  async function handleOpen() {
    if (selectedFiles.value.length === 1) {
      const file = selectedFiles.value[0]
      if (onFileAction) {
        await onFileAction('open', file)
      }
    }
  }

  async function handleCopy() {
    if (selectedFiles.value.length > 0 && onFileAction) {
      await onFileAction('copy', selectedFiles.value)
    }
  }

  async function handlePaste() {
    if (onFileAction) {
      await onFileAction('paste', currentPath.value)
    }
  }

  async function handleDelete() {
    if (selectedFiles.value.length > 0 && onFileAction) {
      await onFileAction('delete', selectedFiles.value)
    }
  }

  async function handleRename() {
    if (selectedFiles.value.length === 1 && onFileAction) {
      await onFileAction('rename', selectedFiles.value[0])
    }
  }

  function handleSelectAll() {
    if (onFileAction) {
      onFileAction('selectAll')
    }
  }

  function handleEscape() {
    if (onFileAction) {
      onFileAction('deselectAll')
    }
  }

  function handleGoBack() {
    if (currentPath.value && onFileAction) {
      onFileAction('goBack')
    }
  }

  // 导航选择
  function handleArrowUp(e) {
    if (onFileAction) {
      e.shiftKey ? onFileAction('extendSelectionUp') : onFileAction('selectUp')
    }
  }

  function handleArrowDown(e) {
    if (onFileAction) {
      e.shiftKey ? onFileAction('extendSelectionDown') : onFileAction('selectDown')
    }
  }

  function handleArrowLeft() {
    if (onFileAction) {
      onFileAction('goBack')
    }
  }

  function handleArrowRight() {
    if (selectedFiles.value.length === 1 && onFileAction) {
      onFileAction('enterFolder', selectedFiles.value[0])
    }
  }

  // 注册快捷键
  const {
    lastKey,
    shortcutHistory,
    getShortcutHelp,
    shouldShowHint,
    SHORTCUTS,
  } = useKeyboardShortcuts({
    onOpen: handleOpen,
    onSelectAll: handleSelectAll,
    onCopy: handleCopy,
    onPaste: handlePaste,
    onDelete: handleDelete,
    onRename: handleRename,
    onEscape: handleEscape,
    onGoBack: handleGoBack,
    onArrowUp: handleArrowUp,
    onArrowDown: handleArrowDown,
    onArrowLeft: handleArrowLeft,
    onArrowRight: handleArrowRight,
    onNewFolder: () => onFileAction?.('newFolder', currentPath.value),
    onNewFile: () => onFileAction?.('newFile', currentPath.value),
    onPreview: () => onFileAction?.('preview', selectedFiles.value[0]),
    onInfo: () => onFileAction?.('info', selectedFiles.value[0]),
  })

  return {
    lastKey,
    shortcutHistory,
    getShortcutHelp,
    shouldShowHint,
    SHORTCUTS,
    isMac,
    modKey,
  }
}

// 快捷键提示菜单项
export function getContextMenuShortcuts(isMac) {
  const mod = isMac ? '⌘' : 'Ctrl'

  return [
    { label: '打开', shortcut: 'Enter', action: 'open' },
    { label: '重命名', shortcut: 'F2', action: 'rename' },
    { separator: true },
    { label: '复制', shortcut: `${mod}+C`, action: 'copy' },
    { label: '剪切', shortcut: `${mod}+X`, action: 'cut' },
    { label: '粘贴', shortcut: `${mod}+V`, action: 'paste' },
    { label: '删除', shortcut: `${mod}+⌫`, action: 'delete' },
    { separator: true },
    { label: '复制到当前', shortcut: `${mod}+D`, action: 'duplicate' },
    { label: '显示详情', shortcut: `${mod}+I`, action: 'info' },
  ]
}