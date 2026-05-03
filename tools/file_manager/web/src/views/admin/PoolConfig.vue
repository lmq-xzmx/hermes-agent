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
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  min-height: 100vh;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.config-header h1 {
  font-size: 24px;
  color: var(--text-primary, #e6edf3);
  margin: 0;
}

.config-content {
  display: grid;
  gap: 24px;
}

.capacity-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 16px;
}

.stat-label {
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.capacity-bar-section {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 16px;
}

.capacity-bar {
  height: 24px;
  background: var(--bg-tertiary, #21262d);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
}

.bar-used {
  background: #238636;
  transition: width 0.3s ease;
}

.bar-reserved {
  background: #9e6a03;
  transition: width 0.3s ease;
}

.bar-legend {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
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

.dot.used { background: #238636; }
.dot.reserved { background: #9e6a03; }
.dot.available { background: var(--bg-tertiary, #21262d); }

.config-form {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

.config-form h2 {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
  margin: 0 0 20px 0;
}

.form-row {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
  margin-bottom: 8px;
}

.input-with-unit {
  display: flex;
  align-items: center;
}

.input-with-unit input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px 0 0 6px;
  color: var(--text-primary, #e6edf3);
}

.input-with-unit .unit {
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-left: none;
  border-radius: 0 6px 6px 0;
  color: var(--text-secondary, #8b949e);
}

select {
  width: 100%;
  padding: 8px 12px;
  background: var(--bg-tertiary, #21262d);
  border: 1px solid var(--border, #30363d);
  border-radius: 6px;
  color: var(--text-primary, #e6edf3);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: 18px;
  height: 18px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.health-gauge-section {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  padding: 24px;
}

.health-gauge-section h2 {
  font-size: 16px;
  color: var(--text-primary, #e6edf3);
  margin: 0 0 20px 0;
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
  stroke: var(--bg-tertiary, #21262d);
}

.gauge-fill {
  stroke: #238636;
  transition: stroke-dashoffset 0.5s ease;
}

.gauge-circle.warning .gauge-fill {
  stroke: #9e6a03;
}

.gauge-circle.critical .gauge-fill {
  stroke: #da3633;
}

.gauge-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.gauge-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--text-primary, #e6edf3);
}

.gauge-label {
  font-size: 14px;
  color: var(--text-secondary, #8b949e);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  border: none;
  font-size: 14px;
}

.btn-primary {
  background: #238636;
  color: white;
}

.btn-primary:disabled {
  background: #21262d;
  color: #484f58;
}

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}
</style>
