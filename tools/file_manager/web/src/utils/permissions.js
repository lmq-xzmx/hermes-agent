/**
 * Permission Utilities - RBAC 前端权限控制
 *
 * 基于角色优先级的权限检查工具
 * 对应后端 Role.priority 体系
 */

// 角色优先级映射
export const ROLE_PRIORITY = {
  'admin': 100,
  'editor': 50,
  'viewer': 10,
  'guest': 1,
  'member': 50, // editor 别名，兼容旧代码
}

/**
 * 检查用户是否有足够权限
 * @param {string} userRole - 用户角色名
 * @param {string|number} requiredRole - 所需角色名或优先级阈值
 * @returns {boolean}
 */
export function hasPermission(userRole, requiredRole) {
  const userPriority = ROLE_PRIORITY[userRole] || 0

  if (typeof requiredRole === 'string') {
    return userPriority >= (ROLE_PRIORITY[requiredRole] || 0)
  }

  return userPriority >= requiredRole
}

/**
 * 检查是否为管理员
 */
export function isAdmin(userRole) {
  return hasPermission(userRole, 'admin')
}

/**
 * 检查是否为编辑者或更高
 */
export function isEditor(userRole) {
  return hasPermission(userRole, 'editor')
}

/**
 * 检查是否为查看者或更高
 */
export function isViewer(userRole) {
  return hasPermission(userRole, 'viewer')
}

/**
 * 获取角色显示名称
 */
export function getRoleLabel(role) {
  const labels = {
    'admin': '管理员',
    'editor': '编辑者',
    'viewer': '查看者',
    'guest': '访客',
    'member': '成员'
  }
  return labels[role] || role
}

/**
 * 知识库功能权限矩阵
 */
export const KNOWLEDGE_PERMISSIONS = {
  checkStatus: ['admin', 'editor', 'viewer', 'guest'],
  syncSettings: ['admin', 'editor'],
  syncFile: ['admin', 'editor'],
  search: ['admin', 'editor', 'viewer', 'guest']
}

/**
 * 检查知识库功能权限
 */
export function canAccessKnowledgeFeature(feature, userRole) {
  const allowed = KNOWLEDGE_PERMISSIONS[feature]
  return allowed ? allowed.includes(userRole) : false
}

/**
 * 存储池功能权限矩阵
 */
export const POOL_PERMISSIONS = {
  view: ['admin', 'editor', 'viewer'],
  create: ['admin'],
  update: ['admin'],
  delete: ['admin'],
  cleanup: ['admin']
}

/**
 * 检查存储池功能权限
 */
export function canAccessPoolFeature(feature, userRole) {
  const allowed = POOL_PERMISSIONS[feature]
  return allowed ? allowed.includes(userRole) : false
}
