import { defineStore } from 'pinia'
import { adminAnalyticsApi } from '@/services/adminAnalytics'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null,
    storagePools: [],
    userSpaces: { nodes: [], links: [] },
    quotaHeatmap: { heatmap: [], legend: {} },
    operationTrends: { dates: [], series: [] },
    activeUsers: [],
    alerts: [],
    loading: false,
    error: null,
    lastUpdated: null
  }),

  getters: {
    totalStorage: (state) => {
      if (!state.storagePools.length) return 0
      return state.storagePools.reduce((sum, p) => sum + p.totalBytes, 0)
    },
    usedStorage: (state) => {
      if (!state.storagePools.length) return 0
      return state.storagePools.reduce((sum, p) => sum + p.usedBytes, 0)
    },
    criticalAlerts: (state) => state.alerts.filter(a => a.level === 'critical'),
    warningAlerts: (state) => state.alerts.filter(a => a.level === 'warning')
  },

  actions: {
    async fetchOverview() {
      this.loading = true
      try {
        const data = await adminAnalyticsApi.getOverview()
        this.overview = data.summary
        this.alerts = data.alerts || []
        this.lastUpdated = new Date()
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    async fetchStoragePools() {
      try {
        const data = await adminAnalyticsApi.getStoragePools()
        this.storagePools = data.pools
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchUserSpaces() {
      try {
        const data = await adminAnalyticsApi.getUserSpaces()
        this.userSpaces = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchQuotaHeatmap() {
      try {
        const data = await adminAnalyticsApi.getQuotaHeatmap()
        this.quotaHeatmap = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchOperationTrends(days = 30) {
      try {
        const data = await adminAnalyticsApi.getOperationTrends(days)
        this.operationTrends = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchActiveUsers(days = 7) {
      try {
        const data = await adminAnalyticsApi.getActiveUsers(days)
        this.activeUsers = data
      } catch (e) {
        this.error = e.message
      }
    },

    async fetchAll() {
      await Promise.all([
        this.fetchOverview(),
        this.fetchStoragePools(),
        this.fetchUserSpaces(),
        this.fetchQuotaHeatmap(),
        this.fetchOperationTrends(),
        this.fetchActiveUsers()
      ])
    }
  }
})