<template>
  <div class="dropdown-item" :class="{ disabled, danger }" @click="handleClick">
    <span v-if="icon" class="dropdown-item-icon">{{ icon }}</span>
    <slot />
    <span v-if="label" class="dropdown-item-label">{{ label }}</span>
    <span v-if="badge" class="dropdown-item-badge">{{ badge }}</span>
  </div>
</template>

<script setup>
const props = defineProps({
  disabled: { type: Boolean, default: false },
  danger: { type: Boolean, default: false },
  icon: { type: String, default: '' },
  label: { type: String, default: '' },
  badge: { type: [String, Number], default: null }
})

const emit = defineEmits(['click'])

function handleClick() {
  if (!props.disabled) {
    emit('click')
  }
}
</script>

<style scoped>
.dropdown-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 10px 12px;
  border-radius: var(--radius-md);
  font-family: var(--font-family-text);
  font-size: 15px;
  color: var(--color-ink);
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.dropdown-item:hover:not(.disabled) {
  background: var(--color-surface-pearl);
}

.dropdown-item:active:not(.disabled) {
  transform: scale(0.98);
}

.dropdown-item.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.dropdown-item.danger {
  color: var(--color-danger);
}

.dropdown-item.danger:hover:not(.disabled) {
  background: var(--color-danger-hover);
}

.dropdown-item-icon {
  font-size: 16px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.dropdown-item-label {
  flex: 1;
}

.dropdown-item-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: var(--color-surface-pearl);
  border-radius: var(--radius-pill);
  color: var(--color-ink-muted-48);
}
</style>
