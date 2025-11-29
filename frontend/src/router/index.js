import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/admin'
  },

  // 관리자 라우트 (현재 구현)
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
        meta: { title: 'HR 챗봇' }
      },
      {
        path: 'documents',
        name: 'AdminDocuments',
        component: () => import('@/views/admin/DocumentsView.vue'),
        meta: { title: '문서 관리' }
      }
    ]
  },

  // 일반사용자 라우트 (향후 확장)
  // {
  //   path: '/user',
  //   component: () => import('@/views/user/UserLayout.vue'),
  //   children: [
  //     {
  //       path: '',
  //       name: 'UserChat',
  //       component: () => import('@/views/user/ChatView.vue'),
  //       meta: { title: 'HR 챗봇' }
  //     }
  //   ]
  // },

  // 404 - 홈으로 리다이렉트
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
  const appTitle = import.meta.env.VITE_APP_TITLE || 'HR Chatbot'
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
