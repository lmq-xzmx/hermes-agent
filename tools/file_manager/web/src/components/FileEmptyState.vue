<template>
  <div class="file-view__empty-state" :class="{ 'file-view__empty-state--show': show }">
    <!-- Search No Results -->
    <div v-if="searchQuery && filteredFiles.length === 0 && totalFiles > 0" class="empty-state__search-no-results">
      <p>未找到包含「{{ searchQuery }}」的文件</p>
    </div>

    <!-- No Spaces: User has no workspaces -->
    <template v-if="type === 'no-spaces'">
      <div class="empty-state__guidance">
        <Icon name="folder" :size="48" class="guidance__icon" />
        <h3 class="guidance__title">暂无工作空间</h3>
        <p class="guidance__desc">您还没有分配任何工作空间，请联系管理员或创建新空间</p>
        <div class="guidance__actions">
          <button v-if="userRole === 'admin'" class="btn-apple-primary" @click="emit('go-to-spaces')">
            创建工作空间
          </button>
          <button class="btn-apple-secondary" @click="emit('go-to-spaces')">
            查看所有空间
          </button>
        </div>
      </div>
    </template>

    <!-- Select Space: Multiple spaces available but none selected -->
    <template v-else-if="type === 'select-space'">
      <div class="empty-state__guidance">
        <Icon name="folder-open" :size="48" class="guidance__icon" />
        <h3 class="guidance__title">请选择工作空间</h3>
        <p class="guidance__desc">您有多个工作空间，请在左侧选择要访问的空间</p>
        <div class="guidance__space-list" v-if="spaces && spaces.length > 0">
          <button
            v-for="space in spaces.slice(0, 4)"
            :key="space.space_id"
            class="btn-apple-secondary guidance__space-btn"
            @click="emit('select-space', space)"
          >
            {{ space.name || space.space_id }}
          </button>
        </div>
        <button class="btn-apple-secondary btn-sm" @click="emit('go-to-spaces')">
          查看全部 {{ spaces ? spaces.length : 0 }} 个空间
        </button>
      </div>
    </template>

    <!-- Empty Folder: Space selected but folder is empty -->
    <template v-else>
      <Icon name="folder" :size="48" class="empty-state__icon" />
      <h3 class="empty-state__title">文件夹为空</h3>
      <p class="empty-state__desc">此文件夹还没有任何文件</p>
      <div v-if="canUpload" class="empty-state__actions">
        <button class="btn-apple-primary" @click="emit('upload')">上传文件</button>
        <button class="btn-apple-secondary" @click="emit('create-folder')">新建文件夹</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { Icon } from './common'

defineProps({
  type: {
    type: String,
    default: 'empty-folder'
    // 'no-spaces' | 'select-space' | 'empty-folder' | 'search-no-results'
  },
  show: {
    type: Boolean,
    default: true
  },
  searchQuery: {
    type: String,
    default: ''
  },
  filteredFiles: {
    type: Array,
    default: () => []
  },
  totalFiles: {
    type: Number,
    default: 0
  },
  spaces: {
    type: Array,
    default: () => []
  },
  userRole: {
    type: String,
    default: ''
  },
  canUpload: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['go-to-spaces', 'select-space', 'upload', 'create-folder'])
</script>

<style scoped>
.file-view__empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--color-label-secondary, #86868b);
}

.file-view__empty-state--show {
  display: flex;
}

.empty-state__icon {
  color: var(--color-label-tertiary, #aeaeb2);
  margin-bottom: 16px;
}

.empty-state__title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-label, #1d1d1f);
  margin: 0 0 8px;
}

.empty-state__desc {
  font-size: 14px;
  color: var(--color-label-secondary, #86868b);
  margin: 0 0 20px;
}

.empty-state__actions {
  display: flex;
  gap: 12px;
}

.empty-state__search-no-results {
  padding: 20px;
  color: var(--color-label-secondary, #86868b);
}

.empty-state__guidance {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  max-width: 400px;
}

.guidance__icon {
  color: var(--color-label-tertiary, #aeaeb2);
}

.guidance__title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-label, #1d1d1f);
  margin: 0;
}

.guidance__desc {
  font-size: 14px;
  color: var(--color-label-secondary, #86868b);
  margin: 0;
  line-height: 1.5;
}

.guidance__actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.guidance__space-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  margin-top: 8px;
}

.guidance__space-btn {
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-apple-primary {
  padding: 10px 20px;
  background-color: var(--color-primary, #007aff);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-apple-primary:hover {
  background-color: var(--color-primary-dark, #0056b3);
}

.btn-apple-secondary {
  padding: 10px 20px;
  background-color: var(--color-fill-secondary, #f5f5f7);
  color: var(--color-label, #1d1d1f);
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.btn-apple-secondary:hover {
  background-color: var(--color-fill-tertiary, #e8e8ed);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}
</style>