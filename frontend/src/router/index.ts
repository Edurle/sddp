import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginPage.vue'),
  },
  {
    path: '/',
    component: () => import('@/components/layout/AppLayout.vue'),
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardPage.vue'),
      },
      {
        path: 'teams',
        name: 'TeamList',
        component: () => import('@/views/team/TeamListPage.vue'),
      },
      {
        path: 'teams/:id',
        name: 'TeamDetail',
        component: () => import('@/views/team/TeamDetailPage.vue'),
      },
      {
        path: 'projects/:id',
        name: 'ProjectDetail',
        component: () => import('@/views/project/ProjectDetailPage.vue'),
      },
      {
        path: 'iterations/:id/kanban',
        name: 'IterationKanban',
        component: () => import('@/views/iteration/IterationKanbanPage.vue'),
      },
      {
        path: 'requirements/:id',
        name: 'RequirementDetail',
        component: () => import('@/views/requirement/RequirementDetailPage.vue'),
      },
      {
        path: 'tasks/:id',
        name: 'TaskDetail',
        component: () => import('@/views/task/TaskDetailPage.vue'),
      },
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/AdminUsersPage.vue'),
      },
      {
        path: 'profile/api-keys',
        name: 'ApiKeys',
        component: () => import('@/views/profile/ApiKeyPage.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

function decodeTokenPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    return JSON.parse(atob(parts[1]))
  } catch {
    return null
  }
}

router.beforeEach((to, from, next) => {
  if (to.path.startsWith('/admin')) {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (!token) {
      return next('/login')
    }
    const payload = decodeTokenPayload(token)
    if (!payload?.is_admin) {
      return next('/dashboard')
    }
  }
  next()
})

export default router
