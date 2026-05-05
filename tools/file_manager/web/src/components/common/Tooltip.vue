<template>
  <div class="tooltip-wrapper" @mouseenter="show" @mouseleave="hide" @focus="show" @blur="hide">
    <slot />
    <Transition name="tooltip">
      <div v-if="visible && content" class="tooltip" :class="position" role="tooltip">
        {{ content }}
        <div class="tooltip-arrow"></div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  content: { type: String, default: '' },
  position: { type: String, default: 'top' }, // top/bottom/left/right
  delay: { type: Number, default: 200 }
})

const visible = ref(false)
let timeout = null

function show() {
  timeout = setTimeout(() => {
    visible.value = true
  }, delay)
}

function hide() {
  clearTimeout(timeout)
  visible.value = false
}
</script>

<script>
const delay = 200
</script>

<style scoped>
.tooltip-wrapper {
  position: relative;
  display: inline-flex;
}

.tooltip {
  position: absolute;
  padding: 8px 12px;
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 13px;
  line-height: 1.4;
  white-space: nowrap;
  z-index: var(--z-tooltip);
  pointer-events: none;
  box-shadow: var(--shadow-md);
}

.tooltip.top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.tooltip.bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}

.tooltip.left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.tooltip.right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.tooltip-arrow {
  position: absolute;
  width: 8px;
  height: 8px;
  background: var(--color-ink);
  transform: rotate(45deg);
}

.tooltip.top .tooltip-arrow {
  bottom: -4px;
  left: 50%;
  margin-left: -4px;
}

.tooltip.bottom .tooltip-arrow {
  top: -4px;
  left: 50%;
  margin-left: -4px;
}

.tooltip.left .tooltip-arrow {
  right: -4px;
  top: 50%;
  margin-top: -4px;
}

.tooltip.right .tooltip-arrow {
  left: -4px;
  top: 50%;
  margin-top: -4px;
}

/* Transitions */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}

.tooltip.top.tooltip-enter-from,
.tooltip.top.tooltip-leave-to {
  transform: translateX(-50%) translateY(4px);
}

.tooltip.bottom.tooltip-enter-from,
.tooltip.bottom.tooltip-leave-to {
  transform: translateX(-50%) translateY(-4px);
}
</style>
