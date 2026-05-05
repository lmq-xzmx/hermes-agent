<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="handleOverlayClick">
        <div class="modal-content" :class="sizeClass" role="dialog" aria-modal="true">
          <!-- Header -->
          <div class="modal-header" v-if="title || $slots.header">
            <slot name="header">
              <h3 class="modal-title">{{ title }}</h3>
            </slot>
            <button v-if="closable" class="modal-close" @click="close" aria-label="关闭">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="modal-body">
            <slot />
          </div>

          <!-- Footer -->
          <div class="modal-footer" v-if="$slots.footer">
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: '' },
  size: { type: String, default: 'md' }, // sm/md/lg/xl
  closable: { type: Boolean, default: true },
  closeOnOverlay: { type: Boolean, default: true }
})

const emit = defineEmits(['update:modelValue', 'close'])

const sizeClass = computed(() => `modal-${props.size}`)

function close() {
  emit('update:modelValue', false)
  emit('close')
}

function handleOverlayClick() {
  if (props.closeOnOverlay) {
    close()
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  padding: 20px;
}

.modal-content {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 100%;
  max-height: calc(100vh - 40px);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-sm { max-width: 360px; }
.modal-md { max-width: 500px; }
.modal-lg { max-width: 700px; }
.modal-xl { max-width: 900px; }

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-hairline);
  flex-shrink: 0;
}

.modal-title {
  font: var(--text-tagline);
  color: var(--color-ink);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  padding: 8px;
  margin: -8px;
  border-radius: var(--radius-sm);
  transition: background-color 0.15s ease, color 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  background: var(--color-surface-pearl);
  color: var(--color-ink);
}

.modal-close:active {
  transform: scale(0.95);
}

.modal-body {
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-hairline);
  flex-shrink: 0;
}

/* Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: scale(0.95) translateY(10px);
}
</style>
