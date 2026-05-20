<template>
  <div class="file-view__file-list-container" ref="containerRef">
    <table class="file-list" v-if="files.length > 0">
      <thead>
        <tr>
          <th class="file-list__header-cell" style="width:40%">
            <label class="file-view__checkbox-label">
              <input type="checkbox" class="apple-checkbox" @change="emit('select-all', $event.target.checked)" :checked="allSelected">
              <span>名称</span>
            </label>
          </th>
          <th class="file-list__header-cell" style="width:15%">大小</th>
          <th class="file-list__header-cell" style="width:20%">修改时间</th>
          <th class="file-list__header-cell" style="width:20%">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="file in files"
          :key="file.path"
          class="file-list__row"
          :class="{ 'file-list__row--selected': selectedPaths.has(file.path) }"
          :data-path="file.path"
          draggable="true"
          @dragstart="emit('drag-start', $event, file)"
          @dragover="emit('drag-over', $event, file)"
          @dragleave="emit('drag-leave', $event)"
          @drop="emit('drop', $event, file)"
          @click="emit('row-click', file, $event)"
          @contextmenu.prevent="emit('row-contextmenu', $event, file)"
        >
          <td class="file-list__cell">
            <label class="file-view__checkbox-label" @click.stop>
              <input
                type="checkbox"
                class="apple-checkbox"
                :checked="selectedPaths.has(file.path)"
                @change="emit('checkbox-change', file.path)"
              >
              <Icon :name="file.is_directory ? 'folder' : fileIcon" :size="16" class="file-list__icon" />
              <span class="file-list__name-text">{{ file.name }}</span>
            </label>
          </td>
          <td class="file-list__cell file-list__size">
            {{ file.is_directory ? '-' : formatSize(file.size) }}
          </td>
          <td class="file-list__cell">{{ formatDate(file.modified) }}</td>
          <td class="file-list__cell">
            <div class="file-actions">
              <button class="file-actions__btn" @click.stop="emit('action', 'finder', file.path)">Finder 中显示</button>
              <button class="file-actions__btn file-actions__btn--danger" @click.stop="emit('action', 'delete', file.path)">删除</button>
              <button class="file-actions__btn" @click.stop="emit('action', 'share', file.path)">分享</button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
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

const fileIcon = computed(() => 'file')

function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    return '今天 ' + date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return days + ' 天前'
  } else {
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
  }
}
</script>

<style scoped>
.file-view__file-list-container {
  flex: 1;
  overflow: auto;
  overflow-x: auto;
  background: var(--color-background, #f5f5f7);
}

.file-list {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.file-list__header-cell {
  padding: 10px 16px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-label-secondary, #86868b);
  background: var(--color-background-secondary, #ffffff);
  border-bottom: 1px solid var(--color-separator, rgba(0, 0, 0, 0.1));
  position: sticky;
  top: 0;
  z-index: 1;
  min-width: 180px;
  width: 180px;
}

.file-list__row {
  cursor: pointer;
  transition: background-color 0.1s ease;
}

.file-list__row:hover {
  background-color: var(--color-fill-secondary, #f5f5f7);
}

.file-list__row--selected {
  background-color: var(--color-fill-secondary, #e8e8ed);
}

.file-list__cell {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-separator, rgba(0, 0, 0, 0.05));
  font-size: 14px;
  color: var(--color-label, #1d1d1f);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-list__icon {
  margin-right: 8px;
  vertical-align: middle;
  color: var(--color-label-secondary, #86868b);
}

.file-list__name-text {
  vertical-align: middle;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-list__size {
  color: var(--color-label-secondary, #86868b);
  font-size: 13px;
}

.file-view__checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.apple-checkbox {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.file-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
  flex-shrink: 0;
  min-width: 180px;
  overflow: visible;
  position: relative;
  z-index: 10;
}

.file-list__row:hover .file-actions {
  opacity: 1;
}

.file-list__cell:last-child {
  min-width: 180px;
  width: 180px;
  overflow: visible;
  vertical-align: middle;
}

.file-actions__btn {
  padding: 4px 8px;
  background: none;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  color: var(--color-label-secondary, #86868b);
  cursor: pointer;
  transition: all 0.15s ease;
}

.file-actions__btn:hover {
  background-color: var(--color-fill-secondary, #e8e8ed);
  color: var(--color-label, #1d1d1f);
}

.file-actions__btn--danger:hover {
  background-color: rgba(255, 59, 48, 0.1);
  color: var(--color-system-red, #ff3b30);
}
</style>