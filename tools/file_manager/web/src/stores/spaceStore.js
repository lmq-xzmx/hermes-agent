// ============================================================================
// Space Store - Pinia Store for Space Management
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export const useSpaceStore = defineStore('spaces', () => {
  // State
  const spaces = ref([])
  const selectedSpace = ref(null)
  const currentSpaceId = ref(null)
  const members = ref([])
  const workflows = ref([])
  const notebooks = ref([])
  const activities = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const hasSpaces = computed(() => spaces.value.length > 0)
  const spaceCount = computed(() => spaces.value.length)
  const activeSpace = computed(() => selectedSpace.value)

  // Helper: get auth headers
  function getAuthHeaders() {
    const token = localStorage.getItem('hfm_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  // Actions
  async function loadSpaces() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/spaces`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load spaces')
      const data = await res.json()
      spaces.value = data.spaces || []
    } catch (e) {
      error.value = e.message
      console.error('loadSpaces error:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createSpace(name, teamId = null, spaceType = 'private') {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/spaces`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name,
          team_id: teamId,
          space_type: spaceType
        })
      })
      if (!res.ok) throw new Error('Failed to create space')
      const data = await res.json()
      await loadSpaces()
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteSpace(spaceId) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to delete space')
      await loadSpaces()
      if (selectedSpace.value?.space_id === spaceId) {
        selectedSpace.value = null
        currentSpaceId.value = null
      }
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function selectSpace(space) {
    selectedSpace.value = space
    currentSpaceId.value = space?.space_id
    await Promise.all([
      loadSpaceMembers(space.space_id),
      loadSpaceWorkflows(space.space_id),
      loadSpaceNotebooks(space.space_id)
    ])
  }

  async function loadSpaceDetail(spaceId) {
    try {
      const [membersData, workflowsData, notebooksData] = await Promise.all([
        loadSpaceMembers(spaceId),
        loadSpaceWorkflows(spaceId),
        loadSpaceNotebooks(spaceId)
      ])
      members.value = membersData || []
      workflows.value = workflowsData || []
      notebooks.value = notebooksData || []
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadSpaceMembers(spaceId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/members`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load members')
      const data = await res.json()
      members.value = data.members || []
      return members.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadSpaceWorkflows(spaceId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/workflows`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load workflows')
      const data = await res.json()
      workflows.value = data.workflows || []
      return workflows.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadSpaceNotebooks(spaceId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/notebooks`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load notebooks')
      const data = await res.json()
      notebooks.value = data.notebooks || []
      return notebooks.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function loadSpaceActivities(spaceId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/activities`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load activities')
      const data = await res.json()
      activities.value = data.activities || []
      return activities.value
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function inviteSpaceMember(spaceId, username, role = 'member') {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/members`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ username, role })
      })
      if (!res.ok) throw new Error('Failed to invite member')
      await loadSpaceMembers(spaceId)
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function removeSpaceMember(spaceId, userId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/members/${userId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to remove member')
      await loadSpaceMembers(spaceId)
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function createCrossTeamSpaceLink(spaceId, targetTeamId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/cross-team-links`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ target_team_id: targetTeamId })
      })
      if (!res.ok) throw new Error('Failed to create cross-team link')
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function updateSpaceQuota(spaceId, quotaTotal) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${spaceId}/quota`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ quota_total: quotaTotal })
      })
      if (!res.ok) throw new Error('Failed to update quota')
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function setCurrentSpaceId(spaceId) {
    currentSpaceId.value = spaceId
  }

  function clearSpaces() {
    spaces.value = []
    selectedSpace.value = null
    currentSpaceId.value = null
    members.value = []
    workflows.value = []
    notebooks.value = []
    activities.value = []
  }

  return {
    // State
    spaces,
    selectedSpace,
    currentSpaceId,
    members,
    workflows,
    notebooks,
    activities,
    loading,
    error,
    // Getters
    hasSpaces,
    spaceCount,
    activeSpace,
    // Actions
    loadSpaces,
    createSpace,
    deleteSpace,
    selectSpace,
    loadSpaceDetail,
    loadSpaceMembers,
    loadSpaceWorkflows,
    loadSpaceNotebooks,
    loadSpaceActivities,
    inviteSpaceMember,
    removeSpaceMember,
    createCrossTeamSpaceLink,
    updateSpaceQuota,
    setCurrentSpaceId,
    clearSpaces
  }
})

export default useSpaceStore
