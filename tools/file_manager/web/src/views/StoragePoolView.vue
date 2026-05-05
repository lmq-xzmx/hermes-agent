<template>
  <div class="storage-pool-view">
    <!-- Header -->
    <div class="view-header">
      <h2 class="section-title">存储池</h2>
      <ButtonPrimary @click="showCreatePool">+ 创建存储池</ButtonPrimary>
    </div>

    <!-- Content -->
    <div class="pool-content">
      <div v-if="loading" class="loading-state">
        <span>加载中...</span>
      </div>

      <div v-else-if="pools.length === 0" class="empty-state">
        <div class="empty-icon">💾</div>
        <p class="empty-text">暂无存储池</p>
        <ButtonSecondary @click="showCreatePool">创建第一个存储池</ButtonSecondary>
      </div>

      <div v-else class="pool-grid">
        <div v-for="pool in pools" :key="pool.pool_id" class="pool-card">
          <div class="pool-card-header">
            <div class="pool-info">
              <span class="pool-name">{{ pool.name }}</span>
              <span v-if="pool.description" class="pool-desc">{{ pool.description }}</span>
            </div>
            <span class="badge" :class="pool.status === 'active' ? 'active' : 'inactive'">
              {{ pool.status === 'active' ? '活跃' : '停用' }}
            </span>
          </div>

          <div class="pool-stats">
            <div class="stat-row">
              <span class="stat-label">类型</span>
              <span class="stat-value">{{ pool.type || '标准' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">容量</span>
              <span class="stat-value">{{ formatSize(pool.total_bytes) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">已用</span>
              <span class="stat-value">{{ formatSize(pool.used_bytes) }}</span>
            </div>
          </div>

          <div class="pool-progress">
            <div class="progress-bar">
              <div
                class="progress-fill"
                :class="getQuotaClass(pool.usage_ratio)"
                :style="{ width: `${(pool.usage_ratio * 100).toFixed(1)}%` }"
              ></div>
            </div>
            <span class="progress-text">{{ ((pool.usage_ratio || 0) * 100).toFixed(1) }}%</span>
          </div>

          <div class="pool-actions">
            <ButtonSecondary size="sm" @click="editPool(pool)">编辑</ButtonSecondary>
            <ButtonSecondary size="sm" @click="viewPoolDetails(pool)">详情</ButtonSecondary>
            <ButtonPearl size="sm" @click="confirmDeletePool(pool)">删除</ButtonPearl>
          </div>
        </div>
      </div>
    </div>

    <!-- Pool Details Panel -->
    <div v-if="selectedPool" class="details-panel">
      <TileDark>
        <div class="details-content">
          <div class="details-header">
            <h3 class="details-title">{{ selectedPool.name }}</h3>
            <ButtonIcon @click="closeDetails">✕</ButtonIcon>
          </div>

          <div class="details-body">
            <div class="detail-row">
              <span class="detail-label">类型</span>
              <span class="detail-value">{{ selectedPool.type || '标准' }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">总容量</span>
              <span class="detail-value">{{ formatSize(selectedPool.total_bytes) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">已使用</span>
              <span class="detail-value">{{ formatSize(selectedPool.used_bytes) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">使用率</span>
              <span class="detail-value">{{ ((selectedPool.usage_ratio || 0) * 100).toFixed(1) }}%</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态</span>
              <span class="badge" :class="selectedPool.status === 'active' ? 'active' : 'inactive'">
                {{ selectedPool.status === 'active' ? '活跃' : '停用' }}
              </span>
            </div>
            <div v-if="selectedPool.description" class="detail-row">
              <span class="detail-label">描述</span>
              <span class="detail-value">{{ selectedPool.description }}</span>
            </div>
          </div>

          <div class="details-footer">
            <ButtonSecondary @click="runCleanup(selectedPool.pool_id)">清理临时文件</ButtonSecondary>
          </div>
        </div>
      </TileDark>
    </div>

    <!-- Create/Edit Pool Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <CardUtility class="modal-card">
        <div class="modal-header">
          <h3 class="modal-title">{{ editingPool ? '编辑存储池' : '创建存储池' }}</h3>
          <button class="modal-close" @click="closeModal">✕</button>
        </div>

        <div class="modal-body">
          <div class="form-field">
            <label class="form-label">名称</label>
            <input v-model="poolForm.name" type="text" placeholder="存储池名称" class="apple-input full-width">
          </div>

          <div class="form-field">
            <label class="form-label">类型</label>
            <select v-model="poolForm.type" class="apple-select full-width">
              <option value="standard">标准</option>
              <option value="high-performance">高性能</option>
              <option value="archival">归档</option>
            </select>
          </div>

          <div class="form-field">
            <label class="form-label">最大容量</label>
            <select v-model="poolForm.sizePreset" @change="onSizePresetChange" class="apple-select full-width">
              <option value="">自定义</option>
              <option value="10GB">10 GB</option>
              <option value="50GB">50 GB</option>
              <option value="100GB">100 GB</option>
              <option value="500GB">500 GB</option>
              <option value="1TB">1 TB</option>
            </select>
            <input v-if="!poolForm.sizePreset" v-model="poolForm.size" type="text" placeholder="例如: 100GB" class="apple-input full-width" style="margin-top: var(--spacing-xs)">
          </div>

          <div class="form-field">
            <label class="form-label">描述 (可选)</label>
            <textarea v-model="poolForm.description" rows="3" placeholder="描述存储池用途" class="apple-textarea full-width"></textarea>
          </div>
        </div>

        <div class="modal-footer">
          <ButtonSecondary @click="closeModal">取消</ButtonSecondary>
          <ButtonPrimary @click="submitPool" :disabled="!poolForm.name">
            {{ editingPool ? '保存' : '创建' }}
          </ButtonPrimary>
        </div>
      </CardUtility>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { usePoolStore } from '../stores/poolStore.js'
import {
  ButtonPrimary,
  ButtonSecondary,
  ButtonPearl,
  ButtonIcon,
  CardUtility,
  TileDark
} from '../components/common'

const emit = defineEmits(['show-toast'])

const poolStore = usePoolStore()

const pools = computed(() => poolStore.pools)
const selectedPool = ref(null)
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

async function viewPoolDetails(pool) {
  try {
    const details = await poolStore.getPoolDetails(pool.pool_id)
    selectedPool.value = details
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function closeDetails() {
  selectedPool.value = null
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
  if (!confirm(`确定要删除存储池 "${pool.name}" 吗？此操作不可恢复。`)) return
  deletePool(pool.pool_id)
}

async function deletePool(poolId) {
  try {
    await poolStore.deletePool(poolId)
    emit('show-toast', { type: 'success', title: '成功', message: '存储池已删除' })
    if (selectedPool.value?.pool_id === poolId) {
      selectedPool.value = null
    }
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

async function runCleanup(poolId) {
  try {
    await poolStore.runCleanup(poolId, 'temp')
    emit('show-toast', { type: 'success', title: '成功', message: '清理完成' })
    await loadPools()
  } catch (err) {
    emit('show-toast', { type: 'error', title: '错误', message: err.message })
  }
}

function getQuotaClass(usage) {
  if (usage > 0.9) return 'danger'
  if (usage > 0.7) return 'warn'
  return 'ok'
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
.storage-pool-view {
  flex: 1;
  overflow: auto;
  padding: var(--space-section, 80px);
  background: var(--color-canvas-parchment, #f5f5f7);
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-xl, 32px);
  max-width: 1440px;
  margin-left: auto;
  margin-right: auto;
}

.section-title {
  font: var(--text-display-lg, 40px/1.1 0);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.loading-state {
  text-align: center;
  padding: var(--space-xxl, 48px);
  color: var(--color-ink-muted-48, #7a7a7a);
  font: var(--text-body, 17px/1.47 -0.374px);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-xxl, 48px);
}

.empty-icon {
  font-size: 64px;
  margin-bottom: var(--space-lg, 24px);
  opacity: 0.5;
}

.empty-text {
  font: var(--text-body, 17px/1.47 -0.374px);
  color: var(--color-ink-muted-48, #7a7a7a);
  margin-bottom: var(--space-lg, 24px);
}

.pool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-lg, 24px);
  max-width: 1440px;
  margin: 0 auto;
}

.pool-card {
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-lg, 18px);
  padding: var(--space-lg, 24px);
}

.pool-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: var(--space-md, 17px);
}

.pool-info {
  flex: 1;
}

.pool-name {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  display: block;
}

.pool-desc {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
  display: block;
  margin-top: var(--spacing-xxs);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--rounded-pill, 9999px);
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
}

.badge.active {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.badge.inactive {
  background: var(--color-surface-chip-translucent-bg);
  color: var(--color-ink-muted-48);
}

.pool-stats {
  margin-bottom: var(--space-md, 17px);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: var(--spacing-xs) 0;
  border-bottom: 1px solid var(--color-divider-soft, #f0f0f0);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48, #7a7a7a);
}

.stat-value {
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
}

.pool-progress {
  display: flex;
  align-items: center;
  gap: var(--space-sm, 12px);
  margin-bottom: var(--space-md, 17px);
}

.progress-bar {
  flex: 1;
  height: var(--spacing-xs);
  background: var(--color-hairline, #e0e0e0);
  border-radius: var(--rounded-pill, 9999px);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: var(--rounded-pill, 9999px);
  transition: width 0.3s ease;
}

.progress-fill.ok { background: var(--color-primary); }
.progress-fill.warn { background: var(--color-warning); }
.progress-fill.danger { background: var(--color-danger); }

.progress-text {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-ink-muted-48);
  min-width: 50px;
  text-align: right;
}

.pool-actions {
  display: flex;
  gap: var(--space-xs, 8px);
}

/* Details Panel - Dark Tile */
.details-panel {
  position: fixed;
  right: 0;
  top: 0;
  bottom: 0;
  width: 360px;
  z-index: 1000;
}

.details-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface-tile-1, #272729);
  padding: var(--space-lg, 24px);
}

.details-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg, 24px);
}

.details-title {
  font: var(--text-display-md, 34px/1.47 -0.374px);
  font-weight: 600;
  color: var(--color-body-on-dark, #ffffff);
  margin: 0;
}

.details-body {
  flex: 1;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm, 12px) 0;
  border-bottom: 1px solid var(--color-border-on-dark);
}

.detail-label {
  font: var(--text-caption, 14px/1.43 -0.224px);
  color: var(--color-body-muted, #cccccc);
}

.detail-value {
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
  color: var(--color-body-on-dark, #ffffff);
}

.details-footer {
  padding-top: var(--space-lg, 24px);
  border-top: 1px solid var(--color-border-on-dark);
  margin-top: var(--space-lg, 24px);
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: var(--space-lg, 24px);
}

.modal-card {
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg, 24px);
}

.modal-title {
  font: var(--text-body-strong, 17px/1.24 -0.374px 600);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-ink-muted-48);
  padding: 4px;
}

.modal-close:hover {
  color: var(--color-ink, #1d1d1f);
}

.modal-body {
  margin-bottom: var(--space-lg, 24px);
}

.form-field {
  margin-bottom: var(--space-md, 17px);
}

.form-label {
  display: block;
  font: var(--text-caption, 14px/1.43 -0.224px);
  font-weight: 600;
  color: var(--color-ink, #1d1d1f);
  margin-bottom: var(--space-xxs, 4px);
}

.apple-input,
.apple-select,
.apple-textarea {
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas, #ffffff);
  border: 1px solid var(--color-hairline, #e0e0e0);
  border-radius: var(--radius-md);
  color: var(--color-ink, #1d1d1f);
  font: var(--text-body, 17px/1.47 -0.374px);
  transition: border-color 0.2s;
  width: 100%;
  box-sizing: border-box;
}

.apple-input:focus,
.apple-select:focus,
.apple-textarea:focus {
  outline: none;
  border-color: var(--color-primary, #0066cc);
}

.apple-textarea {
  resize: vertical;
  min-height: 80px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm, 12px);
  padding-top: var(--space-md, 17px);
  border-top: 1px solid var(--color-divider-soft, #f0f0f0);
}
</style>