<template>
  <span
    class="color-icon"
    :class="[`color-icon--${name}`, sizeClass]"
    :style="customStyle"
  >{{ emoji }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** 图标名称 */
  name: {
    type: String,
    required: true
  },
  /** 图标尺寸: sm, md, lg, xl */
  size: {
    type: String,
    default: 'md'
  },
  /** 自定义字体大小 */
  fontSize: {
    type: [Number, String],
    default: null
  }
})

const emojiMap = {
  // Navigation
  'file': '📄',
  'files': '📁',
  'team': '👥',
  'teams': '👥',
  'users': '👤',
  'rocket': '🚀',
  'space': '🚀',
  'spaces': '🚀',
  'pool': '🗄️',
  'pools': '🗄️',
  'database': '🗄️',
  'brain': '🧠',
  'knowledge': '🧠',
  'trash': '🗑️',
  'server': '🖥️',
  'book-open': '📖',
  // Actions
  'plus': '➕',
  'minus': '➖',
  'close': '✖️',
  'check': '✅',
  'search': '🔍',
  'refresh': '🔄',
  'upload': '⬆️',
  'download': '⬇️',
  'share': '📤',
  'copy': '📋',
  'edit': '✏️',
  'delete': '🗑️',
  'folder': '📁',
  'folder-open': '📂',
  'folder-plus': '📁➕',
  'eye': '👁️',
  'eye-off': '👁️‍🗨️',
  'settings': '⚙️',
  'menu': '☰',
  'chevron-right': '›',
  'chevron-down': '⌄',
  'chevron-left': '‹',
  'chevron-up': '⌃',
  'trending-up': '📈',
  // View Toggle
  'list': '☰',
  'grid': '⊞',
  // Status
  'warning': '⚠️',
  'info': 'ℹ️',
  'success': '✅',
  'error': '❌',
  'loading': '⏳',
  // Misc
  'theme': '🎨',
  'palette': '🎨',
  'logout': '🚪',
  'log-out': '🚪',
  'avatar': '👤',
  'moon': '🌙',
  'sun': '☀️',
  // File Types
  'file-generic': '📄',
  'file-image': '🖼️',
  'file-video': '🎬',
  'file-audio': '🎵',
  'file-code': '💻',
  'file-archive': '📦',
  // Arrow Navigation
  'arrow-left': '←',
  'arrow-right': '→',
  'arrow-up': '↑',
  'arrow-down': '↓',
  // Folder
  'folder-closed': '📁'
}

const emoji = computed(() => emojiMap[props.name] || '📄')

const sizeClass = computed(() => `color-icon--${props.size}`)

const customStyle = computed(() => {
  if (props.fontSize) {
    return { fontSize: typeof props.fontSize === 'number' ? `${props.fontSize}px` : props.fontSize }
  }
  return {}
})
</script>

<style scoped>
.color-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  font-style: normal;
}

.color-icon--sm {
  font-size: 14px;
}

.color-icon--md {
  font-size: 18px;
}

.color-icon--lg {
  font-size: 24px;
}

.color-icon--xl {
  font-size: 32px;
}
</style>
