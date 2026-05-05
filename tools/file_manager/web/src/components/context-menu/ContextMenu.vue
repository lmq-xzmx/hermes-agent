<template>
  <Teleport to="body">
    <div v-if="visible" class="context-menu-overlay" @click="close" @contextmenu.prevent="close">
      <div
        class="context-menu"
        :style="{ left: x + 'px', top: y + 'px' }"
        @click.stop
      >
        <div class="context-menu-item" @click="handleAction('open')">
          <span class="menu-icon">📂</span>
          <span class="menu-label">打开</span>
          <span class="menu-shortcut">Enter</span>
        </div>
        <div class="context-menu-item" @click="handleAction('rename')">
          <span class="menu-icon">✏️</span>
          <span class="menu-label">重命名</span>
          <span class="menu-shortcut">F2</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" @click="handleAction('copy')">
          <span class="menu-icon">📋</span>
          <span class="menu-label">复制</span>
          <span class="menu-shortcut">Ctrl+C</span>
        </div>
        <div class="context-menu-item" @click="handleAction('cut')">
          <span class="menu-icon">✂️</span>
          <span class="menu-label">剪切</span>
          <span class="menu-shortcut">Ctrl+X</span>
        </div>
        <div class="context-menu-item" @click="handleAction('paste')">
          <span class="menu-icon">📥</span>
          <span class="menu-label">粘贴</span>
          <span class="menu-shortcut">Ctrl+V</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" @click="handleAction('share')">
          <span class="menu-icon">🔗</span>
          <span class="menu-label">分享</span>
        </div>
        <div class="context-menu-item" @click="handleAction('download')">
          <span class="menu-icon">⬇️</span>
          <span class="menu-label">下载</span>
        </div>
        <div class="context-menu-item" @click="handleAction('showInFinder')">
          <span class="menu-icon">📍</span>
          <span class="menu-label">在 Finder 中显示</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item danger" @click="handleAction('delete')">
          <span class="menu-icon">🗑️</span>
          <span class="menu-label">删除</span>
          <span class="menu-shortcut">Del</span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { ContextMenuItem, FileItem } from '@/types/context-menu'

const props = defineProps<{
  items?: ContextMenuItem[]
}>()

const emit = defineEmits<{
  (e: 'action', item: ContextMenuItem, target: FileItem): void
  (e: 'hide'): void
}>()

// 默认菜单项（当未传入 items 时使用）
const defaultItems: ContextMenuItem[] = [
  { id: 'open', label: '打开', icon: '📂', shortcut: 'Enter' },
  { id: 'rename', label: '重命名', icon: '✏️', shortcut: 'F2' },
  { id: 'copy', label: '复制', icon: '📋', shortcut: 'Ctrl+C' },
  { id: 'cut', label: '剪切', icon: '✂️', shortcut: 'Ctrl+X' },
  { id: 'paste', label: '粘贴', icon: '📥', shortcut: 'Ctrl+V' },
  { id: 'share', label: '分享', icon: '🔗' },
  { id: 'delete', label: '删除', icon: '🗑️', danger: true, shortcut: 'Del' },
]

const menuItems = computed<ContextMenuItem[]>(() => props.items || defaultItems)

function show(event, data) {
  fileData.value = data
  targetEl.value = event.target

  // Calculate position
  const menuWidth = 200
  const menuHeight = 320

  let newX = event.clientX
  let newY = event.clientY

  // Prevent menu from going off-screen
  if (newX + menuWidth > window.innerWidth) {
    newX = window.innerWidth - menuWidth - 8
  }
  if (newY + menuHeight > window.innerHeight) {
    newY = window.innerHeight - menuHeight - 8
  }

  x.value = newX
  y.value = newY
  visible.value = true
}

function close() {
  visible.value = false
  fileData.value = null
  targetEl.value = null
}

function handleAction(action) {
  emit('action', { action, file: fileData.value })
  close()
}

// Global click handler to close menu
function handleGlobalClick(e) {
  if (visible.value && !e.target.closest('.context-menu')) {
    close()
  }
}

// Escape key to close
function handleKeydown(e) {
  if (e.key === 'Escape') {
    close()
  }
}

onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({
  show,
  close
})
</script>

<style scoped>
.context-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.context-menu {
  position: fixed;
  min-width: 200px;
  background: var(--color-surface-tile-2, #2a2a2c);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md, 11px);
  padding: var(--spacing-xxs, 4px) 0;
  z-index: 10000;
  box-shadow: rgba(0, 0, 0, 0.22) 3px 5px 30px 0;
}

.context-menu-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  height: 36px;
  cursor: pointer;
  transition: background 0.15s ease;
  gap: var(--spacing-sm, 8px);
  border-radius: var(--radius-sm, 8px);
  margin: 2px 6px;
}

.context-menu-item:hover {
  background: var(--color-surface-tile-1, #272729);
}

.context-menu-item.danger {
  color: var(--color-danger, #ff3b30);
}

.context-menu-item.danger:hover {
  background: rgba(255, 59, 48, 0.15);
}

.menu-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
}

.menu-label {
  flex: 1;
  font-family: var(--font-body);
  font-size: 15px;
  color: var(--color-body-on-dark, #ffffff);
}

.menu-shortcut {
  font-family: var(--font-body);
  font-size: 12px;
  color: var(--color-body-muted, #cccccc);
  opacity: 0.7;
  letter-spacing: -0.224px;
}

.context-menu-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: var(--spacing-xxs, 4px) 0;
}
</style>
