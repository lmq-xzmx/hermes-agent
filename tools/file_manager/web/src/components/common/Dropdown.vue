<template>
  <div class="dropdown" ref="dropdownRef">
    <div class="dropdown__trigger" @click="toggle" :aria-expanded="isOpen">
      <slot name="trigger" />
    </div>
    <Transition name="dropdown">
      <div v-if="isOpen" class="dropdown__menu" :class="`dropdown__menu--${align}`">
        <slot :close="close" />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  align: { type: String, default: 'left' }, // left/right
  width: { type: String, default: '' }
})

const isOpen = ref(false)
const dropdownRef = ref(null)

const alignClass = computed(() => `dropdown__menu--${props.align}`)

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}

function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})

defineExpose({ isOpen, toggle, close })
</script>

<style scoped>
/* ============================================
   Dropdown - Apple Design System
   ============================================ */

.dropdown {
  /* Layout */
  position: relative;
  display: inline-block;
}

/* ============================================
   Element: dropdown__menu
   ============================================ */
.dropdown__menu {
  /* Layout */
  position: absolute;
  top: 100%;
  z-index: var(--z-dropdown);

  /* Box Model */
  min-width: 160px;
  padding: var(--spacing-xs) 0;
  margin-top: var(--spacing-xxs);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);

  /* Animation */
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown__menu--left {
  left: 0;
}

.dropdown__menu--right {
  right: 0;
}

/* ============================================
   Transition Animations
   ============================================ */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>