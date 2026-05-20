<template>
  <div
    class="avatar"
    :class="[
      `avatar--${size}`,
      `avatar--${shape}`
    ]"
    :style="customStyle"
  >
    <img v-if="src && !imageError" :src="src" :alt="alt" @error="onImageError" class="avatar__image">
    <span v-else class="avatar__fallback">{{ fallbackText }}</span>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  src: { type: String, default: '' },
  alt: { type: String, default: '' },
  name: { type: String, default: '' },
  size: { type: String, default: 'md' }, // xs/sm/md/lg/xl
  shape: { type: String, default: 'circle' }, // circle/square/rounded
  bgColor: { type: String, default: '' }
})

const imageError = ref(false)

const customStyle = computed(() => {
  if (props.bgColor) {
    return { backgroundColor: props.bgColor }
  }
  return {}
})

const fallbackText = computed(() => {
  if (props.name) {
    return props.name.charAt(0).toUpperCase()
  }
  return '?'
})

function onImageError() {
  imageError.value = true
}
</script>

<style scoped>
/* ============================================
   Avatar - Apple Design System
   ============================================ */

.avatar {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;

  /* Visual */
  background: var(--color-canvas-parchment);
  color: var(--color-ink-muted-48);

  /* Shape variants */
  border-radius: var(--radius-full);
}

/* Size Variants */
.avatar--xs { width: 24px; height: 24px; font-size: 12px; }
.avatar--sm { width: 32px; height: 32px; font-size: 14px; }
.avatar--md { width: 40px; height: 40px; font-size: 16px; }
.avatar--lg { width: 56px; height: 56px; font-size: 20px; }
.avatar--xl { width: 80px; height: 80px; font-size: 28px; }

/* Shape Variants */
.avatar--circle { border-radius: var(--radius-full); }
.avatar--square { border-radius: var(--radius-none); }
.avatar--rounded { border-radius: var(--radius-md); }

/* ============================================
   Element: avatar__image
   ============================================ */
.avatar__image {
  /* Layout */
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* ============================================
   Element: avatar__fallback
   ============================================ */
.avatar__fallback {
  /* Typography */
  font: var(--text-caption-strong);
  color: inherit;

  /* Layout */
  text-transform: uppercase;
}
</style>