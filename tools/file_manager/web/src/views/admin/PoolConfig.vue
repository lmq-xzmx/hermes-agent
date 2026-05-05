<template>
  <LifecycleProvider>
  <div class="pool-config">
    <header class="config-header">
      <h1>存储容量管理</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn-apple-secondary">🔄 刷新</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="config-content">
      <!-- 容量总览卡片 -->
      <div class="capacity-overview">
        <div class="stat-card">
          <div class="stat-label">总容量</div>
          <div class="stat-value">{{ formatBytes(poolStats.total_bytes) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已用</div>
          <div class="stat-value">{{ formatBytes(poolStats.actual_used_bytes) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">可用</div>
          <div class="stat-value">{{ formatBytes(poolStats.available_bytes) }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">使用率</div>
          <div class="stat-value">{{ (poolStats.usage_ratio * 100).toFixed(1) }}%</div>
        </div>
      </div>

      <!-- 容量进度条 -->
      <div class="capacity-bar-section">
        <div class="capacity-bar">
          <div class="bar-used" :style="{ width: (poolStats.usage_ratio * 100) + '%' }"></div>
          <div class="bar-reserved" :style="{ width: (poolStats.reserved_ratio * 100) + '%' }"></div>
        </div>
        <div class="bar-legend">
          <span class="legend-item"><span class="dot used"></span> 已用</span>
          <span class="legend-item"><span class="dot reserved"></span> 预留</span>
          <span class="legend-item"><span class="dot available"></span> 可用</span>
        </div>
      </div>

      <!-- 配置表单 -->
      <div class="config-form">
        <h2>资源池配置</h2>

        <div class="form-row">
          <div class="form-group">
            <label for="reservedBytes">预留空间</label>
            <div class="input-with-unit">
              <input
                id="reservedBytes"
                v-model.number="config.reserved_bytes"
                type="number"
                min="0"
                :max="poolStats.total_bytes"
              />
              <span class="unit">GB</span>
            </div>
          </div>

          <div class="form-group">
            <label for="bufferRatio">缓冲比例</label>
            <div class="input-with-unit">
              <input
                id="bufferRatio"
                v-model.number="config.buffer_ratio"
                type="number"
                min="0"
                max="100"
                step="1"
              />
              <span class="unit">%</span>
            </div>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="config.allow_overcommit" type="checkbox" />
              <span>允许透支</span>
            </label>
          </div>
        </div>

        <div class="form-row">
          <div class="form-group">
            <label for="softWarning">软预警阈值</label>
            <select id="softWarning" v-model.number="config.soft_warning_ratio">
              <option :value="0.7">70%</option>
              <option :value="0.8">80%</option>
              <option :value="0.9">90%</option>
            </select>
          </div>

          <div class="form-group">
            <label for="hardBlock">硬阻塞阈值</label>
            <select id="hardBlock" v-model.number="config.hard_block_ratio">
              <option :value="0.9">90%</option>
              <option :value="0.95">95%</option>
              <option :value="1.0">100%</option>
            </select>
          </div>
        </div>

        <div class="form-actions">
          <button @click="saveConfig" class="btn-apple-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button @click="resetConfig" class="btn-apple-secondary">重置</button>
        </div>
      </div>

      <!-- 健康度仪表 -->
      <div class="health-gauge-section">
        <h2>容量健康度</h2>
        <div class="health-gauge">
          <div class="gauge-circle" :class="healthStatus">
            <svg viewBox="0 0 100 100">
              <circle
                class="gauge-bg"
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke-width="10"
              />
              <circle
                class="gauge-fill"
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke-width="10"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="gaugeOffset"
              />
            </svg>
            <div class="gauge-text">
              <div class="gauge-value">{{ (poolStats.usage_ratio * 100).toFixed(0) }}%</div>
              <div class="gauge-label">{{ healthLabel }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAdminStore } from '@/stores/adminStore'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const store = useAdminStore()
const loading = ref(true)
const saving = ref(false)

const poolStats = ref({
  total_bytes: 2 * 1024 * 1024 * 1024 * 1024, // 2TB default
  actual_used_bytes: 850 * 1024 * 1024 * 1024,
  available_bytes: 1.15 * 1024 * 1024 * 1024 * 1024,
  usage_ratio: 0.425,
  reserved_ratio: 0.25
})

const config = ref({
  reserved_bytes: 500,
  buffer_ratio: 10,
  allow_overcommit: false,
  soft_warning_ratio: 0.8,
  hard_block_ratio: 1.0
})

const originalConfig = { ...config.value }

const healthStatus = computed(() => {
  const ratio = poolStats.value.usage_ratio
  if (ratio >= config.value.hard_block_ratio) return 'critical'
  if (ratio >= config.value.soft_warning_ratio) return 'warning'
  return 'normal'
})

const healthLabel = computed(() => {
  const status = healthStatus.value
  if (status === 'critical') return '严重'
  if (status === 'warning') return '警告'
  return '正常'
})

const circumference = 2 * Math.PI * 45

const gaugeOffset = computed(() => {
  return circumference * (1 - poolStats.value.usage_ratio)
})

function formatBytes(bytes) {
  if (bytes >= 1024 * 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024 * 1024)).toFixed(2) + ' TB'
  }
  if (bytes >= 1024 * 1024 * 1024) {
    return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
  }
  return (bytes / (1024 * 1024)).toFixed(2) + ' MB'
}

async function refresh() {
  loading.value = true
  try {
    await store.fetchStoragePools()
    // Update poolStats from store
    if (store.storagePools.length > 0) {
      const pool = store.storagePools[0]
      poolStats.value = {
        total_bytes: pool.total_bytes,
        actual_used_bytes: pool.used_bytes,
        available_bytes: pool.total_bytes - pool.used_bytes - (pool.reserved_bytes || 0),
        usage_ratio: pool.used_bytes / pool.total_bytes,
        reserved_ratio: (pool.reserved_bytes || 0) / pool.total_bytes
      }
    }
  } finally {
    loading.value = false
  }
}

async function saveConfig() {
  saving.value = true
  try {
    // API call to save config
    await store.updatePoolConfig(config.value)
    originalConfig.value = { ...config.value }
  } finally {
    saving.value = false
  }
}

function resetConfig() {
  config.value = { ...originalConfig }
}

onMounted(() => {
  refresh()
})
</script>

<style scoped>
/* === PoolConfig - 存储容量管理页面 === */

.pool-config {
  padding: var(--spacing-lg);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}

.pool-config__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.pool-config__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

.pool-config__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.pool-config__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.capacity-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.stat-card__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.stat-card__value {
  font: var(--text-display-sm);
  color: var(--color-ink);
}

.capacity-bar-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.capacity-bar {
  height: var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-pill);
  overflow: hidden;
  display: flex;
}

.capacity-bar__used {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s;
}

.capacity-bar__reserved {
  height: 100%;
  background: var(--color-warning);
  transition: width 0.3s;
}

.bar-legend {
  display: flex;
  gap: var(--spacing-lg);
}

.bar-legend__item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.bar-legend__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
}

.bar-legend__dot--used { background: var(--color-primary); }
.bar-legend__dot--reserved { background: var(--color-warning); }
.bar-legend__dot--available { background: var(--color-canvas-parchment); }

.config-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.config-form__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xxs);
}

.form-group__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font: var(--text-body);
  color: var(--color-ink);
  cursor: pointer;
}

.input-with-unit {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.input-with-unit__input {
  width: 120px;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.input-with-unit__input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.input-with-unit__unit {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.form-select {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-select:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

.health-gauge-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.health-gauge-section__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.health-gauge {
  display: flex;
  justify-content: center;
  padding: var(--spacing-lg) 0;
}

.health-gauge__circle {
  position: relative;
  width: 200px;
  height: 200px;
}

.health-gauge__circle svg {
  transform: rotate(-90deg);
}

.health-gauge__bg {
  fill: none;
  stroke: var(--color-canvas-parchment);
  stroke-width: 10;
}

.health-gauge__fill {
  fill: none;
  stroke-width: 10;
  stroke-linecap: round;
  transition: stroke-dashoffset 0.3s;
}

.health-gauge__fill--normal { stroke: var(--color-success); }
.health-gauge__fill--warning { stroke: var(--color-warning); }
.health-gauge__fill--critical { stroke: var(--color-danger); }

.health-gauge__text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.health-gauge__value {
  font: var(--text-display-lg);
  color: var(--color-ink);
}

.health-gauge__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.btn-apple-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.btn-apple-primary:active {
  transform: scale(0.95);
}

.btn-apple-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-apple-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, background 0.15s ease;
}

.btn-apple-secondary:active {
  transform: scale(0.95);
}
</style>

