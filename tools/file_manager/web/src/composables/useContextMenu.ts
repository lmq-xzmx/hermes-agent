/**
 * useContextMenu - 右键菜单 composable
 *
 * 管理右键菜单的状态和操作处理
 * 契约接口定义在 VUE3迁移工作文档.md Section 2.1
 */

import { ref, reactive, computed } from 'vue'

// 类型定义
export interface ContextMenuItem {
  id: string
  icon?: string
  label: string
  shortcut?: string
  danger?: boolean
  disabled?: boolean
  separator?: boolean
}

export interface ContextMenuPosition {
  x: number
  y: number
}

export interface FileItem {
  path: string
  name: string
  is_directory: boolean
  size?: number
  modified?: string
}

// 默认菜单项
const DEFAULT_ITEMS: ContextMenuItem[] = [
  { id: 'open', icon: '📂', label: '打开', shortcut: 'Enter' },
  { id: 'rename', icon: '✏️', label: '重命名', shortcut: 'F2' },
  { separator: true } as ContextMenuItem,
  { id: 'copy', icon: '📋', label: '复制', shortcut: 'Cmd+C' },
  { id: 'cut', icon: '✂️', label: '剪切', shortcut: 'Cmd+X' },
  { id: 'paste', icon: '📥', label: '粘贴', shortcut: 'Cmd+V' },
  { separator: true } as ContextMenuItem,
  { id: 'share', icon: '🔗', label: '获取链接' },
  { id: 'info', icon: 'ℹ️', label: '显示详情', shortcut: 'Alt+I' },
  { separator: true } as ContextMenuItem,
  { id: 'delete', icon: '🗑️', label: '删除', shortcut: '⌫', danger: true }
]

export function useContextMenu() {
  // 菜单状态
  const visible = ref(false)
  const position = reactive<ContextMenuPosition>({ x: 0, y: 0 })
  const target = ref<FileItem | null>(null)
  const menuItems = ref<ContextMenuItem[]>([...DEFAULT_ITEMS])

  // 计算菜单位置（防止超出屏幕）
  const adjustedPosition = computed<ContextMenuPosition>(() => {
    const menuWidth = 200
    const menuHeight = 300
    const padding = 10

    return {
      x: Math.min(position.x, window.innerWidth - menuWidth - padding),
      y: Math.min(position.y, window.innerHeight - menuHeight - padding)
    }
  })

  /**
   * 显示右键菜单
   */
  function show(event: MouseEvent, fileItem: FileItem | null = null, customItems: ContextMenuItem[] = []) {
    event.preventDefault()

    target.value = fileItem

    // 设置菜单位置
    position.x = event.clientX
    position.y = event.clientY

    // 设置菜单项
    if (customItems.length > 0) {
      menuItems.value = customItems
    } else {
      menuItems.value = [...DEFAULT_ITEMS]
    }

    visible.value = true
  }

  /**
   * 隐藏菜单
   */
  function hide() {
    visible.value = false
    target.value = null
  }

  /**
   * 切换菜单可见性
   */
  function toggle(event: MouseEvent, fileItem: FileItem | null = null) {
    if (visible.value) {
      hide()
    } else {
      show(event, fileItem)
    }
  }

  /**
   * 执行菜单操作
   * @returns 操作结果
   */
  function executeAction(action: string) {
    if (!target.value) {
      return { handled: false }
    }

    const result: any = {
      handled: true,
      action,
      target: target.value,
      timestamp: Date.now()
    }

    switch (action) {
      case 'open':
        if (target.value.is_directory) {
          result.navigate = target.value.path
        } else {
          result.openFile = target.value.path
        }
        break

      case 'rename':
        result.prompt = '请输入新名称:'
        result.oldName = target.value.name
        break

      case 'copy':
        result.operation = 'copy'
        result.paths = [target.value.path]
        break

      case 'cut':
        result.operation = 'cut'
        result.paths = [target.value.path]
        break

      case 'paste':
        result.operation = 'paste'
        result.targetPath = target.value.path
        break

      case 'share':
        result.operation = 'share'
        result.path = target.value.path
        break

      case 'delete':
        result.operation = 'delete'
        result.paths = [target.value.path]
        result.confirm = `确定要删除 "${target.value.name}" 吗？`
        break

      case 'info':
        result.operation = 'info'
        result.path = target.value.path
        break

      default:
        result.handled = false
    }

    hide()
    return result
  }

  /**
   * 创建带危险标记的菜单项
   */
  function createDangerItem(item: ContextMenuItem): ContextMenuItem {
    return {
      ...item,
      danger: true
    }
  }

  /**
   * 过滤禁用项
   */
  function filterDisabled() {
    return menuItems.value.filter(item => {
      if (item.id === 'paste') {
        return false // 暂时禁用
      }
      return true
    })
  }

  return {
    // 状态
    visible,
    position,
    target,
    menuItems,
    adjustedPosition,
    // 方法
    show,
    hide,
    toggle,
    executeAction,
    createDangerItem,
    filterDisabled,
    // 常量
    DEFAULT_ITEMS
  }
}

export default useContextMenu
