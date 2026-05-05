// ============================================================================
// Unified API Service
// ============================================================================

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

class ApiService {
  constructor() {
    this.baseUrl = API_BASE
  }

  getHeaders() {
    const token = localStorage.getItem('hfm_token')
    return {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {})
    }
  }

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${this.baseUrl}${endpoint}`
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(),
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...options.headers
      }
    }

    const maxRetries = 3
    let lastError

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const res = await fetch(url, config)
        if (!res.ok) {
          const error = await res.json().catch(() => ({ detail: `HTTP ${res.status}` }))
          // Don't retry 4xx client errors (except 429 rate limit)
          if (res.status >= 400 && res.status < 500 && res.status !== 429) {
            throw new Error(error.detail || `Request failed: ${res.status}`)
          }
          // Retry 5xx server errors and 429 rate limit
          if (attempt < maxRetries) {
            const delay = Math.min(1000 * Math.pow(2, attempt), 10000)
            console.warn(`Request failed with ${res.status}, retrying in ${delay}ms... (${attempt + 1}/${maxRetries})`)
            await new Promise(resolve => setTimeout(resolve, delay))
            continue
          }
          throw new Error(error.detail || `Request failed: ${res.status}`)
        }
        return await res.json()
      } catch (e) {
        lastError = e
        // Network errors can be retried
        if (attempt < maxRetries && (e.name === 'TypeError' || e.message.includes('fetch'))) {
          const delay = Math.min(1000 * Math.pow(2, attempt), 10000)
          console.warn(`Network error, retrying in ${delay}ms... (${attempt + 1}/${maxRetries})`)
          await new Promise(resolve => setTimeout(resolve, delay))
          continue
        }
        console.error(`API Error [${endpoint}]:`, e)
        throw e
      }
    }

    throw lastError
  }

  // ============================================================================
  // Auth APIs
  // ============================================================================

  async login(username, password) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
  }

  async register(username, password, email) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email })
    })
  }

  async getCurrentUser() {
    return this.request('/auth/me')
  }

  // ============================================================================
  // Files APIs
  // ============================================================================

  async getFiles(spaceId, path = '/') {
    return this.request(`/spaces/${spaceId}/files?path=${encodeURIComponent(path)}`)
  }

  async uploadFile(spaceId, file, path = '/') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('path', path)
    return this.request(`/spaces/${spaceId}/files/upload`, {
      method: 'POST',
      body: formData
    })
  }

  async deleteFile(spaceId, fileId, path = '/') {
    return this.request(`/spaces/${spaceId}/files/${fileId}?path=${encodeURIComponent(path)}`, {
      method: 'DELETE'
    })
  }

  async moveFile(spaceId, fileId, sourcePath, targetPath) {
    return this.request(`/spaces/${spaceId}/files/${fileId}/move`, {
      method: 'POST',
      body: JSON.stringify({ source_path: sourcePath, target_path: targetPath })
    })
  }

  async shareFile(spaceId, fileId) {
    return this.request(`/spaces/${spaceId}/files/${fileId}/share`, {
      method: 'POST'
    })
  }

  async createFolder(spaceId, path) {
    return this.request(`/spaces/${spaceId}/files/mkdir`, {
      method: 'POST',
      body: JSON.stringify({ path })
    })
  }

  async createFile(spaceId, path, content = '') {
    return this.request(`/spaces/${spaceId}/files/write`, {
      method: 'POST',
      body: JSON.stringify({ path, content, overwrite: false })
    })
  }

  async getFileContent(spaceId, filePath) {
    return this.request(`/spaces/${spaceId}/files/content?path=${encodeURIComponent(filePath)}`)
  }

  // ============================================================================
  // Teams APIs
  // ============================================================================

  async getTeams() {
    return this.request('/teams/my')
  }

  async getAllTeams() {
    return this.request('/teams')
  }

  async createTeam(name, description) {
    return this.request('/teams/create', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    })
  }

  async joinTeam(token) {
    return this.request('/teams/join', {
      method: 'POST',
      body: JSON.stringify({ token })
    })
  }

  async deleteTeam(teamId) {
    return this.request(`/teams/${teamId}`, {
      method: 'DELETE'
    })
  }

  async getTeamDetail(teamId) {
    return this.request(`/teams/${teamId}`)
  }

  async getTeamMembers(teamId) {
    return this.request(`/teams/${teamId}/members`)
  }

  async addTeamMember(teamId, username, role = 'member') {
    return this.request(`/teams/${teamId}/members`, {
      method: 'POST',
      body: JSON.stringify({ username, role })
    })
  }

  async removeTeamMember(teamId, memberId) {
    return this.request(`/teams/${teamId}/members/${memberId}`, {
      method: 'DELETE'
    })
  }

  async updateTeam(teamId, updates) {
    return this.request(`/teams/${teamId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    })
  }

  // ============================================================================
  // Spaces APIs
  // ============================================================================

  async getSpaces() {
    return this.request('/spaces')
  }

  async getStorageContexts() {
    return this.request('/my/storage-context')
  }

  async createSpace(name, description) {
    return this.request('/spaces', {
      method: 'POST',
      body: JSON.stringify({ name, description })
    })
  }

  async deleteSpace(spaceId) {
    return this.request(`/spaces/${spaceId}`, {
      method: 'DELETE'
    })
  }

  async getSpaceMembers(spaceId) {
    return this.request(`/spaces/${spaceId}/members`)
  }

  async inviteSpaceMember(spaceId, username, role = 'member') {
    return this.request(`/spaces/${spaceId}/members`, {
      method: 'POST',
      body: JSON.stringify({ username, role })
    })
  }

  async removeSpaceMember(spaceId, memberId) {
    return this.request(`/spaces/${spaceId}/members/${memberId}`, {
      method: 'DELETE'
    })
  }

  async getSpaceWorkflows(spaceId) {
    return this.request(`/spaces/${spaceId}/workflows`)
  }

  async getSpaceNotebooks(spaceId) {
    return this.request(`/spaces/${spaceId}/notebooks`)
  }

  async getSpaceActivities(spaceId) {
    return this.request(`/spaces/${spaceId}/activities`)
  }

  // ============================================================================
  // Workflow APIs
  // ============================================================================

  async getWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`)
  }

  async createWorkflow(spaceId, { name, description, is_shared, tags, steps }) {
    return this.request(`/spaces/${spaceId}/workflows`, {
      method: 'POST',
      body: JSON.stringify({ name, description, is_shared, tags, steps })
    })
  }

  async updateWorkflow(workflowId, { name, description, is_shared, steps }) {
    return this.request(`/workflows/${workflowId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name, description, is_shared, steps })
    })
  }

  async deleteWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}`, {
      method: 'DELETE'
    })
  }

  async executeWorkflow(workflowId) {
    return this.request(`/workflows/${workflowId}/execute`, {
      method: 'POST',
      body: JSON.stringify({})
    })
  }

  // ============================================================================
  // Notebook APIs
  // ============================================================================

  async getNotebook(notebookId) {
    return this.request(`/notebooks/${notebookId}`)
  }

  async createNotebook(spaceId, { name, description, content, tags }) {
    return this.request(`/spaces/${spaceId}/notebooks`, {
      method: 'POST',
      body: JSON.stringify({ name, description, content, tags })
    })
  }

  async updateNotebook(notebookId, { name, description, content, tags }) {
    return this.request(`/notebooks/${notebookId}`, {
      method: 'PATCH',
      body: JSON.stringify({ name, description, content, tags })
    })
  }

  async deleteNotebook(notebookId) {
    return this.request(`/notebooks/${notebookId}`, {
      method: 'DELETE'
    })
  }

  async duplicateNotebook(notebookId) {
    return this.request(`/notebooks/${notebookId}/duplicate`, {
      method: 'POST'
    })
  }

  // ============================================================================
  // Team Credential APIs
  // ============================================================================

  async getTeamCredentials(teamId) {
    return this.request(`/teams/${teamId}/credentials`)
  }

  async createTeamCredential(teamId, { max_uses, expires_at }) {
    return this.request(`/teams/${teamId}/credentials`, {
      method: 'POST',
      body: JSON.stringify({ max_uses, expires_at })
    })
  }

  async deleteTeamCredential(teamId, credId) {
    return this.request(`/teams/${teamId}/credentials/${credId}`, {
      method: 'DELETE'
    })
  }

  // ============================================================================
  // Storage Pools APIs
  // ============================================================================

  async getPools() {
    return this.request('/pools')
  }

  async getPoolDetails(poolId) {
    return this.request(`/pools/${poolId}`)
  }

  async createPool(name, protocol, base_path, description) {
    return this.request('/pools', {
      method: 'POST',
      body: JSON.stringify({ name, protocol, base_path, description })
    })
  }

  async updatePool(poolId, updates) {
    return this.request(`/pools/${poolId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    })
  }

  async deletePool(poolId) {
    return this.request(`/pools/${poolId}`, {
      method: 'DELETE'
    })
  }

  async refreshPool(poolId) {
    return this.request(`/pools/${poolId}/refresh`, {
      method: 'POST'
    })
  }

  async runPoolCleanup(poolId, target = 'temp') {
    return this.request(`/pools/${poolId}/cleanup`, {
      method: 'POST',
      body: JSON.stringify({ target })
    })
  }

  // ============================================================================
  // Trash APIs
  // ============================================================================

  async getTrash(spaceId) {
    return this.request(`/spaces/${spaceId}/trash`)
  }

  async restoreTrashItem(spaceId, itemId) {
    return this.request(`/spaces/${spaceId}/trash/${itemId}/restore`, {
      method: 'POST'
    })
  }

  async permanentDeleteTrashItem(spaceId, itemId) {
    return this.request(`/spaces/${spaceId}/trash/${itemId}`, {
      method: 'DELETE'
    })
  }

  async emptyTrash(spaceId) {
    return this.request(`/spaces/${spaceId}/trash`, {
      method: 'DELETE'
    })
  }

  // ============================================================================
  // Knowledge APIs
  // ============================================================================

  async getKnowledgeStatus() {
    return this.request('/knowledge/status')
  }

  async syncToKnowledge(sourcePath, project = 'default') {
    return this.request('/knowledge/sync', {
      method: 'POST',
      body: JSON.stringify({ source_path: sourcePath, project_name: project })
    })
  }

  async searchKnowledge(query, project = 'default') {
    return this.request(`/knowledge/search?q=${encodeURIComponent(query)}&project=${project}`)
  }
}

// Export singleton instance
export const api = new ApiService()
export default api