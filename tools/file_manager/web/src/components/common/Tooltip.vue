<template>
  <div class="tooltip" @mouseenter="show" @mouseleave="hide" @focus="show" @blur="hide">
    <slot />
    <Transition name="tooltip">
      <div v-if="visible && content" class="tooltip__content" :class="`tooltip__content--${position}`" role="tooltip">
        {{ content }}
        <div class="tooltip__arrow"></div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  content: { type: String, default: '' },
  position: { type: String, default: 'top' }, // top/bottom/left/right
  delay: { type: Number, default: 200 }
})

const visible = ref(false)
let timeout = null

function show() {
  timeout = setTimeout(() => {
    visible.value = true
  }, props.delay)
}

function hide() {
  clearTimeout(timeout)
  visible.value = false
}
</script>

<style scoped>
/* ============================================
   Tooltip - Apple Design System
   ============================================ */

.tooltip {
  /* Layout */
  position: relative;
  display: inline-block;
}

/* ============================================
   Element: tooltip__content
   ============================================ */
.tooltip__content {
  /* Layout */
  position: absolute;
  z-index: var(--z-tooltip);
  display: flex;
  flex-direction: column;
  align-items: center;

  /* Box Model */
  padding: var(--spacing-xs) var(--spacing-sm);
  white-space: nowrap;

  /* Visual */
  background: var(--color-ink);
  color: var(--color-body-on-dark);
  border-radius: var(--radius-sm);

  /* Animation */
  transition: opacity 0.15s ease, transform 0.15s ease;
}

/* Position Variants */
.tooltip__content--top {
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(-8px);
}

.tooltip__content--bottom {
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(8px);
}

.tooltip__content--left {
  right: 100%;
  top: 50%;
  transform: translateY(-50%) translateX(-8px);
}

.tooltip__content--right {
  left: 100%;
  top: 50%;
  transform: translateY(-50%) translateX(8px);
}

/* ============================================
   Element: tooltip__arrow
   ============================================ */
.tooltip__arrow {
  /* Size */
  width: 0;
  height: 0;

  /* Border */
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 5px solid var(--color-ink);
}

.tooltip__content--top .tooltip__arrow {
  top: 100%;
}

.tooltip__content--bottom .tooltip__arrow {
  bottom: 100%;
  border-top: none;
  border-bottom: 5px solid var(--color-ink);
}

/* ============================================
   Transition Animations
   ============================================ */
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.15s ease;
}

.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
}

.tooltip-enter-from.tooltip__content--top,
.tooltip-leave-to.tooltip__content--top {
  transform: translateX(-50%) translateY(-4px);
}

.tooltip-enter-from.tooltip__content--bottom,
.tooltip-leave-to.tooltip__content--bottom {
  transform: translateX(-50%) translateY(4px);
}
</style>