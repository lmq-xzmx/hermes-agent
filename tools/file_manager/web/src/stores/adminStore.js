import { defineStore } from 'pinia'
import { adminAnalyticsApi } from '@/services/adminAnalytics'
import { connectAdminAnalytics, disconnectAdminAnalytics } from '@/services/websocket'

export const useAdminStore = defineStore('admin', {
  state: () => ({
    overview: null,
    storagePools: [],
    userSpaces: { nodes: [], links: [] },
    quotaHeatmap: { heatmap: [], legend: {} },
    operationTrends: { dates: [], series: [] },
    activeUsers: [],
    alerts: [],
    teamsByPool: [],
    currentPoolName: null,
    loading: false,
    error: null,
    lastUpdated: null,
    wsEnabled: false,
    wsToken: null
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
    },

    async fetchTeamsByPool(poolId) {
      this.loading = true
      try {
        const data = await adminAnalyticsApi.getTeamsByPool(poolId)
        this.teamsByPool = data.teams
        this.currentPoolName = data.poolName
      } catch (e) {
        this.error = e.message
      } finally {
        this.loading = false
      }
    },

    /**
     * 启用 WebSocket 实时更新
     * @param {string} token - 认证 token
     */
    enableWebSocket(token) {
      if (this.wsEnabled) return

      this.wsEnabled = true
      this.wsToken = token

      connectAdminAnalytics(token, (data) => {
        // 更新各个数据源
        if (data.overview) {
          this.overview = { ...this.overview, ...data.overview }
        }
        if (data.storagePools) {
          this.storagePools = data.storagePools
        }
        if (data.alerts) {
          this.alerts = data.alerts
        }
        this.lastUpdated = new Date()
      })
    },

    /**
     * 禁用 WebSocket
     */
    disableWebSocket() {
      disconnectAdminAnalytics()
      this.wsEnabled = false
      this.wsToken = null
    }
  }
})