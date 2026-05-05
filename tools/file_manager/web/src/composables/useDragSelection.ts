// useDragSelection - 文件框选功能 Composable
import { ref, computed } from 'vue'

export function useDragSelection() {
  const isDragging = ref(false)
  const startX = ref(0)
  const startY = ref(0)
  const dragRect = ref<DOMRect | null>(null)
  const selectedElements = ref<Set<Element>>(new Set())

  // 开始框选
  function startDrag(e: MouseEvent) {
    isDragging.value = true
    startX.value = e.clientX
    startY.value = e.clientY
    dragRect.value = {
      left: e.clientX,
      top: e.clientY,
      right: e.clientX,
      bottom: e.clientY,
      width: 0,
      height: 0,
      x: e.clientX,
      y: e.clientY,
    } as DOMRect
    selectedElements.value.clear()
  }

  // 更新框选
  function updateDrag(e: MouseEvent) {
    if (!isDragging.value) return

    const minX = Math.min(startX.value, e.clientX)
    const minY = Math.min(startY.value, e.clientY)
    const maxX = Math.max(startX.value, e.clientX)
    const maxY = Math.max(startY.value, e.clientY)

    dragRect.value = {
      left: minX,
      top: minY,
      right: maxX,
      bottom: maxY,
      width: maxX - minX,
      height: maxY - minY,
      x: minX,
      y: minY,
    } as DOMRect
  }

  // 结束框选
  function endDrag() {
    isDragging.value = false
  }

  // 重置选择
  function reset() {
    isDragging.value = false
    startX.value = 0
    startY.value = 0
    dragRect.value = null
    selectedElements.value.clear()
  }

  // 检查元素是否在选框内
  function isInRect(el: Element): boolean {
    if (!dragRect.value) return false
    const rect = el.getBoundingClientRect()
    return !(
      rect.right < dragRect.value.left ||
      rect.left > dragRect.value.right ||
      rect.bottom < dragRect.value.top ||
      rect.top > dragRect.value.bottom
    )
  }

  // 选择容器内的文件元素
  function selectFilesInRect(container: Element, selector: string = '.file-item') {
    const files = container.querySelectorAll(selector)
    const selected: Element[] = []

    files.forEach(file => {
      if (isInRect(file)) {
        selected.push(file)
        selectedElements.value.add(file)
      }
    })

    return selected.map(el => el.getAttribute('data-path')).filter(Boolean) as string[]
  }

  const isActive = computed(() => isDragging.value && dragRect.value !== null)

  return {
    isDragging,
    dragRect,
    selectedElements,
    isActive,
    startDrag,
    updateDrag,
    endDrag,
    reset,
    isInRect,
    selectFilesInRect,
  }
}