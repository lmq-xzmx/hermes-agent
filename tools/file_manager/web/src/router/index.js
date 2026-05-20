// ============================================================================
// Vue Router Configuration
// ============================================================================

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

// 视图组件
import LoginView from '../views/LoginView.vue'
import FileView from '../views/FileView.vue'
import TeamView from '../views/TeamView.vue'
import SpaceView from '../views/SpaceView.vue'
import StoragePoolView from '../views/StoragePoolView.vue'
import KnowledgeView from '../views/KnowledgeView.vue'
import TrashView from '../views/TrashView.vue'
import AdminDashboard from '../views/AdminDashboard.vue'

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    name: 'Main',
    redirect: '/files',
    children: [
      {
        path: 'files',
        name: 'Files',
        component: FileView
      },
      {
        path: 'teams',
        name: 'Teams',
        component: TeamView
      },
      {
        path: 'spaces',
        name: 'Spaces',
        component: SpaceView
      },
      {
        path: 'pools',
        name: 'Pools',
        component: StoragePoolView,
        meta: { requiresAuth: true, requiredPriority: 100 }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: KnowledgeView
      },
      {
        path: 'trash',
        name: 'Trash',
        component: TrashView
      },
      {
        path: 'admin',
        name: 'Admin',
        component: AdminDashboard,
        meta: { requiresAuth: true, requiredPriority: 100 }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

// 创建 router 实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 角色优先级映射
const ROLE_PRIORITY = {
  'admin': 100,
  'editor': 50,
  'viewer': 10,
  'guest': 1,
  'member': 50
}

// 导航守卫 - 认证 + 权限检查
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 需要认证但没有 token
  if (to.meta.requiresAuth !== false && !authStore.isAuthenticated) {
    // 尝试从 localStorage 恢复会话
    const token = localStorage.getItem('hfm_token')
    if (token) {
      try {
        await authStore.fetchCurrentUser()
      } catch {
        // 获取用户信息失败，跳转登录
        next({ name: 'Login' })
        return
      }
    } else {
      next({ name: 'Login' })
      return
    }
  }

  // 已登录访问登录页，跳转首页
  if (to.name === 'Login' && authStore.isAuthenticated) {
    next({ name: 'Files' })
    return
  }

  // 管理员专属路由检查
  if (to.meta.requiredPriority) {
    const userPriority = ROLE_PRIORITY[authStore.userRole] || 0
    if (userPriority < to.meta.requiredPriority) {
      // 权限不足，跳转首页
      next({ name: 'Files' })
      return
    }
  }

  next()
})

export default router
