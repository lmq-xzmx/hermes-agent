<template>
  <div class="floating-window">
    <!-- Status Bar -->
    <div class="status-bar">
      <span class="status-dot" :class="isConnected ? 'ok' : 'err'"></span>
      <span class="status-text">{{ isConnected ? '已连接' : '未连接' }}</span>
      <span class="toolbar-spacer"></span>
      <ButtonIcon @click="toggleWindow">✕</ButtonIcon>
    </div>

    <!-- Drop Zone -->
    <div
      class="drop-zone"
      :class="{ 'drag-over': isDragOver }"
      @dragover.prevent="onDragOver"
      @dragleave="onDragLeave"
      @drop.prevent="onDrop"
    >
      <div class="drop-icon">📤</div>
      <div class="drop-text">拖放文件到此处上传</div>
      <div class="drop-target" v-if="targetPath">{{ targetPath }}</div>
    </div>

    <!-- Path Section -->
    <div class="path-section">
      <div class="path-label">上传路径</div>
      <div class="path-row">
        <select v-model="selectedSpaceId" @change="onSpaceChange" class="apple-select">
          <option value="">-- 选择空间 --</option>
          <option v-for="ctx in storageContexts" :key="ctx.space_id" :value="ctx.space_id">
            {{ ctx.space_name || ctx.space_id }}
          </option>
        </select>
      </div>
      <div class="path-input-wrapper">
        <input
          type="text"
          v-model="targetPath"
          placeholder="/path/to/upload"
          class="apple-input full-width"
        >
      </div>
      <div class="path-hint">
        当前: <code>{{ currentDisplayPath }}</code>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <ButtonSecondary size="sm" @click="selectFiles">选择文件</ButtonSecondary>
      <ButtonSecondary size="sm" @click="clearList">清空</ButtonSecondary>
      <ButtonPrimary size="sm" @click="uploadAll" :disabled="files.length === 0 || uploading">
        {{ uploading ? '上传中...' : `上传 (${files.length})` }}
      </ButtonPrimary>
    </div>

    <!-- File List -->
    <div class="file-list" v-if="files.length > 0">
      <div v-for="(file, index) in files" :key="index" class="file-item">
        <span class="file-icon">{{ getFileIcon(file.type) }}</span>
        <span class="file-name">{{ file.name }}</span>
        <span class="file-size">{{ formatSize(file.size) }}</span>
        <button class="btn-remove" @click="removeFile(index)">×</button>
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

const currentDisplayPath = computed(() => {
  return targetPath.value || '/'
})

onMounted(async () => {
  await loadStorageContexts()
  checkConnection()
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
  // Space changed
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
}

function removeFile(index) {
  files.value.splice(index, 1)
}

function clearList() {
  files.value = []
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
.floating-window {
  display: flex;
  flex-direction: column;
  height: 100vh;
  padding: var(--space-md);
  background: var(--color-surface-black);
  color: var(--color-body-on-dark);
  font-family: var(--font-body);
}

.status-bar {
  display: flex;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: rgba(0, 102, 204, 0.2);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-md);
  font-size: 13px;
  flex-shrink: 0;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  margin-right: var(--space-sm);
}

.status-dot.ok {
  background: var(--color-success);
}

.status-dot.err {
  background: var(--color-danger);
}

.status-text {
  font-size: 13px;
}

.toolbar-spacer {
  flex: 1;
}

.drop-zone {
  flex: 1;
  min-height: 120px;
  border: 2px dashed rgba(255, 255, 255, 0.2);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  margin-bottom: var(--space-md);
}

.drop-zone.drag-over {
  border-color: var(--color-primary);
  background: rgba(0, 102, 204, 0.1);
}

.drop-icon {
  font-size: 36px;
  margin-bottom: var(--space-xs);
}

.drop-text {
  font-size: 13px;
  color: var(--color-body-muted);
}

.drop-target {
  font-size: 11px;
  color: var(--color-primary-on-dark);
  margin-top: var(--space-xs);
  max-width: 90%;
  word-break: break-all;
  text-align: center;
}

.path-section {
  flex-shrink: 0;
  margin-bottom: var(--space-md);
}

.path-label {
  font-size: 11px;
  color: var(--color-body-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.path-row {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: 6px;
}

.path-input-wrapper {
  margin-bottom: 6px;
}

.apple-select,
.apple-input {
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md, 18px);
  color: var(--color-body-on-dark);
  font-family: var(--font-body);
  font-size: 13px;
  transition: border-color 0.2s;
}

.apple-select {
  cursor: pointer;
}

.apple-select:focus,
.apple-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.apple-input.full-width {
  width: 100%;
  box-sizing: border-box;
}

.path-hint {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}

.path-hint code {
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 5px;
  border-radius: var(--radius-xs);
  font-family: 'SF Mono', 'Monaco', monospace;
}

.toolbar {
  display: flex;
  gap: var(--space-sm);
  flex-shrink: 0;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  margin-top: var(--space-sm);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  padding-top: var(--space-sm);
}

.file-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  gap: var(--space-sm);
}

.file-item:last-child {
  border-bottom: none;
}

.file-icon {
  font-size: 16px;
}

.file-name {
  flex: 1;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 11px;
  color: var(--color-body-muted);
}

.btn-remove {
  background: none;
  border: none;
  color: var(--color-body-muted);
  cursor: pointer;
  font-size: 18px;
  padding: 0 4px;
  transition: color 0.15s;
}

.btn-remove:hover {
  color: var(--color-danger);
}
</style>