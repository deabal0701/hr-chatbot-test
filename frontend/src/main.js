import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import store from './store'
import './assets/styles/main.scss'

const app = createApp(App)

// Element Plus Icons 등록
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: undefined }) // 한국어는 별도 설정 필요시 추가
app.use(router)
app.use(store)

// 앱 마운트 전 저장된 테마 적용
store.dispatch('app/initTheme')

app.mount('#app')
