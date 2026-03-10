<template>
  <div class="sso-callback">
    <div class="sso-card">
      <!-- 로딩 상태 -->
      <template v-if="loading">
        <el-icon :size="48" class="sso-spinner"><Loading /></el-icon>
        <h2 class="sso-title">SSO 로그인 중...</h2>
        <p class="sso-desc">인증 정보를 확인하고 있습니다.</p>
      </template>

      <!-- 에러 상태 -->
      <template v-else-if="errorMessage">
        <el-icon :size="48" color="var(--color-danger)"><CircleCloseFilled /></el-icon>
        <h2 class="sso-title">SSO 로그인 실패</h2>
        <p class="sso-desc">{{ errorMessage }}</p>
        <el-button type="primary" @click="goLogin" class="sso-btn">로그인 페이지로 이동</el-button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { Loading, CircleCloseFilled } from '@element-plus/icons-vue'
import authApi from '@/api/auth'

const store = useStore()
const router = useRouter()

const loading = ref(true)
const errorMessage = ref('')

const goLogin = () => {
  router.push('/login')
}

/** 쿠키 읽기 헬퍼 */
const getCookie = (name) => {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? match[1] : null
}

/** 쿠키 삭제 헬퍼 */
const deleteCookie = (name) => {
  document.cookie = `${name}=; path=/; max-age=0`
}

/** Base64URL 디코딩 (RFC 4648 §5, JWT와 동일 방식) */
const decodeBase64URL = (str) => {
  let b64 = str.replace(/-/g, '+').replace(/_/g, '/')
  b64 += '='.repeat((4 - b64.length % 4) % 4)
  return atob(b64)
}

onMounted(async () => {
  // 쿠키에서 SSO 인증 토큰 읽기 (Base64URL 인코딩)
  const authB64url = getCookie('sso_auth')

  if (!authB64url) {
    loading.value = false
    errorMessage.value = 'SSO 인증 정보가 전달되지 않았습니다.'
    return
  }

  // 쿠키 즉시 삭제 (1회용)
  deleteCookie('sso_auth')

  try {
    // Base64URL 디코딩 → { at: access_token, rt: refresh_token }
    const { at: accessToken, rt: refreshToken } = JSON.parse(decodeBase64URL(authB64url))

    // 토큰을 localStorage에 저장 (API 호출 시 Authorization 헤더에 사용)
    localStorage.setItem('mureum_access_token', accessToken)
    localStorage.setItem('mureum_refresh_token', refreshToken)

    // /me API로 사용자 정보 조회 (메뉴 권한 포함)
    const user = await authApi.getMe()

    // Vuex store + localStorage에 저장
    store.commit('auth/SET_AUTH', { accessToken, refreshToken, user })
    store.dispatch('chat/clearChat', null, { root: true })
    store.dispatch('dashboard/clearState', null, { root: true })

    router.replace(user.landing_page || '/chat')
  } catch (err) {
    console.error('[SSO] 인증 처리 실패:', err)
    loading.value = false
    errorMessage.value = 'SSO 인증 정보 처리에 실패했습니다.'
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.sso-callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color-page);
}

.sso-card {
  text-align: center;
  padding: 48px 40px;
  background-color: var(--bg-color-card);
  border-radius: 12px;
  box-shadow: var(--box-shadow);
  border: 1px solid var(--border-color-lighter);
  max-width: 420px;
  width: 90vw;
}

.sso-spinner {
  color: var(--color-primary);
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sso-title {
  margin: 16px 0 8px;
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color-primary);
}

.sso-desc {
  margin: 0 0 24px;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.sso-btn {
  min-width: 180px;
}
</style>
