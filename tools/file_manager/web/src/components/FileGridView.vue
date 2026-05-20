<template>
  <div class="file-view__file-grid-container" ref="containerRef">
    <div class="file-grid" v-if="files.length > 0">
      <div
        v-for="file in files"
        :key="file.path"
        class="file-grid__item"
        :class="{ 'file-grid__item--selected': selectedPaths.has(file.path) }"
        :data-path="file.path"
        draggable="true"
        @dragstart="emit('drag-start', $event, file)"
        @dragover="emit('drag-over', $event, file)"
        @dragleave="emit('drag-leave', $event)"
        @drop="emit('drop', $event, file)"
        @click="emit('row-click', file, $event)"
        @contextmenu.prevent="emit('row-contextmenu', $event, file)"
      >
        <div class="file-grid__checkbox" @click.stop>
          <input
            type="checkbox"
            class="apple-checkbox"
            :checked="selectedPaths.has(file.path)"
            @change="emit('checkbox-change', file.path)"
          >
        </div>
        <div class="file-grid__icon-wrapper">
          <Icon :name="file.is_directory ? 'folder' : getFileIcon(file.name)" :size="48" class="file-grid__icon" />
        </div>
        <div class="file-grid__name">{{ file.name }}</div>
        <div class="file-grid__actions">
          <button class="file-grid__action-btn" @click.stop="emit('action', 'finder', file.path)">Finder</button>
          <button class="file-grid__action-btn file-grid__action-btn--danger" @click.stop="emit('action', 'delete', file.path)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Icon } from './common'

const props = defineProps({
  files: {
    type: Array,
    default: () => []
  },
  selectedPaths: {
    type: Object,
    default: () => new Set()
  },
  allSelected: {
    type: Boolean,
    default: false
  }
})

const containerRef = ref(null)

const emit = defineEmits([
  'row-click',
  'row-contextmenu',
  'checkbox-change',
  'select-all',
  'drag-start',
  'drag-over',
  'drag-leave',
  'drop',
  'action'
])

const ICON_MAP = {
  '.pdf': 'file-text',
  '.doc': 'file-text',
  '.docx': 'file-text',
  '.xls': 'table',
  '.xlsx': 'table',
  '.ppt': 'presentation',
  '.pptx': 'presentation',
  '.jpg': 'image',
  '.jpeg': 'image',
  '.png': 'image',
  '.gif': 'image',
  '.mp3': 'music',
  '.mp4': 'video',
  '.mov': 'video',
  '.zip': 'archive',
  '.tar': 'archive',
  '.gz': 'archive'
}

function getFileIcon(name) {
  const ext = name.substring(name.lastIndexOf('.')).toLowerCase()
  return ICON_MAP[ext] || 'file'
}
</script>

<style scoped>
.file-view__file-grid-container {
  flex: 1;
  overflow: auto;
  background: var(--color-background, #f5f5f7);
  padding: 16px;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 16px;
}

.file-grid__item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.file-grid__item:hover {
  background-color: var(--color-fill-secondary, #f5f5f7);
}

.file-grid__item--selected {
  background-color: var(--color-fill-secondary, #e8e8ed);
}

.file-grid__checkbox {
  position: absolute;
  top: 8px;
  left: 8px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.file-grid__item:hover .file-grid__checkbox,
.file-grid__item--selected .file-grid__checkbox {
  opacity: 1;
}

.apple-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.file-grid__icon-wrapper {
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.file-grid__icon {
  color: var(--color-label-secondary, #86868b);
}

.file-grid__name {
  font-size: 13px;
  color: var(--color-label, #1d1d1f);
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: break-all;
}

.file-grid__actions {
  display: flex;
  gap: 4px;
  margin-top: 8px;
  opacity: 1;
  transition: opacity 0.15s ease;
}

.file-grid__item:hover .file-grid__actions {
  opacity: 1;
}

.file-grid__action-btn {
  padding: 2px 6px;
  background: none;
  border: none;
  border-radius: 4px;
  font-size: 11px;
  color: var(--color-label-secondary, #86868b);
  cursor: pointer;
  transition: all 0.15s ease;
}

.file-grid__action-btn:hover {
  background-color: var(--color-fill-tertiary, #e8e8ed);
  color: var(--color-label, #1d1d1f);
}

.file-grid__action-btn--danger:hover {
  background-color: rgba(255, 59, 48, 0.1);
  color: var(--color-system-red, #ff3b30);
}
</style>
