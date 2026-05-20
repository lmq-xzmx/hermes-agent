<template>
  <Modal v-model="isOpen" title="选择文件或文件夹" size="lg" :closable="true">
    <!-- Path Input with Browse Button -->
    <div class="path-picker">
      <div class="path-picker__input-row">
        <input
          type="text"
          v-model="currentPath"
          placeholder="/path/to/folder"
          class="apple-input path-picker__input"
          @keydown.enter="navigateTo(currentPath)"
        >
        <button class="btn-apple-secondary" @click="navigateTo(currentPath)">
          跳转
        </button>
      </div>

      <!-- Breadcrumb Navigation -->
      <div class="path-picker__breadcrumb">
        <button
          v-for="(crumb, index) in breadcrumbs"
          :key="crumb.path"
          class="path-picker__crumb"
          :class="{ 'path-picker__crumb--active': index === breadcrumbs.length - 1 }"
          @click="navigateTo(crumb.path)"
        >
          <span v-if="index > 0" class="path-picker__crumb-sep">/</span>
          {{ crumb.name }}
        </button>
      </div>

      <!-- File/Folder List -->
      <div class="path-picker__list" v-if="!loading">
        <div
          v-for="item in items"
          :key="item.path"
          class="path-picker__item"
          :class="{
            'path-picker__item--folder': item.is_directory,
            'path-picker__item--selected': selectedPath === item.path
          }"
          @click="selectItem(item)"
          @dblclick="item.is_directory && navigateTo(item.path)"
        >
          <span class="path-picker__item-icon">{{ item.is_directory ? '📁' : '📄' }}</span>
          <span class="path-picker__item-name">{{ item.name }}</span>
          <span class="path-picker__item-size">{{ item.is_directory ? '-' : formatSize(item.size) }}</span>
        </div>
        <div v-if="items.length === 0" class="path-picker__empty">
          此文件夹为空
        </div>
      </div>
      <div v-if="loading" class="path-picker__loading">
        加载中...
      </div>
    </div>

    <template #footer>
      <div class="path-picker__footer">
        <span class="path-picker__selected">
          已选择: {{ selectedPath || '未选择' }}
        </span>
        <div class="path-picker__actions">
          <button class="btn-apple-secondary" @click="isOpen = false">
            取消
          </button>
          <button class="btn-apple-primary" @click="confirmSelection" :disabled="!selectedPath">
            确定
          </button>
        </div>
      </div>
    </template>
  </Modal>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { api } from '../../services/api'
import Modal from './Modal.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  initialPath: { type: String, default: '/' }
})

const emit = defineEmits(['update:modelValue', 'select'])

// Modal visibility
const isOpen = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

// State
const currentPath = ref(props.initialPath || '/')
const items = ref([])
const loading = ref(false)
const selectedPath = ref('')
const currentSpaceId = ref('')

// Load space on mount
async function loadCurrentSpace() {
  // 尝试从 localStorage 获取当前 spaceId
  const stored = localStorage.getItem('hfm_current_space')
  if (stored) {
    try {
      currentSpaceId.value = JSON.parse(stored)?.space_id || ''
    } catch {
      currentSpaceId.value = ''
    }
  }
}

// Navigate to path
async function navigateTo(path) {
  if (!path) return
  loading.value = true
  currentPath.value = path

  try {
    // Use space_id if available, otherwise fallback to path-based lookup
    const spaceId = currentSpaceId.value || 'default'
    const data = await api.getFiles(spaceId, path)
    items.value = data.files || []
  } catch (err) {
    console.error('Failed to load path:', err)
    items.value = []
  } finally {
    loading.value = false
  }
}

// Select item
function selectItem(item) {
  selectedPath.value = item.path
  if (item.is_directory) {
    currentPath.value = item.path
  }
}

// Confirm selection
function confirmSelection() {
  if (selectedPath.value) {
    emit('select', selectedPath.value)
    isOpen.value = false
  }
}

// Breadcrumbs
const breadcrumbs = computed(() => {
  const parts = currentPath.value.split('/').filter(Boolean)
  const crumbs = [{ name: '根目录', path: '/' }]
  let accumulated = ''
  for (const part of parts) {
    accumulated += '/' + part
    crumbs.push({ name: part, path: accumulated })
  }
  return crumbs
})

// Format size
function formatSize(bytes) {
  if (!bytes) return '-'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024
    i++
  }
  return `${bytes.toFixed(1)} ${units[i]}`
}

// Watch for modal open
watch(isOpen, async (val) => {
  if (val) {
    await loadCurrentSpace()
    await navigateTo(props.initialPath || '/')
    selectedPath.value = ''
  }
})
</script>

<style scoped>
/* === Block: path-picker === */
.path-picker {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

/* === Element: path-picker__input-row === */
.path-picker__input-row {
  display: flex;
  gap: var(--spacing-sm);
}

.path-picker__input {
  flex: 1;
  height: 44px;
}

/* === Element: path-picker__breadcrumb === */
.path-picker__breadcrumb {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--spacing-xxs);
  padding: var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.path-picker__crumb {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: none;
  border: none;
  border-radius: var(--radius-sm);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: all 0.15s ease;
}

.path-picker__crumb:hover {
  background: var(--color-surface-pearl);
  color: var(--color-ink);
}

.path-picker__crumb--active {
  color: var(--color-ink);
  font-weight: 500;
}

.path-picker__crumb-sep {
  color: var(--color-ink-muted-48);
}

/* === Element: path-picker__list === */
.path-picker__list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
}

.path-picker__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background 0.15s ease;
  border-bottom: 1px solid var(--color-hairline);
}

.path-picker__item:last-child {
  border-bottom: none;
}

.path-picker__item:hover {
  background: var(--color-canvas-parchment);
}

.path-picker__item--selected {
  background: var(--color-primary-subtle);
}

.path-picker__item-icon {
  flex-shrink: 0;
}

.path-picker__item-name {
  flex: 1;
  font: var(--text-body);
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.path-picker__item-size {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  flex-shrink: 0;
}

.path-picker__empty,
.path-picker__loading {
  padding: var(--spacing-xl);
  text-align: center;
  color: var(--color-ink-muted-48);
  font: var(--text-body);
}

/* === Element: path-picker__footer === */
.path-picker__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.path-picker__selected {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.path-picker__actions {
  display: flex;
  gap: var(--spacing-sm);
}
</style>