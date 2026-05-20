/**
 * Approval API Service
 *
 * API endpoints for approval workflow:
 * - POST /api/v1/approvals - Create approval request
 * - GET /api/v1/approvals/my - Get my requests
 * - GET /api/v1/approvals/pending - Get pending requests (admin)
 * - GET /api/v1/approvals/{id} - Get request details
 * - POST /api/v1/approvals/{id}/decide - Process decision
 * - DELETE /api/v1/approvals/{id} - Cancel request
 */

const API_BASE = '/api/v1/approvals'

/**
 * Get auth headers
 */
function getAuthHeaders() {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
}

/**
 * Create a new approval request
 * @param {Object} params
 * @param {string} params.type - Approval type (join_team, private_space, quota_extend, team_create, storage_pool)
 * @param {string} [params.targetId] - Target resource ID
 * @param {string} [params.reason] - Reason for request
 * @param {Object} [params.params] - Additional parameters
 */
export async function createApproval({ type, targetId, reason, params }) {
  const resp = await fetch(`${API_BASE}`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({
      type,
      target_id: targetId,
      reason,
      params
    })
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Get my approval requests
 * @param {string} [status] - Filter by status (pending, approved, rejected, cancelled)
 */
export async function getMyApprovals(status) {
  const url = status ? `${API_BASE}/my?status=${status}` : `${API_BASE}/my`
  const resp = await fetch(url, {
    headers: getAuthHeaders()
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Get pending approvals (admin only)
 */
export async function getPendingApprovals() {
  const resp = await fetch(`${API_BASE}/pending`, {
    headers: getAuthHeaders()
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Get approval request details
 * @param {string} requestId
 */
export async function getApproval(requestId) {
  const resp = await fetch(`${API_BASE}/${requestId}`, {
    headers: getAuthHeaders()
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Process approval decision
 * @param {string} requestId
 * @param {string} decision - 'approved' or 'rejected'
 * @param {string} [comment] - Approval comment
 */
export async function processApproval(requestId, decision, comment) {
  const resp = await fetch(`${API_BASE}/${requestId}/decide`, {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify({ decision, comment })
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Cancel an approval request (by applicant)
 * @param {string} requestId
 */
export async function cancelApproval(requestId) {
  const resp = await fetch(`${API_BASE}/${requestId}`, {
    method: 'DELETE',
    headers: getAuthHeaders()
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `API error: ${resp.status}`)
  }
  return resp.json()
}

/**
 * Approval type labels
 */
export const APPROVAL_TYPES = {
  join_team: '加入团队',
  private_space: '创建私人空间',
  quota_extend: '扩展配额',
  team_create: '创建团队',
  storage_pool: '申请存储池'
}

/**
 * Status labels
 */
export const STATUS_LABELS = {
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
  cancelled: '已取消'
}

/**
 * Status colors - Apple System Colors
 * Note: These are used in JS context; in Vue templates, prefer CSS variables
 */
export const STATUS_COLORS = {
  pending: '#ff9500',   // Apple warning orange
  approved: '#34c759',  // Apple success green
  rejected: '#ff3b30',  // Apple danger red
  cancelled: '#8e8e93'   // Apple secondary gray
}
