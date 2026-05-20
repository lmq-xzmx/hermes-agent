<template>
  <div class="form-field">
    <label v-if="label" class="form-field__label" :for="inputId">
      {{ label }}
      <span v-if="required" class="form-field__required">*</span>
    </label>
    <div class="form-field__body">
      <slot>
        <input
          :id="inputId"
          class="form-field__input"
          :class="{ 'form-field__input--error': error }"
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
    <p v-if="hint && !error" class="form-field__hint">{{ hint }}</p>
    <p v-if="error" class="form-field__error">{{ error }}</p>
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
/* ============================================
   FormField - Apple Design System
   ============================================ */

.form-field {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);

  /* Spacing */
  margin-bottom: var(--spacing-md);
}

/* ============================================
   Element: form-field__label
   ============================================ */
.form-field__label {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  /* Layout */
  display: block;
}

/* ============================================
   Element: form-field__required
   ============================================ */
.form-field__required {
  color: var(--color-danger);
}

/* ============================================
   Element: form-field__input
   ============================================ */
.form-field__input {
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

.form-field__input::placeholder {
  color: var(--color-ink-muted-48);
}

.form-field__input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-faint);
}

.form-field__input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--color-canvas-parchment);
}

.form-field__input--error {
  border-color: var(--color-danger);
}

.form-field__input--error:focus {
  box-shadow: 0 0 0 3px var(--color-danger-subtle);
}

/* ============================================
   Element: form-field__hint
   ============================================ */
.form-field__hint {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  /* Layout */
  margin: 0;
}

/* ============================================
   Element: form-field__error
   ============================================ */
.form-field__error {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-danger);

  /* Layout */
  margin: 0;
}
</style>