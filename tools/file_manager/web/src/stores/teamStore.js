// ============================================================================
// Team Store - Pinia Store for Team Management
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

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
  const isAdmin = computed(() => localStorage.getItem('hfm_role') === 'admin')

  // Helper: get auth headers
  function getAuthHeaders() {
    const token = localStorage.getItem('hfm_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  // Actions
  async function loadTeams() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/teams`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load teams')
      const data = await res.json()
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
      const res = await fetch(`${API_BASE}/teams/all`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load all teams')
      const data = await res.json()
      allTeams.value = data.teams || []
    } catch (e) {
      error.value = e.message
    } finally {
      loading.value = false
    }
  }

  async function createTeam(name, description = '', storagePoolId = 'default', maxBytes = 1073741824) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/teams`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name,
          description,
          storage_pool_id: storagePoolId,
          max_bytes: maxBytes
        })
      })
      if (!res.ok) throw new Error('Failed to create team')
      const data = await res.json()
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
      const res = await fetch(`${API_BASE}/teams/join`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ invite_code: inviteCode })
      })
      if (!res.ok) throw new Error('Failed to join team')
      await loadTeams()
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function leaveTeam(teamId) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/teams/${teamId}/leave`, {
        method: 'POST',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to leave team')
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
      const res = await fetch(`${API_BASE}/teams/${teamId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to delete team')
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
      const res = await fetch(`${API_BASE}/teams/${teamId}/members`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load members')
      const data = await res.json()
      teamMembers.value = data.members || []
      return teamMembers.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function inviteMember(teamId, username) {
    try {
      const res = await fetch(`${API_BASE}/teams/${teamId}/invite`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ username })
      })
      if (!res.ok) throw new Error('Failed to invite member')
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function removeMember(teamId, userId) {
    try {
      const res = await fetch(`${API_BASE}/teams/${teamId}/members/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to remove member')
      await loadTeamMembers(teamId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function createInviteCode(teamId) {
    try {
      const res = await fetch(`${API_BASE}/teams/${teamId}/invite-code`, {
        method: 'POST',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to create invite code')
      return await res.json()
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
    leaveTeam,
    deleteTeam,
    loadTeamMembers,
    inviteMember,
    removeMember,
    createInviteCode,
    setCurrentTeam,
    clearTeams
  }
})

export default useTeamStore
