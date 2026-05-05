<template>
  <LifecycleProvider>
  <div class="role-config">
    <header class="config-header">
      <h1>角色权限配置</h1>
      <div class="header-actions">
        <button @click="exportTemplate" class="btn-apple-secondary">📤 导出模板</button>
        <button @click="showImport = true" class="btn-apple-secondary">📥 导入模板</button>
        <button @click="showCreateRole = true" class="btn-apple-primary">+ 创建角色</button>
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
          <button @click="savePermissions" class="btn-apple-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存' }}
          </button>
          <button @click="resetPermissions" class="btn-apple-secondary">重置</button>
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
          <button @click="showCreateRole = false" class="btn-apple-secondary">取消</button>
          <button @click="createRole" class="btn-apple-primary">创建</button>
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
          <button @click="showImport = false" class="btn-apple-secondary">取消</button>
          <button @click="importRoleTemplate" class="btn-apple-primary" :disabled="!importTemplate">导入</button>
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
/* === RoleConfig - 角色权限配置页面 === */

.role-config {
  padding: var(--spacing-lg);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}

.role-config__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-xl);
}

.role-config__title {
  font: var(--text-display-md);
  color: var(--color-ink);
  margin: 0;
}

.role-config__loading {
  text-align: center;
  padding: var(--spacing-xxl);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
}

.role-config__content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xl);
}

.role-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xxs);
  padding: var(--spacing-xs);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.role-tab {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing-sm) var(--spacing-md);
  background: transparent;
  border: none;
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink-muted-48);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.role-tab:hover {
  background: var(--color-canvas-parchment);
}

.role-tab--active {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.role-tab__count {
  font: var(--text-caption);
  opacity: 0.8;
}

.permission-matrix {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.permission-matrix__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.matrix-table {
  width: 100%;
  border-collapse: collapse;
}

.matrix-table th,
.matrix-table td {
  padding: var(--spacing-md);
  text-align: center;
  border-bottom: 1px solid var(--color-divider-soft);
}

.matrix-table th {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.matrix-table td {
  font: var(--text-body);
  color: var(--color-ink);
}

.matrix-table__resource-name {
  text-align: left;
  font: var(--text-body-strong);
}

.matrix-table__checkbox {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.matrix-actions {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

.user-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
  padding: var(--spacing-lg);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-lg);
}

.user-stats__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-md);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xxs);
  padding: var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.stat-item__value {
  font: var(--text-display-sm);
  color: var(--color-ink);
}

.stat-item__label {
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}

.user-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.user-list__title {
  font: var(--text-caption-strong);
  color: var(--color-ink-muted-48);
  margin: 0;
}

.user-chips {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xxs);
}

.user-chip {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
  color: var(--color-ink);
}

.more-users {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-primary-subtle);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
  color: var(--color-primary);
}

.btn-apple-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.btn-apple-primary:active {
  transform: scale(0.95);
}

.btn-apple-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-apple-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, background 0.15s ease;
}

.btn-apple-secondary:active {
  transform: scale(0.95);
}

.btn-apple-danger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-danger);
  color: var(--color-on-primary);
  border: none;
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
  font: var(--text-body);
  cursor: pointer;
  transition: transform 0.1s ease, opacity 0.15s ease;
}

.btn-apple-danger:active {
  transform: scale(0.95);
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
  z-index: var(--z-modal-backdrop);
}

.modal {
  background: var(--color-canvas);
  border-radius: var(--radius-lg);
  width: 90%;
  max-width: 500px;
  max-height: 80vh;
  overflow: auto;
}

.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--color-divider-soft);
}

.modal__title {
  font: var(--text-body-strong);
  margin: 0;
}

.modal__close {
  background: none;
  border: none;
  font-size: 24px;
  color: var(--color-ink-muted-48);
  cursor: pointer;
}

.modal__body {
  padding: var(--spacing-lg);
}

.modal__footer {
  display: flex;
  gap: var(--spacing-sm);
  justify-content: flex-end;
  padding: var(--spacing-lg);
  border-top: 1px solid var(--color-divider-soft);
}

.form-group {
  margin-bottom: var(--spacing-md);
}

.form-group__label {
  display: block;
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
  margin-bottom: var(--spacing-xxs);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-pill);
  font: var(--text-body);
  color: var(--color-ink);
  box-sizing: border-box;
}

.form-input:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.form-textarea {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-md);
  font: var(--text-body);
  color: var(--color-ink);
  resize: vertical;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 2px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font: var(--text-body);
  color: var(--color-ink);
  cursor: pointer;
}

.template-preview {
  margin-top: var(--spacing-md);
  padding: var(--spacing-md);
  background: var(--color-canvas-parchment);
  border-radius: var(--radius-md);
}

.template-preview__title {
  font: var(--text-body-strong);
  color: var(--color-ink);
  margin: 0 0 var(--spacing-sm) 0;
}

.permissions-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-xxs);
}

.perm-tag {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: var(--color-canvas);
  border-radius: var(--radius-pill);
  font: var(--text-caption);
  color: var(--color-ink-muted-48);
}
</style>

