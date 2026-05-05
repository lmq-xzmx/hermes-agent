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
        <div class="context-menu-item" @click="handleAction('open-in-finder')">
          <span class="menu-icon">📍</span>
          <span class="menu-label">在 Finder 中显示</span>
        </div>
        <div class="context-menu-divider"></div>
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
        <div class="context-menu-item" :class="{ disabled: !canPaste }" @click="canPaste && handleAction('paste')">
          <span class="menu-icon">📥</span>
          <span class="menu-label">粘贴</span>
          <span class="menu-shortcut">Ctrl+V</span>
        </div>
        <div class="context-menu-divider"></div>
        <div class="context-menu-item" @click="handleAction('share')">
          <span class="menu-icon">🔗</span>
          <span class="menu-label">分享</span>
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
import { ref } from 'vue'

const props = defineProps({
  canPaste: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'open',
  'open-in-finder',
  'rename',
  'copy',
  'cut',
  'paste',
  'share',
  'delete'
])

const visible = ref(false)
const x = ref(0)
const y = ref(0)

function show(event, data) {
  // Calculate position
  const menuWidth = 200
  const menuHeight = 340

  let newX = event.clientX
  let newY = event.clientY

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
}

function handleAction(action) {
  emit(action)
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

if (typeof window !== 'undefined') {
  document.addEventListener('click', handleGlobalClick)
  document.addEventListener('keydown', handleKeydown)
}

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
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md, 11px);
  padding: var(--spacing-xxs, 4px) 0;
  z-index: 10000;
  box-shadow: var(--shadow-product);
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

.context-menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.context-menu-item.danger {
  color: var(--color-danger, #ff3b30);
}

.context-menu-item.danger:hover {
  background: var(--color-danger-subtle);
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
  background: var(--color-border-on-dark);
  margin: var(--spacing-xxs, 4px) 0;
}
</style>
