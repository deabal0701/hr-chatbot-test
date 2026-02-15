import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },

  // 로그인 페이지
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '로그인', public: true }
  },

  // 일반 사용자 채팅 (메인 페이지) - ChatGPT 스타일 레이아웃
  {
    path: '/chat',
    name: 'UserChat',
    component: () => import('@/components/user/UserChatLayout.vue')
  },

  // 관리자 라우트
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      // /admin 접속 시 대시보드로 리다이렉트
      {
        path: '',
        redirect: '/admin/dashboard'
      },
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '대시보드', menuCode: 'DASHBOARD' }
      },
      {
        path: 'chat',
        name: 'AdminChat',
        component: () => import('@/views/admin/ChatView.vue'),
        meta: { title: '자연어 검색', menuCode: 'AI_SEARCH' }
      },
      {
        path: 'documents',
        name: 'AdminDocuments',
        component: () => import('@/views/admin/DocumentsView.vue'),
        meta: { title: '지식문서 관리', menuCode: 'DOC_MGMT' }
      },
      {
        path: 'documents/new',
        name: 'AdminDocumentNew',
        component: () => import('@/views/admin/DocumentEditView.vue'),
        meta: { title: '새 문서 등록', menuCode: 'DOC_MGMT' }
      },
      {
        path: 'documents/:id',
        name: 'AdminDocumentDetail',
        component: () => import('@/views/admin/DocumentDetailView.vue'),
        meta: { title: '문서 상세', menuCode: 'DOC_MGMT' }
      },
      {
        path: 'documents/:id/edit',
        name: 'AdminDocumentEdit',
        component: () => import('@/views/admin/DocumentEditView.vue'),
        meta: { title: '문서 수정', menuCode: 'DOC_MGMT' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { title: '시스템 설정', menuCode: 'SYS_SETTING' }
      },
      {
        path: 'codes',
        name: 'AdminCodes',
        component: () => import('@/views/admin/CodesView.vue'),
        meta: { title: '코드 관리', menuCode: 'CODE_MGMT' }
      },
      {
        path: 'history',
        name: 'AdminHistory',
        component: () => import('@/views/admin/HistoryView.vue'),
        meta: { title: '검색 이력', menuCode: 'SEARCH_HIST' }
      },
      {
        path: 'history/:requestId',
        name: 'AdminHistoryDetail',
        component: () => import('@/views/admin/HistoryDetailView.vue'),
        meta: { title: '요청 상세', menuCode: 'SEARCH_HIST' }
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/UsersView.vue'),
        meta: { title: '사용자 관리', menuCode: 'USER_MGMT' }
      },
      {
        path: 'roles',
        name: 'AdminRoles',
        component: () => import('@/views/admin/RolesView.vue'),
        meta: { title: '역할 관리', menuCode: 'ROLE_MGMT' }
      },
      {
        path: 'tenants',
        name: 'AdminTenants',
        component: () => import('@/views/admin/TenantsView.vue'),
        meta: { title: '테넌트 관리', menuCode: 'TENANT_MGMT' }
      },
      {
        path: 'menus',
        name: 'AdminMenus',
        component: () => import('@/views/admin/MenusView.vue'),
        meta: { title: '메뉴 관리', menuCode: 'MENU_MGMT' }
      }
    ]
  },

  // 404 - 채팅으로 리다이렉트
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 페이지 타이틀 업데이트
router.afterEach((to) => {
  const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
  document.title = to.meta.title ? `${to.meta.title} - ${appTitle}` : appTitle
})

// 인증 라우터 가드 (v2.0 메뉴 기반)
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 1. 로그인 페이지: 이미 인증됐으면 랜딩 페이지로
  if (to.path === '/login') {
    if (isAuthenticated) {
      return next(store.getters['auth/landingPage'])
    }
    return next()
  }

  // 2. 공개 페이지: 인증 불필요
  if (to.meta.public) return next()

  // 3. 관리자 페이지: 인증 + 메뉴 권한 필요
  if (to.meta.requiresAdmin || to.matched.some(r => r.meta.requiresAdmin)) {
    if (!isAuthenticated) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    const canAdmin = store.getters['auth/canAccessAdmin']
    if (!canAdmin) {
      return next('/chat')
    }
    // 개별 메뉴 권한 체크 (menuCode가 있는 라우트만)
    const menuCode = to.meta.menuCode
    if (menuCode) {
      const hasAccess = store.getters['auth/hasMenuPermission'](menuCode, 'read')
      if (!hasAccess) {
        return next(store.getters['auth/landingPage'])
      }
    }
    return next()
  }

  // 4. 일반 페이지 (/chat 등): 인증 필요
  if (!isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  next()
})

export default router
