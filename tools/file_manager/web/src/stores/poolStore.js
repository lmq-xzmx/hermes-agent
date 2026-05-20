// ============================================================================
// Pool Store - Pinia Store for Storage Pool Management
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export const usePoolStore = defineStore('pools', () => {
  // State
  const pools = ref([])
  const selectedPool = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const hasPools = computed(() => pools.value.length > 0)
  const poolCount = computed(() => pools.value.length)

  // Helper: get auth headers
  function getAuthHeaders() {
    const token = localStorage.getItem('hfm_token')
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  }

  // Parse size string like "100GB" to bytes
  function parseSize(sizeStr) {
    if (!sizeStr) return 0
    const match = sizeStr.match(/^(\d+(?:\.\d+)?)\s*(B|KB|MB|GB|TB)?$/i)
    if (!match) return 0
    const value = parseFloat(match[1])
    const unit = (match[2] || 'B').toUpperCase()
    const units = { 'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4 }
    return Math.floor(value * (units[unit] || 1))
  }

  // Actions
  async function loadPools() {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/pools`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load pools')
      const data = await res.json()
      // Normalize response format - backend returns {pools: [...]} or [...]
      const rawPools = Array.isArray(data) ? data : (data.pools || [])
      // Map backend fields to frontend expected fields
      pools.value = rawPools.map(p => ({
        pool_id: p.id,
        name: p.name,
        description: p.description || '',
        status: p.is_active ? 'active' : 'inactive',
        type: p.protocol || 'local',
        total_bytes: p.total_bytes || 0,
        used_bytes: p.used_bytes || (p.total_bytes && p.free_bytes ? p.total_bytes - p.free_bytes : 0),
        free_bytes: p.free_bytes || 0,
        usage_ratio: p.total_bytes > 0 ? ((p.used_bytes || (p.total_bytes - p.free_bytes)) / p.total_bytes) : 0,
        base_path: p.base_path,
        protocol: p.protocol,
        is_active: p.is_active,
        created_at: p.created_at
      }))
    } catch (e) {
      error.value = e.message
      console.error('loadPools error:', e)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createPool(name, type = 'standard', sizeStr = '100GB') {
    loading.value = true
    error.value = null
    try {
      const sizeBytes = parseSize(sizeStr)
      const res = await fetch(`${API_BASE}/pools`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          name,
          protocol: type === 'high-performance' ? 'smb' : (type === 'archival' ? 'nfs' : 'local'),
          total_bytes: sizeBytes,
          base_path: `/data/pools/${name.replace(/\s+/g, '_')}`,
          description: ''
        })
      })
      if (!res.ok) throw new Error('Failed to create pool')
      const data = await res.json()
      await loadPools()
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function updatePool(poolId, updates) {
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`${API_BASE}/pools/${poolId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(updates)
      })
      if (!res.ok) throw new Error('Failed to update pool')
      const data = await res.json()
      await loadPools()
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deletePool(poolId) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/pools/${poolId}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to delete pool')
      await loadPools()
      if (selectedPool.value?.pool_id === poolId) {
        selectedPool.value = null
      }
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getPoolDetails(poolId) {
    try {
      const res = await fetch(`${API_BASE}/pools/${poolId}`, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to get pool details')
      const data = await res.json()
      selectedPool.value = data
      return data
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function runCleanup(poolId, target = 'temp') {
    try {
      const res = await fetch(`${API_BASE}/pools/${poolId}/cleanup`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ target })
      })
      if (!res.ok) throw new Error('Failed to run cleanup')
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function setSelectedPool(pool) {
    selectedPool.value = pool
  }

  function clearPools() {
    pools.value = []
    selectedPool.value = null
  }

  return {
    // State
    pools,
    selectedPool,
    loading,
    error,
    // Getters
    hasPools,
    poolCount,
    // Actions
    loadPools,
    createPool,
    updatePool,
    deletePool,
    getPoolDetails,
    runCleanup,
    setSelectedPool,
    clearPools
  }
})

export default usePoolStore
