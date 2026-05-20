<template>
  <span class="chip" :class="{ selected }">
    <slot />
    <button v-if="closable" class="chip-close" @click.stop="$emit('close')" aria-label="关闭">
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path d="M9 3L3 9M3 3L9 9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
      </svg>
    </button>
  </span>
</template>

<script setup>
defineProps({
  selected: { type: Boolean, default: false },
  closable: { type: Boolean, default: false }
})

defineEmits(['close'])
</script>

