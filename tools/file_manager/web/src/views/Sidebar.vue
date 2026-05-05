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
/* Apple Global Navigation Bar - Strict DESIGN.md Compliance */
.global-nav {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  background: var(--color-surface-black);
  color: var(--color-on-dark);
  display: flex;
  flex-direction: column;
  height: 100vh; /* Sidebar 全屏高度 */
  font: var(--text-nav-link);
}

/* Brand - Apple global-nav height 44px */
.nav-brand {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xs);
  padding: 0 var(--spacing-md);
  border-bottom: 1px solid var(--color-border-on-dark);
  flex-shrink: 0;
}

.brand-icon {
  font-size: 16px;
}

.brand-text {
  font: var(--text-nav-link);
  color: var(--color-body-on-dark);
}

/* Navigation Items - 44px touch target per DESIGN.md */
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
  justify-content: center;
  gap: var(--spacing-xs);
  padding: 0 var(--spacing-md);
  height: 44px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-body-muted);
  font: var(--text-nav-link);
  text-align: center;
  transition: background-color 0.15s ease, color 0.15s ease;
  margin: 2px var(--spacing-xs);
}

.nav-item:hover {
  background: var(--color-border-on-dark-soft);
  color: var(--color-body-on-dark);
}

.nav-item.active {
  background: var(--color-primary-focus);
  color: var(--color-primary-on-dark);
}

.nav-icon {
  font-size: 18px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.nav-label {
  font: inherit;
}

/* Footer - Apple nav-link style */
.nav-footer {
  padding: var(--spacing-sm);
  border-top: 1px solid var(--color-border-on-dark);
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-xxs);
}

.user-avatar {
  font-size: 14px;
  flex-shrink: 0;
}

.user-name {
  font: var(--text-nav-link);
  color: var(--color-body-muted);
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-logout {
  padding: var(--spacing-xxs) var(--spacing-sm);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-body-muted);
  font: var(--text-nav-link);
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
  text-align: center;
  margin-left: var(--spacing-xs);
}

.btn-logout:hover {
  background: var(--color-border-on-dark-soft);
  color: var(--color-body-on-dark);
}
</style>