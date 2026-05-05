<template>
  <Teleport to="body">
    <div v-if="visible" class="context-menu-overlay" @click="close" @contextmenu.prevent="close">
      <div
        class="context-menu"
        :style="{ left: x + 'px', top: y + 'px' }"
        @click.stop
      >
        <template v-for="(item, index) in displayItems" :key="item.id || 'sep-' + index">
          <div v-if="item.separator" class="context-menu-divider"></div>
          <div
            v-else
            class="context-menu-item"
            :class="{ disabled: item.disabled || (item.id === 'paste' && !canPaste) }"
            @click="item.disabled || (item.id === 'paste' && !canPaste) ? null : handleAction(item.id)"
          >
            <span class="menu-icon">{{ item.icon }}</span>
            <span class="menu-label">{{ item.label }}</span>
            <span v-if="item.shortcut" class="menu-shortcut">{{ item.shortcut }}</span>
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
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-md);
  padding: var(--spacing-xxs) 0;
  z-index: 10000;
}

.context-menu-item {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  height: 36px;
  cursor: pointer;
  transition: background 0.15s ease;
  gap: var(--spacing-sm);
  border-radius: var(--radius-md);
  margin: 2px 6px;
}

.context-menu-item:hover {
  background: var(--color-surface-tile-1);
}

.context-menu-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.context-menu-item.danger {
  color: var(--color-danger);
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
  font-family: var(--font-family-text);
  font-size: 15px;
  color: var(--color-body-on-dark);
}

.menu-shortcut {
  font-family: var(--font-family-text);
  font-size: 12px;
  color: var(--color-body-muted);
  opacity: 0.7;
  letter-spacing: -0.224px;
}

.context-menu-divider {
  height: 1px;
  background: var(--color-border-on-dark);
  margin: var(--spacing-xxs) 0;
}
</style>
