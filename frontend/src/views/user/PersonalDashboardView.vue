<template>
  <div class="personal-dashboard" :class="dashboardThemeClass">
    <!-- 툴바 -->
    <DashboardToolbar
      :edit-mode="editMode"
      :widget-count="widgetCount"
      :dashboard-theme="dashboardTheme"
      :exporting="exporting"
      @edit="handleEnterEdit"
      @cancel="handleCancelEdit"
      @save="handleSaveEdit"
      @refresh-all="handleRefreshAll"
      @go-chat="goToChat"
      @toggle-theme="handleToggleTheme"
      @export-png="handleExportPng"
      @export-pdf="handleExportPdf"
    />

    <!-- 메인 영역 -->
    <div ref="dashboardContentRef" class="dashboard-content">
      <!-- 빈 상태 -->
      <DashboardEmptyState
        v-if="!isLoading && widgetCount === 0"
        @go-chat="goToChat"
        @load-demo="loadDemo"
      />

      <!-- 위젯 그리드 -->
      <DashboardGrid
        v-else
        :edit-mode="editMode"
        :col-num="gridColNum"
        :dark-mode="effectiveDark"
        @edit-widget="openEditModal"
        @delete-widget="handleDeleteWidget"
        @refresh-widget="handleRefreshWidget"
      />

      <!-- 편집 모드: 위젯 추가 플로팅 버튼 -->
      <div v-if="editMode" class="fab-container">
        <el-button type="primary" circle :icon="Plus" size="large" @click="showAddModal = true" />
      </div>
    </div>

    <!-- 모달 -->
    <WidgetEditModal
      v-model="showEditModal"
      :widget="editingWidget"
      @saved="handleWidgetSaved"
    />

    <AddWidgetModal
      v-model="showAddModal"
      @saved="handleWidgetSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { captureElementPng, exportElementPdf, formatTimestamp } from '@/utils/exportUtils'
import DashboardToolbar from '@/components/dashboard-personal/DashboardToolbar.vue'
import DashboardEmptyState from '@/components/dashboard-personal/DashboardEmptyState.vue'
import DashboardGrid from '@/components/dashboard-personal/DashboardGrid.vue'
import WidgetEditModal from '@/components/dashboard-personal/WidgetEditModal.vue'
import AddWidgetModal from '@/components/dashboard-personal/AddWidgetModal.vue'

const store = useStore()
const router = useRouter()

// 상태
const showEditModal = ref(false)
const showAddModal = ref(false)
const editingWidget = ref(null)
const windowWidth = ref(window.innerWidth)
const dashboardContentRef = ref(null)
const exporting = ref(false)

// 반응형
const isMobile = computed(() => windowWidth.value <= 768)
const gridColNum = computed(() => {
  if (isMobile.value) return 1
  if (windowWidth.value <= 1024) return 8
  return 12
})

const handleResize = () => { windowWidth.value = window.innerWidth }
onMounted(() => {
  window.addEventListener('resize', handleResize)
  store.dispatch('dashboard/fetchWidgets')
})
onUnmounted(() => { window.removeEventListener('resize', handleResize) })

// Vuex 연결
const isLoading = computed(() => store.state.dashboard.isLoading)
const editMode = computed(() => store.state.dashboard.editMode)
const widgetCount = computed(() => store.getters['dashboard/widgetCount'])
const dashboardTheme = computed(() => store.getters['dashboard/dashboardTheme'])

// 대시보드 테마: auto=사용자화면 모드 따라감, light/dark=고정
const isUserDark = computed(() => store.getters['app/isUserDarkMode'])
const effectiveDark = computed(() => {
  if (dashboardTheme.value === 'auto') return isUserDark.value
  return dashboardTheme.value === 'dark'
})
const dashboardThemeClass = computed(() => effectiveDark.value ? 'dashboard-dark' : 'dashboard-light')

// 편집 모드
const handleEnterEdit = () => {
  if (isMobile.value) {
    ElMessage.warning('모바일에서는 편집 모드를 지원하지 않습니다')
    return
  }
  store.dispatch('dashboard/enterEditMode')
}

const handleCancelEdit = () => { store.dispatch('dashboard/cancelEditMode') }

const handleSaveEdit = () => {
  store.dispatch('dashboard/saveEditMode')
  ElMessage.success('레이아웃이 저장되었습니다')
}

// 위젯 관리
const openEditModal = (widget) => {
  editingWidget.value = widget
  showEditModal.value = true
}

const handleDeleteWidget = async (widgetId) => {
  store.dispatch('dashboard/deleteWidget', widgetId)
  ElMessage.success('위젯이 삭제되었습니다')
}

const handleRefreshWidget = (widgetId) => { store.dispatch('dashboard/refreshWidget', widgetId) }
const handleRefreshAll = () => { store.dispatch('dashboard/refreshAllWidgets') }
const handleWidgetSaved = () => { /* 모달에서 저장 완료 후 콜백 */ }

// 테마 토글 (auto → light → dark → auto)
const handleToggleTheme = () => {
  const cycle = { auto: 'light', light: 'dark', dark: 'auto' }
  store.dispatch('dashboard/setDashboardTheme', cycle[dashboardTheme.value] || 'auto')
}

// PNG 내보내기
const handleExportPng = async () => {
  if (!dashboardContentRef.value) return
  exporting.value = true
  try {
    const filename = `BI_대시보드_${formatTimestamp()}.png`
    await captureElementPng(dashboardContentRef.value, filename)
    ElMessage.success('이미지가 저장되었습니다')
  } catch {
    ElMessage.error('이미지 내보내기에 실패했습니다')
  } finally {
    exporting.value = false
  }
}

// PDF 내보내기
const handleExportPdf = async () => {
  if (!dashboardContentRef.value) return
  exporting.value = true
  try {
    const filename = `BI_대시보드_${formatTimestamp()}.pdf`
    await exportElementPdf(dashboardContentRef.value, 'BI 대시보드', filename)
    ElMessage.success('PDF가 저장되었습니다')
  } catch {
    ElMessage.error('PDF 내보내기에 실패했습니다')
  } finally {
    exporting.value = false
  }
}

// 네비게이션
const goToChat = () => { router.push('/chat') }
const loadDemo = () => {
  store.dispatch('dashboard/resetToMock')
  ElMessage.success('데모 위젯이 로드되었습니다')
}
</script>

<style lang="scss" scoped>
.personal-dashboard {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--dashboard-bg);
  overflow: hidden;
}

.dashboard-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  position: relative;
}

.fab-container {
  position: fixed;
  bottom: 32px;
  right: 32px;
  z-index: 100;

  :deep(.el-button) {
    width: 56px;
    height: 56px;
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);

    &:hover {
      transform: scale(1.1);
      box-shadow: 0 6px 16px rgba(64, 158, 255, 0.5);
    }
  }
}

@media (max-width: 768px) {
  .dashboard-content {
    padding: 8px;
  }

  .fab-container {
    bottom: 20px;
    right: 20px;
  }
}
</style>
