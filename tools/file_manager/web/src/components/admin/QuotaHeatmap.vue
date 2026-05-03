<template>
  <div class="quota-heatmap">
    <div class="chart-header">
      <h3>配额告警</h3>
      <div class="legend">
        <span class="legend-item normal"><span class="dot"></span> &lt; 60%</span>
        <span class="legend-item warning"><span class="dot"></span> 60-80%</span>
        <span class="legend-item critical"><span class="dot"></span> &gt; 80%</span>
      </div>
    </div>
    <div class="heatmap-container">
      <table class="heatmap-table">
        <thead>
          <tr>
            <th>团队/空间</th>
            <th v-for="space in visibleSpaces" :key="space.space_id">
              {{ space.space_name }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in heatmapData" :key="team.team_id">
            <td class="team-name">{{ team.team_name }}</td>
            <td v-for="space in team.spaces" :key="space.space_id"
                :class="['usage-cell', space.status]"
                :title="`${Math.round(space.usage_rate * 100)}%`">
              <div class="usage-bar" :style="{ width: `${space.usage_rate * 100}%` }">
                <span class="usage-text">{{ Math.round(space.usage_rate * 100) }}%</span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, required: true }
})

const heatmapData = computed(() => props.data.heatmap || [])

const visibleSpaces = computed(() => {
  const allSpaces = heatmapData.value.flatMap(t => t.spaces)
  return [...new Map(allSpaces.map(s => [s.space_id, s])).values()]
})
</script>

<style scoped>
.quota-heatmap {
  background: var(--bg-secondary, #161b22);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.legend {
  display: flex;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.legend-item .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-item.normal .dot { background: #3fb950; }
.legend-item.warning .dot { background: #d29922; }
.legend-item.critical .dot { background: #f85149; }

.heatmap-table {
  width: 100%;
  border-collapse: collapse;
}

.heatmap-table th,
.heatmap-table td {
  padding: 8px;
  text-align: left;
  border-bottom: 1px solid var(--border, #30363d);
}

.team-name {
  font-weight: 500;
}

.usage-cell { padding: 4px 8px !important; }

.usage-bar {
  height: 20px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 4px;
  min-width: 40px;
}

.usage-cell.normal .usage-bar { background: rgba(63, 185, 80, 0.3); }
.usage-cell.warning .usage-bar { background: rgba(210, 153, 34, 0.3); }
.usage-cell.critical .usage-bar { background: rgba(248, 81, 73, 0.3); }

.usage-text {
  font-size: 11px;
  color: var(--text-secondary, #8b949e);
}
</style>