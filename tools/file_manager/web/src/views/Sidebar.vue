<template>
  <nav class="sidebar">
    <!-- Brand -->
    <div class="sidebar__brand">
      <Icon name="rocket" :size="16" class="sidebar__brand-icon" />
      <span class="sidebar__brand-text">Hermes</span>
    </div>

    <!-- Navigation Items -->
    <div class="sidebar__nav">
      <button
        v-for="item in navItems"
        :key="item.id"
        class="sidebar__nav-item"
        :class="{ 'is-active': activeView === item.id }"
        @click="onNavigate(item.id)"
      >
        <Icon :name="item.icon" :size="18" class="sidebar__nav-icon" />
        <span class="sidebar__nav-label">{{ item.label }}</span>
      </button>
    </div>

    <!-- Footer -->
    <div class="sidebar__footer">
      <button class="sidebar__theme-btn" @click="onOpenTheme" title="配色调整">
        <Icon name="palette" :size="14" />
      </button>
      <div class="sidebar__user">
        <Icon name="users" :size="12" class="sidebar__user-avatar" />
        <span class="sidebar__user-name">{{ username }}</span>
      </div>
      <button class="sidebar__logout" @click="onLogout">
        <Icon name="log-out" :size="12" />
      </button>
    </div>
  </nav>
</template>

<script setup>
import { Icon } from '@/components/common'
import { useAuthStore } from '@/stores/authStore'

defineProps({
  activeView: { type: String, default: 'files' },
  username: { type: String, default: '-' }
})

const emit = defineEmits(['navigate', 'logout', 'open-theme'])
const authStore = useAuthStore()

// 路由权限配置：role 需要 >= requiredPriority
const ROLE_PRIORITY = {
  'admin': 100,
  'editor': 50,
  'member': 50,
  'viewer': 10,
  'guest': 1
}

// 导航项权限配置
const navItemsDef = [
  { id: 'files', icon: 'file', label: '文件', requiredPriority: 0 },
  { id: 'teams', icon: 'users', label: '团队', requiredPriority: 0 },
  { id: 'spaces', icon: 'rocket', label: '空间', requiredPriority: 0 },
  { id: 'pools', icon: 'database', label: '存储池', requiredPriority: 100 },
  { id: 'knowledge', icon: 'brain', label: '知识', requiredPriority: 0 },
  { id: 'trash', icon: 'trash', label: '回收站', requiredPriority: 0 }
]

// 根据用户权限过滤导航项
const navItems = navItemsDef.filter(item => {
  const userPriority = ROLE_PRIORITY[authStore.userRole] || 0
  return userPriority >= item.requiredPriority
})

function onNavigate(view) {
  emit('navigate', view)
}

function onLogout() {
  emit('logout')
}

function onOpenTheme() {
  emit('open-theme')
}
</script>

<style scoped>
/* ============================================
   Block: sidebar
   Apple Global Navigation - DESIGN.md Compliant
   ============================================ */

.sidebar {
  /* Layout */
  display: flex;
  flex-direction: column;
  width: var(--sidebar-width, 180px);
  min-width: var(--sidebar-width, 180px);
  height: 100vh;

  /* Visual */
  background: var(--color-surface-black);

  /* Typography */
  font-family: var(--font-family-text);
  color: var(--color-body-on-dark);
}

/* ============================================
   Element: sidebar__brand
   ============================================ */
.sidebar__brand {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);

  /* Box Model */
  height: 44px;
  padding: 0 var(--spacing-lg);

  /* Border */
  border-bottom: 1px solid var(--color-border-on-dark);

  /* Layout */
  flex-shrink: 0;
}

.sidebar__brand-icon {
  /* Layout */
  flex-shrink: 0;

  /* Color */
  color: var(--color-body-on-dark);
}

.sidebar__brand-text {
  /* Typography - nav-link: 12px/400/-0.12px */
  font-size: 12px;
  font-weight: 400;
  letter-spacing: -0.12px;
  color: var(--color-body-on-dark);
}

/* ============================================
   Element: sidebar__nav
   ============================================ */
.sidebar__nav {
  /* Layout */
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--spacing-xs) 0;
  overflow-y: auto;
}

/* ============================================
   Element: sidebar__nav-item
   ============================================ */
.sidebar__nav-item {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);

  /* Box Model */
  height: 36px;
  margin: 1px var(--spacing-xs);
  padding: 0 var(--spacing-sm);

  /* Visual */
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);

  /* Typography */
  font-size: 12px;
  font-weight: 400;
  letter-spacing: -0.12px;
  color: var(--color-body-muted);

  /* Text */
  text-align: left;

  /* Interaction */
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.sidebar__nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: var(--color-body-on-dark);
}

.sidebar__nav-item.is-active {
  background: var(--color-primary-on-dark);
  color: var(--color-body-on-dark);
}

.sidebar__nav-item.is-active:hover {
  background: var(--color-primary-on-dark);
}

.sidebar__nav-icon {
  /* Layout */
  flex-shrink: 0;
}

.sidebar__nav-label {
  /* Typography */
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  line-height: 1;
}

/* ============================================
   Element: sidebar__footer
   ============================================ */
.sidebar__footer {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);

  /* Box Model */
  height: 44px;
  padding: 0 var(--spacing-xs);

  /* Border */
  border-top: 1px solid var(--color-border-on-dark);

  /* Layout */
  flex-shrink: 0;
}

/* ============================================
   Element: sidebar__theme-btn
   ============================================ */
.sidebar__theme-btn {
  /* Layout */
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  /* Box Model */
  width: 28px;
  height: 28px;
  padding: 0;

  /* Visual */
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);

  /* Interaction */
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.sidebar__theme-btn:hover {
  background: rgba(255, 255, 255, 0.06);
}

.sidebar__theme-btn:focus-visible {
  outline: 2px solid var(--color-primary-focus);
  outline-offset: 1px;
}

/* ============================================
   Element: sidebar__user
   ============================================ */
.sidebar__user {
  /* Layout */
  display: flex;
  align-items: center;
  gap: var(--spacing-xxs);

  /* Layout */
  flex: 1;
  min-width: 0;
}

.sidebar__user-avatar {
  /* Layout */
  flex-shrink: 0;
}

.sidebar__user-name {
  /* Typography */
  font-size: 11px;
  font-weight: 400;
  letter-spacing: -0.08px;
  color: var(--color-body-muted);

  /* Layout */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* ============================================
   Element: sidebar__logout
   ============================================ */
.sidebar__logout {
  /* Layout */
  flex-shrink: 0;

  /* Box Model */
  padding: var(--spacing-xxs) var(--spacing-xs);

  /* Visual */
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);

  /* Typography */
  font-size: 11px;
  font-weight: 400;
  letter-spacing: -0.08px;
  color: var(--color-body-muted);

  /* Interaction */
  cursor: pointer;
  transition: background-color 0.15s ease, color 0.15s ease;
}
</style>