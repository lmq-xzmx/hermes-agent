<template>
  <input
    class="apple-text-input"
    :class="{ 'has-error': error }"
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
.apple-text-input {
  width: 100%;
  height: 44px;
  padding: var(--spacing-sm) var(--spacing-md);
  background-color: var(--color-canvas);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.apple-text-input::placeholder {
  color: var(--color-ink-muted-48);
}

.apple-text-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-hover);
}

.apple-text-input:disabled {
  background-color: var(--color-surface-pearl);
  color: var(--color-ink-muted-48);
  cursor: not-allowed;
}

.apple-text-input.has-error {
  border-color: var(--color-danger);
}

.apple-text-input.has-error:focus {
  box-shadow: 0 0 0 3px var(--color-danger-subtle);
}
</style>
