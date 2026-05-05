// ============================================================================
// File Store - Pinia Store for File Management
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export const useFileStore = defineStore('files', () => {
  // State
  const currentPath = ref('/')
  const currentSpaceId = ref(null)
  const files = ref([])
  const selectedFiles = ref(new Set())
  const viewMode = ref('list') // 'list' or 'grid'
  const loading = ref(false)
  const error = ref(null)
  const currentTeam = ref(null)

  // Getters
  const hasSelectedFiles = computed(() => selectedFiles.value.size > 0)
  const selectedCount = computed(() => selectedFiles.value.size)
  const fileList = computed(() => files.value)
  const isListView = computed(() => viewMode.value === 'list')

  // Actions
  async function loadFiles(path = currentPath.value, spaceId = currentSpaceId.value) {
    if (!spaceId) {
      error.value = 'No space selected'
      return
    }
    loading.value = true
    error.value = null
    try {
      const url = `${API_BASE}/spaces/${spaceId}/files?path=${encodeURIComponent(path)}`
      const res = await fetch(url, {
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Failed to load files')
      const data = await res.json()
      files.value = data.files || []
      currentPath.value = path
    } catch (e) {
      error.value = e.message
      console.error('loadFiles error:', e)
    } finally {
      loading.value = false
    }
  }

  async function uploadFile(file, targetPath = currentPath.value) {
    if (!currentSpaceId.value) {
      throw new Error('No space selected')
    }
    loading.value = true
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('path', targetPath)

      const res = await fetch(`${API_BASE}/spaces/${currentSpaceId.value}/files/upload`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData
      })
      if (!res.ok) throw new Error('Upload failed')
      // Refresh file list
      await loadFiles()
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function deleteFile(fileId, path = currentPath.value) {
    loading.value = true
    try {
      const res = await fetch(`${API_BASE}/spaces/${currentSpaceId.value}/files/${fileId}?path=${encodeURIComponent(path)}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Delete failed')
      // Refresh file list
      await loadFiles()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function moveFile(fileId, sourcePath, targetPath) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${currentSpaceId.value}/files/${fileId}/move`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ source_path: sourcePath, target_path: targetPath })
      })
      if (!res.ok) throw new Error('Move failed')
      await loadFiles()
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function shareFile(fileId) {
    try {
      const res = await fetch(`${API_BASE}/spaces/${currentSpaceId.value}/files/${fileId}/share`, {
        method: 'POST',
        headers: getAuthHeaders()
      })
      if (!res.ok) throw new Error('Share failed')
      return await res.json()
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  function setViewMode(mode) {
    viewMode.value = mode
  }

  function toggleViewMode() {
    viewMode.value = viewMode.value === 'list' ? 'grid' : 'list'
  }

  function selectFile(fileId, multi = false) {
    if (multi) {
      if (selectedFiles.value.has(fileId)) {
        selectedFiles.value.delete(fileId)
      } else {
        selectedFiles.value.add(fileId)
      }
    } else {
      selectedFiles.value.clear()
      selectedFiles.value.add(fileId)
    }
  }

  function selectAll() {
    files.value.forEach(f => selectedFiles.value.add(f.id))
  }

  function clearSelection() {
    selectedFiles.value.clear()
  }

  function setCurrentPath(path) {
    currentPath.value = path
  }

  function setCurrentSpaceId(spaceId) {
    currentSpaceId.value = spaceId
  }

  function getAuthHeaders() {
    const token = localStorage.getItem('hfm_token')
    return {
      'Authorization': `Bearer ${token}`
    }
  }

  return {
    // State
    currentPath,
    currentSpaceId,
    files,
    selectedFiles,
    viewMode,
    loading,
    error,
    currentTeam,
    // Getters
    hasSelectedFiles,
    selectedCount,
    fileList,
    isListView,
    // Actions
    loadFiles,
    uploadFile,
    deleteFile,
    moveFile,
    shareFile,
    setViewMode,
    toggleViewMode,
    selectFile,
    selectAll,
    clearSelection,
    setCurrentPath,
    setCurrentSpaceId
  }
})

export default useFileStore