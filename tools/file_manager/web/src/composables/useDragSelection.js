/**
 * useDragSelection - 框选功能 composable
 *
 * 实现文件列表的矩形框选功能
 * 契约接口定义在 VUE3迁移工作文档.md Section 2.2
 */

import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'

export function useDragSelection(containerRef, options = {}) {
  const {
    onSelectionChange = () => {},
    enabled = true
  } = options

  // 选择状态
  const selectedPaths = ref(new Set())
  const isSelecting = ref(false)
  const dragStart = reactive({ x: 0, y: 0 })
  const dragEnd = reactive({ x: 0, y: 0 })

  // 拖拽选择矩形（用于渲染）
  const selectionRect = computed(() => {
    if (!isSelecting.value) return null

    const left = Math.min(dragStart.x, dragEnd.x)
    const top = Math.min(dragStart.y, dragEnd.y)
    const width = Math.abs(dragEnd.x - dragStart.x)
    const height = Math.abs(dragEnd.y - dragStart.y)

    return { left, top, width, height }
  })

  /**
   * 检测指定点是否在选择矩形内
   */
  function isPointInSelection(x, y) {
    if (!selectionRect.value) return false
    const { left, top, width, height } = selectionRect.value
    return x >= left && x <= left + width && y >= top && y <= top + height
  }

  /**
   * 检测元素是否与选择矩形相交
   */
  function isElementInSelection(element) {
    if (!selectionRect.value || !element) return false

    const rect = element.getBoundingClientRect()
    const { left, top, width, height } = selectionRect.value

    // 检测两个矩形是否相交
    const horizontal = rect.left < left + width && rect.left + rect.width > left
    const vertical = rect.top < top + height && rect.top + rect.height > top

    return horizontal && vertical
  }

  /**
   * 开始框选
   */
  function startSelection(event) {
    if (!enabled) return
    if (event.button !== 0) return // 只响应左键

    isSelecting.value = true
    dragStart.x = event.clientX
    dragStart.y = event.clientY
    dragEnd.x = event.clientX
    dragEnd.y = event.clientY

    // 清除之前的选择（按住 Shift 可以追加）
    if (!event.shiftKey) {
      selectedPaths.value.clear()
    }
  }

  /**
   * 更新框选范围
   */
  function updateSelection(event) {
    if (!isSelecting.value) return

    dragEnd.x = event.clientX
    dragEnd.y = event.clientY

    // 查找所有与选择矩形相交的文件行
    const fileRows = document.querySelectorAll('.file-row[data-path]')
    fileRows.forEach(row => {
      const path = row.dataset.path
      if (isElementInSelection(row)) {
        selectedPaths.value.add(path)
      }
    })

    // 通知选择变更
    onSelectionChange([...selectedPaths.value])
  }

  /**
   * 结束框选
   */
  function endSelection() {
    isSelecting.value = false
  }

  /**
   * 全选
   */
  function selectAll(paths) {
    paths.forEach(path => selectedPaths.value.add(path))
    onSelectionChange([...selectedPaths.value])
  }

  /**
   * 清除选择
   */
  function clearSelection() {
    selectedPaths.value.clear()
    onSelectionChange([])
  }

  /**
   * 切换单个文件的选择状态
   */
  function toggleSelection(path, multi = false) {
    if (multi) {
      if (selectedPaths.value.has(path)) {
        selectedPaths.value.delete(path)
      } else {
        selectedPaths.value.add(path)
      }
    } else {
      selectedPaths.value.clear()
      selectedPaths.value.add(path)
    }
    onSelectionChange([...selectedPaths.value])
  }

  /**
   * 添加到选择
   */
  function addToSelection(paths) {
    paths.forEach(path => selectedPaths.value.add(path))
    onSelectionChange([...selectedPaths.value])
  }

  // 全局事件监听
  function handleMouseMove(event) {
    updateSelection(event)
  }

  function handleMouseUp(event) {
    if (isSelecting.value) {
      endSelection()
    }
  }

  onMounted(() => {
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
  })

  onUnmounted(() => {
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
  })

  return {
    // 状态
    selectedPaths,
    isSelecting,
    selectionRect,
    // 方法
    startSelection,
    updateSelection,
    endSelection,
    selectAll,
    clearSelection,
    toggleSelection,
    addToSelection,
    isPointInSelection,
    isElementInSelection
  }
}

export default useDragSelection