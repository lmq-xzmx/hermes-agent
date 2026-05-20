<template>
  <div class="trash-view">
    <header class="trash-view__header">
      <div class="trash-view__header-left">
        <h2 class="trash-view__title">
          <Icon name="trash" :size="20" />
          <span>回收站</span>
        </h2>
        <span
          v-if="trashItems.length > 0"
          class="trash-view__count"
        >{{ trashItems.length }} 项</span>
      </div>

      <div class="trash-view__actions">
        <div class="trash-view__select-wrapper">
          <select
            v-model="selectedSpaceId"
            @change="onSpaceChange"
            class="trash-view__select"
          >
            <option value="">-- 选择空间 --</option>
            <option
              v-for="ctx in storageContexts"
              :key="ctx.space_id"
              :value="ctx.space_id"
            >
              {{ ctx.space_name || ctx.space_id }}
            </option>
          </select>
          <span class="trash-view__select-arrow">›</span>
        </div>

        <button class="trash-view__btn trash-view__btn--secondary" @click="loadTrash">
          <Icon name="refresh" :size="14" class="trash-view__btn-icon" />
          刷新
        </button>
        <button
          class="trash-view__btn trash-view__btn--danger"
          @click="emptyTrash"
          :disabled="trashItems.length === 0 || !canEmptyTrash"
          :title="!canEmptyTrash ? '只有空间所有者可以清空回收站' : ''"
        >
          <Icon name="trash" :size="14" class="trash-view__btn-icon" />
          清空
        </button>
      </div>
    </header>

    <main class="trash-view__content">
      <div v-if="loading" class="trash-view__loading">
        <div class="trash-view__spinner"></div>
        <span class="trash-view__loading-text">加载中...</span>
      </div>

      <div v-else-if="trashItems.length === 0" class="trash-view__empty">
        <Icon name="trash" :size="48" class="trash-view__empty-icon" />
        <p class="trash-view__empty-title">回收站为空</p>
        <p class="trash-view__empty-desc">删除的文件将显示在这里</p>
      </div>

      <div v-else class="trash-view__table-wrapper">
        <table class="trash-view__table">
          <thead class="trash-view__table-head">
            <tr>
              <th class="trash-view__th trash-view__th--name">名称</th>
              <th class="trash-view__th trash-view__th--type">类型</th>
              <th class="trash-view__th trash-view__th--date">删除时间</th>
              <th class="trash-view__th trash-view__th--path">原始位置</th>
              <th class="trash-view__th trash-view__th--actions">操作</th>
            </tr>
          </thead>
          <tbody class="trash-view__table-body">
            <tr
              v-for="item in trashItems"
              :key="item.id"
              class="trash-view__row"
            >
              <td class="trash-view__cell trash-view__cell--name">
                <div class="trash-view__file">
                  <Icon :name="item.is_directory ? 'folder' : 'file'" :size="28" class="trash-view__file-icon" />
                  <span class="trash-view__file-name">{{ item.name }}</span>
                </div>
              </td>
              <td class="trash-view__cell trash-view__cell--type">
                <span
                  class="trash-view__badge"
                  :class="item.is_directory ? 'trash-view__badge--folder' : 'trash-view__badge--file'"
                >
                  {{ item.is_directory ? '文件夹' : '文件' }}
                </span>
              </td>
              <td class="trash-view__cell trash-view__cell--date">
                {{ formatDate(item.deleted_at) }}
              </td>
              <td class="trash-view__cell trash-view__cell--path">
                <code class="trash-view__path">{{ item.original_path }}</code>
              </td>
              <td class="trash-view__cell trash-view__cell--actions">
                <div class="trash-view__cell-actions">
                  <button
                    class="trash-view__btn trash-view__btn--primary trash-view__btn--sm"
                    @click="restoreItem(item)"
                    :disabled="!canRestoreItem(item)"
                    :title="!canRestoreItem(item) ? '您只能恢复自己删除的文件' : ''"
                  >
                    恢复
                  </button>
                  <button
                    class="trash-view__btn trash-view__btn--danger trash-view__btn--sm"
                    @click="deleteItem(item)"
                    :disabled="!canDelete"
                    :title="!canDelete ? '只有空间所有者可以永久删除' : ''"
                  >
                    删除
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
/**
 * TrashView - 回收站视图
 *
 * 功能:
 * - 查看已删除文件列表
 * - 按空间筛选
 * - 恢复或永久删除文件
 * - 清空回收站
 *
 * === 生命周期规则 ===
 * | 操作 | admin | owner | member | viewer |
 * |------|-------|-------|--------|--------|
 * | 查看列表 | ✓ | ✓ | ✓ | ✓ |
 * | 恢复文件 | ✓ | ✓ | 只能恢复自己的 | ✗ |
 * | 永久删除 | ✓ | ✓ | ✗ | ✗ |
 * | 清空回收站 | ✓ | ✓ | ✗ | ✗ |
 */

import { ref, computed, onMounted } from 'vue'
import { api } from '../services/api.js'
import { Icon } from '../components/common'
import { useAuthStore } from '../stores/authStore.js'

const emit = defineEmits(['show-toast'])

const authStore = useAuthStore()

// State
const trashItems = ref([])
const storageContexts = ref([])
const selectedSpaceId = ref('')
const loading = ref(false)
const currentSpaceRole = ref(null)
const currentUser = ref(null)

// System role check (admin from authStore)
const isAdmin = computed(() => authStore.userRole === 'admin')

// Space role check (from current context)
const isOwner = computed(() => currentSpaceRole.value === 'owner')
const isMember = computed(() => currentSpaceRole.value === 'member')
const isViewer = computed(() => currentSpaceRole.value === 'viewer')

// Permission helpers
const canRestore = computed(() => isAdmin.value || isOwner.value || isMember.value)
const canDelete = computed(() => isAdmin.value || isOwner.value)
const canEmptyTrash = computed(() => isAdmin.value || isOwner.value)

// Check if user can restore a specific item (member can only restore their own)
function canRestoreItem(item) {
  if (isAdmin.value || isOwner.value) return true
  if (isMember.value && item.deleted_by === currentUser.value?.id) return true
  return false
}

// Lifecycle
onMounted(async () => {
  await loadCurrentUser()
  await loadStorageContexts()
})

async function loadCurrentUser() {
  // 直接从 authStore 获取当前用户
  currentUser.value = authStore.user
}

async function loadStorageContexts() {
  try {
    const data = await api.getStorageContexts()
    storageContexts.value = data.contexts || []

    // Find current space role from storage contexts
    if (selectedSpaceId.value) {
      const ctx = storageContexts.value.find(c => c.space_id === selectedSpaceId.value)
      currentSpaceRole.value = ctx?.role || null
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function onSpaceChange() {
  // Update current space role when space changes
  const ctx = storageContexts.value.find(c => c.space_id === selectedSpaceId.value)
  currentSpaceRole.value = ctx?.role || null

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
  if (!canRestoreItem(item)) {
    emit('show-toast', {
      type: 'warning',
      title: '权限不足',
      message: '您只能恢复自己删除的文件'
    })
    return
  }

  try {
    await api.restoreTrashItem(selectedSpaceId.value, item.id)
    emit('show-toast', { type: 'success', title: '成功', message: '文件已恢复' })
    loadTrash()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function deleteItem(item) {
  if (!canDelete.value) {
    emit('show-toast', {
      type: 'warning',
      title: '权限不足',
      message: '只有空间所有者可以永久删除文件'
    })
    return
  }

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

  if (!canEmptyTrash.value) {
    emit('show-toast', {
      type: 'warning',
      title: '权限不足',
      message: '只有空间所有者可以清空回收站'
    })
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
/* ============================================
   Block: trash-view
   Trash View - Apple DESIGN.md Compliant
   ============================================ */

/* === Layout === */
.trash-view {
  /* Layout */
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: auto;
  padding: var(--spacing-lg);

  /* Visual */
  background: transparent;
  box-sizing: border-box;
}

/* === Header === */
.trash-view__header {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-md);

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin-left: auto;
  margin-right: auto;
  box-sizing: border-box;
}

.trash-view__header-left {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
}

.trash-view__title {
  /* Typography */
  font: var(--text-tagline);
  color: var(--color-ink);

  /* Reset */
  margin: 0;
}

.trash-view__count {
  /* Typography */
  font: var(--text-caption);

  /* Visual */
  color: var(--color-ink-muted-48);
  background: var(--color-surface-pearl);

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-sm);

  /* Shape */
  border-radius: var(--radius-pill);
}

.trash-view__actions {
  /* Layout */
  display: flex;
  gap: var(--spacing-sm);
  align-items: center;
}

/* === Select === */
.trash-view__select-wrapper {
  /* Positioning */
  position: relative;
}

.trash-view__select {
  /* Layout */
  appearance: none;

  /* Box Model */
  padding: var(--spacing-sm) 36px var(--spacing-sm) var(--spacing-sm);
  height: 44px;
  min-width: 180px;
  box-sizing: border-box;

  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);

  /* Interaction */
  cursor: pointer;
  transition: border-color 0.2s ease;
}

.trash-view__select:focus {
  /* Outline */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

.trash-view__select-arrow {
  /* Positioning */
  position: absolute;
  right: var(--spacing-md);
  top: 50%;
  transform: translateY(-50%);

  /* Typography */
  font: var(--text-caption);

  /* Visual */
  color: var(--color-ink-muted-48);

  /* Interaction */
  pointer-events: none;
}

/* === Buttons === */
.trash-view__btn {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xxs);

  /* Box Model */
  padding: 11px 22px;

  /* Typography */
  font: var(--text-body);
  color: inherit;

  /* Shape */
  border-radius: var(--radius-pill);
  border: none;

  /* Interaction */
  cursor: pointer;
  transition: transform 0.1s ease, background-color 0.2s ease;
  white-space: nowrap;
}

.trash-view__btn:active:not(:disabled) {
  /* Interaction */
  transform: scale(0.95);
}

.trash-view__btn:focus {
  /* Outline */
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.trash-view__btn:disabled {
  /* Visual */
  opacity: 0.5;

  /* Interaction */
  cursor: not-allowed;
}

.trash-view__btn:disabled:hover {
  /* Reset hover state when disabled */
  transform: none;
}

.trash-view__btn--primary {
  /* Visual */
  background-color: var(--color-primary);
  color: var(--color-body-on-dark);
}

.trash-view__btn--primary:hover {
  /* Visual */
  background-color: var(--color-primary-hover);
}

.trash-view__btn--secondary {
  /* Visual */
  background-color: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.trash-view__btn--secondary:hover {
  /* Visual */
  background-color: var(--color-primary);
  color: var(--color-body-on-dark);
}

.trash-view__btn--danger {
  /* Visual */
  background-color: var(--color-danger);
  color: var(--color-body-on-dark);
}

.trash-view__btn--danger:hover {
  /* Visual */
  background-color: var(--color-danger-strong);
}

.trash-view__btn--sm {
  /* Box Model */
  padding: 6px 14px;

  /* Typography */
  font: var(--text-caption);
}

.trash-view__btn-icon {
  /* Layout */
  flex-shrink: 0;
}

/* === Content === */
.trash-view__content {
  /* Visual */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);

  /* Layout */
  overflow: hidden;

  /* Constraint */
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
  box-sizing: border-box;

  /* Box Model - padding like FileView content */
  padding: var(--spacing-lg);
}

/* === Loading === */
.trash-view__loading {
  /* Layout */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  /* Box Model */
  padding: var(--spacing-xxl);
  gap: var(--spacing-md);

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.trash-view__spinner {
  /* Box Model */
  width: var(--spacing-lg);
  height: var(--spacing-lg);

  /* Border */
  border: 2px solid var(--color-hairline);
  border-top-color: var(--color-primary);

  /* Shape */
  border-radius: var(--radius-full);

  /* Animation */
  animation: trash-view__spin 0.8s linear infinite;
}

@keyframes trash-view__spin {
  to {
    transform: rotate(360deg);
  }
}

.trash-view__loading-text {
  /* Typography */
  font: var(--text-body);
}

/* === Empty === */
.trash-view__empty {
  /* Layout */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;

  /* Box Model */
  padding: var(--spacing-xxl) var(--spacing-lg);

  /* Typography */
  text-align: center;
}

.trash-view__empty-icon {
  /* Box Model */
  margin-bottom: var(--spacing-md);

  /* Visual */
  opacity: 0.5;
}

.trash-view__empty-title {
  /* Typography */
  font: var(--text-body-strong);
  color: var(--color-ink);

  /* Reset */
  margin: 0 0 var(--spacing-xs);
}

.trash-view__empty-desc {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);

  /* Reset */
  margin: 0;
}

/* === Table === */
.trash-view__table-wrapper {
  /* Layout */
  overflow-x: auto;
}

.trash-view__table {
  /* Layout */
  width: 100%;

  /* Border */
  border-collapse: collapse;
}

.trash-view__table-head {
  /* Visual */
  background: var(--color-canvas-parchment);
}

.trash-view__th {
  /* Typography */
  font: var(--text-caption-strong);
  text-transform: uppercase;
  color: var(--color-ink-muted-48);

  /* Box Model */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Border */
  border-bottom: 1px solid var(--color-hairline);

  /* Layout */
  text-align: left;
  vertical-align: middle;
}

/* === Row === */
.trash-view__table-body .trash-view__row td {
  /* Border */
  border-bottom: 1px solid var(--color-divider-soft);
}

.trash-view__table-body .trash-view__row:last-child td {
  /* Border */
  border-bottom: none;
}

.trash-view__table-body .trash-view__row:hover td {
  /* Visual */
  background: var(--color-surface-pearl);
}

/* === Cell === */
.trash-view__cell {
  /* Box Model */
  padding: var(--spacing-sm) var(--spacing-md);

  /* Layout */
  vertical-align: middle;
  text-align: left;
}

.trash-view__cell--name {
  /* Layout */
  min-width: 200px;
}

.trash-view__cell--type {
  /* Layout */
  width: 100px;
}

.trash-view__cell--date {
  /* Layout */
  width: 160px;

  /* Typography */
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.trash-view__cell--path {
  /* Layout */
  max-width: 200px;
}

.trash-view__cell--actions {
  /* Layout */
  width: 140px;
}

/* === File === */
.trash-view__file {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.trash-view__file-icon {
  /* Layout */
  flex-shrink: 0;
}

.trash-view__file-name {
  /* Typography */
  font: var(--text-body);
  color: var(--color-ink);

  /* Layout */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* === Badge === */
.trash-view__badge {
  /* Layout */
  display: inline-flex;
  align-items: center;

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-sm);

  /* Typography */
  font: var(--text-caption);

  /* Shape */
  border-radius: var(--radius-pill);
}

.trash-view__badge--folder {
  /* Visual */
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.trash-view__badge--file {
  /* Visual */
  background: var(--color-surface-pearl);
  color: var(--color-ink-muted-80);
}

/* === Path === */
.trash-view__path {
  /* Typography */
  font: var(--text-caption);
  color: var(--color-ink-muted-48);

  /* Visual */
  background: var(--color-canvas-parchment);

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-xs);

  /* Shape */
  border-radius: var(--radius-xs);

  /* Layout */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
  max-width: 200px;
}

/* === Cell Actions === */
.trash-view__cell-actions {
  /* Layout */
  display: flex;
  gap: var(--spacing-xs);

  /* Interaction */
  opacity: 0.8;
  transition: opacity 0.2s ease;
}

.trash-view__row:hover .trash-view__cell-actions {
  /* Interaction */
  opacity: 1;
}
</style>
