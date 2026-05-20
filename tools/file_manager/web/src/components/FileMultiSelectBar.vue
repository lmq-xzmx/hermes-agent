<template>
  <!-- Multi-Selection Action Bar -->
  <div v-if="selectedCount > 0" class="file-view__multi-select-bar">
    <div class="multi-select-bar__info">
      <span class="multi-select-bar__count">已选择 {{ selectedCount }} 项</span>
      <button class="btn-apple-link-sm" @click="emit('clear-selection')">取消选择</button>
    </div>
    <div class="multi-select-bar__actions">
      <button class="btn-apple-secondary btn-sm" @click="emit('share')" :disabled="!canShare">分享</button>
      <button class="btn-apple-secondary btn-sm" @click="emit('download')">下载</button>
      <button class="btn-apple-secondary btn-sm" @click="emit('paste')" :disabled="!canPaste || !canWrite">粘贴</button>
      <button class="btn-apple-danger btn-sm" @click="emit('delete')" :disabled="!canDelete">删除</button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  selectedCount: {
    type: Number,
    default: 0
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
  },
  canDelete: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['share', 'download', 'paste', 'delete', 'clear-selection'])
</script>

<style scoped>
.file-view__multi-select-bar {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  background: var(--color-overlay-background, rgba(255, 255, 255, 0.95));
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.15), 0 0 0 0.5px rgba(0, 0, 0, 0.05);
  z-index: 100;
}

.multi-select-bar__info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.multi-select-bar__count {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-label, #1d1d1f);
}

.btn-apple-link-sm {
  background: none;
  border: none;
  color: var(--color-link, #007aff);
  font-size: 13px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.15s ease;
}

.btn-apple-link-sm:hover {
  background-color: var(--color-fill-secondary, rgba(0, 122, 255, 0.1));
}

.multi-select-bar__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.multi-select-bar__actions .btn-sm {
  padding: 6px 12px;
  font-size: 13px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-apple-secondary {
  background-color: var(--color-fill-secondary, #f5f5f7);
  color: var(--color-label, #1d1d1f);
}

.btn-apple-secondary:hover:not(:disabled) {
  background-color: var(--color-fill-tertiary, #e8e8ed);
}

.btn-apple-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-apple-danger {
  background-color: var(--color-system-red, #ff3b30);
  color: white;
}

.btn-apple-danger:hover:not(:disabled) {
  background-color: var(--color-system-red-dark, #d93030);
}
</style>