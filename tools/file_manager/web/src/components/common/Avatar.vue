<template>
  <div class="avatar" :class="[sizeClass, shapeClass]" :style="customStyle">
    <img v-if="src && !imageError" :src="src" :alt="alt" @error="onImageError" class="avatar-image">
    <span v-else class="avatar-fallback">{{ fallbackText }}</span>
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

const sizeClass = computed(() => `avatar-${props.size}`)
const shapeClass = computed(() => `avatar-${props.shape}`)

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
.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-body-on-dark);
  font-family: var(--font-body);
  font-weight: 600;
  overflow: hidden;
  flex-shrink: 0;
}

.avatar-xs { width: 24px; height: 24px; font-size: 10px; }
.avatar-sm { width: 32px; height: 32px; font-size: 12px; }
.avatar-md { width: 40px; height: 40px; font-size: 14px; }
.avatar-lg { width: 56px; height: 56px; font-size: 18px; }
.avatar-xl { width: 80px; height: 80px; font-size: 24px; }

.avatar-circle { border-radius: var(--radius-full); }
.avatar-square { border-radius: var(--radius-none, 0); }
.avatar-rounded { border-radius: var(--radius-md, 18px); }

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-fallback {
  text-transform: uppercase;
}
</style>
