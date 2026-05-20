<template>
  <div class="color-picker">
    <!-- Color Swatch Preview -->
    <div class="color-picker__swatch" :style="{ backgroundColor: modelValue }"></div>

    <!-- Token Name -->
    <span class="color-picker__token">{{ tokenName }}</span>

    <!-- Color Input + Hex Input -->
    <div class="color-picker__controls">
      <input
        type="color"
        class="color-picker__input"
        :value="modelValue"
        @input="handleColorInput"
      />
      <input
        type="text"
        class="color-picker__hex"
        :value="modelValue"
        @input="handleHexInput"
        @blur="validateHex"
        placeholder="#000000"
      />
    </div>

    <!-- Reset Button -->
    <button
      v-if="isModified"
      class="color-picker__reset"
      @click="handleReset"
      title="重置为默认值"
    >
      ↺
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  token: { type: String, required: true },
  modelValue: { type: String, default: '' },
  defaultValue: { type: String, default: '' }
})

const emit = defineEmits(['update:modelValue', 'reset'])

const tokenName = computed(() => {
  // 简化 token 显示名称
  return props.token.replace('--color-', '').replace(/-/g, ' ')
})

const isModified = computed(() => {
  return props.modelValue !== props.defaultValue
})

function handleColorInput(event) {
  emit('update:modelValue', event.target.value)
}

function handleHexInput(event) {
  let value = event.target.value.trim()
  if (!value.startsWith('#')) {
    value = '#' + value
  }
  emit('update:modelValue', value)
}

function validateHex(event) {
  // 确保 hex 值合法
  const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/
  if (!hexRegex.test(event.target.value)) {
    event.target.value = props.modelValue
  }
}

function handleReset() {
  emit('reset', props.token)
  emit('update:modelValue', props.defaultValue)
}
</script>

<style scoped>
.color-picker {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-sm);

  /* Box Model */
  padding: var(--spacing-sm) var(--space-md);
}

.color-picker__swatch {
  /* Layout */
  flex-shrink: 0;

  /* Box Model */
  width: 32px;
  height: 32px;

  /* Visual */
  border-radius: var(--radius-md);
  border: 1px solid var(--color-hairline);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.06);

  /* Sizing */
  box-sizing: border-box;
}

.color-picker__token {
  /* Text */
  font: var(--text-caption);
  color: var(--color-ink);

  /* Sizing */
  min-width: 120px;
  max-width: 180px;

  /* Layout */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.color-picker__controls {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex: 1;
  justify-content: flex-end;
}

.color-picker__input {
  /* Box Model */
  width: 36px;
  height: 36px;
  padding: 0;

  /* Visual */
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  cursor: pointer;

  /* Appearance */
  appearance: none;
  -webkit-appearance: none;
  background: none;
}

.color-picker__input::-webkit-color-swatch-wrapper {
  padding: 2px;
}

.color-picker__input::-webkit-color-swatch {
  /* Visual */
  border: none;
  border-radius: var(--radius-sm);
}

.color-picker__hex {
  /* Box Model */
  width: 90px;
  height: 36px;
  padding: var(--spacing-xs) var(--space-sm);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);

  /* Text */
  font: var(--text-caption);
  font-family: var(--font-family-text);
  color: var(--color-ink);
  letter-spacing: 0.5px;

  /* Layout */
  text-align: center;
}

.color-picker__hex:focus {
  /* Visual */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

.color-picker__reset {
  /* Box Model */
  width: 32px;
  height: 32px;
  padding: 0;

  /* Visual */
  background: none;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  color: var(--color-ink-muted-48);
  cursor: pointer;

  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;

  /* Transition */
  transition: all 0.15s ease;
}

.color-picker__reset:hover {
  /* Visual */
  background: var(--color-canvas-parchment);
  color: var(--color-ink);
  border-color: var(--color-secondary);
}

.color-picker__reset:focus-visible {
  /* Visual */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}
</style>