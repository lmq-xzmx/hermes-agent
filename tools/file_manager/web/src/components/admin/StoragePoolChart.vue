<template>
  <div class="storage-pool-chart">
    <div class="chart-header">
      <h3>存储池使用率</h3>
      <span class="total">{{ formatBytes(totalBytes) }} 总计</span>
    </div>
    <div class="pools-container">
      <div v-for="pool in pools" :key="pool.id" class="pool-card">
        <div class="pool-ring">
          <canvas :id="'ring-' + pool.id" width="120" height="120"></canvas>
        </div>
        <div class="pool-info">
          <h4>{{ pool.name }}</h4>
          <div class="pool-stats">
            <span class="used">{{ formatBytes(pool.usedBytes) }} 已用</span>
            <span class="free">{{ formatBytes(pool.freeBytes) }} 可用</span>
          </div>
          <div class="pool-status" :class="pool.status">
            {{ pool.status === 'critical' ? '⚠ 告警' : pool.status === 'warning' ? '⚡ 注意' : '✓ 正常' }}
          </div>
          <button class="detail-btn" @click="showPoolDetail(pool)">详情</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  pools: { type: Array, required: true }
})

const totalBytes = computed(() =>
  props.pools.reduce((sum, p) => sum + p.totalBytes, 0)
)

function getRingOption(pool) {
  return {
    series: [{
      type: 'pie',
      radius: ['60%', '85%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#1a1f26',
        borderWidth: 2
      },
      label: { show: false },
      data: [
        {
          value: pool.usedBytes,
          name: '已用',
          itemStyle: { color: pool.status === 'critical' ? '#f85149' : pool.status === 'warning' ? '#d29922' : '#58a6ff' }
        },
        {
          value: pool.freeBytes,
          name: '可用',
          itemStyle: { color: '#30363d' }
        }
      ]
    }],
    graphic: [{
      type: 'text',
      left: 'center',
      top: 'center',
      style: {
        text: `${Math.round(pool.usageRate * 100)}%`,
        fill: '#e6edf3',
        fontSize: 18,
        fontWeight: 'bold'
      }
    }]
  }
}

function renderChart(pool) {
  const dom = document.getElementById('ring-' + pool.id)
  if (!dom) return
  const chart = echarts.init(dom)
  chart.setOption(getRingOption(pool))
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

function showPoolDetail(pool) {
  console.log('Show pool detail:', pool)
}

onMounted(() => {
  props.pools.forEach(renderChart)
})

watch(() => props.pools, () => {
  props.pools.forEach(renderChart)
}, { deep: true })
</script>

<style scoped>
.storage-pool-chart {
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.pools-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.pool-card {
  display: flex;
  gap: 16px;
  padding: 12px;
  background: var(--bg-primary, #0d1117);
  border-radius: 8px;
  border: 1px solid var(--border, #30363d);
}

.pool-ring {
  flex-shrink: 0;
}

.pool-info {
  flex: 1;
  min-width: 0;
}

.pool-info h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.pool-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  display: inline-block;
  margin: 4px 0;
}

.pool-status.normal { background: rgba(63, 185, 80, 0.2); color: #3fb950; }
.pool-status.warning { background: rgba(210, 153, 34, 0.2); color: #d29922; }
.pool-status.critical { background: rgba(248, 81, 73, 0.2); color: #f85149; }

.detail-btn {
  margin-top: 8px;
  padding: 4px 12px;
  background: var(--accent, #58a6ff);
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>