<template>
  <div class="operation-trends">
    <div class="chart-header">
      <h3>操作趋势</h3>
      <div class="days-selector">
        <button v-for="d in [7, 14, 30]" :key="d" :class="{ active: days === d }" @click="changeDays(d)">
          {{ d }}天
        </button>
      </div>
    </div>
    <div ref="chartRef" style="width: 100%; height: 300px;"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { adminChartTheme } from '@/theme/adminTheme'

const props = defineProps({
  data: { type: Object, required: true }
})

const chartRef = ref(null)
const days = ref(30)

function changeDays(d) {
  days.value = d
}

function renderChart() {
  if (!chartRef.value) return
  const chart = echarts.init(chartRef.value)
  const option = {
    backgroundColor: 'transparent',
    tooltip: { ...adminChartTheme.tooltip, trigger: 'axis' },
    legend: { ...adminChartTheme.legend, data: props.data.series?.map(s => s.name) || [] },
    grid: adminChartTheme.grid,
    xAxis: { ...adminChartTheme.categoryAxis, type: 'category', data: props.data.dates || [], boundaryGap: false },
    yAxis: adminChartTheme.valueAxis,
    series: (props.data.series || []).map(s => ({
      name: s.name,
      type: 'line',
      smooth: true,
      data: s.data,
      areaStyle: { opacity: 0.1 },
      ...adminChartTheme.line
    }))
  }
  chart.setOption(option)
}

onMounted(renderChart)
watch(() => props.data, renderChart, { deep: true })
</script>

<style scoped>
.operation-trends {
  background: var(--color-surface-tile-1);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 16px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.days-selector {
  display: flex;
  gap: 8px;
}

.days-selector button {
  padding: 4px 12px;
  background: var(--color-surface-tile-3);
  color: var(--color-ink-muted-48);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  cursor: pointer;
}

.days-selector button.active {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}
</style>