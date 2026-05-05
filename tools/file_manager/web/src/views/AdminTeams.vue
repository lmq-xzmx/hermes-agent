<template>
  <div class="admin-teams">
    <header class="page-header">
      <h1>存储池 {{ poolName ? ` - ${poolName}` : '' }}</h1>
      <div class="header-actions">
        <button @click="refresh" class="btn-apple-secondary">🔄 刷新</button>
        <button @click="goBack" class="btn-apple-secondary">← 返回</button>
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
  min-height: 100vh;
  background: var(--color-canvas-parchment);
  padding: var(--space-section);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-xl);
  max-width: 1440px;
  margin-left: auto;
  margin-right: auto;
}

.page-header h1 {
  font: var(--text-display-md);
  font-weight: 600;
  color: var(--color-ink);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.loading, .empty-state {
  text-align: center;
  padding: var(--space-xl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.teams-summary {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--space-md);
}

.teams-table-container {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--rounded-lg);
  overflow: hidden;
  max-width: 1440px;
  margin: 0 auto;
}

.teams-table {
  width: 100%;
  border-collapse: collapse;
}

.teams-table th,
.teams-table td {
  padding: var(--space-md);
  text-align: left;
  border-bottom: 1px solid var(--color-hairline);
}

.teams-table th {
  background: var(--color-canvas-parchment);
  font: var(--text-caption);
  font-weight: 600;
  color: var(--color-ink-muted-48);
}

.teams-table td {
  font: var(--text-body);
  color: var(--color-ink);
}

.teams-table tr:last-child td {
  border-bottom: none;
}

.teams-table tr:hover td {
  background: var(--color-canvas-parchment);
}

.team-name {
  font-weight: 600;
}

.usage-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: var(--rounded-pill);
  font: var(--text-caption);
  font-weight: 600;
}

.usage-badge.normal {
  background: var(--color-primary-subtle);
  color: var(--color-primary);
}

.usage-badge.warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

.usage-badge.critical {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}
</style>
