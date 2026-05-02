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

export const adminAnalyticsApi = {
  async getOverview() {
    return fetchWithCache('overview', `${API_BASE}/overview`)
  },
  async getStoragePools() {
    return fetchWithCache('storage_pools', `${API_BASE}/storage-pools`)
  },
  async getUserSpaces() {
    return fetchWithCache('user_spaces', `${API_BASE}/user-spaces`)
  },
  async getQuotaHeatmap() {
    return fetchWithCache('quota_heatmap', `${API_BASE}/quota-heatmap`)
  },
  async getOperationTrends(days = 30) {
    return fetchWithCache(`trends_${days}`, `${API_BASE}/operation-trends?days=${days}`)
  },
  async getActiveUsers(days = 7) {
    return fetchWithCache(`active_users_${days}`, `${API_BASE}/active-users?days=${days}`)
  },
  async getAlerts() {
    return fetchWithCache('alerts', `${API_BASE}/alerts`)
  }
}