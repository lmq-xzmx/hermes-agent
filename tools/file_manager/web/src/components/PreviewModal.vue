<template>
  <Teleport to="body">
    <div v-if="visible" class="preview-modal-overlay" @click="close" @keydown.esc="close">
      <div class="preview-modal" @click.stop>
        <div class="preview-header">
          <div>
            <div class="preview-title">{{ fileName }}</div>
            <div class="preview-info">{{ fileInfo }}</div>
          </div>
          <button class="preview-close" @click="close">&times;</button>
        </div>

        <div class="preview-content" :class="contentClass">
          <div v-if="loading" class="preview-placeholder">加载中...</div>
          <div v-else-if="error" class="preview-error">{{ error }}</div>
          <template v-else>
            <img
              v-if="type === 'image'"
              :src="content"
              :alt="fileName"
              class="preview-image"
              @keydown.arrow-left="navigatePrev"
              @keydown.arrow-right="navigateNext"
            />
            <video
              v-else-if="type === 'video'"
              :src="content"
              controls
              class="preview-video"
            />
            <audio
              v-else-if="type === 'audio'"
              :src="content"
              controls
              class="preview-audio"
            />
            <iframe
              v-else-if="type === 'pdf'"
              :src="content"
              class="preview-pdf"
            />
            <pre v-else-if="type === 'text' || type === 'markdown'" class="preview-text">{{ content }}</pre>
            <div
              v-else-if="type === 'markdown-html'"
              class="preview-markdown"
              v-html="content"
            />
            <div v-else class="preview-placeholder">
              <p>此文件类型不支持预览</p>
              <p class="preview-hint-small">按 Esc 关闭</p>
            </div>
          </template>
        </div>

        <div class="preview-footer">
          <div class="preview-hint">
            <span><kbd>Space</kbd> 预览</span>
            <span><kbd>Esc</kbd> 关闭</span>
            <span v-if="hasMultipleFiles"><kbd>←</kbd><kbd>→</kbd> 切换</span>
          </div>
          <div class="preview-nav-info">
            {{ navInfo }}
          </div>
        </div>
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
.preview-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay-strong);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-modal {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90vw;
  max-width: 1200px;
  height: 85vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) var(--spacing-lg);
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-canvas-parchment);
}

.preview-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-ink);
  letter-spacing: -0.374px;
}

.preview-info {
  font-size: 14px;
  color: var(--color-ink-muted-48);
  margin-top: var(--spacing-xxs);
  letter-spacing: -0.224px;
}

.preview-close {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  font-size: 24px;
  cursor: pointer;
  border-radius: 6px;
  color: var(--text-secondary, #666);
  transition: background 0.15s;
}

.preview-close:hover {
  background: var(--color-hairline);
  color: var(--color-ink);
}

.preview-content {
  flex: 1;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
}

.preview-placeholder,
.preview-error {
  color: var(--color-ink-muted-48);
  font-size: 17px;
  text-align: center;
}

.preview-error {
  color: var(--color-danger);
}

.preview-hint-small {
  font-size: 12px;
  margin-top: var(--spacing-xs);
}

.preview-image {
  max-width: 100%;
  max-height: 70vh;
  object-fit: contain;
  border-radius: var(--radius-xs);
}

.preview-video,
.preview-audio {
  max-width: 100%;
  max-height: 70vh;
}

.preview-pdf {
  width: 100%;
  height: 70vh;
  border: none;
}

.preview-text {
  width: 100%;
  height: 70vh;
  overflow: auto;
  background: var(--color-canvas-parchment);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  font-family: 'SF Mono', 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}

.preview-markdown {
  width: 100%;
  max-width: 800px;
  padding: var(--spacing-lg);
  overflow: auto;
}

.preview-markdown :deep(h1),
.preview-markdown :deep(h2),
.preview-markdown :deep(h3) {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
}

.preview-markdown :deep(p) {
  margin: 1em 0;
  line-height: 1.7;
}

.preview-markdown :deep(code) {
  background: var(--color-canvas-parchment);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-family: monospace;
}

.preview-markdown :deep(pre) {
  background: var(--color-canvas-parchment);
  padding: var(--spacing-md);
  border-radius: var(--radius-sm);
  overflow-x: auto;
}

.preview-markdown :deep(pre code) {
  background: none;
  padding: 0;
}

.preview-markdown :deep(ul),
.preview-markdown :deep(ol) {
  padding-left: var(--spacing-lg);
}

.preview-markdown :deep(blockquote) {
  border-left: 4px solid var(--color-primary);
  padding-left: var(--spacing-md);
  margin-left: 0;
  color: var(--color-ink-muted-48);
}

.preview-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-sm) var(--spacing-lg);
  border-top: 1px solid var(--color-hairline);
  background: var(--color-canvas-parchment);
}

.preview-hint {
  display: flex;
  gap: var(--spacing-lg);
  font-size: 14px;
  color: var(--color-ink-muted-48);
  letter-spacing: -0.224px;
}

.preview-hint kbd {
  background: var(--color-surface-pearl);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-size: 12px;
  font-family: inherit;
}

.preview-nav-info {
  font-size: 14px;
  color: var(--color-ink-muted-48);
  letter-spacing: -0.224px;
}
</style>
