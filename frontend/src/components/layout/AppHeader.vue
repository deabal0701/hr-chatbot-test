<template>
  <div class="header-container">
    <!-- 좌측: 사이드바 토글 + 페이지 제목 -->
    <div class="header-left">
      <el-tooltip :content="sidebarCollapsed ? '사이드바 열기' : '사이드바 닫기'" placement="bottom">
        <button class="sidebar-toggle-btn" @click="toggleSidebar">
          <el-icon :size="20"><Expand v-if="sidebarCollapsed" /><Fold v-else /></el-icon>
        </button>
      </el-tooltip>
      <span class="page-title">{{ pageTitle }}</span>
    </div>

    <!-- 우측: 액션 버튼들 -->
    <div class="header-right">
      <!-- [TODO] 테마 토글 - 추후 복원 예정 (디폴트: 다크 모드)
      <el-tooltip :content="isDarkMode ? '라이트 모드로 전환' : '다크 모드로 전환'" placement="bottom">
        <el-button circle size="small" @click="toggleDarkMode" class="theme-toggle-btn">
          <el-icon><Sunny v-if="isDarkMode" /><Moon v-else /></el-icon>
        </el-button>
      </el-tooltip>
      -->

      <!-- API 상태 표시 -->
      <el-tooltip :content="apiHealthy ? 'API 연결됨' : 'API 연결 안됨'" placement="bottom">
        <el-tag :type="apiHealthy ? 'success' : 'danger'" size="small" effect="plain">
          <el-icon class="mr-5"><Connection /></el-icon>
          {{ apiHealthy ? 'Online' : 'Offline' }}
        </el-tag>
      </el-tooltip>

      <!-- 사용자 메뉴 (인증된 경우) -->
      <el-dropdown v-if="currentUser" @command="handleUserCommand" trigger="click">
        <div class="user-info">
          <el-avatar :size="24" class="user-avatar">
            <el-icon :size="14"><UserFilled /></el-icon>
          </el-avatar>
          <span class="user-name">{{ displayName }}</span>
          <el-icon class="user-arrow"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <div class="user-detail">
                <span class="user-scope-name">권한 : {{ roleName }}</span>
              </div>
            </el-dropdown-item>
            <el-dropdown-item command="password" divided>
              <el-icon><Lock /></el-icon> 비밀번호 변경
            </el-dropdown-item>
            <el-dropdown-item command="logout">
              <el-icon><SwitchButton /></el-icon> 로그아웃
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 미인증 상태: 로그인 버튼 -->
      <el-button v-else type="primary" size="small" @click="goToLogin">
        로그인
      </el-button>
    </div>

    <!-- 비밀번호 변경 다이얼로그 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="비밀번호 변경"
      width="420px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-position="top"
      >
        <el-form-item label="현재 비밀번호" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="새 비밀번호" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="비밀번호 확인" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">취소</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">변경</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Connection, Fold, Expand, ArrowDown, Lock, SwitchButton, UserFilled, Sunny, Moon } from '@element-plus/icons-vue'
import axios from 'axios'
import apiClient from '@/api'
import { useAuth } from '@/composables/useAuth'
import { useTheme } from '@/composables/useTheme'

const route = useRoute()
const router = useRouter()
const store = useStore()

const { currentUser, displayName, roleName, logout } = useAuth()
const { isDarkMode, toggleDarkMode } = useTheme()
const apiHealthy = computed(() => store.state.app.apiHealthy)
const sidebarCollapsed = computed(() => store.state.app.sidebarCollapsed)
const toggleSidebar = () => store.dispatch('app/toggleSidebar')

const pageTitle = computed(() => {
  return route.meta.title || import.meta.env.VITE_APP_TITLE || 'MUREUM'
})



// 사용자 메뉴 커맨드 처리
const handleUserCommand = async (command) => {
  if (command === 'logout') {
    await logout()
    router.push('/login')
  } else if (command === 'password') {
    passwordDialogVisible.value = true
  }
}

// 로그인 페이지로 이동
const goToLogin = () => {
  router.push('/login')
}

// ===== 비밀번호 변경 =====
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '현재 비밀번호를 입력해주세요', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '새 비밀번호를 입력해주세요', trigger: 'blur' },
    { min: 8, message: '8자 이상 입력해주세요', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) return callback()
        const hasUpper = /[A-Z]/.test(value)
        const hasLower = /[a-z]/.test(value)
        const hasDigit = /[0-9]/.test(value)
        if (!(hasUpper && hasLower && hasDigit)) {
          callback(new Error('대문자, 소문자, 숫자를 포함해야 합니다'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  confirmPassword: [
    { required: true, message: '비밀번호를 다시 입력해주세요', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('비밀번호가 일치하지 않습니다'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleChangePassword = async () => {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await store.dispatch('auth/changePassword', {
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    ElMessage.success('비밀번호가 변경되었습니다')
    passwordDialogVisible.value = false
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (err) {
    ElMessage.error(err.detail || err.message || '비밀번호 변경에 실패했습니다')
  } finally {
    passwordLoading.value = false
  }
}

// API 헬스 체크
const checkApiHealth = async () => {
  try {
    await axios.get((import.meta.env.VITE_API_URL || '') + '/health')
    store.commit('app/SET_API_HEALTH', true)
  } catch {
    store.commit('app/SET_API_HEALTH', false)
  }
}

onMounted(() => {
  checkApiHealth()
  // 30초마다 헬스 체크
  setInterval(checkApiHealth, 30000)
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.header-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;

  .sidebar-toggle-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: none;
    border-radius: 6px;
    background-color: transparent;
    color: var(--text-color-regular);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background-color: var(--bg-color-hover);
      color: var(--text-color-primary);
    }
  }

  .page-title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-color-primary);

    @include mx.mobile {
      font-size: 15px;
    }
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;

  :deep(.el-tag__content) {
    display: inline-flex;
    align-items: center;
  }

  @include mx.mobile {
    gap: 8px;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.2s;

  &:hover {
    background-color: var(--bg-color-hover);
  }

  .user-avatar {
    background-color: var(--color-info);
    color: var(--bg-color-card);
  }

  .user-name {
    font-size: 14px;
    color: var(--text-color-primary);
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;

    @include mx.mobile {
      @include mx.hide-mobile;
    }
  }

  .user-arrow {
    font-size: 12px;
    color: var(--text-color-secondary);

    @include mx.mobile {
      @include mx.hide-mobile;
    }
  }
}

.user-detail {
  display: flex;
  align-items: center;
  gap: 8px;

  .user-scope-name {
    font-size: 13px;
    color: var(--text-color-primary);
    font-weight: 500;
  }
}

.theme-toggle-btn {
  border: 1px solid var(--border-color);
  background-color: transparent;
  color: var(--text-color-regular);
  transition: all 0.2s;

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}

.mr-5 {
  margin-right: 5px;
}
</style>
