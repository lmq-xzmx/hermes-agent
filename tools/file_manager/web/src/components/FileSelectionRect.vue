<template>
  <div
    v-if="rect"
    class="selection-rect"
    :style="{
      left: rect.left + 'px',
      top: rect.top + 'px',
      width: rect.width + 'px',
      height: rect.height + 'px'
    }"
  ></div>
</template>

<script setup>
defineProps({
  rect: {
    type: Object,
    default: null
    // { left, top, width, height }
  }
})
</script>

<style scoped>
.selection-rect {
  position: fixed;
  background: rgba(0, 122, 255, 0.2);
  border: 1px solid rgba(0, 122, 255, 0.5);
  border-radius: 4px;
  pointer-events: none;
  z-index: 1000;
}
</style>