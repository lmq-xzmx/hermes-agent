<template>
  <Teleport to="body">
    <div v-if="visible" class="context-menu-overlay" @click="close" @contextmenu.prevent="close">
      <div
        class="context-menu"
        :style="{ left: x + 'px', top: y + 'px' }"
        @click.stop
      >
        <template v-for="(item, index) in displayItems" :key="item.id || 'sep-' + index">
          <div v-if="item.separator" class="divider"></div>
          <div
            v-else
            class="item"
            :class="getItemClass(item)"
            @click="isItemDisabled(item) ? null : handleAction(item.id)"
          >
            <span class="icon">{{ item.icon }}</span>
            <span class="label">{{ item.label }}</span>
            <span v-if="item.shortcut" class="shortcut">{{ item.shortcut }}</span>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useContextMenu, DEFAULT_ITEMS } from '@/composables/useContextMenu.js'

const props = defineProps({
  canPaste: {
    type: Boolean,
    default: false
  },
  canWrite: {
    type: Boolean,
    default: true
  },
  canDelete: {
    type: Boolean,
    default: true
  },
  canRename: {
    type: Boolean,
    default: true
  },
  items: {
    type: Array,
    default: null
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
  'delete',
  'action'
])

const visible = ref(false)
const x = ref(0)
const y = ref(0)

const displayItems = computed(() => {
  return props.items || DEFAULT_ITEMS
})

// 判断菜单项是否应被禁用
function isItemDisabled(item) {
  if (item.disabled) return true

  switch (item.id) {
    case 'paste':
      return !props.canPaste
    case 'rename':
      return !props.canRename
    case 'delete':
      return !props.canDelete
    case 'share':
      return false // 任何成员都可以分享
    case 'copy':
    case 'cut':
      return false // 任何人都可以复制/剪切
    default:
      return false
  }
}

// 获取菜单项的 class
function getItemClass(item) {
  const classes = []

  if (isItemDisabled(item)) {
    classes.push('item--disabled')
  }

  if (item.id === 'delete' && !isItemDisabled(item)) {
    classes.push('item--danger')
  }

  return classes.join(' ')
}

function show(event, data) {
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

function handleAction(actionId) {
  emit('action', actionId)
  if (actionId === 'open-in-finder') {
    emit('open-in-finder')
  } else if (actionId) {
    emit(actionId)
  }
  close()
}

function handleGlobalClick(e) {
  if (visible.value && !e.target.closest('.context-menu')) {
    close()
  }
}

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
/* ============================================
   FileContextMenu — 右键菜单
   DESIGN.md Apple Design System
   ============================================ */

.context-menu-overlay {
  position: fixed;
  inset: 0;
  z-index: var(--z-dropdown, 100);
}

.context-menu {
  position: fixed;
  min-width: 200px;
  background-color: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md);
  padding: var(--spacing-xxs) 0;
  font: 400 17px/1.47 var(--font-family-text);
  color: var(--color-body-on-dark);
  box-shadow: var(--shadow-md);
}

.item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  height: 36px;
  padding: var(--spacing-xs) var(--spacing-sm);
  margin: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast);
}

.item:hover:not(.item--disabled) {
  background-color: var(--color-surface-tile-2);
}

.item--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.item--danger {
  color: var(--color-danger);
}

.item--danger:hover:not(.item--disabled) {
  background-color: var(--color-danger-subtle);
}

.icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.label {
  flex: 1;
}

.shortcut {
  font-size: 12px;
  line-height: 1.0;
  letter-spacing: -0.12px;
  color: var(--color-body-muted);
  opacity: 0.7;
  flex-shrink: 0;
}

.divider {
  height: 1px;
  background-color: var(--color-border-on-dark);
  margin: var(--spacing-xxs) 0;
}
</style>