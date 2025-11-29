import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/chat'
  },

  // 일반 사용자 채팅 (메인 페이지)
  {
    path: '/chat',
    name: 'UserChat',
    component: () => import('@/views/user/UserChatView.vue'),
    meta: { title: 'DocuRAG' }
  },

  // 관리자 라우트
  {
    path: '/admin',
    component: () => import('@/views/admin/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      {
        path: '',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardView.vue'),
        meta: { title: '대시보드' }
      },
      {
        path: 'chat',
        name: 'AdminChat',
        component: () => import('@/views/admin/ChatView.vue'),
        meta: { title: '자연어 검색' }
      },
      {
        path: 'documents',
        name: 'AdminDocuments',
        component: () => import('@/views/admin/DocumentsView.vue'),
        meta: { title: 'RAG 문서관리' }
      },
      {
        path: 'documents/new',
        name: 'AdminDocumentNew',
        component: () => import('@/views/admin/DocumentEditView.vue'),
        meta: { title: '새 문서 등록' }
      },
      {
        path: 'documents/:id',
        name: 'AdminDocumentDetail',
        component: () => import('@/views/admin/DocumentDetailView.vue'),
        meta: { title: '문서 상세' }
      },
      {
        path: 'documents/:id/edit',
        name: 'AdminDocumentEdit',
        component: () => import('@/views/admin/DocumentEditView.vue'),
        meta: { title: '문서 수정' }
      },
      {
        path: 'settings',
        name: 'AdminSettings',
        component: () => import('@/views/admin/SettingsView.vue'),
        meta: { title: '시스템 설정' }
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
  const appTitle = import.meta.env.VITE_APP_TITLE || 'DocuRAG'
  document.title = to.meta.title ? `${to.meta.title} - ${appTitle}` : appTitle
})

// 향후 인증 가드 추가 위치
// router.beforeEach((to, from, next) => {
//   const store = useStore()
//   if (to.meta.requiresAdmin && !store.getters['app/isAdmin']) {
//     next('/user')
//   } else {
//     next()
//   }
// })

export default router
