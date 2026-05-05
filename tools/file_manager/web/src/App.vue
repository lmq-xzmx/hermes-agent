<script setup>
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/authStore'
import { useGuidanceStore } from './stores/guidanceStore'
import { useGuidanceTrigger } from './services/guidanceTrigger'
import Sidebar from './views/Sidebar.vue'
import GuidanceModal from './components/common/GuidanceModal.vue'

const router = useRouter()
const authStore = useAuthStore()
const guidanceStore = useGuidanceStore()

// 初始化引导触发器
onMounted(() => {
  const trigger = useGuidanceTrigger()
  trigger.init()
})

const isAuthenticated = computed(() => authStore.isAuthenticated)
const currentView = computed(() => authStore.currentView)

// Handle view change from sidebar
const handleNavigate = (view) => {
  authStore.setView(view)
  router.push(`/${view === 'files' ? '' : view}`)
}

// Logout handler
const onLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Derive current view from route name
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

// Initialize auth on mount
onMounted(async () => {
  await authStore.checkAuth()
  if (!authStore.isAuthenticated) {
    router.push('/login')
  }
})

// Watch for auth changes
watch(isAuthenticated, (isAuth) => {
  if (!isAuth) {
    router.push('/login')
  }
})
</script>

<template>
  <div id="app-container" class="app-container">
    <!-- Authenticated Layout -->
    <template v-if="isAuthenticated">
      <Sidebar
        :activeView="sidebarCurrentView"
        :username="username"
        @navigate="handleNavigate"
        @logout="onLogout"
      />
      <main class="main-content">
        <router-view />
      </main>
    </template>

    <!-- Login Layout -->
    <template v-else>
      <router-view />
    </template>

    <!-- 全局引导弹窗 - 放在 v-if 之外以便未登录时也能显示 -->
    <GuidanceModal
      v-model="guidanceStore.modalVisible"
      v-bind="guidanceStore.modalConfig"
      @action="guidanceStore.executeAction"
      @close="guidanceStore.dismiss(guidanceStore.currentEventName)"
    />
  </div>
</template>

<style scoped>
.app-container {
  display: flex;
  height: 100vh;
  background: var(--color-surface-black);
  color: var(--color-body-on-dark);
}

.main-content {
  flex: 1;
  overflow: auto;
  background: var(--color-canvas-parchment);
  max-width: var(--content-max-width-universal);
  margin: 0 auto;
}
</style>
