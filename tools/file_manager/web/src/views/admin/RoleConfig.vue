<template>
  <LifecycleProvider>
  <div class="role-config">
    <header class="config-header">
      <h1>角色权限配置</h1>
      <div class="header-actions">
        <button @click="exportTemplate" class="btn btn-secondary">📤 导出模板</button>
        <button @click="showImport = true" class="btn btn-secondary">📥 导入模板</button>
        <button @click="showCreateRole = true" class="btn btn-primary">+ 创建角色</button>
      </div>
    </header>

    <div v-if="loading" class="loading">加载中...</div>

    <div v-else class="config-content">
      <!-- 角色选择标签 -->
      <div class="role-tabs">
        <button
          v-for="role in roles"
          :key="role.id"
          :class="['role-tab', { active: selectedRole?.id === role.id }]"
          @click="selectRole(role)"
        >
          {{ role.name }}
          <span class="user-count">({{ role.user_count }})</span>
        </button>
      </div>

      <!-- 权限矩阵配置 -->
      <div v-if="selectedRole" class="permission-matrix">
        <h2>{{ selectedRole.name }} 权限</h2>

        <table class="matrix-table">
          <thead>
            <tr>
              <th>资源</th>
              <th>创建</th>
              <th>读取</th>
              <th>更新</th>
              <th>删除</th>
              <th>管理</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="resource in resources" :key="resource.id">
              <td class="resource-name">{{ resource.name }}</td>
              <td v-for="action in ['create', 'read', 'update', 'delete', 'manage']" :key="action">
                <label class="checkbox-cell">
                  <input
                    type="checkbox"
                    :checked="hasPermission(resource.id, action)"
                    @change="togglePermission(resource.id, action)"
                    :disabled="selectedRole.is_system && resource.id === 'roles'"
                  />
                </label>
              </td>
            </tr>
          </tbody>
        </table>

        <div class="matrix-actions">
          <button @click="savePermissions" class="btn btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button @click="resetPermissions" class="btn btn-secondary">重置</button>
        </div>
      </div>

      <!-- 用户分配统计 -->
      <div v-if="selectedRole" class="user-stats">
        <h3>用户分配统计</h3>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ selectedRole.user_count }}</div>
            <div class="stat-label">已分配用户</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ totalUsers }}</div>
            <div class="stat-label">总用户数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">{{ ((selectedRole.user_count / totalUsers) * 100).toFixed(1) }}%</div>
            <div class="stat-label">占比</div>
          </div>
        </div>

        <div class="user-list">
          <h4>最近分配的用户</h4>
          <div class="user-chips">
            <span v-for="user in recentUsers" :key="user.id" class="user-chip">
              {{ user.username }}
            </span>
            <span v-if="selectedRole.user_count > 5" class="more-users">
              +{{ selectedRole.user_count - 5 }} 更多
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建角色弹窗 -->
    <div v-if="showCreateRole" class="modal-overlay" @click.self="showCreateRole = false">
      <div class="modal">
        <div class="modal-header">
          <h3>创建角色</h3>
          <button @click="showCreateRole = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>角色名称</label>
            <input v-model="newRole.name" type="text" placeholder="输入角色名称" />
          </div>
          <div class="form-group">
            <label>角色描述</label>
            <textarea v-model="newRole.description" placeholder="输入角色描述" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="newRole.is_system" type="checkbox" />
              <span>系统角色（不可删除）</span>
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateRole = false" class="btn btn-secondary">取消</button>
          <button @click="createRole" class="btn btn-primary">创建</button>
        </div>
      </div>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="showImport" class="modal-overlay" @click.self="showImport = false">
      <div class="modal">
        <div class="modal-header">
          <h3>导入权限模板</h3>
          <button @click="showImport = false" class="btn-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>选择模板文件</label>
            <input type="file" @change="handleFileUpload" accept=".json" />
          </div>
          <div class="template-preview" v-if="importTemplate">
            <h4>预览: {{ importTemplate.name }}</h4>
            <div class="permissions-summary">
              <span v-for="(perms, resource) in importTemplate.permissions" :key="resource" class="perm-tag">
                {{ resource }}: {{ Object.entries(perms).filter(([k, v]) => v).length }} 项权限
              </span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showImport = false" class="btn btn-secondary">取消</button>
          <button @click="importRoleTemplate" class="btn btn-primary" :disabled="!importTemplate">导入</button>
        </div>
      </div>
    </div>
  </LifecycleProvider>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import LifecycleProvider from '@/components/lifecycle/LifecycleProvider.vue'

const loading = ref(true)
const saving = ref(false)
const roles = ref([])
const selectedRole = ref(null)
const showCreateRole = ref(false)
const showImport = ref(false)
const importTemplate = ref(null)
const totalUsers = ref(0)
const recentUsers = ref([])

const newRole = ref({
  name: '',
  description: '',
  is_system: false
})

const resources = ref([
  { id: 'files', name: '文件' },
  { id: 'spaces', name: '空间' },
  { id: 'teams', name: '团队' },
  { id: 'storage', name: '存储' },
  { id: 'roles', name: '角色' },
  { id: 'users', name: '用户' }
])

const permissionMatrix = ref({})

async function loadRoles() {
  roles.value = [
    { id: 'admin', name: 'admin', user_count: 2, is_system: true, permissions: {} },
    { id: 'editor', name: 'editor', user_count: 15, is_system: true, permissions: {} },
    { id: 'viewer', name: 'viewer', user_count: 30, is_system: true, permissions: {} },
    { id: 'guest', name: 'guest', user_count: 5, is_system: true, permissions: {} }
  ]

  // Load permissions for each role
  for (const role of roles.value) {
    permissionMatrix.value[role.id] = {
      files: { create: true, read: true, update: role.id !== 'viewer', delete: role.id === 'admin', manage: role.id === 'admin' },
      spaces: { create: role.id !== 'viewer', read: true, update: role.id !== 'viewer', delete: role.id === 'admin', manage: role.id === 'admin' },
      teams: { create: role.id === 'admin', read: true, update: role.id === 'admin', delete: role.id === 'admin', manage: role.id === 'admin' },
      storage: { create: role.id === 'admin', read: true, update: role.id === 'admin', delete: role.id === 'admin', manage: role.id === 'admin' },
      roles: { create: false, read: true, update: false, delete: false, manage: role.id === 'admin' },
      users: { create: role.id === 'admin', read: true, update: role.id === 'admin', delete: role.id === 'admin', manage: role.id === 'admin' }
    }
  }

  totalUsers.value = roles.value.reduce((sum, r) => sum + r.user_count, 0)
}

function selectRole(role) {
  selectedRole.value = role
  recentUsers.value = [
    { id: '1', username: 'admin' },
    { id: '2', username: 'lmq' },
    { id: '3', username: 'test' },
    { id: '4', username: 'dev' },
    { id: '5', username: 'ops' }
  ].slice(0, Math.min(5, role.user_count))
}

function hasPermission(resourceId, action) {
  if (!selectedRole.value) return false
  return permissionMatrix.value[selectedRole.value.id]?.[resourceId]?.[action] || false
}

function togglePermission(resourceId, action) {
  if (!selectedRole.value) return
  const roleId = selectedRole.value.id
  if (!permissionMatrix.value[roleId]) {
    permissionMatrix.value[roleId] = {}
  }
  if (!permissionMatrix.value[roleId][resourceId]) {
    permissionMatrix.value[roleId][resourceId] = {}
  }
  permissionMatrix.value[roleId][resourceId][action] = !permissionMatrix.value[roleId][resourceId][action]
}

async function savePermissions() {
  saving.value = true
  try {
    // API call to save permissions
    await new Promise(resolve => setTimeout(resolve, 500))
  } finally {
    saving.value = false
  }
}

function resetPermissions() {
  // Reset to original state
}

async function createRole() {
  if (!newRole.value.name) return
  const role = {
    id: newRole.value.name.toLowerCase().replace(/\s+/g, '_'),
    name: newRole.value.name,
    description: newRole.value.description,
    is_system: newRole.value.is_system,
    user_count: 0,
    permissions: {}
  }
  roles.value.push(role)
  permissionMatrix.value[role.id] = {
    files: { create: false, read: true, update: false, delete: false, manage: false },
    spaces: { create: false, read: true, update: false, delete: false, manage: false },
    teams: { create: false, read: true, update: false, delete: false, manage: false },
    storage: { create: false, read: true, update: false, delete: false, manage: false },
    roles: { create: false, read: true, update: false, delete: false, manage: false },
    users: { create: false, read: true, update: false, delete: false, manage: false }
  }
  showCreateRole.value = false
  newRole.value = { name: '', description: '', is_system: false }
}

function exportTemplate() {
  if (!selectedRole.value) return
  const template = {
    name: selectedRole.value.name,
    permissions: permissionMatrix.value[selectedRole.value.id]
  }
  const blob = new Blob([JSON.stringify(template, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${selectedRole.value.name}_permissions.json`
  a.click()
  URL.revokeObjectURL(url)
}

function handleFileUpload(event) {
  const file = event.target.files[0]
  if (!file) return
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      importTemplate.value = JSON.parse(e.target.result)
    } catch (err) {
      alert('无效的模板文件')
    }
  }
  reader.readAsText(file)
}

function importRoleTemplate() {
  if (!importTemplate.value) return
  // Apply template to selected role
  if (selectedRole.value) {
    permissionMatrix.value[selectedRole.value.id] = { ...importTemplate.value.permissions }
  }
  showImport.value = false
  importTemplate.value = null
}

onMounted(async () => {
  await loadRoles()
  if (roles.value.length > 0) {
    selectRole(roles.value[0])
  }
  loading.value = false
})
</script>

<style scoped>
.role-config {
  padding: var(--spacing-lg);
  background: var(--color-surface-tile-1);
  min-height: 100vh;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.config-header h1 {
  font-family: var(--font-display);
  font-size: 28px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0;
  letter-spacing: -0.374px;
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

.config-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.role-tabs {
  display: flex;
  gap: var(--space-xs);
  background: var(--color-surface-tile-2);
  padding: var(--space-xs);
  border-radius: var(--radius-md);
}

.role-tab {
  padding: 10px 20px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-body-muted);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.role-tab:hover {
  background: var(--color-surface-tile-3);
}

.role-tab.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.user-count {
  font-size: 12px;
  opacity: 0.8;
}

.permission-matrix {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.permission-matrix h2 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0 0 var(--spacing-lg) 0;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: var(--space-sm);
  text-align: center;
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.matrix-table th {
  font-size: 12px;
  color: var(--color-body-muted);
  font-weight: 500;
}

.resource-name {
  text-align: left !important;
  font-weight: 500;
  color: var(--color-body-on-dark);
}

.checkbox-cell {
  display: flex;
  justify-content: center;
}

.checkbox-cell input {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.checkbox-cell input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.matrix-actions {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--spacing-lg);
}

.user-stats {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  padding: var(--spacing-lg);
}

.user-stats h3 {
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  margin: 0 0 var(--space-md) 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.stat-item {
  text-align: center;
  padding: var(--spacing-md);
  background: var(--color-surface-tile-3);
  border-radius: var(--radius-md);
}

.stat-value {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.stat-label {
  font-size: 12px;
  color: var(--color-body-muted);
  margin-top: var(--space-xxs);
}

.user-list h4 {
  font-size: 14px;
  color: var(--color-body-muted);
  margin: 0 0 var(--space-sm) 0;
}

.user-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.user-chip {
  background: var(--color-surface-tile-3);
  padding: 6px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  color: var(--color-body-on-dark);
}

.more-users {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--color-body-muted);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--color-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal {
  background: var(--color-surface-tile-2);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-lg);
  width: 500px;
  max-width: 90vw;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  border-bottom: 1px solid var(--color-border-on-dark-soft);
}

.modal-header h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 20px;
  font-weight: 600;
  color: var(--color-body-on-dark);
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--color-body-muted);
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  transition: all 0.2s;
}

.btn-close:hover {
  background: var(--color-surface-tile-1);
}

.btn-close:active {
  transform: scale(0.95);
}

.modal-body {
  padding: var(--space-md);
}

.form-group {
  margin-bottom: var(--space-md);
}

.form-group label {
  display: block;
  font-size: 14px;
  color: var(--color-body-muted);
  margin-bottom: var(--space-xs);
}

.form-group input[type="text"],
.form-group textarea {
  width: 100%;
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-surface-tile-3);
  border: 1px solid var(--color-border-on-dark);
  border-radius: var(--radius-sm);
  color: var(--color-body-on-dark);
  font-family: var(--font-family-text);
  font-size: 17px;
}

.form-group textarea {
  resize: vertical;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  cursor: pointer;
}

.template-preview {
  background: var(--color-surface-tile-3);
  padding: var(--space-sm);
  border-radius: var(--radius-sm);
}

.template-preview h4 {
  margin: 0 0 var(--space-xs) 0;
  font-size: 14px;
  color: var(--color-body-on-dark);
}

.permissions-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-xs);
}

.perm-tag {
  background: var(--color-surface-tile-1);
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  color: var(--color-body-muted);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-top: 1px solid var(--color-border-on-dark-soft);
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--color-body-muted);
}

.btn {
  padding: 11px 22px;
  border-radius: var(--radius-pill);
  cursor: pointer;
  border: none;
  font-family: var(--font-family-text);
  font-size: 17px;
  font-weight: 400;
  line-height: 1.47;
  letter-spacing: -0.374px;
  transition: var(--transition-active);
}

.btn-primary {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.btn-primary:active {
  transform: scale(0.95);
}

.btn-primary:disabled {
  background: var(--color-surface-tile-2);
  color: var(--color-body-muted);
}

.btn-secondary {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
}

.btn-secondary:active {
  transform: scale(0.95);
}
</style>
