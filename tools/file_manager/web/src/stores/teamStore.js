// ============================================================================
// Team Store - Pinia Store for Team Management
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './authStore'
import { api } from '../services/api.js'

export const useTeamStore = defineStore('teams', () => {
  // State
  const myTeams = ref([])
  const allTeams = ref([])
  const currentTeam = ref(null)
  const teamMembers = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const hasTeams = computed(() => myTeams.value.length > 0)
  const teamCount = computed(() => myTeams.value.length)

  // Admin getter: 必须通过 authStore 获取，禁止直接读取 localStorage
  const isAdmin = computed(() => useAuthStore().isAdmin)

  // Helper: get auth headers
  function getAuthHeaders() {
    return api.getHeaders()
  }

  // Actions
  async function loadTeams() {
    loading.value = true
    error.value = null
    try {
      const data = await api.getTeams()
      myTeams.value = data.teams || []
    } catch (e) {
      error.value = e.message
      console.error('loadTeams error:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadAllTeams() {
    if (!isAdmin.value) return
    loading.value = true
    try {
      const data = await api.getAllTeams()
      allTeams.value = data.teams || []
    } catch (e) {
      console.warn('[teamStore] loadAllTeams failed:', e.message)
      allTeams.value = []
    } finally {
      loading.value = false
    }
  }

  async function createTeam(name, description = '', storagePoolId = null, maxBytes = null) {
    loading.value = true
    error.value = null
    try {
      const data = await api.createTeam(name, description, storagePoolId, maxBytes)
      await loadTeams()
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function joinTeam(inviteCode) {
    loading.value = true
    error.value = null
    try {
      await api.joinTeam(inviteCode)
      await loadTeams()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  // 验证邀请码有效性（预检）- FE-022
  async function validateInviteCode(inviteCode) {
    try {
      return await api.validateInviteCodeByToken(inviteCode)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  // 先预检再加入团队（符合 FE-022 规范）
  async function joinTeamWithValidation(inviteCode) {
    // 1. 预检邀请码
    await validateInviteCode(inviteCode)
    // 2. 预检通过，执行加入
    return await joinTeam(inviteCode)
  }

  async function leaveTeam(teamId) {
    loading.value = true
    try {
      await api.leaveTeam(teamId)
      await loadTeams()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteTeam(teamId) {
    loading.value = true
    try {
      await api.deleteTeam(teamId)
      await loadTeams()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function loadTeamMembers(teamId) {
    try {
      const data = await api.getTeamMembers(teamId)
      teamMembers.value = data.members || []
      return teamMembers.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function inviteMember(teamId, username) {
    try {
      return await api.addTeamMember(teamId, username)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function removeMember(teamId, userId) {
    try {
      await api.removeTeamMember(teamId, userId)
      await loadTeamMembers(teamId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function createInviteCode(teamId, maxUses = 10, expiresAt = null) {
    try {
      return await api.createTeamCredential(teamId, { max_uses: maxUses, expires_at: expiresAt })
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function getTeamCredentials(teamId) {
    try {
      return await api.getTeamCredentials(teamId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function fetchTeamQuotaStatus(teamId) {
    try {
      return await api.getTeamQuotaStatus(teamId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function deleteTeamCredential(teamId, credId) {
    try {
      return await api.deleteTeamCredential(teamId, credId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  // 获取管理员的所有待审批任务
  async function fetchPendingTasks() {
    try {
      return await api.getPendingApprovals()
    } catch (e) {
      console.warn('[teamStore] fetchPendingTasks failed:', e.message)
      return { requests: [] }
    }
  }

  // 成员申请退出团队
  async function requestTeamExit(teamId) {
    try {
      return await api.requestTeamExit(teamId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  // 管理员移除团队成员
  async function removeTeamMember(teamId, memberId) {
    try {
      return await api.removeTeamMember(teamId, memberId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  // 处理审批（批准/拒绝）
  async function processApproval(requestId, decision, comment = null) {
    try {
      return await api.processApproval(requestId, decision, comment)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function updateTeam(teamId, data) {
    try {
      return await api.updateTeam(teamId, data)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function setCurrentTeam(team) {
    currentTeam.value = team
  }

  function clearTeams() {
    myTeams.value = []
    allTeams.value = []
    currentTeam.value = null
    teamMembers.value = []
  }

  return {
    // State
    myTeams,
    allTeams,
    currentTeam,
    teamMembers,
    loading,
    error,
    // Getters
    hasTeams,
    teamCount,
    isAdmin,
    // Actions
    loadTeams,
    loadAllTeams,
    createTeam,
    joinTeam,
    joinTeamWithValidation,
    validateInviteCode,
    leaveTeam,
    deleteTeam,
    loadTeamMembers,
    inviteMember,
    removeMember,
    createInviteCode,
    getTeamCredentials,
    fetchTeamQuotaStatus,
    deleteTeamCredential,
    fetchPendingTasks,
    requestTeamExit,
    removeTeamMember,
    processApproval,
    updateTeam,
    setCurrentTeam,
    clearTeams
  }
})

export default useTeamStore
