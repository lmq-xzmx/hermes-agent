<script setup>
// ============================================
// App.vue - Root Component
// ============================================
// Design System: Apple Design System (DESIGN.md)
// Layout: Flexbox sidebar + main content
// BEM Naming: .app__element
// ============================================

import { computed, onMounted, watch, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/authStore'
import { useGuidanceStore } from './stores/guidanceStore'
import { useGuidanceTrigger } from './services/guidanceTrigger'
import { useToast } from './composables/useToast'
import Sidebar from './views/Sidebar.vue'
import GuidanceModal from './components/common/GuidanceModal.vue'
import ThemePanel from './components/common/ThemePanel.vue'
import Toast from './components/common/Toast.vue'

const router = useRouter()
const authStore = useAuthStore()
const guidanceStore = useGuidanceStore()
const { toastVisible, toastConfig, hideToast } = useToast()

// Theme panel visibility
const showThemePanel = ref(false)

// ============================================
// Lifecycle
// ============================================
onMounted(() => {
  const trigger = useGuidanceTrigger()
  trigger.init()
})

onMounted(async () => {
  await authStore.checkAuth()
  if (!authStore.isAuthenticated) {
    router.push('/login')
  }
})

// ============================================
// State
// ============================================
const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentView = computed(() => authStore.currentView)

// ============================================
// Handlers
// ============================================
const handleNavigate = (view) => {
  authStore.setView(view)
  router.push(`/${view === 'files' ? '' : view}`)
}

const onLogout = () => {
  authStore.logout()
  router.push('/login')
}

const onOpenTheme = () => {
  showThemePanel.value = true
}

const route = useRoute()
const username = computed(() => authStore.user?.username || '-')

const sidebarCurrentView = computed(() => {
  const name = route.name?.toLowerCase() || ''
  const viewMap = {
    'files': 'files',
    'teams': 'teams',
    'spaces': 'spaces',
    'pools': 'pools',
    'knowledge': 'knowledge',
    'trash': 'trash'
  }
  return viewMap[name] || 'files'
})

watch(isAuthenticated, (isAuth) => {
  if (!isAuth) {
    router.push('/login')
  }
})
</script>

<template>
  <div class="app">
    <!-- Authenticated Layout -->
    <template v-if="isAuthenticated">
      <Sidebar
        class="app__sidebar"
        :activeView="sidebarCurrentView"
        :username="username"
        @navigate="handleNavigate"
        @logout="onLogout"
        @open-theme="onOpenTheme"
      />
      <main class="app__main">
        <router-view />
      </main>
    </template>

    <!-- Login Layout -->
    <template v-else>
      <router-view />
    </template>

    <!-- Global Guidance Modal -->
    <GuidanceModal
      v-model="guidanceStore.modalVisible"
      v-bind="guidanceStore.modalConfig"
      @action="guidanceStore.executeAction"
      @close="guidanceStore.dismiss(guidanceStore.currentEventName)"
    />

    <!-- Theme Panel Modal -->
    <ThemePanel v-model="showThemePanel" />

    <!-- Global Toast -->
    <Toast
      :visible="toastVisible"
      :type="toastConfig.type"
      :message="toastConfig.message"
      :closable="toastConfig.closable"
      :duration="toastConfig.duration"
      @close="hideToast"
      @update:visible="hideToast"
    />
  </div>
</template>

<style scoped>
/* ============================================
   App Root - .app
   Design System: Apple Design System (DESIGN.md)
   Layout: Flex row (sidebar + main content)
   Background: surface-black (global-nav style)
   ============================================ */
.app {
  /* Flex layout - horizontal row */
  display: flex;
  flex-direction: row;
  height: 100vh;
  width: 100%;

  /* Colors - global-nav on dark */
  background: var(--color-surface-black);
  color: var(--color-body-on-dark);
}

/* ============================================
   Main Content - .app__main
   Design: Apple canvas-parchment background
   ============================================ */
.app__main {
  /* Flex grow to fill remaining space */
  flex: 1;
  min-width: 0;

  /* Box model */
  height: 100vh;

  /* Scroll behavior */
  overflow: auto;
  overflow-x: hidden;

  /* Background - Apple parchment canvas per DESIGN.md */
  background: var(--color-canvas-parchment);
}

/* Ensure router-view content fills full width and inherits background */
.app__main :deep(> *) {
  width: 100%;
  min-height: 100vh;
  flex: 1;
}

/* Also ensure router-view itself fills width */
.app__main :deep(.router-view) {
  width: 100%;
  display: flex;
  flex-direction: column;
}
</style>

