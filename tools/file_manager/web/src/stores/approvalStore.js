/**
 * Approval Store - 审批状态管理
 *
 * 管理审批申请和审批列表的状态
 */

import { defineStore } from 'pinia'
import {
  createApproval,
  getMyApprovals,
  getPendingApprovals,
  getApproval,
  processApproval,
  cancelApproval,
  APPROVAL_TYPES,
  STATUS_LABELS,
  STATUS_COLORS
} from '@/services/approvalApi'

export const useApprovalStore = defineStore('approval', {
  state: () => ({
    // 我的申请
    myRequests: [],
    myRequestsLoading: false,
    myRequestsError: null,

    // 待审批列表（管理员）
    pendingRequests: [],
    pendingLoading: false,
    pendingError: null,

    // 当前选中的申请
    selectedRequest: null,
    selectedLoading: false,

    // 错误状态
    error: null
  }),

  getters: {
    // 获取状态标签
    getStatusLabel: (state) => (status) => STATUS_LABELS[status] || status,

    // 获取状态颜色
    getStatusColor: (state) => (status) => STATUS_COLORS[status] || '#6b7280',

    // 获取类型标签
    getTypeLabel: (state) => (type) => APPROVAL_TYPES[type] || type,

    // 待审批数量
    pendingCount: (state) => state.pendingRequests.length,

    // 我的待处理申请数量
    myPendingCount: (state) =>
      state.myRequests.filter(r => r.status === 'pending').length
  },

  actions: {
    /**
     * 创建审批申请
     */
    async createRequest({ type, targetId, reason, params }) {
      this.error = null
      try {
        const result = await createApproval({ type, targetId, reason, params })
        // 刷新我的申请列表
        await this.fetchMyRequests()
        return result
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    /**
     * 获取我的申请列表
     */
    async fetchMyRequests(status = null) {
      this.myRequestsLoading = true
      this.myRequestsError = null
      try {
        this.myRequests = await getMyApprovals(status)
      } catch (e) {
        this.myRequestsError = e.message
        this.myRequests = []
      } finally {
        this.myRequestsLoading = false
      }
    },

    /**
     * 获取待审批列表（管理员）
     */
    async fetchPendingRequests() {
      this.pendingLoading = true
      this.pendingError = null
      try {
        this.pendingRequests = await getPendingApprovals()
      } catch (e) {
        this.pendingError = e.message
        this.pendingRequests = []
      } finally {
        this.pendingLoading = false
      }
    },

    /**
     * 获取申请详情
     */
    async fetchRequest(requestId) {
      this.selectedLoading = true
      try {
        this.selectedRequest = await getApproval(requestId)
        return this.selectedRequest
      } catch (e) {
        this.error = e.message
        throw e
      } finally {
        this.selectedLoading = false
      }
    },

    /**
     * 处理审批决定
     */
    async decideRequest(requestId, decision, comment) {
      this.error = null
      try {
        const result = await processApproval(requestId, decision, comment)
        // 刷新待审批列表
        await this.fetchPendingRequests()
        // 清空选中
        this.selectedRequest = null
        return result
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    /**
     * 取消申请
     */
    async cancelRequest(requestId) {
      this.error = null
      try {
        const result = await cancelApproval(requestId)
        // 刷新我的申请列表
        await this.fetchMyRequests()
        return result
      } catch (e) {
        this.error = e.message
        throw e
      }
    },

    /**
     * 清空错误状态
     */
    clearError() {
      this.error = null
      this.myRequestsError = null
      this.pendingError = null
    },

    /**
     * 重置状态
     */
    reset() {
      this.myRequests = []
      this.myRequestsLoading = false
      this.myRequestsError = null
      this.pendingRequests = []
      this.pendingLoading = false
      this.pendingError = null
      this.selectedRequest = null
      this.selectedLoading = false
      this.error = null
    }
  }
})

// 导出常量供其他组件使用
export { APPROVAL_TYPES, STATUS_LABELS, STATUS_COLORS }
