<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="visible" class="guidance-modal-overlay" @click.self="handleClose">
        <div class="guidance-modal-dialog" role="dialog" aria-modal="true">
          <div class="guidance-modal-header">
            <span class="guidance-icon">{{ icon }}</span>
            <h3 class="guidance-title">{{ title }}</h3>
            <button class="guidance-close" @click="handleClose" aria-label="关闭">×</button>
          </div>

          <div class="guidance-modal-body">
            <p class="guidance-message">{{ message }}</p>
            <div v-if="details" class="guidance-details">
              <code>{{ details }}</code>
            </div>
          </div>

          <div class="guidance-modal-footer">
            <!-- 多个 actions -->
            <template v-if="displayActions.length > 1">
              <button
                v-for="(action, index) in displayActions"
                :key="action.label"
                :class="['guidance-action', index === 0 ? 'primary' : 'secondary']"
                @click="handleAction(action)"
              >
                <span v-if="action.icon" class="action-icon">{{ action.icon }}</span>
                <span class="action-label">{{ action.label }}</span>
              </button>
            </template>
            <!-- 单个 action -->
            <template v-else-if="displayActions.length === 1">
              <button class="guidance-action primary" @click="handleAction(displayActions[0])">
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
            <button v-if="displayActions.length > 1" class="guidance-action secondary" @click="handleClose">
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
.guidance-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.guidance-modal-dialog {
  background: var(--bg-primary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 12px;
  width: 90%;
  max-width: 420px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.4);
}

.guidance-modal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border, #30363d);
}

.guidance-icon {
  font-size: 28px;
  line-height: 1;
}

.guidance-title {
  flex: 1;
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.guidance-close {
  background: none;
  border: none;
  color: var(--text-secondary, #8b949e);
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
}

.guidance-close:hover {
  background: var(--bg-secondary, #21262d);
  color: var(--text-primary, #e6edf3);
}

.guidance-modal-body {
  padding: 24px;
}

.guidance-message {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary, #8b949e);
}

.guidance-details {
  margin-top: 12px;
  padding: 8px 12px;
  background: var(--bg-tertiary, #0d1117);
  border-radius: 6px;
}

.guidance-details code {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  font-family: monospace;
}

.guidance-modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border, #30363d);
  flex-wrap: wrap;
  align-items: center;
}

.guidance-action {
  flex: 1;
  min-width: 100px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.guidance-action.primary {
  background: var(--accent-primary, #238636);
  color: #ffffff;
}

.guidance-action.primary:hover {
  background: var(--accent-primary-hover, #2ea043);
}

.guidance-action.secondary {
  background: var(--bg-secondary, #21262d);
  color: var(--text-primary, #e6edf3);
  border-color: var(--border, #30363d);
}

.guidance-action.secondary:hover {
  background: var(--bg-tertiary, #30363d);
}

.action-icon {
  font-size: 16px;
}

.guidance-dismiss-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  cursor: pointer;
  padding: 0 4px;
  white-space: nowrap;
}

.guidance-dismiss-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .guidance-modal-dialog,
.modal-leave-active .guidance-modal-dialog {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .guidance-modal-dialog,
.modal-leave-to .guidance-modal-dialog {
  transform: scale(0.95);
  opacity: 0;
}
</style>
