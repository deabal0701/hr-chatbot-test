<template>
  <div class="login-container">
    <div class="login-card">
      <!-- 로고 + 타이틀 -->
      <div class="login-header">
        <el-icon :size="48" color="var(--color-primary)"><ChatDotRound /></el-icon>
        <h1 class="login-title">{{ appTitle }}</h1>
        <p class="login-subtitle">AI 통합 검색 어시스턴트</p>
      </div>

      <!-- 로그인 폼 -->
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        @submit.prevent="handleLogin"
        class="login-form"
      >
        <el-form-item prop="loginId">
          <el-input
            v-model="form.loginId"
            placeholder="아이디"
            :prefix-icon="User"
            size="large"
            :disabled="loginLoading"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="비밀번호"
            :prefix-icon="Lock"
            size="large"
            show-password
            :disabled="loginLoading"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <!-- 에러 메시지 -->
        <el-alert
          v-if="loginError"
          :title="loginError"
          type="error"
          show-icon
          :closable="false"
          class="login-error"
        />

        <!-- 로그인 버튼 -->
        <el-button
          type="primary"
          size="large"
          :loading="loginLoading"
          @click="handleLogin"
          class="login-btn"
        >
          {{ loginLoading ? '로그인 중...' : '로그인' }}
        </el-button>
      </el-form>
    </div>

    <!-- SSO 로그인 버튼 (배포 시 임시 주석처리, 배포 후 원복 예정) -->
    <!-- <div class="sso-test-area">
      <el-button type="info" text @click="openSSOTest">
        SSO 로그인
      </el-button>
    </div> -->

    <!-- 하단 정보 -->
    <div class="login-footer">
      <span>{{ appTitle }} v2.0.0</span>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { ChatDotRound, User, Lock } from '@element-plus/icons-vue'

const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
const store = useStore()
const router = useRouter()
const route = useRoute()
const { isAuthenticated, landingPage, login } = useAuth()
const formRef = ref(null)

const form = reactive({
  loginId: '',
  password: ''
})

const rules = {
  loginId: [
    { required: true, message: '아이디를 입력해주세요', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '비밀번호를 입력해주세요', trigger: 'blur' }
  ]
}

const loginLoading = computed(() => store.state.auth.loginLoading)
const loginError = computed(() => store.state.auth.loginError)

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await login(form.loginId, form.password)

    // 로그인 성공 → 랜딩 페이지로 리다이렉트
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)
    } else {
      router.push(landingPage.value)
    }
  } catch {
    // loginError가 store에 설정됨 (계정잠금, 비활성화, 인증실패 등)
  }
}

// SSO 테스트: 현재 탭에서 외부 시스템 시뮬레이터 열기 (public/sso_test.html)
const openSSOTest = () => {
  window.location.href = '/sso_test.html'
}

// 이미 로그인된 상태면 랜딩 페이지로 리다이렉트
onMounted(() => {
  if (isAuthenticated.value) {
    router.replace(landingPage.value)
  }
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color-page);
  transition: var(--theme-transition);
  position: relative;
  overflow: hidden;

  // 배경: 대각선 블루/틸 글로우
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    background:
      radial-gradient(ellipse 600px 400px at 20% 30%, rgba(99, 102, 241, 0.18) 0%, transparent 70%),
      radial-gradient(ellipse 500px 350px at 80% 70%, rgba(6, 182, 212, 0.14) 0%, transparent 70%),
      radial-gradient(ellipse 300px 300px at 50% 50%, rgba(64, 158, 255, 0.08) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }

  // 배경: 그리드 라인
  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(64, 158, 255, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(64, 158, 255, 0.08) 1px, transparent 1px);
    background-size: 48px 48px;
    mask-image: radial-gradient(ellipse 80% 70% at center, black 0%, transparent 65%);
    -webkit-mask-image: radial-gradient(ellipse 80% 70% at center, black 0%, transparent 65%);
    pointer-events: none;
    z-index: 0;
  }
}

.login-card {
  position: relative;
  z-index: 1;
  width: 400px;
  max-width: 90vw;
  padding: 40px 32px;
  background-color: var(--bg-color-card);
  border-radius: 12px;
  border: 1px solid var(--border-color);
  box-shadow: var(--box-shadow), 0 0 0 1px rgba(64, 158, 255, 0.15);

  @include mx.mobile {
    padding: 32px 20px;
  }
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

  .login-title {
    margin: 12px 0 4px;
    font-size: 28px;
    font-weight: 700;
    color: var(--text-color-primary);
    letter-spacing: 2px;

    @include mx.mobile {
      font-size: 24px;
    }
  }

  .login-subtitle {
    margin: 0;
    font-size: 14px;
    color: var(--text-color-secondary);
  }
}

.login-form {
  .el-form-item {
    margin-bottom: 20px;
  }

  .el-input {
    :deep(.el-input__wrapper) {
      padding: 4px 12px;
      background-color: var(--bg-color-card);
      border: 1px solid var(--border-color);
      transition: var(--theme-transition);

      &:hover,
      &.is-focus {
        border-color: var(--color-primary);
      }
    }

    :deep(.el-input__inner) {
      &:-webkit-autofill,
      &:-webkit-autofill:hover,
      &:-webkit-autofill:focus {
        -webkit-box-shadow: 0 0 0 1000px var(--bg-color-card) inset !important;
        -webkit-text-fill-color: var(--text-color-primary) !important;
        transition: background-color 5000s ease-in-out 0s;
      }
    }


  }
}

.login-error {
  margin-bottom: 20px;

  :deep(.el-alert__title) {
    font-size: 13px;
  }
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  margin-top: 4px;
}

.sso-test-area {
  position: relative;
  z-index: 1;
  margin-top: 16px;
  text-align: center;
}

.login-footer {
  position: relative;
  z-index: 1;
  margin-top: 24px;
  font-size: 12px;
  color: var(--text-color-secondary);
}
</style>
