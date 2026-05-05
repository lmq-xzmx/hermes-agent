// ============================================================================
// Auth Store - Pinia Store for Authentication
// ============================================================================

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const TOKEN_KEY = 'hfm_token'
const USER_KEY = 'hfm_user'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref(localStorage.getItem(TOKEN_KEY) || null)
  const user = ref(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const loading = ref(false)
  const error = ref(null)
  const currentView = ref('files') // 'files' | 'teams' | 'spaces' | 'pools' | 'knowledge' | 'trash'

  // Getters
  const isAuthenticated = computed(() => !!token.value)
  const username = computed(() => user.value?.username || '-')
  const userRole = computed(() => user.value?.role || 'member')

  // Actions
  async function login(username, password) {
    loading.value = true
    error.value = null
    try {
      const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      })
      const data = await res.json()
      if (data.access_token) {
        token.value = data.access_token
        localStorage.setItem(TOKEN_KEY, data.access_token)
        // Fetch user info
        await fetchCurrentUser()
        return data
      }
      throw new Error(data.detail || 'Login failed')
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function register(username, password, email) {
    loading.value = true
    error.value = null
    try {
      const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password, email })
      })
      const data = await res.json()
      if (data.access_token) {
        token.value = data.access_token
        localStorage.setItem(TOKEN_KEY, data.access_token)
        await fetchCurrentUser()
        return data
      }
      throw new Error(data.detail || 'Registration failed')
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) return null
    try {
      const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token.value}` }
      })
      if (!res.ok) throw new Error('Auth check failed')
      const userData = await res.json()
      user.value = userData
      localStorage.setItem(USER_KEY, JSON.stringify(userData))
      return userData
    } catch (e) {
      // Token invalid, clear auth
      logout()
      throw e
    }
  }

  // Alias for fetchCurrentUser
  async function checkAuth() {
    return fetchCurrentUser()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    // Dispatch event for cleanup
    window.dispatchEvent(new CustomEvent('auth:logout'))
  }

  function setToken(newToken) {
    token.value = newToken
    if (newToken) {
      localStorage.setItem(TOKEN_KEY, newToken)
    } else {
      localStorage.removeItem(TOKEN_KEY)
    }
  }

  function setView(view) {
    currentView.value = view
  }

  return {
    // State
    token,
    user,
    loading,
    error,
    currentView,
    // Getters
    isAuthenticated,
    username,
    userRole,
    // Actions
    login,
    register,
    fetchCurrentUser,
    checkAuth,
    logout,
    setToken,
    setView
  }
})

export default useAuthStore