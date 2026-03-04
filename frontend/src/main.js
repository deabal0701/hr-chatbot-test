import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import store from './store'
import './assets/styles/main.scss'

// vue3-grid-layout
import { GridLayout, GridItem } from 'vue3-grid-layout-next'
import 'vue3-grid-layout-next/dist/style.css'

const app = createApp(App)

// Element Plus Icons 등록
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: undefined }) // 한국어는 별도 설정 필요시 추가
app.use(router)
app.use(store)

// Grid Layout 전역 컴포넌트 등록
app.component('grid-layout', GridLayout)
app.component('grid-item', GridItem)

// 앱 마운트 전 저장된 테마 적용
store.dispatch('app/initTheme')

// 저장된 토큰이 있으면 /me 호출하여 최신 사용자 정보(menus) 갱신
// APP을 마운트 하기 전에 인증체크를 먼저 수행하여, 인증이 필요한 라우트 접근 시 로그인 페이지로 리다이렉트 되도록 함
store.dispatch('auth/initAuth').finally(() => {
  app.mount('#app')
})
