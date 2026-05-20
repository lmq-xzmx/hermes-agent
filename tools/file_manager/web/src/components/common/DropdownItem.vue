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

