<template>
  <Teleport to="body">
    <Transition name="toast">
      <div v-if="visible" class="toast" :class="type" role="alert">
        <span class="toast-icon">{{ iconMap[type] }}</span>
        <span class="toast-message">{{ message }}</span>
        <button v-if="closable" class="toast-close" @click="close" aria-label="关闭">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M10.5 3.5L3.5 10.5M3.5 3.5L10.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

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
.toast {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 20px;
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-radius: var(--radius-pill);
  font-family: var(--font-body);
  font-size: 15px;
  line-height: 1.4;
  z-index: var(--z-toast);
  display: flex;
  align-items: center;
  gap: 10px;
  max-width: calc(100vw - 48px);
  box-shadow: var(--shadow-lg);
}

.toast.info {
  background: var(--color-ink);
}

.toast.success {
  background: var(--color-success);
}

.toast.error {
  background: var(--color-danger);
}

.toast.warning {
  background: var(--color-warning);
}

.toast-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.toast-message {
  flex: 1;
}

.toast-close {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  padding: 4px;
  margin-left: 4px;
  opacity: 0.7;
  transition: opacity 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toast-close:hover {
  opacity: 1;
}

.toast-close:active {
  transform: scale(0.95);
}

/* Transitions */
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}
</style>
