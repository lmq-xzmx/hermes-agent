<template>
  <div class="floating-window">
    <!-- Status Bar -->
    <div class="floating-window__status-bar">
      <span class="floating-window__status-dot" :class="isConnected ? 'floating-window__status-dot--ok' : 'floating-window__status-dot--err'"></span>
      <span class="floating-window__status-text">{{ isConnected ? '已连接' : '未连接' }}</span>
      <span class="floating-window__spacer"></span>
      <ButtonIcon @click="toggleWindow">✕</ButtonIcon>
    </div>

    <!-- Drop Zone -->
    <div
      class="floating-window__drop-zone"
      :class="{ 'floating-window__drop-zone--drag-over': isDragOver }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <div class="floating-window__drop-icon">📤</div>
      <div class="floating-window__drop-text">拖放文件到此处上传</div>
      <div class="floating-window__drop-target" v-if="targetPath">{{ targetPath }}</div>
    </div>

    <!-- Path Section -->
    <div class="floating-window__path-section">
      <div class="floating-window__path-label">上传路径</div>
      <div class="floating-window__path-row">
        <select v-model="selectedSpaceId" @change="onSpaceChange" class="floating-window__select">
          <option value="">-- 选择空间 --</option>
          <option v-for="ctx in storageContexts" :key="ctx.space_id" :value="ctx.space_id">
            {{ ctx.space_name || ctx.space_id }}
          </option>
        </select>
      </div>
      <div class="floating-window__path-input-wrapper">
        <input
          type="text"
          v-model="targetPath"
          placeholder="/path/to/upload"
          class="floating-window__input floating-window__input--full"
        >
      </div>
      <div class="floating-window__path-hint">
        当前: <code class="floating-window__path-code">{{ currentDisplayPath }}</code>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="floating-window__toolbar">
      <ButtonSecondary size="sm" @click="selectFiles">选择文件</ButtonSecondary>
      <ButtonSecondary size="sm" @click="clearList">清空</ButtonSecondary>
      <ButtonPrimary size="sm" @click="uploadAll" :disabled="files.length === 0 || uploading">
        {{ uploading ? '上传中...' : `上传 (${files.length})` }}
      </ButtonPrimary>
    </div>

    <!-- Knowledge Sync Toolbar -->
    <div class="floating-window__knowledge-bar">
      <div class="floating-window__knowledge-status">
        <span class="floating-window__knowledge-dot" :class="llmWikiStatus === '运行中' ? 'floating-window__knowledge-dot--ok' : 'floating-window__knowledge-dot--err'"></span>
        <span class="floating-window__knowledge-label">知识库 {{ llmWikiStatus }}</span>
      </div>
      <ButtonSecondary size="sm" @click="syncToKnowledgeBase" :disabled="!targetPath || targetPath === '/' || syncingToKnowledge">
        {{ syncingToKnowledge ? '同步中...' : '同步到知识库' }}
      </ButtonSecondary>
    </div>

    <!-- File List -->
    <div class="floating-window__file-list" v-if="files.length > 0">
      <div v-for="(file, index) in files" :key="index" class="floating-window__file-item">
        <span class="floating-window__file-icon">{{ getFileIcon(file.type) }}</span>
        <span class="floating-window__file-name">{{ file.name }}</span>
        <span class="floating-window__file-size">{{ formatSize(file.size) }}</span>
        <button class="floating-window__file-remove" @click="removeFile(index)">×</button>
      </div>
    </div>

    <!-- Hidden file input -->
    <input
      type="file"
      ref="fileInput"
      multiple
      style="display:none"
      @change="handleFileSelect"
    >
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api.js'
import { ButtonPrimary, ButtonSecondary, ButtonIcon } from '../components/common'

const emit = defineEmits(['show-toast', 'close'])

const isConnected = ref(false)
const isDragOver = ref(false)
const storageContexts = ref([])
const selectedSpaceId = ref('')
const targetPath = ref('/')
const files = ref([])
const uploading = ref(false)
const fileInput = ref(null)
const llmWikiStatus = ref('检查中...')
const syncingToKnowledge = ref(false)

const currentDisplayPath = computed(() => {
  return targetPath.value || '/'
})

onMounted(async () => {
  await loadStorageContexts()
  checkConnection()
  await checkLlmWikiStatus()
})

async function loadStorageContexts() {
  try {
    const data = await api.getStorageContexts()
    storageContexts.value = data.contexts || []
    if (storageContexts.value.length > 0) {
      selectedSpaceId.value = storageContexts.value[0].space_id
    }
    isConnected.value = true
  } catch (err) {
    isConnected.value = false
    console.error('Failed to load storage contexts:', err)
  }
}

function checkConnection() {
  isConnected.value = storageContexts.value.length > 0
}

function onSpaceChange() {
  // 切换空间时重置上传路径为根目录
  targetPath.value = '/'
}

function onDragOver(event) {
  isDragOver.value = true
}

function onDragLeave(event) {
  isDragOver.value = false
}

function onDrop(event) {
  isDragOver.value = false
  const droppedFiles = Array.from(event.dataTransfer.files)
  addFiles(droppedFiles)

  // 如果拖拽的是单个文件/文件夹，自动设置上传路径
  if (droppedFiles.length === 1 && droppedFiles[0].path) {
    // 从完整路径中提取父目录作为上传目标
    const fullPath = droppedFiles[0].path
    const lastSlash = fullPath.lastIndexOf('/')
    if (lastSlash > 0) {
      targetPath.value = fullPath.substring(0, lastSlash)
    }

    // 如果是文件夹（type为空或是目录），提示可同步到知识库
    const file = droppedFiles[0]
    const isDirectory = file.type === '' || file.type === 'directory' ||
      (file.webkitRelativePath && file.webkitRelativePath.includes('/'))
    if (isDirectory) {
      emit('show-toast', {
        type: 'info',
        title: '已添加文件夹',
        message: '点击"同步到知识库"可将整个文件夹同步'
      })
    }
  }
}

function handleFileSelect(event) {
  const selectedFiles = Array.from(event.target.files)
  addFiles(selectedFiles)
  event.target.value = ''
}

function selectFiles() {
  fileInput.value?.click()
}

function addFiles(newFiles) {
  for (const file of newFiles) {
    if (!files.value.find(f => f.name === file.name && f.size === file.size)) {
      files.value.push(file)
    }
  }

  // 自动检测文件夹并设置上传路径
  const hasDirectory = newFiles.some(f => f.type === '' || f.type === 'directory' || (f.webkitRelativePath && f.webkitRelativePath.includes('/')))
  if (hasDirectory && newFiles.length > 0) {
    const firstFile = newFiles[0]
    if (firstFile.webkitRelativePath) {
      // webkitRelativePath 包含 "folder_name/file.txt" 格式
      const parts = firstFile.webkitRelativePath.split('/')
      if (parts.length > 1) {
        // 去掉文件名，保留文件夹路径
        const folderPath = parts.slice(0, -1).join('/')
        targetPath.value = '/' + folderPath
      }
    } else if (firstFile.path) {
      // 尝试从 path 中提取父目录
      const lastSlash = firstFile.path.lastIndexOf('/')
      if (lastSlash > 0) {
        targetPath.value = firstFile.path.substring(0, lastSlash)
      }
    }
  }
}

function removeFile(index) {
  files.value.splice(index, 1)
}

function clearList() {
  files.value = []
}

async function checkLlmWikiStatus() {
  try {
    const data = await api.getKnowledgeStatus()
    llmWikiStatus.value = data.running ? '运行中' : '已停止'
  } catch (err) {
    llmWikiStatus.value = '未知'
  }
}

async function syncToKnowledgeBase() {
  if (!targetPath.value || targetPath.value === '/') {
    emit('show-toast', { type: 'error', title: '同步失败', message: '请先选择上传路径' })
    return
  }

  syncingToKnowledge.value = true
  try {
    const result = await api.syncToKnowledge(targetPath.value, 'default')
    if (result.status === 'completed') {
      emit('show-toast', {
        type: 'success',
        title: '同步完成',
        message: result.files_synced > 0 ? `已同步 ${result.files_synced} 个文件` : '同步完成'
      })
    } else if (result.status === 'failed') {
      emit('show-toast', { type: 'error', title: '同步失败', message: result.error_message || '未知错误' })
    } else {
      emit('show-toast', { type: 'success', title: '同步已启动', message: '文档正在同步到知识库' })
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '同步失败', message: err.message })
  } finally {
    syncingToKnowledge.value = false
  }
}

async function uploadAll() {
  if (!selectedSpaceId.value || files.value.length === 0) return

  uploading.value = true
  let successCount = 0
  let failCount = 0

  for (const file of files.value) {
    try {
      await api.uploadFile(selectedSpaceId.value, file, targetPath.value)
      successCount++
    } catch (err) {
      failCount++
      console.error(`Failed to upload ${file.name}:`, err)
    }
  }

  uploading.value = false

  if (failCount === 0) {
    emit('show-toast', { type: 'success', title: '上传完成', message: `${successCount} 个文件已上传` })
    files.value = []
  } else {
    emit('show-toast', { type: 'error', title: '部分失败', message: `${successCount} 成功, ${failCount} 失败` })
  }
}

async function toggleWindow() {
  if (window.platform?.api?.isTauri) {
    try {
      await window.platform.api.switchWindow()
    } catch (e) {
      console.warn('switch_window not available:', e)
    }
  }
}

function getFileIcon(type) {
  if (!type) return '📄'
  if (type.startsWith('image/')) return '🖼️'
  if (type.startsWith('video/')) return '🎬'
  if (type.startsWith('audio/')) return '🎵'
  if (type.startsWith('text/')) return '📝'
  return '📄'
}

function formatSize(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}
</script>

<style scoped>
/* === Block: floating-window === */
.floating-window {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* === Element: floating-window__status-bar === */
.floating-window__status-bar {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-hairline);
}

/* === Element: floating-window__status-dot === */
.floating-window__status-dot {
  width: var(--spacing-xs);
  height: var(--spacing-xs);
  border-radius: var(--radius-full);
}

.floating-window__status-dot--ok {
  background: var(--color-success);
}

.floating-window__status-dot--err {
  background: var(--color-danger);
}

/* === Element: floating-window__status-text === */
.floating-window__status-text {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: floating-window__spacer === */
.floating-window__spacer {
  flex: 1;
}

/* === Element: floating-window__drop-zone === */
.floating-window__drop-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  margin: var(--spacing-md);
  background: var(--color-canvas-parchment);
  border: 2px dashed var(--color-hairline);
  border-radius: var(--radius-lg);
  transition: border-color var(--transition-base), background-color var(--transition-base);
}

.floating-window__drop-zone--drag-over {
  background: var(--color-primary-faint);
  border-color: var(--color-primary);
}

/* === Element: floating-window__drop-icon === */
.floating-window__drop-icon {
  font-size: 48px;
  margin-bottom: var(--spacing-md);
}

/* === Element: floating-window__drop-text === */
.floating-window__drop-text {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* === Element: floating-window__drop-target === */
.floating-window__drop-target {
  font: var(--text-caption);
  color: var(--color-primary);
  margin-top: var(--spacing-sm);
}

/* === Element: floating-window__path-section === */
.floating-window__path-section {
  padding: 0 var(--spacing-md) var(--spacing-md);
}

/* === Element: floating-window__path-label === */
.floating-window__path-label {
  font: var(--text-caption-strong);
  color: var(--color-ink);
  margin-bottom: var(--spacing-xxs);
}

/* === Element: floating-window__path-row === */
.floating-window__path-row {
  margin-bottom: var(--spacing-sm);
}

/* === Element: floating-window__select === */
.floating-window__select {
  appearance: none;
  width: 100%;
  padding: var(--spacing-sm);
  height: 36px;
  box-sizing: border-box;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  cursor: pointer;
}

.floating-window__select:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* === Element: floating-window__path-input-wrapper === */
.floating-window__path-input-wrapper {
  margin-bottom: var(--spacing-sm);
}

/* === Element: floating-window__input === */
.floating-window__input {
  width: 100%;
  padding: var(--spacing-sm);
  height: 36px;
  box-sizing: border-box;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
}

.floating-window__input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

/* === Element: floating-window__path-hint === */
.floating-window__path-hint {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: floating-window__path-code === */
.floating-window__path-code {
  font: var(--text-caption);
  color: var(--color-primary);
}

/* === Element: floating-window__toolbar === */
.floating-window__toolbar {
  display: flex;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-hairline);
}

/* === Element: floating-window__file-list === */
.floating-window__file-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-sm) var(--spacing-md);
}

/* === Element: floating-window__file-item === */
.floating-window__file-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-divider-soft);
}

.floating-window__file-item:last-child {
  border-bottom: none;
}

/* === Element: floating-window__file-icon === */
.floating-window__file-icon {
  font-size: 20px;
  flex-shrink: 0;
}

/* === Element: floating-window__file-name === */
.floating-window__file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font: var(--text-body);
  color: var(--color-ink);
}

/* === Element: floating-window__file-size === */
.floating-window__file-size {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: floating-window__file-remove === */
.floating-window__file-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  background: transparent;
  border: none;
  border-radius: var(--radius-full);
  font-size: 18px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: background-color var(--transition-fast), color var(--transition-fast);
}

.floating-window__file-remove:hover {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}

/* === Element: floating-window__knowledge-bar === */
.floating-window__knowledge-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  border-top: 1px solid var(--color-hairline);
  background: var(--color-canvas-parchment);
}

.floating-window__knowledge-status {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
}

.floating-window__knowledge-dot {
  width: var(--spacing-xs);
  height: var(--spacing-xs);
  border-radius: var(--radius-full);
}

.floating-window__knowledge-dot--ok {
  background: var(--color-success);
}

.floating-window__knowledge-dot--err {
  background: var(--color-danger);
}

.floating-window__knowledge-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}
</style>
