// ============================================================================
// Vue Router Configuration
// ============================================================================

import { createRouter, createWebHistory } from 'vue-router'

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
        component: StoragePoolView
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
        meta: { requiresAuth: true, requiresAdmin: true }
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

// 导航守卫 - 认证检查
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('hfm_token')
  
  if (to.meta.requiresAuth !== false && !token) {
    // 需要认证但没有 token，跳转登录
    next({ name: 'Login' })
  } else if (to.name === 'Login' && token) {
    // 已登录访问登录页，跳转首页
    next({ name: 'Files' })
  } else {
    next()
  }
})

export default router
