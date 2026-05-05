<template>
  <div class="storage-pool-chart">
    <div class="chart-header">
      <h3>存储池使用率</h3>
      <span class="total">{{ formatBytes(totalBytes) }} 总计</span>
    </div>
    <div class="pools-grid">
      <div v-for="pool in pools" :key="pool.id" class="pool-card card-utility">
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
          <button class="btn-apple-primary btn-sm" @click="showPoolTeams(pool)">查看团队</button>
        </div>
      </div>
    </div>

    <!-- Teams Modal - Apple Style -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ currentPool?.name }} - 使用中的团队</h3>
          <button class="modal-close" @click="closeModal">×</button>
        </div>
        <div v-if="modalLoading" class="modal-loading">加载中...</div>
        <div v-else-if="modalError" class="modal-error">{{ modalError }}</div>
        <div v-else-if="poolTeams.length === 0" class="modal-empty">
          该存储池下暂无团队
        </div>
        <div v-else class="modal-teams">
          <table class="teams-table">
            <thead>
              <tr>
                <th>团队名称</th>
                <th>成员数</th>
                <th>配额</th>
                <th>已用</th>
                <th>使用率</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="team in poolTeams" :key="team.team_id">
                <td>👥 {{ team.team_name }}</td>
                <td>{{ team.member_count }}</td>
                <td>{{ team.storage_quota ? formatBytes(team.storage_quota) : '无限' }}</td>
                <td>{{ formatBytes(team.storage_used) }}</td>
                <td>
                  <div class="usage-bar">
                    <div class="usage-fill" :style="{ width: (team.usage_rate * 100) + '%' }"></div>
                  </div>
                  {{ Math.round(team.usage_rate * 100) }}%
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { adminChartTheme, statusColors } from '@/theme/adminTheme'

const props = defineProps({
  pools: { type: Array, required: true }
})

const showModal = ref(false)
const currentPool = ref(null)
const poolTeams = ref([])
const modalLoading = ref(false)
const modalError = ref(null)

const totalBytes = computed(() =>
  props.pools.reduce((sum, p) => sum + p.totalBytes, 0)
)

function getRingOption(pool) {
  const statusColor = statusColors[pool.status] || statusColors.normal
  return {
    backgroundColor: 'transparent',
    tooltip: adminChartTheme.tooltip,
    series: [{
      type: 'pie',
      radius: ['60%', '85%'],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 4,
        borderColor: '#161b22',
        borderWidth: 2
      },
      label: { show: false },
      data: [
        {
          value: pool.usedBytes,
          name: '已用',
          itemStyle: { color: statusColor }
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

async function showPoolTeams(pool) {
  currentPool.value = pool
  showModal.value = true
  modalLoading.value = true
  modalError.value = null
  poolTeams.value = []

  try {
    const resp = await fetch(`/api/v1/admin/analytics/teams-by-pool/${pool.id}`)
    if (!resp.ok) throw new Error(`API error: ${resp.status}`)
    const data = await resp.json()
    poolTeams.value = data.teams || []
  } catch (e) {
    modalError.value = e.message
  } finally {
    modalLoading.value = false
  }
}

function closeModal() {
  showModal.value = false
  currentPool.value = null
  poolTeams.value = []
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
  padding: var(--space-lg);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-lg);
}

.chart-header h3 {
  font: var(--text-body-strong);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.total {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.pools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-md);
}

.pool-card {
  display: flex;
  gap: var(--space-md);
  padding: var(--space-md);
}

.pool-ring {
  flex-shrink: 0;
}

.pool-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-xxs);
}

.pool-info h4 {
  font: var(--text-body-strong);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.pool-stats {
  display: flex;
  gap: var(--space-sm);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.pool-status {
  font: var(--text-caption);
  padding: 2px 10px;
  border-radius: var(--rounded-pill);
  display: inline-block;
  width: fit-content;
}

.pool-status.normal { background: var(--color-primary-subtle); color: var(--color-primary); }
.pool-status.warning { background: var(--color-warning-subtle); color: var(--color-warning-strong); }
.pool-status.critical { background: var(--color-danger-subtle); color: var(--color-danger); }

/* Modal Styles */
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
}

.modal-content {
  background: var(--color-canvas);
  border-radius: var(--rounded-lg);
  width: 90%;
  max-width: 700px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-hairline);
}

.modal-header h3 {
  font: var(--text-body-strong);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-ink-muted-48);
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover {
  color: var(--color-ink);
}

.modal-loading,
.modal-error,
.modal-empty {
  padding: var(--space-xl);
  text-align: center;
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.modal-error {
  color: var(--color-danger);
}

.modal-teams {
  overflow-y: auto;
  padding: var(--space-md);
}

.teams-table {
  width: 100%;
  border-collapse: collapse;
}

.teams-table th,
.teams-table td {
  padding: var(--space-sm) var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.teams-table th {
  font: var(--text-caption);
  font-weight: 600;
  color: var(--color-ink-muted-48);
}

.usage-bar {
  width: 80px;
  height: 6px;
  background: var(--color-hairline);
  border-radius: var(--radius-xs);
  display: inline-block;
  vertical-align: middle;
  margin-right: 8px;
}

.usage-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-xs);
}
</style>