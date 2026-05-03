/**
 * LifecycleInterceptor - Frontend interceptor for lifecycle constraint violations.
 *
 * Transforms API errors into lifecycle violations and delegates modal display
 * to the lifecycleStore. This module is a pure error transformation layer.
 *
 * Architecture:
 *   API Response → handleApiError() → isLifecycleViolation() → lifecycleStore.showGuidance()
 */

import { useLifecycleStore } from '@/stores/lifecycleStore'

// Lifecycle violation error codes (同步自 lifecycle_engine.py)
const LIFECYCLE_CODES = new Set([
  // Pool constraints
  'POOL_NOT_FOUND', 'STORAGE_POOL_IN_USE', 'POOL_INACTIVE', 'NO_AVAILABLE_POOL',
  'POOL_TEAMS_MIGRATING',
  // Space constraints
  'SPACE_NOT_FOUND', 'SPACE_HAS_MEMBERS', 'SPACE_NO_MEMBERS', 'NOT_SPACE_OWNER',
  'NOT_SPACE_MEMBER', 'SPACE_QUOTA_EXCEEDED', 'QUOTA_EXCEEDED',
  'SPACE_HAS_PENDING_REQUESTS',
  // Team constraints
  'TEAM_NOT_FOUND', 'NOT_TEAM_OWNER', 'MEMBER_LIMIT_EXCEEDED', 'TEAM_QUOTA_EXCEEDED',
  'MEMBER_RECENTLY_REMOVED',
  // Credential constraints
  'INVALID_CREDENTIAL', 'CREDENTIAL_EXPIRED', 'CREDENTIAL_USED_UP', 'CREDENTIAL_VALID',
  // Private space constraints
  'NOT_TEAM_MEMBER', 'PRIVATE_SPACE_REQUIRED',
  // Quota update constraints
  'NOT_QUOTA_OWNER', 'QUOTA_RESERVED',
  // Generic
  'LIFECYCLE_VIOLATION', 'OPERATION_NOT_ALLOWED'
])

/**
 * Check if error is a lifecycle violation
 * @param {object} error - Error object from API
 * @returns {boolean}
 */
export function isLifecycleViolation(error) {
  return error?.code && LIFECYCLE_CODES.has(error.code)
}

/**
 * Convert API error to violation format
 * @param {object} error - Error from API response
 * @returns {object} Violation object
 */
function toViolation(error) {
  return {
    code: error.code,
    message: error.message,
    details: error.details || {},
    guidance: error.guidance || null,
    // Ensure guidance has required fields
    error: {
      title: getDefaultTitle(error.code),
      icon: '⚠️'
    }
  }
}

/**
 * Get default title for error code
 */
function getDefaultTitle(code) {
  const titles = {
    'STORAGE_POOL_IN_USE': '无法删除存储池',
    'POOL_TEAMS_MIGRATING': '存储池正在迁移',
    'NOT_SPACE_MEMBER': '无法上传文件',
    'QUOTA_SUFFICIENT': '配额不足',
    'QUOTA_EXCEEDED': '配额不足',
    'QUOTA_RESERVED': '配额预占中',
    'NO_AVAILABLE_POOL': '无法创建团队',
    'NOT_SPACE_OWNER': '权限不足',
    'NOT_TEAM_OWNER': '无法删除团队',
    'CREDENTIAL_VALID': '邀请码无效',
    'SPACE_NO_MEMBERS': '无法删除空间',
    'SPACE_HAS_PENDING_REQUESTS': '有待处理申请',
    'SPACE_HAS_MEMBERS': '空间仍有成员',
    'NOT_TEAM_MEMBER': '无法申请私人空间',
    'NOT_QUOTA_OWNER': '无法修改配额',
    'MEMBER_RECENTLY_REMOVED': '成员刚被移除',
    'LIFECYCLE_VIOLATION': '操作受限'
  }
  return titles[code] || '操作受限'
}

/**
 * Handle API response, check for lifecycle violations
 * @param {Response} response - Fetch response
 * @returns {Promise<object|null>} Parsed data or null if violation
 */
export async function handleApiResponse(response) {
  if (!response.ok) {
    const contentType = response.headers.get('content-type')
    if (contentType?.includes('application/json')) {
      const error = await response.json()
      if (isLifecycleViolation(error)) {
        const violation = toViolation(error)
        // Delegate to store for modal display
        const store = useLifecycleStore()
        store.showGuidance(violation)
        return null
      }
    }
    throw new Error(`API error: ${response.status}`)
  }
  return response.json()
}

/**
 * Wrap fetch with lifecycle handling
 * @param {Function} fetchFn - Custom fetch function
 * @returns {Function} Wrapped function
 */
export function withLifecycleHandling(fetchFn) {
  return async (...args) => {
    try {
      const response = await fetchFn(...args)
      return await handleApiResponse(response)
    } catch (error) {
      // Handle thrown violations (e.g., from withLifecycleHandling itself)
      if (error.code && isLifecycleViolation(error)) {
        const violation = toViolation(error)
        const store = useLifecycleStore()
        store.showGuidance(violation)
        return null
      }
      throw error
    }
  }
}

/**
 * Lifecycle-aware API call helpers
 * Use these instead of raw fetch for lifecycle-constrained operations
 */
export const lifecycleApi = {
  async deletePool(poolId) {
    const resp = await fetch(`/api/v1/admin/pools/${poolId}`, { method: 'DELETE' })
    return handleApiResponse(resp)
  },

  async uploadFile(spaceId, formData) {
    const resp = await fetch(`/api/v1/spaces/${spaceId}/files`, {
      method: 'POST',
      body: formData
    })
    return handleApiResponse(resp)
  },

  async createTeam(name, poolId) {
    const resp = await fetch('/api/v1/teams', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, storage_pool_id: poolId })
    })
    return handleApiResponse(resp)
  },

  async inviteMember(teamId, email) {
    const resp = await fetch(`/api/v1/teams/${teamId}/members`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    })
    return handleApiResponse(resp)
  },

  async deleteTeam(teamId) {
    const resp = await fetch(`/api/v1/teams/${teamId}`, { method: 'DELETE' })
    return handleApiResponse(resp)
  },

  async deleteSpace(spaceId) {
    const resp = await fetch(`/api/v1/spaces/${spaceId}`, { method: 'DELETE' })
    return handleApiResponse(resp)
  },

  async joinTeam(credential) {
    const resp = await fetch('/api/v1/teams/join', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential })
    })
    return handleApiResponse(resp)
  },

  async updateQuota(spaceId, maxBytes) {
    const resp = await fetch(`/api/v1/spaces/${spaceId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_bytes: maxBytes })
    })
    return handleApiResponse(resp)
  },

  async createPrivateSpace(spaceId, name, requestedBytes) {
    const resp = await fetch(`/api/v1/spaces/${spaceId}/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requested_name: name, requested_bytes: requestedBytes })
    })
    return handleApiResponse(resp)
  }
}

// Export for direct usage
export { handleApiResponse as default }
