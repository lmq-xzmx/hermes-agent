<template>
  <nav class="global-nav">
    <!-- Brand -->
    <div class="nav-brand">
      <span class="brand-icon">🚀</span>
      <span class="brand-text">Hermes</span>
    </div>

    <!-- Navigation Items - Apple global-nav style -->
    <div class="nav-items">
      <button
        v-for="item in navItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: activeView === item.id }"
        @click="onNavigate(item.id)"
      >
        <span class="nav-icon">{{ item.icon }}</span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </div>

    <!-- Footer: User & Logout -->
    <div class="nav-footer">
      <div class="user-section">
        <span class="user-avatar">👤</span>
        <span class="user-name">{{ username }}</span>
      </div>
      <button class="btn-logout" @click="onLogout">退出</button>
    </div>
  </nav>
</template>

<script setup>
defineProps({
  activeView: { type: String, default: 'files' },
  username: { type: String, default: '-' }
})

const emit = defineEmits(['navigate', 'logout'])

const navItems = [
  { id: 'files', icon: '📁', label: '文件' },
  { id: 'teams', icon: '👥', label: '团队' },
  { id: 'spaces', icon: '🚀', label: '空间' },
  { id: 'pools', icon: '💾', label: '存储池' },
  { id: 'knowledge', icon: '🧠', label: '知识' },
  { id: 'trash', icon: '🗑️', label: '回收站' }
]

function onNavigate(view) {
  emit('navigate', view)
}

function onLogout() {
  emit('logout')
}
</script>

<style scoped>
/* Apple Global Navigation Bar */
.global-nav {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--color-surface-black);
  display: flex;
  flex-direction: column;
  height: 100vh;
}

/* Brand - 44px Apple nav bar height */
.nav-brand {
  height: 44px;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-icon {
  font-size: 16px;
}

.brand-text {
  font-family: var(--font-family-display);
  font-size: 14px;
  font-weight: 600;
  color: var(--color-body-on-dark);
  letter-spacing: -0.12px;
}

/* Navigation Items */
.nav-items {
  flex: 1;
  padding: var(--spacing-xs) 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: 0 var(--spacing-md);
  height: 28px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-body-muted);
  font-family: var(--font-family-text);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.0;
  letter-spacing: -0.12px;
  text-align: left;
  width: 100%;
  transition: background-color 0.15s ease, color 0.15s ease;
  margin: var(--spacing-2xs) var(--spacing-sm);
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-body-on-dark);
}

.nav-item.active {
  background: rgba(0, 102, 204, 0.25);
  color: var(--color-primary-on-dark);
}

.nav-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.nav-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Footer */
.nav-footer {
  padding: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.user-section {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-sm);
}

.user-avatar {
  font-size: 14px;
  flex-shrink: 0;
}

.user-name {
  font-family: var(--font-family-text);
  font-size: 12px;
  font-weight: 400;
  letter-spacing: -0.12px;
  color: var(--color-body-muted);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-logout {
  width: 100%;
  padding: var(--spacing-2xs) var(--spacing-sm);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-body-muted);
  font-family: var(--font-family-text);
  font-size: 12px;
  font-weight: 400;
  line-height: 1.0;
  letter-spacing: -0.12px;
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  text-align: center;
}

.btn-logout:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--color-body-on-dark);
}
</style>