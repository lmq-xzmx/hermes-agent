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

