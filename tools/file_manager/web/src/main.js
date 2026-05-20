// ============================================================================
// Vue Application Entry Point
// ============================================================================

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'

// Platform Adapter - 必须在 Vue app 创建之前加载
import './tauri-adapter.js'

// Apple Design System Tokens
import './assets/tokens.css'

// Create Vue app
const app = createApp(App)

// Use Pinia for state management
const pinia = createPinia()
app.use(pinia)

// Use Vue Router
app.use(router)

// Apply saved theme tokens (after Pinia is ready)
// We need to wait for pinia to be installed before accessing stores
import { useThemeStore } from './stores/themeStore'
const themeStore = useThemeStore()
themeStore.applyAllTokens()

// Mount the app
app.mount('#app')
