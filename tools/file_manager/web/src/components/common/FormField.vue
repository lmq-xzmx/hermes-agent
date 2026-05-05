<template>
  <div class="form-field">
    <label v-if="label" class="field-label" :for="inputId">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </label>
    <div class="field-body">
      <slot>
        <input
          :id="inputId"
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
      </slot>
    </div>
    <p v-if="hint && !error" class="field-hint">{{ hint }}</p>
    <p v-if="error" class="field-error">{{ error }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  label: {
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
  hint: {
    type: String,
    default: ''
  },
  error: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  id: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue', 'focus', 'blur'])

const inputId = computed(() => props.id || `field-${Math.random().toString(36).substr(2, 9)}`)
</script>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-family: var(--font-family-text);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--color-ink);
}

.required-mark {
  color: var(--color-danger);
  margin-left: 2px;
}

.field-body {
  width: 100%;
}

.apple-text-input {
  width: 100%;
  height: 44px;
  padding: 11px 15px;
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

.field-hint {
  font-family: var(--font-family-text);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--color-ink-muted-48);
  margin: 0;
}

.field-error {
  font-family: var(--font-family-text);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.43;
  letter-spacing: -0.224px;
  color: var(--color-danger);
  margin: 0;
}
</style>
