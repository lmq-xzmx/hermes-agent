<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click.self="handleOverlayClick">
        <div class="modal" :class="`modal--${size}`" role="dialog" aria-modal="true">
          <!-- Header -->
          <div v-if="title || $slots.header" class="modal__header">
            <slot name="header">
              <h3 class="modal__title">{{ title }}</h3>
            </slot>
            <button v-if="closable" class="modal__close" @click="close" aria-label="关闭">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M13.5 4.5L4.5 13.5M4.5 4.5L13.5 13.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="modal__body">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="modal__footer">
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

const sizeClass = computed(() => `modal--${props.size}`)

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
/* ============================================
   Modal - Apple Design System
   ============================================ */

/* Overlay */
.modal-overlay {
  /* Layout */
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  /* Visual */
  background: var(--color-overlay);
  z-index: var(--z-modal-backdrop);
}

/* Modal Container */
.modal {
  /* Layout */
  display: flex;
  flex-direction: column;

  /* Visual */
  background: var(--color-canvas);
  border-radius: var(--radius-lg);

  /* Box Model */
  max-height: 80vh;
  overflow: hidden;

  /* Animation */
  transition: transform 0.2s ease, opacity 0.2s ease;
}

/* Size Variants */
.modal--sm { width: 90%; max-width: 400px; }
.modal--md { width: 90%; max-width: 500px; }
.modal--lg { width: 90%; max-width: 700px; }
.modal--xl { width: 90%; max-width: 900px; }

/* ============================================
   Element: modal__header
   ============================================ */
.modal__header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;

  /* Box Model */
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
  flex-shrink: 0;
}

/* ============================================
   Element: modal__title
   ============================================ */
.modal__title {
  /* Typography */
  font: var(--text-body-strong);
  color: var(--color-ink);

  /* Layout */
  margin: 0;
}

/* ============================================
   Element: modal__close
   ============================================ */
.modal__close {
  /* Visual */
  background: none;
  border: none;
  color: var(--color-ink-muted-48);
  cursor: pointer;

  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxs);

  /* Animation */
  transition: color 0.15s ease, transform 0.1s ease;
}

.modal__close:hover {
  color: var(--color-ink);
}

.modal__close:active {
  transform: scale(0.95);
}

/* ============================================
   Element: modal__body
   ============================================ */
.modal__body {
  /* Layout */
  padding: var(--spacing-lg);
  overflow-y: auto;
  flex: 1;
}

/* ============================================
   Element: modal__footer
   ============================================ */
.modal__footer {
  /* Layout */
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;

  /* Box Model */
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
  flex-shrink: 0;
}

/* ============================================
   Transition Animations
   ============================================ */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal,
.modal-leave-active .modal {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal,
.modal-leave-to .modal {
  transform: scale(0.95);
  opacity: 0;
}
</style>