<template>
  <Teleport to="body">
    <div v-if="visible" class="preview-modal__overlay" @click="close" @keydown.esc="close">
      <div class="preview-modal" @click.stop>
        <header class="preview-modal__header">
          <div class="preview-modal__title-group">
            <h2 class="preview-modal__title">{{ fileName }}</h2>
            <span class="preview-modal__info">{{ fileInfo }}</span>
          </div>
          <button class="preview-modal__close" @click="close" aria-label="关闭预览">&times;</button>
        </header>

        <main class="preview-modal__content" :class="contentClass">
          <div v-if="loading" class="preview-modal__placeholder">加载中...</div>
          <div v-else-if="error" class="preview-modal__error">{{ error }}</div>
          <template v-else>
            <img
              v-if="type === 'image'"
              :src="content"
              :alt="fileName"
              class="preview-modal__image"
              @keydown.arrow-left="navigatePrev"
              @keydown.arrow-right="navigateNext"
            />
            <video
              v-else-if="type === 'video'"
              :src="content"
              controls
              class="preview-modal__video"
            />
            <audio
              v-else-if="type === 'audio'"
              :src="content"
              controls
              class="preview-modal__audio"
            />
            <iframe
              v-else-if="type === 'pdf'"
              :src="content"
              class="preview-modal__pdf"
            />
            <pre v-else-if="type === 'text'" class="preview-modal__content--text">{{ content }}</pre>
            <div
              v-else-if="type === 'markdown' || type === 'markdown-html'"
              class="preview-modal__markdown"
              v-html="type === 'markdown' ? processedContent : content"
            />
            <div v-else class="preview-modal__placeholder">
              <p>此文件类型不支持预览</p>
              <p class="preview-modal__hint-small">按 Esc 关闭</p>
            </div>
          </template>
        </main>

        <footer class="preview-modal__footer">
          <div class="preview-modal__hint">
            <span><kbd>Esc</kbd> 关闭</span>
            <span v-if="hasMultipleFiles"><kbd>←</kbd><kbd>→</kbd> 切换</span>
          </div>
          <span class="preview-modal__nav-info">{{ navInfo }}</span>
        </footer>
      </div>
    </div>
  </Teleport>
</template>


<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  visible: { type: Boolean, default: false },
  file: { type: Object, default: null }, // { path, name, type, size, modified }
  files: { type: Array, default: () => [] }, // Available files for navigation
  currentIndex: { type: Number, default: 0 },
  content: { type: String, default: '' }, // URL for media, content for text
  loading: { type: Boolean, default: false },
  error: { type: String, default: '' }
})

const emit = defineEmits(['close', 'navigate', 'load'])

// Configure marked
marked.setOptions({
  breaks: true,
  gfm: true
})

const fileName = computed(() => props.file?.name || '-')
const fileInfo = computed(() => {
  if (!props.file) return '-'
  const size = formatSize(props.file.size || 0)
  const modified = formatDate(props.file.modified)
  return `${size} | ${modified}`
})

const hasMultipleFiles = computed(() => props.files.length > 1)
const navInfo = computed(() => {
  if (!hasMultipleFiles.value) return '-'
  return `${props.currentIndex + 1} / ${props.files.length}`
})

const type = computed(() => {
  if (!props.file) return 'other'
  const name = props.file.name || ''
  const ext = name.split('.').pop()?.toLowerCase() || ''

  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return 'image'
  if (['mp4', 'webm', 'ogg', 'mov'].includes(ext)) return 'video'
  if (['mp3', 'wav', 'ogg', 'flac'].includes(ext)) return 'audio'
  if (ext === 'pdf') return 'pdf'
  if (['txt', 'log', 'json', 'xml', 'yaml', 'yml', 'js', 'ts', 'py', 'html', 'css'].includes(ext)) return 'text'
  if (['md', 'markdown'].includes(ext)) return 'markdown'
  return 'other'
})

const contentClass = computed(() => `preview-type-${type.value}`)

// Process markdown content
const processedContent = computed(() => {
  if (type.value === 'markdown' && props.content) {
    return marked.parse(props.content)
  }
  return props.content
})

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(str) {
  if (!str) return '-'
  const d = new Date(str)
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

function close() {
  emit('close')
}

function navigatePrev() {
  if (props.currentIndex > 0) {
    emit('navigate', props.currentIndex - 1)
  }
}

function navigateNext() {
  if (props.currentIndex < props.files.length - 1) {
    emit('navigate', props.currentIndex + 1)
  }
}

// Keyboard navigation
function handleKeydown(e) {
  if (!props.visible) return

  switch (e.key) {
    case 'Escape':
      close()
      break
    case 'ArrowLeft':
      navigatePrev()
      break
    case 'ArrowRight':
      navigateNext()
      break
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

defineExpose({
  close,
  navigatePrev,
  navigateNext
})
</script>

<style scoped>
/* ============================================
 * PreviewModal - 预览弹窗
 * BEM: preview-modal__block--modifier
 * ============================================ */

/* --------------------------------------------
 * Block: Overlay
 * -------------------------------------------- */
.preview-modal__overlay {
  /* Layout */
  position: fixed;
  inset: 0;
  z-index: var(--z-modal-backdrop);
  display: flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  padding: var(--spacing-lg);

  /* Visual */
  background: var(--color-overlay);
}

/* --------------------------------------------
 * Block: Modal Container
 * -------------------------------------------- */
.preview-modal {
  /* Layout */
  position: relative;
  z-index: var(--z-modal);
  display: flex;
  flex-direction: column;

  /* Box Model */
  width: 100%;
  max-width: 1000px;
  max-height: calc(100vh - var(--spacing-xxl) * 2);

  /* Visual */
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-product);
  overflow: hidden;
}

/* --------------------------------------------
 * Element: Header
 * -------------------------------------------- */
.preview-modal__header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);

  /* Visual */
  border-bottom: 1px solid var(--color-hairline);
}

.preview-modal__title-group {
  /* Layout */
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
  min-width: 0;
}

.preview-modal__title {
  /* Typography */
  font: var(--text-body-strong);
  text-align: left;
  color: var(--color-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;

  /* Reset */
  margin: 0;
}

.preview-modal__info {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.preview-modal__close {
  /* Layout */
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  /* Box Model */
  width: 28px;
  height: 28px;

  /* Typography */
  font-size: 20px;
  line-height: 1;

  /* Visual */
  color: var(--color-ink-muted-48);
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition:
    background var(--transition-fast),
    color var(--transition-fast);

  &:hover {
    background: var(--color-gray-subtle);
    color: var(--color-ink);
  }

  &:active {
    background: var(--color-gray-subtle);
  }
}

/* --------------------------------------------
 * Element: Content
 * -------------------------------------------- */
.preview-modal__content {
  /* Layout */
  flex: 1;
  min-height: 0;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;

  /* Visual */
  background: var(--color-canvas-parchment);
}

.preview-modal__placeholder,
.preview-modal__error {
  /* Typography */
  font: var(--text-body);
  text-align: center;
  color: var(--color-ink-muted-48);

  /* Box Model */
  padding: var(--spacing-xl);
}

.preview-modal__error {
  color: var(--color-danger);
}

.preview-modal__hint-small {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  /* Box Model */
  margin-top: var(--spacing-sm);
}

/* --------------------------------------------
 * Modifier: Content Type - Image
 * -------------------------------------------- */
.preview-type-image.preview-modal__content {
  /* Box Model */
  padding: var(--spacing-md);
}

.preview-modal__image {
  /* Box Model */
  max-width: 100%;
  max-height: calc(100vh - 200px);

  /* Visual */
  object-fit: contain;
  border-radius: var(--radius-sm);
}

/* --------------------------------------------
 * Modifier: Content Type - Video
 * -------------------------------------------- */
.preview-modal__video {
  /* Box Model */
  max-width: 100%;
  max-height: calc(100vh - 200px);

  /* Visual */
  border-radius: var(--radius-sm);
}

/* --------------------------------------------
 * Modifier: Content Type - Audio
 * -------------------------------------------- */
.preview-modal__audio {
  /* Box Model */
  width: 100%;
  max-width: 600px;
  padding: var(--spacing-lg);
}

/* --------------------------------------------
 * Modifier: Content Type - PDF
 * -------------------------------------------- */
.preview-modal__pdf {
  /* Box Model */
  width: 100%;
  height: calc(100vh - 200px);

  /* Visual */
  border: none;
}

/* --------------------------------------------
 * Modifier: Content Type - Text
 * -------------------------------------------- */
.preview-modal__content--text {
  /* Typography */
  font: var(--text-body);
  font-family: var(--font-family-text);
  color: var(--color-ink);

  /* Box Model */
  margin: 0;
  padding: var(--spacing-lg);
  width: 100%;
  max-width: 800px;

  /* Text */
  white-space: pre-wrap;
  word-break: break-word;

  /* Visual */
  background: var(--color-canvas);
}

/* --------------------------------------------
 * Modifier: Content Type - Markdown
 * -------------------------------------------- */
.preview-modal__markdown {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);

  /* Box Model */
  padding: var(--spacing-lg);
  width: 100%;
  max-width: 800px;

  /* Visual */
  background: var(--color-canvas);
  overflow-y: auto;

  /* Nested headings */
  :deep(h1),
  :deep(h2),
  :deep(h3) {
    margin-top: var(--spacing-md);
    margin-bottom: var(--spacing-sm);
    font-weight: 600;
  }

  :deep(p) {
    margin-bottom: var(--spacing-sm);
  }

  :deep(code) {
    font-family: var(--font-family-text);
    background: var(--color-gray-subtle);
    padding: 2px 6px;
    border-radius: var(--radius-xs);
  }

  :deep(pre) {
    background: var(--color-canvas-parchment);
    padding: var(--spacing-md);
    border-radius: var(--radius-sm);
    overflow-x: auto;

    code {
      background: transparent;
      padding: 0;
    }
  }
}

/* --------------------------------------------
 * Element: Footer
 * -------------------------------------------- */
.preview-modal__footer {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;

  /* Box Model */
  padding: var(--spacing-sm) var(--spacing-lg);

  /* Visual */
  border-top: 1px solid var(--color-hairline);
}

.preview-modal__hint {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-md);

  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  kbd {
    /* Layout */
    display: inline-flex;
    align-items: center;
    justify-content: center;

    /* Box Model */
    min-width: 20px;
    height: 20px;
    padding: 0 var(--spacing-xxs);

    /* Typography */
    font-family: var(--font-family-text);
    font-size: 11px;
    color: var(--color-ink-muted-48);

    /* Visual */
    background: var(--color-canvas-parchment);
    border: 1px solid var(--color-hairline);
    border-radius: var(--radius-xs);
  }
}

.preview-modal__nav-info {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}
</style>

