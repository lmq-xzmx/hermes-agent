<template>
  <input
    class="text-input"
    :class="{ 'text-input--error': error }"
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    @input="$emit('update:modelValue', $event.target.value)"
    @focus="$emit('focus', $event)"
    @blur="$emit('blur', $event)"
  >
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  }
})

defineEmits(['update:modelValue', 'focus', 'blur'])
</script>

<style scoped>
/* ============================================
   TextInput - Apple Design System
   Based on DESIGN.md search-input component
   ============================================ */

.text-input {
  /* Box Model */
  width: 100%;
  height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
  box-sizing: border-box;

  /* Visual */
  background: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);

  /* Typography */
  font: var(--text-body);

  /* Interactive */
  outline: none;
  cursor: text;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

/* Placeholder */
.text-input::placeholder {
  color: var(--color-ink-muted-48);
}

/* Focus State */
.text-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-faint);
}

/* Disabled State */
.text-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-canvas-parchment);
}

/* Error State */
.text-input--error {
  border-color: var(--color-danger);
}

.text-input--error:focus {
  box-shadow: 0 0 0 3px var(--color-danger-subtle);
}
</style>