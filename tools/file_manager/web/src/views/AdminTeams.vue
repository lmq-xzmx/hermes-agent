<template>
  <div class="admin-teams">
    <header class="page-header">
      <h1>存储池 {{ poolName ? ` - ${poolName}` : '' }}</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn btn-secondary">🔄 刷新</button>
        <button @click="goBack" class="btn btn-secondary">← 返回</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else-if="teams.length === 0" class="empty-state">
      <p>该存储池暂无团队使用</p>
    </div>

    <div v-else class="teams-table-container">
      <p class="teams-summary">共 {{ teams.length }} 个团队使用此存储池</p>
      <table class="teams-table">
        <thead>
          <tr>
            <th>团队名称</th>
            <th>成员数</th>
            <th>存储使用</th>
            <th>配额</th>
            <th>使用率</th>
            <th>所有者</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="team in teams" :key="team.teamId">
            <td class="team-name">{{ team.teamName }}</td>
            <td>{{ team.memberCount }}</td>
            <td>{{ formatBytes(team.storageUsed) }}</td>
            <td>{{ formatBytes(team.storageQuota) }}</td>
            <td>
              <span :class="['usage-badge', getUsageClass(team.usageRate)]">
                {{ (team.usageRate * 100).toFixed(1) }}%
              </span>
            </td>
            <td>{{ team.owner?.username || '-' }}</td>
            <td>{{ formatDate(team.createdAt) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAdminStore } from '@/stores/adminStore'

const route = useRoute()
const router = useRouter()
const store = useAdminStore()

const poolId = computed(() => route.query.pool_id || route.params.poolId || '')
const poolName = computed(() => store.currentPoolName)
const teams = computed(() => store.teamsByPool)
const loading = computed(() => store.loading)

function refresh() {
  store.fetchTeamsByPool(poolId.value)
}

function goBack() {
  router.push('/admin/dashboard')
}

function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

function getUsageClass(rate) {
  if (rate > 0.9) return 'critical'
  if (rate > 0.7) return 'warning'
  return 'normal'
}

onMounted(() => {
  if (poolId.value) {
    store.fetchTeamsByPool(poolId.value)
  }
})
</script>

<style scoped>
.admin-teams {
  padding: 20px;
  background: var(--bg-primary, #0d1117);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary, #e6edf3);
}

.header-actions {
  display: flex;
  gap: 12px;
}

.btn {
  padding: 8px 16px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary {
  background: var(--bg-secondary, #161b22);
  color: var(--text-primary, #e6edf3);
  border: 1px solid var(--border, #30363d);
}

.loading, .empty-state {
  text-align: center;
  padding: 40px;
  color: var(--text-secondary, #8b949e);
}

.teams-summary {
  color: var(--text-secondary, #8b949e);
  margin-bottom: 16px;
}

.teams-table-container {
  background: var(--bg-secondary, #161b22);
  border: 1px solid var(--border, #30363d);
  border-radius: 8px;
  overflow: hidden;
}

.teams-table {
  width: 100%;
  border-collapse: collapse;
}

.teams-table th,
.teams-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border, #30363d);
}

.teams-table th {
  background: var(--bg-tertiary, #21262d);
  color: var(--text-secondary, #8b949e);
  font-weight: 500;
  font-size: 13px;
}

.teams-table td {
  color: var(--text-primary, #e6edf3);
  font-size: 14px;
}

.teams-table tr:last-child td {
  border-bottom: none;
}

.teams-table tr:hover td {
  background: var(--bg-tertiary, #21262d);
}

.team-name {
  font-weight: 500;
}

.usage-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.usage-badge.normal {
  background: rgba(63, 185, 80, 0.2);
  color: #3fb950;
}

.usage-badge.warning {
  background: rgba(210, 153, 34, 0.2);
  color: #d29922;
}

.usage-badge.critical {
  background: rgba(248, 81, 73, 0.2);
  color: #f85149;
}
</style>
