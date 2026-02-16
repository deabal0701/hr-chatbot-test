<template>
  <div class="login-container">
    <div class="login-card">
      <!-- 로고 + 타이틀 -->
      <div class="login-header">
        <el-icon :size="48" color="#409eff"><ChatDotRound /></el-icon>
        <h1 class="login-title">MUREUM</h1>
        <p class="login-subtitle">AI 지식 도우미</p>
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

    <!-- 하단 정보 -->
    <div class="login-footer">
      <span>MUREUM v1.0.0</span>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ChatDotRound, User, Lock } from '@element-plus/icons-vue'

const store = useStore()
const router = useRouter()
const route = useRoute()
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
    await store.dispatch('auth/login', {
      loginId: form.loginId,
      password: form.password
    })

    // 로그인 성공 → 랜딩 페이지로 리다이렉트
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)
    } else {
      router.push(store.getters['auth/landingPage'])
    }
  } catch {
    // loginError가 store에 설정됨 (계정잠금, 비활성화, 인증실패 등)
  }
}

// 이미 로그인된 상태면 랜딩 페이지로 리다이렉트
onMounted(() => {
  if (store.getters['auth/isAuthenticated']) {
    router.replace(store.getters['auth/landingPage'])
  }
})
</script>

<style lang="scss" scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: var(--bg-color-page);
  transition: var(--theme-transition);
}

.login-card {
  width: 400px;
  max-width: 90vw;
  padding: 40px 32px;
  background-color: var(--bg-color-card);
  border-radius: 12px;
  box-shadow: var(--box-shadow);
  border: 1px solid var(--border-color-lighter);
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

.login-footer {
  margin-top: 24px;
  font-size: 12px;
  color: var(--text-color-secondary);
}
</style>
