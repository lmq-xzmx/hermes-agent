<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="visible"
        class="guidance-modal__overlay"
        @click.self="handleClose"
      >
        <div
          class="guidance-modal__dialog"
          role="dialog"
          aria-modal="true"
        >
          <!-- Header -->
          <div class="guidance-modal__header">
            <span class="guidance-modal__icon">{{ icon }}</span>
            <h3 class="guidance-modal__title">{{ title }}</h3>
            <button
              class="guidance-modal__close"
              @click="handleClose"
              aria-label="关闭"
            >×</button>
          </div>

          <!-- Body -->
          <div class="guidance-modal__body">
            <p class="guidance-message">{{ message }}</p>
            <div v-if="details" class="guidance-details">
              <code>{{ details }}</code>
            </div>
          </div>

          <!-- Footer -->
          <div class="guidance-modal__footer">
            <!-- 多个 actions -->
            <template v-if="displayActions.length > 1">
              <button
                v-for="(action, index) in displayActions"
                :key="action.label"
                :class="['guidance-action', index === 0 ? 'guidance-action--primary' : 'guidance-action--secondary']"
                @click="handleAction(action)"
              >
                <span v-if="action.icon" class="action-icon">{{ action.icon }}</span>
                <span class="action-label">{{ action.label }}</span>
              </button>
            </template>

            <!-- 单个 action -->
            <template v-else-if="displayActions.length === 1">
              <button
                class="guidance-action guidance-action--primary"
                @click="handleAction(displayActions[0])"
              >
                <span v-if="displayActions[0].icon" class="action-icon">{{ displayActions[0].icon }}</span>
                <span class="action-label">{{ displayActions[0].label }}</span>
              </button>
            </template>

            <!-- 不再显示复选框 -->
            <label v-if="onDismissType" class="guidance-dismiss-checkbox">
              <input type="checkbox" v-model="dismissForever">
              <span>不再显示</span>
            </label>

            <!-- 取消按钮（多个 actions 时显示） -->
            <button
              v-if="displayActions.length > 1"
              class="guidance-action guidance-action--secondary"
              @click="handleClose"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  // v-model
  modelValue: {
    type: Boolean,
    default: false
  },
  // 基本信息
  title: {
    type: String,
    default: '操作受限'
  },
  message: {
    type: String,
    default: ''
  },
  details: {
    type: String,
    default: ''
  },
  icon: {
    type: String,
    default: '⚠️'
  },
  // 单一 action (兼容旧接口)
  actionLabel: {
    type: String,
    default: ''
  },
  actionIcon: {
    type: String,
    default: ''
  },
  actionPath: {
    type: String,
    default: ''
  },
  actionType: {
    type: String,
    default: 'navigate'  // navigate | callback
  },
  actionCallback: {
    type: String,
    default: ''
  },
  // 多个 actions (优先级高于单一 action)
  actions: {
    type: Array,
    default: () => []
  },
  // guidance 对象 (优先级高于 actions)
  guidance: {
    type: Object,
    default: null
  },
  // 不再显示回调
  onDismissType: {
    type: Function,
    default: null
  },
  // 不再显示时传递的事件名称
  dismissEventName: {
    type: String,
    default: ''
  },
  // 是否可关闭
  closable: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'action', 'close', 'dismiss'])

const visible = ref(false)
const dismissForever = ref(false)

// 计算显示的 actions
const displayActions = computed(() => {
  // 1. actions 数组优先
  if (props.actions && props.actions.length > 0) {
    return props.actions
  }
  // 2. guidance 对象
  if (props.guidance) {
    if (Array.isArray(props.guidance)) {
      return props.guidance
    }
    if (props.guidance.label) {
      return [props.guidance]
    }
  }
  // 3. 单一 action 兼容
  if (props.actionLabel) {
    return [{
      label: props.actionLabel,
      icon: props.actionIcon,
      path: props.actionPath,
      action_type: props.actionType,
      callback: props.actionCallback
    }]
  }
  return []
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    dismissForever.value = false
    document.body.style.overflow = 'hidden'
  } else {
    document.body.style.overflow = ''
  }
}, { immediate: true })

function handleClose() {
  visible.value = false
  emit('update:modelValue', false)
  emit('close')
}

function handleAction(action) {
  // 处理不再显示
  if (dismissForever.value && props.onDismissType && props.dismissEventName) {
    props.onDismissType(props.dismissEventName)
  }

  // 执行 action
  if (action) {
    if (action.path || action.action_type === 'navigate') {
      const path = action.path || action.href
      if (path) {
        if (path.startsWith('/') || path.startsWith('#')) {
          window.location.hash = path
        } else {
          window.location.href = path
        }
      }
    } else if (action.callback || action.action_type === 'callback') {
      const callbackName = action.callback || props.actionCallback
      if (callbackName) {
        const callback = typeof callbackName === 'function'
          ? callbackName
          : window[callbackName]
        if (typeof callback === 'function') {
          callback(action)
        }
      }
    }
  }

  emit('action', action)
  visible.value = false
  emit('update:modelValue', false)
}

function handleEsc(e) {
  if (e.key === 'Escape' && visible.value && props.closable) {
    handleClose()
  }
}

// ESC 键监听
if (typeof window !== 'undefined') {
  window.addEventListener('keydown', handleEsc)
}
</script>

<style scoped>
/* ================================================
   GuidanceModal - 引导弹窗
   Apple Design System + BEM
   ================================================ */

/* Block: guidance-modal */
.guidance-modal {
  /* Overlay */
  &__overlay {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-overlay);
    z-index: var(--z-index-modal, 10000);
  }

  /* Dialog */
  &__dialog {
    width: 90%;
    max-width: 420px;
    background: var(--color-canvas);
    border: 1px solid var(--color-hairline);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-modal, 0 8px 32px rgba(0, 0, 0, 0.12));
  }

  /* Header */
  &__header {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--color-divider-soft);
  }

  /* Icon */
  &__icon {
    font-size: 32px;
    line-height: 1;
  }

  /* Title */
  &__title {
    flex: 1;
    margin: 0;
    font: var(--text-display-md);
    color: var(--color-ink);
  }

  /* Close button */
  &__close {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--color-ink-muted-48);
    font-size: 20px;
    cursor: pointer;
    transition: background-color 0.15s ease, color 0.15s ease;

    &:hover {
      background: var(--color-surface-pearl);
      color: var(--color-ink);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  /* Body */
  &__body {
    padding: var(--spacing-lg);
  }

  /* Footer */
  &__footer {
    display: flex;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    border-top: 1px solid var(--color-divider-soft);
    flex-wrap: wrap;
    align-items: center;
  }
}

/* Element: guidance-message */
.guidance-message {
  margin: 0;
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  line-height: 1.6;
}

/* Element: guidance-details */
.guidance-details {
  margin-top: var(--spacing-md);
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);

  code {
    font: var(--text-caption);
    color: var(--color-ink-muted-48);
  }
}

/* Element: guidance-action */
.guidance-action {
  flex: 1;
  min-width: 100px;
  padding: var(--spacing-sm) var(--spacing-lg);
  border: none;
  border-radius: var(--radius-pill);
  font: var(--text-body);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  transition: all 0.15s ease;

  &--primary {
    background: var(--color-primary);
    color: var(--color-on-primary);

    &:hover {
      background: var(--color-primary-focus);
    }

    &:active {
      transform: scale(0.95);
    }
  }

  &--secondary {
    background: transparent;
    color: var(--color-primary);
    border: 1px solid var(--color-primary);

    &:hover {
      background: var(--color-primary);
      color: var(--color-on-primary);
    }

    &:active {
      transform: scale(0.95);
    }
  }
}

/* Element: action-icon */
.action-icon {
  font-size: 16px;
}

/* Element: guidance-dismiss-checkbox */
.guidance-dismiss-checkbox {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: 0 var(--spacing-xs);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  cursor: pointer;
  white-space: nowrap;

  input[type="checkbox"] {
    width: 16px;
    height: 16px;
    cursor: pointer;
    accent-color: var(--color-primary);
  }
}

/* Transition: modal */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;

  .guidance-modal__dialog {
    transition: transform 0.2s ease, opacity 0.2s ease;
  }
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;

  .guidance-modal__dialog {
    transform: scale(0.95);
    opacity: 0;
  }
}
</style>