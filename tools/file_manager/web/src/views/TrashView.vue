<template>
  <div class="trash-view">
    <!-- Header -->
    <div class="view-header">
      <div class="header-left">
        <h2 class="section-title">🗑️ 回收站</h2>
        <span class="item-count" v-if="trashItems.length > 0">{{ trashItems.length }} 项</span>
      </div>
      <div class="header-actions">
        <div class="select-wrapper">
          <select v-model="selectedSpaceId" @change="onSpaceChange" class="apple-select">
            <option value="">-- 选择空间 --</option>
            <option v-for="ctx in storageContexts" :key="ctx.space_id" :value="ctx.space_id">
              {{ ctx.space_name || ctx.space_id }}
            </option>
          </select>
          <span class="select-arrow">›</span>
        </div>
        <button class="btn-apple-secondary" @click="loadTrash">
          <span class="btn-icon">🔄</span>
          刷新
        </button>
        <button
          class="btn-apple-danger"
          @click="emptyTrash"
          :disabled="trashItems.length === 0"
        >
          <span class="btn-icon">🗑️</span>
          清空
        </button>
      </div>
    </div>

    <!-- Content -->
    <div class="trash-content">
      <!-- Loading State -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <span>加载中...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="trashItems.length === 0" class="empty-state">
        <div class="empty-icon">🗑️</div>
        <p class="empty-title">回收站为空</p>
        <p class="empty-desc">删除的文件将显示在这里</p>
      </div>

      <!-- Trash Table -->
      <div v-else class="table-wrapper">
        <table class="apple-table">
          <thead>
            <tr>
              <th class="col-name">名称</th>
              <th class="col-type">类型</th>
              <th class="col-date">删除时间</th>
              <th class="col-path">原始位置</th>
              <th class="col-actions">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in trashItems" :key="item.id" class="table-row">
              <td class="cell-name">
                <div class="file-name">
                  <span class="file-icon">{{ item.is_directory ? '📁' : '📄' }}</span>
                  <span class="file-name-text">{{ item.name }}</span>
                </div>
              </td>
              <td class="cell-type">
                <span class="type-badge" :class="item.is_directory ? 'folder' : 'file'">
                  {{ item.is_directory ? '文件夹' : '文件' }}
                </span>
              </td>
              <td class="cell-date">{{ formatDate(item.deleted_at) }}</td>
              <td class="cell-path">
                <code class="path-code">{{ item.original_path }}</code>
              </td>
              <td class="cell-actions">
                <div class="action-buttons">
                  <button class="btn-apple-primary btn-sm" @click="restoreItem(item)">
                    恢复
                  </button>
                  <button class="btn-apple-danger btn-sm" @click="deleteItem(item)">
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api.js'

const emit = defineEmits(['show-toast'])

const trashItems = ref([])
const storageContexts = ref([])
const selectedSpaceId = ref('')
const loading = ref(false)

onMounted(() => {
  loadStorageContexts()
})

async function loadStorageContexts() {
  try {
    const data = await api.getStorageContexts()
    storageContexts.value = data.contexts || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function onSpaceChange() {
  if (selectedSpaceId.value) {
    loadTrash()
  }
}

async function loadTrash() {
  if (!selectedSpaceId.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请先选择一个空间' })
    return
  }

  loading.value = true
  try {
    const data = await api.getTrash(selectedSpaceId.value)
    trashItems.value = data.items || []
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

async function restoreItem(item) {
  try {
    await api.restoreTrashItem(selectedSpaceId.value, item.id)
    emit('show-toast', { type: 'success', title: '成功', message: '文件已恢复' })
    loadTrash()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function deleteItem(item) {
  if (!confirm(`确定要永久删除 "${item.name}" 吗？此操作不可恢复。`)) return

  try {
    await api.permanentDeleteTrashItem(selectedSpaceId.value, item.id)
    emit('show-toast', { type: 'success', title: '成功', message: '文件已永久删除' })
    loadTrash()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function emptyTrash() {
  if (!selectedSpaceId.value) {
    emit('show-toast', { type: 'error', title: '错误', message: '请先选择一个空间' })
    return
  }

  if (!confirm('确定要清空回收站吗？所有文件将被永久删除，此操作不可恢复。')) return

  loading.value = true
  try {
    await api.emptyTrash(selectedSpaceId.value)
    emit('show-toast', { type: 'success', title: '成功', message: '回收站已清空' })
    loadTrash()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  } finally {
    loading.value = false
  }
}

function formatDate(str) {
  if (!str) return '-'
  const d = new Date(str)
  return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.trash-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-lg);
  background: var(--color-canvas-parchment);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-hairline);
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.section-title {
  font: var(--text-tagline);
  color: var(--color-ink);
  margin: 0;
}

.item-count {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  background: var(--color-surface-pearl);
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

/* Select - Apple Pill Style (DESIGN.md) */
.select-wrapper {
  position: relative;
}

.apple-select {
  appearance: none;
  padding: var(--spacing-sm) 20px;
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  color: var(--color-ink);
  font: var(--text-body);
  cursor: pointer;
  transition: border-color 0.2s;
  height: 44px;
  min-width: 180px;
  box-sizing: border-box;
}

.apple-select:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

.select-arrow {
  position: absolute;
  right: var(--space-md);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-ink-muted-48);
  font-size: 14px;
  pointer-events: none;
}

/* Buttons */
.btn-icon {
  font: var(--text-body);
  line-height: 1;
}

/* Content */
.trash-content {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-hairline);
  overflow: hidden;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl);
  color: var(--color-ink-muted-48);
  font: var(--text-body);
  gap: var(--space-md);
}

.spinner {
  width: var(--spacing-lg);
  height: var(--spacing-lg);
  border: 2px solid var(--color-hairline);
  border-top-color: var(--color-primary);
  border-radius: var(--radius-full);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl) var(--space-lg);
  text-align: center;
}

.empty-icon {
  font-size: var(--spacing-xxl);
  margin-bottom: var(--space-md);
  opacity: 0.5;
}

.empty-title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0 0 var(--spacing-xs);
}

.empty-desc {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0;
}

/* Table */
.table-wrapper {
  overflow-x: auto;
}

.apple-table {
  width: 100%;
  border-collapse: collapse;
}

.apple-table th,
.apple-table td {
  text-align: left;
  padding: var(--space-sm) var(--space-md);
  vertical-align: middle;
}

.apple-table th {
  font: var(--text-caption-strong);
  text-transform: uppercase;
  color: var(--color-ink-muted-48);
  background: var(--color-canvas-parchment);
  border-bottom: 1px solid var(--color-hairline);
}

.apple-table .table-row td {
  border-bottom: 1px solid var(--color-divider-soft);
}

.apple-table .table-row:last-child td {
  border-bottom: none;
}

.apple-table .table-row:hover td {
  background: var(--color-surface-pearl);
}

/* Table Cells */
.cell-name {
  min-width: 200px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.file-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.file-name-text {
  font: var(--text-body);
  color: var(--color-ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-type {
  width: 100px;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.type-badge.folder {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.type-badge.file {
  background: var(--color-surface-pearl);
  color: var(--color-ink-muted-80);
}

.cell-date {
  width: 160px;
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.cell-path {
  max-width: 200px;
}

.path-code {
  font-family: monospace;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  background: var(--color-canvas-parchment);
  padding: var(--spacing-xxs) var(--spacing-xs);
  border-radius: var(--radius-xs);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 200px;
}

.cell-actions {
  width: 140px;
}

.action-buttons {
  display: flex;
  gap: var(--space-xs);
  opacity: 0.8;
  transition: opacity 0.2s;
}

.table-row:hover .action-buttons {
  opacity: 1;
}

</style>
