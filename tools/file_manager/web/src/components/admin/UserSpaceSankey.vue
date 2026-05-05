<template>
  <div class="user-space-sankey">
    <div class="chart-header">
      <h3>用户-空间关系</h3>
      <div class="filter">
        <select v-model="filterType">
          <option value="all">全部</option>
          <option value="user">仅用户</option>
          <option value="team">仅团队</option>
          <option value="space">仅空间</option>
        </select>
        <span v-if="isLargeDataset" class="virtual-badge">虚拟化模式</span>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 400px;"></div>
    <div v-if="isLargeDataset" class="virtual-notice">
      显示前 {{ displayNodeLimit }} 个节点（共 {{ totalNodeCount }} 个）
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { adminChartTheme } from '@/theme/adminTheme'

const VIRTUALIZATION_THRESHOLD = 100  // 启用虚拟化的节点数阈值
const DEFAULT_DISPLAY_LIMIT = 100   // 默认显示的节点数

const props = defineProps({
  data: { type: Object, required: true }
})

const chartRef = ref(null)
const filterType = ref('all')

const totalNodeCount = computed(() => props.data.nodes?.length || 0)
const isLargeDataset = computed(() => totalNodeCount.value > VIRTUALIZATION_THRESHOLD)
const displayNodeLimit = computed(() => isLargeDataset.value ? DEFAULT_DISPLAY_LIMIT : totalNodeCount.value)

// 计算每个节点的连接数（用于排序）
const nodeConnectionCount = computed(() => {
  const counts = {}
  for (const link of (props.data.links || [])) {
    counts[link.source] = (counts[link.source] || 0) + (link.value || 1)
    counts[link.target] = (counts[link.target] || 0) + (link.value || 1)
  }
  return counts
})

// 按连接数排序的节点（虚拟化时显示最重要的节点）
const sortedNodes = computed(() => {
  if (!isLargeDataset.value) return props.data.nodes
  return [...props.data.nodes].sort((a, b) => {
    const countA = nodeConnectionCount.value[a.id] || 0
    const countB = nodeConnectionCount.value[b.id] || 0
    return countB - countA  // 降序排列
  })
})

const filteredNodes = computed(() => {
  const nodes = filterType.value === 'all'
    ? sortedNodes.value
    : sortedNodes.value.filter(n => n.type === filterType.value)
  return nodes.slice(0, displayNodeLimit.value)
})

const filteredLinks = computed(() => {
  const nodeIds = new Set(filteredNodes.value.map(n => n.id))
  return props.data.links.filter(l =>
    nodeIds.has(l.source) && nodeIds.has(l.target)
  )
})

function renderChart() {
  if (!chartRef.value) return
  const chart = echarts.init(chartRef.value)

  const seriesData = filteredNodes.value.map(n => ({
    name: n.name,
    itemStyle: {
      color: n.type === 'user' ? adminChartTheme.color[0] : n.type === 'team' ? adminChartTheme.color[1] : adminChartTheme.color[2]
    }
  }))

  const seriesLinks = filteredLinks.value.map(l => ({
    source: l.source,
    target: l.target,
    value: l.value
  }))

  const option = {
    backgroundColor: 'transparent',
    tooltip: { ...adminChartTheme.tooltip, trigger: 'item', triggerOn: 'mousemove' },
    series: [{
      type: 'sankey',
      layout: 'none',
      emphasis: { focus: 'adjacency' },
      nodeAlign: 'left',
      nodeGap: 12,
      nodeWidth: 20,
      // 虚拟化优化：大数据集启用 large 模式
      large: isLargeDataset.value,
      largeThreshold: VIRTUALIZATION_THRESHOLD,
      lineStyle: { color: 'gradient', curveness: 0.5, ...adminChartTheme.sankey.link },
      data: seriesData,
      links: seriesLinks
    }]
  }
  chart.setOption(option)
}

onMounted(renderChart)
watch([filteredNodes, filteredLinks, isLargeDataset], renderChart)
</script>

<style scoped>
.user-space-sankey {
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

.filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter select {
  padding: 4px 8px;
  background: var(--bg-primary, #0d1117);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
}

.virtual-badge {
  font-size: 11px;
  padding: 2px 6px;
  background: #d29922;
  color: #000;
  border-radius: 4px;
  font-weight: 500;
}

.virtual-notice {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary, #8b949e);
  text-align: center;
}
</style>