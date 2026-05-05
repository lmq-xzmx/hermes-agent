<template>
  <LifecycleProvider>
  <div class="pool-config">
    <header class="config-header">
      <h1>存储容量管理</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn btn-secondary">🔄 刷新</button>
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
          <button @click="saveConfig" class="btn btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button @click="resetConfig" class="btn btn-secondary">重置</button>
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
.pool-config {
  padding: var(--spacing-lg);
  background: var(--color-surface-tile-1);
  min-height: 100vh;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.config-header h1 {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0;
  letter-spacing: -0.374px;
}

.config-content {
  display: grid;
  gap: var(--spacing-lg);
}

.capacity-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--spacing-md);
}

.stat-card {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.stat-label {
  font-size: 12px;
  color: var(--color-body-muted);
  margin-bottom: var(--space-xs);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.capacity-bar-section {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-md);
}

.capacity-bar {
  height: 24px;
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-full);
  overflow: hidden;
  display: flex;
}

.bar-used {
  background: var(--color-success);
  transition: width 0.3s ease;
}

.bar-reserved {
  background: var(--color-warning);
  transition: width 0.3s ease;
}

.bar-legend {
  display: flex;
  gap: var(--spacing-lg);
  margin-top: var(--space-sm);
  font-size: 12px;
  color: var(--color-body-muted);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.dot.used { background: var(--color-success); }
.dot.reserved { background: var(--color-warning); }
.dot.available { background: var(--color-surface-tile-3); }

.config-form {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.config-form h2 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0 0 var(--spacing-lg) 0;
}

.form-row {
  display: flex;
  gap: var(--spacing-md);
  margin-bottom: var(--space-md);
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--color-body-muted);
  margin-bottom: var(--space-xs);
}

.input-with-unit {
  display: flex;
  align-items: center;
}

.input-with-unit input {
  flex: 1;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-sm) 0 0 var(--radius-sm);
  color: var(--color-body-on-dark);
  font-family: var(--font-family-text);
  font-size: 17px;
}

.input-with-unit .unit {
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-left: none;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  color: var(--color-body-muted);
}

select {
  width: 100%;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-sm);
  color: var(--color-body-on-dark);
  font-family: var(--font-family-text);
  font-size: 17px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  cursor: pointer;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
}

.form-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--spacing-lg);
}

.health-gauge-section {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.health-gauge-section h2 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0 0 var(--spacing-lg) 0;
}

.health-gauge {
  display: flex;
  justify-content: center;
}

.gauge-circle {
  position: relative;
  width: 200px;
  height: 200px;
}

.gauge-circle svg {
  transform: rotate(-90deg);
}

.gauge-bg {
  stroke: var(--color-surface-tile-3);
}

.gauge-fill {
  stroke: var(--color-success);
  transition: stroke-dashoffset 0.5s ease;
}

.gauge-circle.warning .gauge-fill {
  stroke: var(--color-warning);
}

.gauge-circle.critical .gauge-fill {
  stroke: var(--color-danger);
}

.gauge-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.gauge-value {
  font-family: var(--font-display);
  font-size: 32px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.gauge-label {
  font-size: 14px;
  color: var(--color-body-muted);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--color-body-muted);
}

.btn {
  padding: 11px 22px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  border: none;
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  transition: var(--transition-active);
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btn-primary:active {
  transform: scale(0.95);
}

.btn-primary:disabled {
  background: var(--color-surface-tile-2);
  color: var(--color-body-muted);
}

.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.btn-secondary:active {
  transform: scale(0.95);
}
</style>
