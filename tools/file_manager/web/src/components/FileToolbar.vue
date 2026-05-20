<template>
  <div class="file-view__toolbar">
    <!-- Breadcrumb Navigation -->
    <div class="file-view__breadcrumb">
      <button
        v-for="(crumb, index) in breadcrumbs"
        :key="crumb.path"
        class="breadcrumb__item"
        :class="{ 'breadcrumb__item--active': index === breadcrumbs.length - 1 }"
        @click="emit('navigate', crumb.path)"
      >
        <span v-if="index > 0" class="breadcrumb__separator">/</span>
        {{ crumb.name }}
      </button>
    </div>

    <!-- Path Navigation Buttons -->
    <button class="btn-apple-icon" @click="emit('go-back')" :disabled="!canGoBack" title="后退">
      <Icon name="arrow-left" :size="18" />
    </button>
    <button class="btn-apple-icon" @click="emit('go-forward')" :disabled="!canGoForward" title="前进">
      <Icon name="arrow-right" :size="18" />
    </button>
    <button class="btn-apple-icon" @click="emit('go-up')" :disabled="currentPath === '/'" title="上级目录">
      <Icon name="arrow-up" :size="18" />
    </button>

    <div class="toolbar__spacer"></div>

    <!-- Search Box -->
    <SearchInput
      :model-value="searchQuery"
      placeholder="搜索文件..."
      @search="emit('search', $event)"
      @clear="emit('clear-search')"
    />

    <button class="btn-apple-secondary" @click="emit('refresh')">刷新</button>
    <button class="btn-apple-secondary" @click="emit('upload')" :disabled="!canUpload">上传</button>
    <button class="btn-apple-secondary" @click="emit('share')" :disabled="!canShare">分享</button>
    <button class="btn-apple-secondary" @click="emit('paste')" :disabled="!canPaste || !canWrite">粘贴</button>

    <div class="toolbar__view-toggle">
      <button
        class="view-toggle__btn"
        :class="{ 'view-toggle__btn--active': viewMode === 'list' }"
        @click="emit('toggle-view', 'list')"
      >
        <Icon name="list" :size="18" />
      </button>
      <button
        class="view-toggle__btn"
        :class="{ 'view-toggle__btn--active': viewMode === 'grid' }"
        @click="emit('toggle-view', 'grid')"
      >
        <Icon name="grid" :size="18" />
      </button>
    </div>

    <button class="btn-apple-secondary" @click="emit('toggle-floating')" title="打开浮窗">浮窗</button>
  </div>
</template>

<script setup>
import { Icon } from './common'
import SearchInput from './common/SearchInput.vue'

defineProps({
  currentPath: {
    type: String,
    default: '/'
  },
  breadcrumbs: {
    type: Array,
    default: () => []
    // [{ name: string, path: string }]
  },
  viewMode: {
    type: String,
    default: 'list'
    // 'list' | 'grid'
  },
  searchQuery: {
    type: String,
    default: ''
  },
  canGoBack: {
    type: Boolean,
    default: false
  },
  canGoForward: {
    type: Boolean,
    default: false
  },
  canUpload: {
    type: Boolean,
    default: false
  },
  canShare: {
    type: Boolean,
    default: false
  },
  canPaste: {
    type: Boolean,
    default: false
  },
  canWrite: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'navigate',
  'go-back',
  'go-forward',
  'go-up',
  'refresh',
  'upload',
  'share',
  'paste',
  'toggle-view',
  'search',
  'clear-search',
  'toggle-floating'
])
</script>

<style scoped>
.file-view__toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--color-overlay-background, #ffffff);
  border-bottom: 1px solid var(--color-separator, rgba(0, 0, 0, 0.1));
  min-height: 48px;
}

.file-view__breadcrumb {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
  max-width: 300px;
}

.breadcrumb__item {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 8px;
  background: none;
  border: none;
  border-radius: 6px;
  font-size: 13px;
  color: var(--color-label, #1d1d1f);
  cursor: pointer;
  transition: all 0.15s ease;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.breadcrumb__item:hover {
  background-color: var(--color-fill-secondary, #f5f5f7);
}

.breadcrumb__item--active {
  font-weight: 600;
  color: var(--color-label, #1d1d1f);
}

.breadcrumb__separator {
  color: var(--color-label-tertiary, #aeaeb2);
  margin: 0 2px;
}

.toolbar__spacer {
  flex: 1;
}

.btn-apple-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: none;
  border: none;
  border-radius: 6px;
  color: var(--color-label, #1d1d1f);
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-apple-icon:hover:not(:disabled) {
  background-color: var(--color-fill-secondary, #f5f5f7);
}

.btn-apple-icon:disabled {
  color: var(--color-label-tertiary, #aeaeb2);
  cursor: not-allowed;
}

.btn-apple-secondary {
  padding: 6px 12px;
  background-color: var(--color-fill-secondary, #f5f5f7);
  color: var(--color-label, #1d1d1f);
  border: none;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.btn-apple-secondary:hover:not(:disabled) {
  background-color: var(--color-fill-tertiary, #e8e8ed);
}

.btn-apple-secondary:disabled {
  color: var(--color-label-tertiary, #aeaeb2);
  cursor: not-allowed;
}

.toolbar__view-toggle {
  display: flex;
  gap: 4px;
  padding: 2px;
  background-color: var(--color-fill-secondary, #f5f5f7);
  border-radius: 6px;
}

.view-toggle__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  border-radius: 4px;
  color: var(--color-label-secondary, #86868b);
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-toggle__btn:hover {
  color: var(--color-label, #1d1d1f);
}

.view-toggle__btn--active {
  background-color: var(--color-overlay-background, #ffffff);
  color: var(--color-label, #1d1d1f);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>