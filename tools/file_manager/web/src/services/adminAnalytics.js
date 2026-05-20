import { defineStore } from 'pinia'

const API_BASE = '/api/v1/admin/analytics'

const cache = new Map()
const CACHE_TTL = 5 * 60 * 1000

async function fetchWithCache(key, url) {
  const cached = cache.get(key)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  const resp = await fetch(url)
  if (!resp.ok) throw new Error(`API error: ${resp.status}`)
  const data = await resp.json()
  cache.set(key, { data, timestamp: Date.now() })
  return data
}

function transformStoragePools(data) {
  return data.pools.map(p => ({
    id: p.id,
    name: p.name,
    protocol: p.protocol,
    basePath: p.base_path,
    totalBytes: p.total_bytes,
    usedBytes: p.used_bytes,
    freeBytes: p.free_bytes,
    effectiveFreeBytes: p.effective_free_bytes,
    usageRate: p.usage_rate,
    teamCount: p.team_count,
    spaceCount: p.space_count,
    maxTeamsEstimate: p.max_teams_estimate,
    status: p.status
  }))
}

function transformUserSpaces(data) {
  return {
    nodes: data.nodes.map(n => ({
      id: n.id,
      name: n.name,
      type: n.type,
      role: n.role
    })),
    links: data.links.map(l => ({
      source: l.source,
      target: l.target,
      value: l.value,
      role: l.role
    })),
    stats: data.stats
  }
}

function transformQuotaHeatmap(data) {
  return {
    heatmap: data.heatmap.map(t => ({
      team_id: t.team_id,
      team_name: t.team_name,
      spaces: t.spaces.map(s => ({
        space_id: s.space_id,
        space_name: s.space_name,
        usage_rate: s.usage_rate,
        status: s.status
      }))
    })),
    legend: data.legend
  }
}

function transformOperationTrends(data) {
  return {
    dates: data.dates,
    series: data.series.map(s => ({
      name: s.name,
      data: s.data
    }))
  }
}

export const adminAnalyticsApi = {
  async getOverview() {
    const data = await fetchWithCache('overview', `${API_BASE}/overview`)
    return {
      summary: {
        total_users: data.total_users,
        active_users_7d: data.active_users_7d,
        new_users_7d: data.new_users_7d,
        total_teams: data.total_teams,
        total_spaces: data.total_spaces,
        total_pools: data.total_pools,
        storage: data.storage,
        alerts: data.alerts || [],
        recent_activities: data.recent_activities || []
      }
    }
  },

  async getStoragePools() {
    const data = await fetchWithCache('storage_pools', `${API_BASE}/storage-pools`)
    return { pools: transformStoragePools(data), summary: data.summary }
  },

  async getUserSpaces() {
    const data = await fetchWithCache('user_spaces', `${API_BASE}/user-spaces`)
    return transformUserSpaces(data)
  },

  async getQuotaHeatmap() {
    const data = await fetchWithCache('quota_heatmap', `${API_BASE}/quota-heatmap`)
    return transformQuotaHeatmap(data)
  },

  async getOperationTrends(days = 30) {
    const data = await fetchWithCache(`trends_${days}`, `${API_BASE}/operation-trends?days=${days}`)
    return transformOperationTrends(data)
  },

  async getActiveUsers(days = 7) {
    return fetchWithCache(`active_users_${days}`, `${API_BASE}/active-users?days=${days}`)
  },

  async getTeamsByPool(poolId) {
    const data = await fetchWithCache(`teams_by_pool_${poolId}`, `${API_BASE}/teams-by-pool/${poolId}`)
    return {
      poolId: data.pool_id,
      poolName: data.pool_name,
      teams: data.teams.map(t => ({
        teamId: t.team_id,
        teamName: t.team_name,
        memberCount: t.member_count,
        storageUsed: t.storage_used,
        storageQuota: t.storage_quota,
        usageRate: t.usage_rate,
        owner: t.owner,
        createdAt: t.created_at
      })),
      total: data.total
    }
  }
}