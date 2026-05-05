<template>
  <div class="dropdown" ref="dropdownRef">
    <div class="dropdown-trigger" @click="toggle" :aria-expanded="isOpen">
      <slot name="trigger" />
    </div>
    <Transition name="dropdown">
      <div v-if="isOpen" class="dropdown-menu" :class="alignClass">
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

const alignClass = computed(() => `dropdown-menu-${props.align}`)

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
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-trigger {
  cursor: pointer;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  min-width: 180px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-xs);
  z-index: var(--z-dropdown);
  font-family: var(--font-family-text);
}

.dropdown-menu-left {
  left: 0;
}

.dropdown-menu-right {
  right: 0;
}

/* Transitions */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
