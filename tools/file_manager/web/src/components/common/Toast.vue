<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast" :class="`toast--${type}`" role="alert">
        <span class="toast__icon">{{ iconMap[type] }}</span>
        <span class="toast__message">{{ message }}</span>
        <button v-if="closable" class="toast__close" @click="close" aria-label="关闭">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
const props = defineProps({
  visible: { type: Boolean, default: false },
  type: { type: String, default: 'info' }, // info/success/error/warning
  message: { type: String, required: true },
  closable: { type: Boolean, default: true },
  duration: { type: Number, default: 3000 }
})

const emit = defineEmits(['close', 'update:visible'])

const iconMap = {
  info: 'ℹ️',
  success: '✓',
  error: '✕',
  warning: '⚠'
}

function close() {
  emit('update:visible', false)
  emit('close')
}
</script>

<style scoped>
/* ============================================
   Toast - Apple Design System
   ============================================ */

.toast {
  /* Layout */
  position: fixed;
  bottom: var(--spacing-xl);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);

  /* Visual */
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);

  /* Z-Index */
  z-index: var(--z-toast);

  /* Animation */
  transition: transform 0.2s ease, opacity 0.2s ease;
}

/* Type Variants */
.toast--success {
  background: var(--color-success);
  color: var(--color-on-primary);
}

.toast--error {
  background: var(--color-danger);
  color: var(--color-on-primary);
}

.toast--warning {
  background: var(--color-warning);
  color: var(--color-ink);
}

.toast--info {
  background: var(--color-ink);
  color: var(--color-body-on-dark);
}

/* ============================================
   Element: toast__icon
   ============================================ */
.toast__icon {
  font-size: 18px;
}

/* ============================================
   Element: toast__message
   ============================================ */
.toast__message {
  /* Typography */
  font: var(--text-body);

  /* Layout */
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ============================================
   Element: toast__close
   ============================================ */
.toast__close {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Visual */
  background: transparent;
  border: none;
  color: inherit;
  opacity: 0.7;
  cursor: pointer;

  /* Animation */
  transition: opacity 0.15s ease, transform 0.1s ease;
}

.toast__close:hover {
  opacity: 1;
}

.toast__close:active {
  transform: scale(0.95);
}

/* ============================================
   Transition Animations
   ============================================ */
.toast-enter-active,
.toast-leave-active {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  transform: translateX(-50%) translateY(20px);
  opacity: 0;
}
</style>