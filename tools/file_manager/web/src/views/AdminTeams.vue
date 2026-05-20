<template>
  <div class="admin-teams">
    <header class="admin-teams__page-header">
      <h1>存储池 {{ poolName ? ` - ${poolName}` : '' }}</h1>
      <div class="admin-teams__header-actions">
        <button @click="refresh" class="btn-apple-secondary">🔄 刷新</button>
        <button @click="goBack" class="btn-apple-secondary">← 返回</button>
      </div>
    </header>

    <div v-if="loading" class="admin-teams__loading">加载中...</div>

    <div v-else-if="teams.length === 0" class="admin-teams__empty-state">
      <p>该存储池暂无团队使用</p>
    </div>

    <div v-else class="admin-teams__table-container">
      <p class="admin-teams__table-summary">共 {{ teams.length }} 个团队使用此存储池</p>
      <table class="admin-teams__table">
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
            <td class="admin-teams__team-name">{{ team.teamName }}</td>
            <td>{{ team.memberCount }}</td>
            <td>{{ formatBytes(team.storageUsed) }}</td>
            <td>{{ formatBytes(team.storageQuota) }}</td>
            <td>
              <span :class="['admin-teams__usage-badge', `admin-teams__usage-badge--${getUsageClass(team.usageRate)}`]">
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
/* === Admin Teams Styles === */

/* --- Page Header --- */
.admin-teams__page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-xl);
}

.admin-teams__page-header h1 {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

.admin-teams__header-actions {
  display: flex;
  gap: var(--spacing-sm);
}

/* --- Loading State --- */
.admin-teams__loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

/* --- Empty State --- */
.admin-teams__empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xxl);
  text-align: center;
}

.admin-teams__empty-state p {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  margin: 0;
}

/* --- Teams Table Container --- */
.admin-teams__table-container {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.admin-teams__table-summary {
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  padding: var(--spacing-md) var(--spacing-lg);
  margin: 0;
  border-bottom: 1px solid var(--color-hairline);
}

/* --- Teams Table --- */
.admin-teams__table {
  width: 100%;
  border-collapse: collapse;
}

.admin-teams__table th {
  font: var(--text-caption-strong);
  text-transform: uppercase;
  letter-spacing: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-align: left;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-bottom: 1px solid var(--color-hairline);
}

.admin-teams__table td {
  font: var(--text-body);
  color: var(--color-ink);
  padding: var(--spacing-sm) var(--spacing-md);
  border-bottom: 1px solid var(--color-divider-soft);
}

.admin-teams__table tr:last-child td {
  border-bottom: none;
}

.admin-teams__table tr:hover td {
  background: var(--color-surface-pearl);
}

/* --- Team Name Cell --- */
.admin-teams__team-name {
  font: var(--text-body-strong);
  color: var(--color-ink);
}

/* --- Usage Badge (stored in tokens.css) --- */
.admin-teams__usage-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--spacing-xxs) var(--spacing-sm);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
}

.admin-teams__usage-badge--normal {
  background: var(--color-success-subtle);
  color: var(--color-success);
}

.admin-teams__usage-badge--warning {
  background: var(--color-warning-subtle);
  color: var(--color-warning-strong);
}

.admin-teams__usage-badge--critical {
  background: var(--color-danger-subtle);
  color: var(--color-danger);
}
</style>

