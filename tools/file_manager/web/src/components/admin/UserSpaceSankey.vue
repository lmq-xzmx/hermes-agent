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
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 400px;"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { adminChartTheme } from '@/theme/adminTheme'

const props = defineProps({
  data: { type: Object, required: true }
})

const chartRef = ref(null)
const filterType = ref('all')

const filteredNodes = computed(() => {
  if (filterType.value === 'all') return props.data.nodes
  return props.data.nodes.filter(n => n.type === filterType.value)
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
      lineStyle: { color: 'gradient', curveness: 0.5, ...adminChartTheme.sankey.link },
      data: filteredNodes.value.map(n => ({
        name: n.name,
        itemStyle: {
          color: n.type === 'user' ? adminChartTheme.color[0] : n.type === 'team' ? adminChartTheme.color[1] : adminChartTheme.color[2]
        }
      })),
      links: filteredLinks.value.map(l => ({
        source: l.source,
        target: l.target,
        value: l.value
      }))
    }]
  }
  chart.setOption(option)
}

onMounted(renderChart)
watch([filteredNodes, filteredLinks], renderChart)
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

.filter select {
  padding: 4px 8px;
  background: var(--bg-primary, #0d1117);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
  border-radius: 4px;
}
</style>