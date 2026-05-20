/**
 * useDragMove Composable 单元测试
 *
 * 测试用例: TC-UI9-001 ~ TC-UI9-005
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useDragMove } from '../useDragMove'

// Mock document methods
const mockAddEventListener = vi.fn()
const mockRemoveEventListener = vi.fn()
const mockQuerySelectorAll = vi.fn()

vi.stubGlobal('document', {
  addEventListener: mockAddEventListener,
  removeEventListener: mockRemoveEventListener,
  querySelectorAll: mockQuerySelectorAll,
  body: {
    appendChild: vi.fn(),
    removeChild: vi.fn()
  },
  createElement: vi.fn((tag) => ({
    className: '',
    textContent: '',
    style: { cssText: '' },
    setAttribute: vi.fn(),
    removeEventListener: vi.fn(),
    appendChild: vi.fn(),
    remove: vi.fn()
  }))
})

describe('useDragMove', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('TC-UI9-001: 拖拽文件到目标文件夹', () => {
    it('should detect valid drop target on dragenter', async () => {
      const onDragEnter = vi.fn()
      const onDragLeave = vi.fn()

      const { handleDragEnter, handleDragLeave, startDrag, isDragging, currentTarget, draggedItems } = useDragMove({
        onDragEnter,
        onDragLeave,
        enabled: true
      })

      // Start dragging
      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      startDrag(mockEvent, ['/path/to/file.txt'], document.createElement('div'))

      expect(isDragging.value).toBe(true)
      expect(draggedItems.value).toEqual(['/path/to/file.txt'])

      // Simulate drag enter on target folder
      const targetEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      await handleDragEnter(targetEvent, '/target/folder')

      expect(onDragEnter).toHaveBeenCalledWith('/target/folder')
      expect(currentTarget.value).toBe('/target/folder')
    })

    it('should highlight drop zone when dragging over valid target', async () => {
      const { handleDragOver, isValidTarget } = useDragMove({
        enabled: true
      })

      const event = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      handleDragOver(event, '/target/folder')

      expect(isValidTarget.value).toBe(true)
    })

    it('should call onDrop callback when dropped on valid target', async () => {
      const onDrop = vi.fn().mockResolvedValue(true)

      const { handleDrop } = useDragMove({
        onDrop,
        enabled: true
      })

      const dropEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move' }
      } as unknown as DragEvent

      // First set dragging state
      const startEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      const { startDrag } = useDragMove({ enabled: true })
      startDrag(startEvent, ['/path/to/file.txt'], document.createElement('div'))

      const result = await handleDrop(dropEvent, '/target/folder')

      expect(onDrop).toHaveBeenCalledWith(['/path/to/file.txt'], '/target/folder')
      expect(result).toBe(true)
    })
  })

  describe('TC-UI9-002: 拖拽过程中按 Escape 取消', () => {
    it('should cancel drag when Escape is pressed', () => {
      const { startDrag, isDragging } = useDragMove({ enabled: true })

      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      // Start dragging
      startDrag(mockEvent, ['/path/to/file.txt'], document.createElement('div'))
      expect(isDragging.value).toBe(true)

      // Simulate Escape key
      const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' })
      document.dispatchEvent(escapeEvent)

      // Check that drag was ended
      expect(mockRemoveEventListener).toHaveBeenCalled()
    })

    it('should not affect non-dragging state on Escape', () => {
      const { isDragging } = useDragMove({ enabled: true })

      expect(isDragging.value).toBe(false)

      const escapeEvent = new KeyboardEvent('keydown', { key: 'Escape' })
      document.dispatchEvent(escapeEvent)

      // Should remain false (no error)
      expect(isDragging.value).toBe(false)
    })
  })

  describe('TC-UI9-003: 拖拽到无效区域自动弹回', () => {
    it('should not call onDrop when dropped on invalid target', async () => {
      const onDrop = vi.fn()

      const { handleDrop, handleDragEnter, isValidTarget } = useDragMove({
        onDrop,
        checkPermission: async () => false, // Permission denied
        enabled: true
      })

      // Start dragging
      const startEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      const { startDrag } = useDragMove({ enabled: true })
      startDrag(startEvent, ['/path/to/file.txt'], document.createElement('div'))

      // Enter invalid target
      const enterEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      await handleDragEnter(enterEvent, '/no-permission/folder')

      expect(isValidTarget.value).toBe(false)

      // Try to drop
      const dropEvent = {
        preventDefault: vi.fn()
      } as unknown as DragEvent

      const result = await handleDrop(dropEvent, '/no-permission/folder')

      expect(onDrop).not.toHaveBeenCalled()
      expect(result).toBe(false)
    })
  })

  describe('TC-UI9-004: 批量拖拽多个文件', () => {
    it('should handle multiple files drag', () => {
      const onDragStart = vi.fn()

      const { startDrag, draggedItems, isDragging } = useDragMove({
        onDragStart,
        enabled: true
      })

      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          effectAllowed: 'move',
          dropEffect: 'move',
          setData: vi.fn()
        }
      } as unknown as DragEvent

      const items = ['/path/to/file1.txt', '/path/to/file2.txt', '/path/to/file3.txt']
      startDrag(mockEvent, items, document.createElement('div'))

      expect(draggedItems.value).toEqual(items)
      expect(draggedItems.value.length).toBe(3)
      expect(onDragStart).toHaveBeenCalledWith(items)
    })

    it('should create preview showing item count for multiple items', () => {
      const { startDrag } = useDragMove({ enabled: true })

      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          effectAllowed: 'move',
          dropEffect: 'move',
          setData: vi.fn()
        }
      } as unknown as DragEvent

      const items = ['/path/to/file1.txt', '/path/to/file2.txt']
      const element = document.createElement('div')

      startDrag(mockEvent, items, element)

      // Preview text should show count
      const preview = mockEvent.dataTransfer.setData.mock.calls.find(
        call => call[0] === 'text/plain'
      )
      expect(preview).toBeDefined()
    })
  })

  describe('TC-UI9-005: 拖拽权限检查', () => {
    it('should check permission before allowing drop', async () => {
      const checkPermission = vi.fn().mockResolvedValue(true)
      const onDrop = vi.fn().mockResolvedValue(true)

      const { handleDragEnter, isValidTarget } = useDragMove({
        checkPermission,
        onDrop,
        enabled: true
      })

      // Start dragging first
      const startEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      const { startDrag } = useDragMove({ enabled: true })
      startDrag(startEvent, ['/path/to/file.txt'], document.createElement('div'))

      // Enter target with permission check
      const enterEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      await handleDragEnter(enterEvent, '/target/folder')

      expect(checkPermission).toHaveBeenCalledWith('/target/folder', 'move')
      expect(isValidTarget.value).toBe(true)
    })

    it('should reject drop when permission check fails', async () => {
      const checkPermission = vi.fn().mockResolvedValue(false)
      const onDrop = vi.fn()

      const { handleDragEnter, handleDrop, isValidTarget } = useDragMove({
        checkPermission,
        onDrop,
        enabled: true
      })

      // Start dragging
      const startEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'move' }
      } as unknown as DragEvent

      const { startDrag } = useDragMove({ enabled: true })
      startDrag(startEvent, ['/path/to/file.txt'], document.createElement('div'))

      // Enter target with permission denied
      const enterEvent = {
        preventDefault: vi.fn(),
        dataTransfer: { effectAllowed: 'move', dropEffect: 'none' }
      } as unknown as DragEvent

      await handleDragEnter(enterEvent, '/forbidden/folder')

      expect(isValidTarget.value).toBe(false)

      // Try to drop
      const dropEvent = {
        preventDefault: vi.fn()
      } as unknown as DragEvent

      const result = await handleDrop(dropEvent, '/forbidden/folder')

      expect(onDrop).not.toHaveBeenCalled()
      expect(result).toBe(false)
    })
  })

  describe('Drag State Management', () => {
    it('should reset state after drag ends', () => {
      const { startDrag, endDrag, isDragging, draggedItems, currentTarget } = useDragMove({
        enabled: true
      })

      const mockEvent = {
        preventDefault: vi.fn(),
        dataTransfer: {
          effectAllowed: 'move',
          dropEffect: 'move',
          setData: vi.fn()
        }
      } as unknown as DragEvent

      startDrag(mockEvent, ['/path/to/file.txt'], document.createElement('div'))

      expect(isDragging.value).toBe(true)
      expect(draggedItems.value).toEqual(['/path/to/file.txt'])

      endDrag()

      expect(isDragging.value).toBe(false)
      expect(draggedItems.value).toEqual([])
      expect(currentTarget.value).toBeNull()
    })

    it('should register drag source on element', () => {
      const getItems = vi.fn().mockReturnValue(['/path/to/file.txt'])
      const element = document.createElement('div')

      const { registerDragSource, startDrag } = useDragMove({ enabled: true })

      registerDragSource(element, getItems)

      // Simulate dragstart
      const dragStartEvent = new DragEvent('dragstart', {
        bubbles: true,
        cancelable: true
      })

      element.dispatchEvent(dragStartEvent)

      expect(getItems).toHaveBeenCalled()
    })
  })
})