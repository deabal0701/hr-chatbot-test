<template>
  <div class="header-container">
    <!-- 좌측: 사이드바 토글 + 페이지 제목 -->
    <div class="header-left">
      <el-button
        :icon="isCollapsed ? Expand : Fold"
        text
        @click="toggleSidebar"
      />
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
import { Fold, Expand, Connection } from '@element-plus/icons-vue'
import apiClient from '@/api'

const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const apiHealthy = computed(() => store.state.app.apiHealthy)

const pageTitle = computed(() => {
  return route.meta.title || 'HR Chatbot'
})

const toggleSidebar = () => {
  store.dispatch('app/toggleSidebar')
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

  .page-title {
    font-size: 18px;
    font-weight: 500;
    color: #303133;
  }
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mr-5 {
  margin-right: 5px;
}
</style>
