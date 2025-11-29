<template>
  <div class="header-container">
    <!-- 좌측: 메뉴 아이콘 + 페이지 제목 -->
    <div class="header-left">
      <el-icon class="menu-icon" :size="20"><Menu /></el-icon>
      <span class="page-title">{{ pageTitle }}</span>
    </div>

    <!-- 우측: 액션 버튼들 -->
    <div class="header-right">
      <!-- API 상태 표시 -->
      <el-tooltip :content="apiHealthy ? 'API 연결됨' : 'API 연결 안됨'" placement="bottom">
        <el-tag :type="apiHealthy ? 'success' : 'danger'" size="small" effect="plain">
          <el-icon class="mr-5"><Connection /></el-icon>
          {{ apiHealthy ? 'Online' : 'Offline' }}
        </el-tag>
      </el-tooltip>

      <!-- 다크모드 토글 버튼 -->
      <el-tooltip :content="isDarkMode ? '라이트 모드로 전환' : '다크 모드로 전환'" placement="bottom">
        <el-button
          circle
          :icon="isDarkMode ? Sunny : Moon"
          @click="toggleDarkMode"
          class="theme-toggle-btn"
        />
      </el-tooltip>

      <!-- 향후 사용자 메뉴 추가 위치 -->
      <!-- <el-dropdown>
        <el-avatar :size="32" icon="UserFilled" />
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>설정</el-dropdown-item>
            <el-dropdown-item divided>로그아웃</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown> -->
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import { Connection, Menu, Moon, Sunny } from '@element-plus/icons-vue'
import apiClient from '@/api'

const route = useRoute()
const store = useStore()

const apiHealthy = computed(() => store.state.app.apiHealthy)
const isDarkMode = computed(() => store.state.app.darkMode)

const pageTitle = computed(() => {
  return route.meta.title || 'DocuRAG'
})

// 다크모드 토글
const toggleDarkMode = () => {
  store.dispatch('app/toggleDarkMode')
}

// API 헬스 체크
const checkApiHealth = async () => {
  try {
    await apiClient.get('/health')
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

  .menu-icon {
    color: var(--text-color-regular);
  }

  .page-title {
    font-size: 18px;
    font-weight: 500;
    color: var(--text-color-primary);
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle-btn {
  border: 1px solid var(--border-color-light);
  background-color: var(--bg-color-overlay);
  color: var(--text-color-regular);
  transition: var(--theme-transition);

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}

.mr-5 {
  margin-right: 5px;
}
</style>
