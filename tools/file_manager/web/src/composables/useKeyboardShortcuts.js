/**
 * useKeyboardShortcuts.js - 快捷键完整支持
 *
 * UI-10: 跨平台文件管理器键盘快捷键
 *
 * 支持的快捷键:
 * - Enter: 打开文件/文件夹
 * - Cmd/Ctrl+A: 全选
 * - Cmd/Ctrl+C: 复制
 * - Cmd/Ctrl+V: 粘贴
 * - Cmd/Ctrl+X: 剪切
 * - Cmd/Ctrl+Backspace/Delete: 删除
 * - Cmd/Ctrl+D: 复制到当前目录 (duplicate)
 * - Cmd/Ctrl+N: 新建文件夹
 * - Cmd/Ctrl+Shift+N: 新建文件
 * - Space: 预览
 * - Alt/Cmd+I: 显示详情 (Get Info)
 * - Cmd/Ctrl+Shift+N: 新建窗口 (Tauri)
 * - Cmd/Ctrl+W: 关闭标签/窗口
 * - Cmd/Ctrl+,: 偏好设置
 * - Escape: 取消选择/关闭预览
 * - Arrow keys: 导航选择
 * - Shift+Arrow: 范围选择
 * - Cmd/Ctrl+Arrow: 快速导航 (到父目录/首字符)
 *
 * 平台适配:
 * - Mac: Cmd键 (metaKey)
 * - Windows/Linux: Ctrl键 (ctrlKey)
 */

import { ref, onMounted, onUnmounted } from 'vue'

// 快捷键定义
const SHORTCUTS = {
  // 文件操作
  OPEN: { key: 'Enter', description: '打开文件/文件夹' },
  SELECT_ALL: { key: 'Mod+A', description: '全选' },
  COPY: { key: 'Mod+C', description: '复制' },
  PASTE: { key: 'Mod+V', description: '粘贴' },
  CUT: { key: 'Mod+X', description: '剪切' },
  DELETE: { key: 'Mod+Backspace', description: '删除' },
  DUPLICATE: { key: 'Mod+D', description: '复制到当前目录' },
  RENAME: { key: 'F2', description: '重命名' },

  // 新建
  NEW_FOLDER: { key: 'Mod+Shift+N', description: '新建文件夹' },
  NEW_FILE: { key: 'Mod+N', description: '新建文件' },

  // 导航
  PREVIEW: { key: 'Space', description: '预览' },
  INFO: { key: 'Mod+I', description: '显示详情' },
  GO_BACK: { key: 'Backspace', description: '返回上级' },
  ESCAPE: { key: 'Escape', description: '取消选择' },

  // 窗口
  CLOSE: { key: 'Mod+W', description: '关闭' },
  PREFERENCES: { key: 'Mod+,', description: '偏好设置' },

  // 选择导航
  ARROW_UP: { key: 'ArrowUp', description: '向上选择' },
  ARROW_DOWN: { key: 'ArrowDown', description: '向下选择' },
  ARROW_LEFT: { key: 'ArrowLeft', description: '向左' },
  ARROW_RIGHT: { key: 'ArrowRight', description: '向右' },
  HOME: { key: 'Home', description: '跳到首位' },
  END: { key: 'End', description: '跳到尾位' },
}

// 修饰符键检测
function isModKey(e) {
  // Mac: metaKey (Cmd), Others: ctrlKey (Ctrl)
  return navigator.platform.toUpperCase().indexOf('MAC') >= 0 ? e.metaKey : e.ctrlKey
}

function isShiftKey(e) {
  return e.shiftKey
}

function isAltKey(e) {
  return e.altKey
}

// 解析快捷键字符串
function parseShortcut(shortcutStr) {
  const parts = shortcutStr.split('+')
  return {
    mod: parts.includes('Mod'),
    shift: parts.includes('Shift'),
    alt: parts.includes('Alt'),
    key: parts[parts.length - 1],
  }
}

// 匹配快捷键
function matchShortcut(e, shortcutStr) {
  const parsed = parseShortcut(shortcutStr)
  const modMatched = !parsed.mod || isModKey(e)
  const shiftMatched = !parsed.shift || isShiftKey(e)
  const altMatched = !parsed.alt || isAltKey(e)
  const keyMatched = e.key === parsed.key || e.code === parsed.key

  return modMatched && shiftMatched && altMatched && keyMatched
}

export function useKeyboardShortcuts(options = {}) {
  const {
    onOpen = null,
    onSelectAll = null,
    onCopy = null,
    onPaste = null,
    onCut = null,
    onDelete = null,
    onDuplicate = null,
    onRename = null,
    onNewFolder = null,
    onNewFile = null,
    onPreview = null,
    onInfo = null,
    onEscape = null,
    onGoBack = null,
    onClose = null,
    onPreferences = null,
    onArrowUp = null,
    onArrowDown = null,
    onArrowLeft = null,
    onArrowRight = null,
    onHome = null,
    onEnd = null,
    // 排除某些快捷键的DOM元素
    excludedElements = ['INPUT', 'TEXTAREA', 'SELECT', 'CONTENTEDITABLE'],
  } = options

  const lastKey = ref('')
  const shortcutHistory = ref([])

  // 处理键盘事件
  function handleKeyDown(e) {
    // 检查是否在排除元素中
    if (excludedElements.includes(e.target.tagName)) {
      // 允许一些通用快捷键（如 Escape）
      if (e.key === 'Escape' && onEscape) {
        e.preventDefault()
        onEscape()
        return true
      }
      return false
    }

    // 遍历所有快捷键
    const handlers = {
      'Enter': onOpen,
      'Mod+A': onSelectAll,
      'Mod+C': onCopy,
      'Mod+V': onPaste,
      'Mod+X': onCut,
      'Mod+Backspace': onDelete,
      'Mod+D': onDuplicate,
      'F2': onRename,
      'Mod+Shift+N': onNewFolder,
      'Mod+N': onNewFile,
      'Space': onPreview,
      'Mod+I': onInfo,
      'Backspace': onGoBack,
      'Escape': onEscape,
      'Mod+W': onClose,
      'Mod+,': onPreferences,
      'ArrowUp': onArrowUp,
      'ArrowDown': onArrowDown,
      'ArrowLeft': onArrowLeft,
      'ArrowRight': onArrowRight,
      'Home': onHome,
      'End': onEnd,
    }

    for (const [shortcut, handler] of Object.entries(handlers)) {
      if (matchShortcut(e, shortcut)) {
        if (handler) {
          e.preventDefault()
          lastKey.value = shortcut
          shortcutHistory.value.push({ shortcut, time: Date.now() })
          handler(e)
          return true
        }
      }
    }

    return false
  }

  // 注册全局快捷键
  function register() {
    document.addEventListener('keydown', handleKeyDown)
  }

  // 注销全局快捷键
  function unregister() {
    document.removeEventListener('keydown', handleKeyDown)
  }

  // 获取快捷键帮助文本
  function getShortcutHelp() {
    const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
    const modKey = isMac ? '⌘' : 'Ctrl'

    return Object.entries(SHORTCUTS).map(([name, info]) => {
      const displayKey = info.key
        .replace('Mod', modKey)
        .replace('Backspace', '⌫')
        .replace('ArrowUp', '↑')
        .replace('ArrowDown', '↓')
        .replace('ArrowLeft', '←')
        .replace('ArrowRight', '→')
        .replace('Escape', 'Esc')
        .replace('Space', '空格')

      return {
        name,
        key: displayKey,
        description: info.description,
      }
    })
  }

  // 检查是否显示快捷键提示
  function shouldShowHint(e) {
    return isModKey(e) || e.shiftKey || e.altKey
  }

  // 生命周期
  onMounted(register)
  onUnmounted(unregister)

  return {
    lastKey,
    shortcutHistory,
    register,
    unregister,
    getShortcutHelp,
    shouldShowHint,
    SHORTCUTS,
  }
}

// 快捷键帮助组件的数据
export function useShortcutHints() {
  const hints = ref([])

  function updateHints(e) {
    if (e.key) {
      hints.value = [
        e.metaKey && '⌘',
        e.ctrlKey && 'Ctrl',
        e.shiftKey && '⇧',
        e.altKey && '⌥',
        e.key !== 'Meta' && e.key !== 'Control' && e.key !== 'Shift' && e.key !== 'Alt' ? e.key.toUpperCase() : '',
      ].filter(Boolean)
    }
  }

  function clearHints() {
    hints.value = []
  }

  return {
    hints,
    updateHints,
    clearHints,
  }
}

// 导出快捷键常量
export { SHORTCUTS }