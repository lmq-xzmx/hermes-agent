<template>
  <div class="storage-pool-view">
    <!-- ============================================
         Header
         ============================================ -->
    <header class="storage-pool-view__header">
      <h2 class="storage-pool-view__title">存储池</h2>
      <ButtonPrimary v-if="isAdmin" @click="showCreatePool">+ 创建存储池</ButtonPrimary>
    </header>

    <!-- ============================================
         Content
         ============================================ -->
    <main class="storage-pool-view__content">
      <!-- Loading State -->
      <div v-if="loading" class="storage-pool-view__loading">
        <span>加载中...</span>
      </div>

      <!-- Empty State -->
      <div v-else-if="pools.length === 0" class="storage-pool-view__empty">
        <div class="storage-pool-view__empty-icon">💾</div>
        <p class="storage-pool-view__empty-text">暂无存储池</p>
        <ButtonSecondary v-if="isAdmin" @click="showCreatePool">创建第一个存储池</ButtonSecondary>
      </div>

      <!-- Pool Grid -->
      <div v-else class="storage-pool-view__grid">
        <article
          v-for="pool in pools"
          :key="pool.pool_id"
          class="pool-card"
        >
          <!-- Card Header -->
          <header class="pool-card__header">
            <div class="pool-card__info">
              <h3 class="pool-card__name">{{ pool.name }}</h3>
              <span v-if="pool.description" class="pool-card__desc">
                {{ pool.description }}
              </span>
            </div>
            <span
              class="pool-card__badge"
              :class="pool.status === 'active' ? 'pool-card__badge--active' : 'pool-card__badge--inactive'"
            >
              {{ pool.status === 'active' ? '活跃' : '停用' }}
            </span>
          </header>

          <!-- Stats -->
          <dl class="pool-card__stats">
            <div class="pool-card__stat-row">
              <dt class="pool-card__stat-label">类型</dt>
              <dd class="pool-card__stat-value">{{ pool.type || '标准' }}</dd>
            </div>
            <div class="pool-card__stat-row">
              <dt class="pool-card__stat-label">容量</dt>
              <dd class="pool-card__stat-value">{{ formatSize(pool.total_bytes) }}</dd>
            </div>
            <div class="pool-card__stat-row">
              <dt class="pool-card__stat-label">已用</dt>
              <dd class="pool-card__stat-value">{{ formatSize(pool.used_bytes) }}</dd>
            </div>
          </dl>

          <!-- Progress -->
          <div class="pool-card__progress">
            <div class="pool-card__progress-bar">
              <div
                class="pool-card__progress-fill"
                :class="getQuotaClass(pool.usage_ratio)"
                :style="{ width: `${(pool.usage_ratio * 100).toFixed(1)}%` }"
              ></div>
            </div>
            <span class="pool-card__progress-text">
              {{ ((pool.usage_ratio || 0) * 100).toFixed(1) }}%
            </span>
          </div>

          <!-- Actions -->
          <footer class="pool-card__actions">
            <template v-if="isAdmin">
              <ButtonSecondary size="sm" @click="runCleanup(pool.pool_id)">清理</ButtonSecondary>
              <ButtonSecondary size="sm" @click="editPool(pool)">编辑</ButtonSecondary>
              <ButtonPearl size="sm" @click="confirmDeletePool(pool)">删除</ButtonPearl>
            </template>
          </footer>
        </article>
      </div>
    </main>

    <!-- ============================================
         Modal
         ============================================ -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <CardUtility class="modal-overlay__card">
        <header class="modal-overlay__header">
          <h3 class="modal-overlay__title">
            {{ editingPool ? '编辑存储池' : '创建存储池' }}
          </h3>
          <button class="modal-overlay__close" @click="closeModal">✕</button>
        </header>

        <div class="modal-overlay__body">
          <div class="form-field">
            <label class="form-field__label">名称</label>
            <input
              v-model="poolForm.name"
              type="text"
              placeholder="存储池名称"
              class="apple-input apple-input--full"
            >
          </div>

          <div class="form-field">
            <label class="form-field__label">类型</label>
            <select v-model="poolForm.type" class="apple-select apple-select--full">
              <option value="standard">标准</option>
              <option value="high-performance">高性能</option>
              <option value="archival">归档</option>
            </select>
          </div>

          <div class="form-field">
            <label class="form-field__label">最大容量</label>
            <select
              v-model="poolForm.sizePreset"
              @change="onSizePresetChange"
              class="apple-select apple-select--full"
            >
              <option value="">自定义</option>
              <option value="10GB">10 GB</option>
              <option value="50GB">50 GB</option>
              <option value="100GB">100 GB</option>
              <option value="500GB">500 GB</option>
              <option value="1TB">1 TB</option>
            </select>
            <input
              v-if="!poolForm.sizePreset"
              v-model="poolForm.size"
              type="text"
              placeholder="例如: 100GB"
              class="apple-input apple-input--full form-field__input"
            >
          </div>

          <div class="form-field">
            <label class="form-field__label">描述 (可选)</label>
            <textarea
              v-model="poolForm.description"
              rows="3"
              placeholder="描述存储池用途"
              class="apple-textarea apple-textarea--full"
            ></textarea>
          </div>
        </div>

        <footer class="modal-overlay__footer">
          <ButtonSecondary @click="closeModal">取消</ButtonSecondary>
          <ButtonPrimary @click="submitPool" :disabled="!poolForm.name">
            {{ editingPool ? '保存' : '创建' }}
          </ButtonPrimary>
        </footer>
      </CardUtility>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePoolStore } from '../stores/poolStore.js'
import { useAuthStore } from '../stores/authStore.js'
import {
  ButtonPrimary,
  ButtonSecondary,
  ButtonPearl,
  CardUtility
} from '../components/common'

const emit = defineEmits(['show-toast'])

const poolStore = usePoolStore()
const authStore = useAuthStore()

// Admin check: only admin role can manage storage pools
const isAdmin = computed(() => authStore.userRole === 'admin')

const pools = computed(() => poolStore.pools)
const loading = computed(() => poolStore.loading)
const showModal = ref(false)
const editingPool = ref(null)
const poolForm = ref({
  name: '',
  type: 'standard',
  sizePreset: '100GB',
  size: '',
  description: ''
})

onMounted(() => {
  loadPools()
})

async function loadPools() {
  try {
    await poolStore.loadPools()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function showCreatePool() {
  editingPool.value = null
  poolForm.value = {
    name: '',
    type: 'standard',
    sizePreset: '100GB',
    size: '',
    description: ''
  }
  showModal.value = true
}

function editPool(pool) {
  if (!isAdmin.value) {
    emit('show-toast', { type: 'error', title: '权限不足', message: '只有管理员可以编辑存储池' })
    return
  }
  editingPool.value = pool
  poolForm.value = {
    name: pool.name,
    type: pool.type || 'standard',
    sizePreset: '',
    size: formatSize(pool.total_bytes),
    description: pool.description || ''
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  editingPool.value = null
}

function onSizePresetChange() {
  if (poolForm.value.sizePreset) {
    poolForm.value.size = poolForm.value.sizePreset
  }
}

async function submitPool() {
  if (!poolForm.value.name) return

  const size = poolForm.value.sizePreset || poolForm.value.size || '100GB'
  const name = poolForm.value.name.trim()

  try {
    if (editingPool.value) {
      await poolStore.updatePool(editingPool.value.pool_id, {
        name,
        type: poolForm.value.type,
        description: poolForm.value.description
      })
      emit('show-toast', { type: 'success', title: '成功', message: '存储池已更新' })
    } else {
      await poolStore.createPool(name, poolForm.value.type, size)
      emit('show-toast', { type: 'success', title: '成功', message: '存储池已创建' })
    }
    closeModal()
    await loadPools()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function confirmDeletePool(pool) {
  if (!isAdmin.value) {
    emit('show-toast', { type: 'error', title: '权限不足', message: '只有管理员可以删除存储池' })
    return
  }
  if (!confirm(`确定要删除存储池 "${pool.name}" 吗？此操作不可恢复。`)) return
  deletePool(pool.pool_id)
}

async function deletePool(poolId) {
  if (!isAdmin.value) return
  try {
    await poolStore.deletePool(poolId)
    emit('show-toast', { type: 'success', title: '成功', message: '存储池已删除' })
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function runCleanup(poolId) {
  if (!isAdmin.value) {
    emit('show-toast', { type: 'error', title: '权限不足', message: '只有管理员可以清理存储池' })
    return
  }
  try {
    await poolStore.runCleanup(poolId, 'temp')
    emit('show-toast', { type: 'success', title: '成功', message: '清理完成' })
    await loadPools()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function getQuotaClass(usage) {
  if (usage > 0.9) return 'pool-card__progress-fill--danger'
  if (usage > 0.7) return 'pool-card__progress-fill--warn'
  return 'pool-card__progress-fill--ok'
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
/* === Block: storage-pool-view === */
.storage-pool-view {
  /* Layout */
  display: flex;
  flex-direction: column;
  flex: 1;
  height: 100%;
  overflow: auto;
  padding: var(--spacing-lg);
  box-sizing: border-box;

  /* Visual */
  background: transparent;
}

/* === Element: storage-pool-view__header === */
.storage-pool-view__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: var(--spacing-sm);

  /* Box Model */
  padding: var(--spacing-md) var(--spacing-lg);
  margin-bottom: var(--spacing-md);

  /* Visual - White card like FileView */
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

/* === Element: storage-pool-view__title === */
.storage-pool-view__title {
  font: var(--text-tagline);
  color: var(--color-ink);
  margin: 0;
}

/* === Element: storage-pool-view__content === */
.storage-pool-view__content {
  width: 100%;
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
  box-sizing: border-box;

  /* Visual - White card like FileView */
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

/* === Element: storage-pool-view__loading === */
.storage-pool-view__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* === Element: storage-pool-view__empty === */
.storage-pool-view__empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
}

/* === Element: storage-pool-view__empty-icon === */
.storage-pool-view__empty-icon {
  font: var(--text-hero-display);
  margin-bottom: var(--spacing-lg);
  opacity: 0.5;
}

/* === Element: storage-pool-view__empty-text === */
.storage-pool-view__empty-text {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--spacing-lg);
}

/* === Element: storage-pool-view__grid === */
.storage-pool-view__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-lg);
}

/* === Block: pool-card === */
.pool-card {
  display: flex;
  flex-direction: column;
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

/* === Element: pool-card__header === */
.pool-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

/* === Element: pool-card__info === */
.pool-card__info {
  flex: 1;
}

/* === Element: pool-card__name === */
.pool-card__name {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

/* === Element: pool-card__desc === */
.pool-card__desc {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  display: block;
  margin-top: var(--spacing-xxs);
}

/* === Element: pool-card__badge === */
.pool-card__badge {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption-strong);
}

.pool-card__badge--active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.pool-card__badge--inactive {
  background: var(--color-gray-subtle);
  color: var(--color-ink-muted-48);
}

/* === Element: pool-card__stats === */
.pool-card__stats {
  margin-bottom: var(--spacing-md);
}

/* === Element: pool-card__stat-row === */
.pool-card__stat-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-divider-soft);
}

.pool-card__stat-row:last-child {
  border-bottom: none;
}

/* === Element: pool-card__stat-label === */
.pool-card__stat-label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: pool-card__stat-value === */
.pool-card__stat-value {
  font: var(--text-caption-strong);
  color: var(--color-ink);
}

/* === Element: pool-card__progress === */
.pool-card__progress {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-md);
}

/* === Element: pool-card__progress-bar === */
.pool-card__progress-bar {
  flex: 1;
  height: var(--spacing-xs);
  background: var(--color-hairline);
  border-radius: var(--radius-pill);
  overflow: hidden;
}

/* === Element: pool-card__progress-fill === */
.pool-card__progress-fill {
  height: 100%;
  border-radius: var(--radius-pill);
  transition: width 0.3s ease;
}

.pool-card__progress-fill--ok {
  background: var(--color-primary);
}

.pool-card__progress-fill--warn {
  background: var(--color-warning);
}

.pool-card__progress-fill--danger {
  background: var(--color-danger);
}

/* === Element: pool-card__progress-text === */
.pool-card__progress-text {
  min-width: 50px;
  text-align: right;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

/* === Element: pool-card__actions === */
.pool-card__actions {
  display: flex;
  gap: var(--spacing-xs);
  margin-top: auto;
}

/* === Block: modal-overlay === */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-lg);
  background: var(--color-overlay);
  z-index: var(--z-modal);
}

/* === Element: modal-overlay__card === */
.modal-overlay__card {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

/* === Element: modal-overlay__header === */
.modal-overlay__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-lg);
}

/* === Element: modal-overlay__title === */
.modal-overlay__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

/* === Element: modal-overlay__close === */
.modal-overlay__close {
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--spacing-xxs);
  font: var(--text-lead);
  color: var(--color-ink-muted-48);
  transition: color var(--transition-base);
}

.modal-overlay__close:hover {
  color: var(--color-ink);
}

/* === Element: modal-overlay__body === */
.modal-overlay__body {
  margin-bottom: var(--spacing-lg);
}

/* === Element: modal-overlay__footer === */
.modal-overlay__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-sm);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-divider-soft);
}

/* === Block: form-field === */
.form-field {
  margin-bottom: var(--spacing-md);
}

/* === Element: form-field__label === */
.form-field__label {
  display: block;
  margin-bottom: var(--spacing-xxs);
  font: var(--text-caption-strong);
  color: var(--color-ink);
}

/* === Element: form-field__input === */
.form-field__input {
  margin-top: var(--spacing-xs);
}

/* === Block: apple-input, apple-select, apple-textarea === */
.apple-input,
.apple-select,
.apple-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  transition: border-color var(--transition-base);
  box-sizing: border-box;
}

.apple-input--full,
.apple-select--full,
.apple-textarea--full {
  width: 100%;
}

.apple-input:focus,
.apple-select:focus,
.apple-textarea:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
  border-color: transparent;
}

/* === Element: apple-textarea === */
.apple-textarea {
  resize: vertical;
  min-height: 80px;
}
</style>
