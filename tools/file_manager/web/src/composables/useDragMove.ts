/**
 * useDragMove - 拖拽移动功能 composable
 *
 * 实现文件/文件夹的拖拽移动功能
 * 支持:
 * - 拖拽文件到目标文件夹
 * - 高亮显示可释放区域
 * - Escape 取消拖拽
 * - 批量拖拽
 * - 权限检查
 */

import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface DragMoveOptions {
  /** 拖拽开始回调 */
  onDragStart?: (items: string[]) => void
  /** 拖入有效目标回调 */
  onDragEnter?: (targetPath: string) => void
  /** 拖出有效目标回调 */
  onDragLeave?: (targetPath: string) => void
  /** 释放成功回调 */
  onDrop?: (items: string[], targetPath: string) => Promise<boolean>
  /** 权限检查回调 */
  checkPermission?: (path: string, action: 'move') => Promise<boolean>
  /** 是否启用 */
  enabled?: boolean
}

export interface DragState {
  isDragging: boolean
  draggedItems: string[]
  draggedElement: Element | null
  currentTarget: string | null
  isValidTarget: boolean
}

export function useDragMove(options: DragMoveOptions = {}) {
  const {
    onDragStart,
    onDragEnter,
    onDragLeave,
    onDrop,
    checkPermission,
    enabled = true
  } = options

  // 拖拽状态
  const isDragging = ref(false)
  const draggedItems = ref<string[]>([])
  const draggedElement = ref<Element | null>(null)
  const currentTarget = ref<string | null>(null)
  const isValidTarget = ref(false)

  // 拖拽预览元素
  const dragPreview = ref<HTMLElement | null>(null)

  // 计算属性
  const dragState = computed<DragState>(() => ({
    isDragging: isDragging.value,
    draggedItems: draggedItems.value,
    draggedElement: draggedElement.value,
    currentTarget: currentTarget.value,
    isValidTarget: isValidTarget.value
  }))

  /**
   * 开始拖拽
   */
  function startDrag(event: DragEvent, items: string[], element: Element) {
    if (!enabled) return

    event.dataTransfer?.setData('text/plain', JSON.stringify(items))
    event.dataTransfer!.effectAllowed = 'move'

    isDragging.value = true
    draggedItems.value = items
    draggedElement.value = element

    // 创建拖拽预览
    createDragPreview(items)

    onDragStart?.(items)
  }

  /**
   * 创建拖拽预览元素
   */
  function createDragPreview(items: string[]) {
    const preview = document.createElement('div')
    preview.className = 'drag-preview'
    preview.textContent = items.length === 1
      ? items[0].split('/').pop()
      : `${items.length} 个项目`
    preview.style.cssText = `
      position: fixed;
      top: -1000px;
      left: -1000px;
      padding: 8px 12px;
      background: var(--color-primary);
      color: var(--color-body-on-dark);
      border-radius: var(--radius-sm);
      font-size: 12px;
      pointer-events: none;
      z-index: 9999;
      white-space: nowrap;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    `
    document.body.appendChild(preview)
    dragPreview.value = preview

    // 跟随鼠标
    document.addEventListener('drag', updatePreviewPosition)
  }

  /**
   * 更新预览位置
   */
  function updatePreviewPosition(event: DragEvent) {
    if (dragPreview.value && event.clientX && event.clientY) {
      dragPreview.value.style.left = `${event.clientX + 10}px`
      dragPreview.value.style.top = `${event.clientY + 10}px`
    }
  }

  /**
   * 结束拖拽
   */
  function endDrag() {
    isDragging.value = false
    draggedItems.value = []
    draggedElement.value = null
    currentTarget.value = null
    isValidTarget.value = false

    // 移除预览元素
    if (dragPreview.value) {
      document.removeEventListener('drag', updatePreviewPosition)
      dragPreview.value.remove()
      dragPreview.value = null
    }
  }

  /**
   * 拖拽进入有效目标
   */
  async function handleDragEnter(event: DragEvent, targetPath: string) {
    event.preventDefault()

    if (!isDragging.value) return

    currentTarget.value = targetPath

    // 权限检查
    if (checkPermission) {
      const hasPermission = await checkPermission(targetPath, 'move')
      isValidTarget.value = hasPermission
      event.dataTransfer!.dropEffect = hasPermission ? 'move' : 'none'
    } else {
      isValidTarget.value = true
    }

    if (isValidTarget.value) {
      onDragEnter?.(targetPath)
    }
  }

  /**
   * 拖拽悬停有效目标
   */
  function handleDragOver(event: DragEvent, targetPath: string) {
    event.preventDefault()

    if (!isDragging.value) return

    event.dataTransfer!.dropEffect = isValidTarget.value ? 'move' : 'none'
  }

  /**
   * 拖拽离开有效目标
   */
  function handleDragLeave(event: DragEvent, targetPath: string) {
    if (!isDragging.value) return

    // 检查是否真正离开了（鼠标移动到子元素不算）
    const relatedTarget = event.relatedTarget as Element
    if (relatedTarget?.closest('[data-drop-target]') === event.target) {
      return
    }

    currentTarget.value = null
    isValidTarget.value = false
    onDragLeave?.(targetPath)
  }

  /**
   * 释放到目标
   */
  async function handleDrop(event: DragEvent, targetPath: string): Promise<boolean> {
    event.preventDefault()

    if (!isDragging.value || !isValidTarget.value) {
      endDrag()
      return false
    }

    try {
      const result = await onDrop?.(draggedItems.value, targetPath)
      endDrag()
      return result ?? false
    } catch (error) {
      console.error('Drop failed:', error)
      endDrag()
      return false
    }
  }

  /**
   * 处理 Escape 取消
   */
  function handleKeyDown(event: KeyboardEvent) {
    if (event.key === 'Escape' && isDragging.value) {
      event.preventDefault()
      endDrag()
    }
  }

  /**
   * 注册拖拽源（文件行）
   */
  function registerDragSource(element: Element, getItems: () => string[]) {
    element.setAttribute('draggable', 'true')

    element.addEventListener('dragstart', (e) => {
      const items = getItems()
      if (items.length === 0) {
        e.preventDefault()
        return
      }
      startDrag(e as DragEvent, items, element)
    })

    element.addEventListener('dragend', () => {
      endDrag()
    })
  }

  /**
   * 注册拖拽目标（文件夹）
   */
  function registerDropTarget(element: Element, getPath: () => string) {
    element.setAttribute('data-drop-target', 'true')

    element.addEventListener('dragenter', (e) => {
      handleDragEnter(e as DragEvent, getPath())
    })

    element.addEventListener('dragover', (e) => {
      handleDragOver(e as DragEvent, getPath())
    })

    element.addEventListener('dragleave', (e) => {
      handleDragLeave(e as DragEvent, getPath())
    })

    element.addEventListener('drop', async (e) => {
      await handleDrop(e as DragEvent, getPath())
    })
  }

  // 生命周期
  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    document.removeEventListener('drag', updatePreviewPosition)
    if (dragPreview.value) {
      dragPreview.value.remove()
    }
  })

  return {
    // 状态
    isDragging: computed(() => isDragging.value),
    draggedItems: computed(() => draggedItems.value),
    currentTarget: computed(() => currentTarget.value),
    isValidTarget: computed(() => isValidTarget.value),
    dragState,

    // 方法
    startDrag,
    endDrag,
    handleDragEnter,
    handleDragOver,
    handleDragLeave,
    handleDrop,
    registerDragSource,
    registerDropTarget
  }
}

export default useDragMove