<template>
  <div class="personal-dashboard" :class="dashboardThemeClass">
    <!-- 툴바 -->
    <DashboardToolbar
      :edit-mode="editMode"
      :widget-count="widgetCount"
      :dashboard-theme="dashboardTheme"
      :exporting="exporting"
      :is-read-only="isReadOnly"
      :current-dashboard="currentDashboard"
      :current-dashboard-id="currentDashboardId"
      :my-dashboards="myDashboards"
      :shared-dashboards="sharedDashboards"
      :can-share="canShare"
      @edit="handleEnterEdit"
      @cancel="handleCancelEdit"
      @save="handleSaveEdit"
      @refresh-all="handleRefreshAll"
      @go-chat="goToChat"
      @set-theme="handleSetTheme"
      @export-png="handleExportPng"
      @export-pdf="handleExportPdf"
      @select-dashboard="handleSelectDashboard"
      @create-dashboard="showManageModal = true; editingDashboard = null"
      @rename-dashboard="handleRenameDashboard"
      @set-default="handleSetDefault"
      @delete-dashboard="handleDeleteDashboard"
      @share="showShareModal = true"
    />

    <!-- 메인 영역 -->
    <div ref="dashboardContentRef" class="dashboard-content">
      <!-- 빈 상태: 대시보드 없음 또는 위젯 없음 -->
      <DashboardEmptyState
        v-if="!isLoading && (noDashboard || widgetCount === 0)"
        :no-dashboard="noDashboard"
        :read-only="isReadOnly"
        @create-dashboard="handleCreateFirstDashboard"
        @go-chat="goToChat"
        @add-widget="handleAddWidgetFromEmpty"
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

      <!-- 편집 모드: 위젯 추가 플로팅 버튼 (readOnly일 때 숨김) -->
      <div v-if="editMode && !isReadOnly" class="fab-container">
        <el-button type="primary" circle :icon="Plus" size="large" @click="showAddModal = true" />
      </div>
    </div>

    <!-- 위젯 모달 -->
    <WidgetEditModal
      v-model="showEditModal"
      :widget="editingWidget"
      @saved="handleWidgetSaved"
    />

    <AddWidgetModal
      v-model="showAddModal"
      @saved="handleWidgetSaved"
    />

    <!-- 대시보드 관리 모달 -->
    <DashboardManageModal
      v-model="showManageModal"
      :dashboard="editingDashboard"
      @saved="handleDashboardManageSaved"
    />

    <!-- 대시보드 공유 모달 -->
    <DashboardShareModal
      v-model="showShareModal"
      :dashboard="currentDashboard"
      @saved="handleDashboardShareSaved"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { captureElementPng, exportElementPdf, formatTimestamp } from '@/utils/exportUtils'
import DashboardToolbar from '@/components/dashboard-personal/DashboardToolbar.vue'
import DashboardEmptyState from '@/components/dashboard-personal/DashboardEmptyState.vue'
import DashboardGrid from '@/components/dashboard-personal/DashboardGrid.vue'
import WidgetEditModal from '@/components/dashboard-personal/WidgetEditModal.vue'
import AddWidgetModal from '@/components/dashboard-personal/AddWidgetModal.vue'
import DashboardManageModal from '@/components/dashboard-personal/DashboardManageModal.vue'
import DashboardShareModal from '@/components/dashboard-personal/DashboardShareModal.vue'

const store = useStore()
const router = useRouter()
const route = useRoute()

// 상태
const showEditModal = ref(false)
const showAddModal = ref(false)
const showManageModal = ref(false)
const showShareModal = ref(false)
const editingWidget = ref(null)
const editingDashboard = ref(null)
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
onMounted(async () => {
  window.addEventListener('resize', handleResize)

  // 대시보드 목록 로드
  await store.dispatch('dashboard/fetchDashboards')

  // route query에서 dashboard_id 확인
  const queryId = route.query.id ? parseInt(route.query.id) : null
  if (queryId) {
    await store.dispatch('dashboard/selectDashboard', queryId)
  } else {
    await store.dispatch('dashboard/fetchWidgets')
  }
})
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (editMode.value) {
    store.dispatch('dashboard/cancelEditMode')
  }
})

// route.query.id 변경 감지
watch(() => route.query.id, async (newId) => {
  if (newId) {
    await store.dispatch('dashboard/selectDashboard', parseInt(newId))
  }
})

// Vuex 연결
const isLoading = computed(() => store.state.dashboard.isLoading)
const editMode = computed(() => store.state.dashboard.editMode)
const widgetCount = computed(() => store.getters['dashboard/widgetCount'])
const dashboardTheme = computed(() => store.getters['dashboard/dashboardTheme'])
const isReadOnly = computed(() => store.getters['dashboard/isReadOnly'])
const currentDashboard = computed(() => store.getters['dashboard/currentDashboard'])
const currentDashboardId = computed(() => store.state.dashboard.currentDashboardId)
const myDashboards = computed(() => store.getters['dashboard/myDashboards'])
const sharedDashboards = computed(() => store.getters['dashboard/sharedDashboardList'])
const canShare = computed(() => store.getters['dashboard/canShare'])
const noDashboard = computed(() => !currentDashboardId.value && myDashboards.value.length === 0)

// 대시보드 테마
const isUserDark = computed(() => store.getters['app/isUserDarkMode'])
const effectiveDark = computed(() => {
  if (dashboardTheme.value === 'auto') return isUserDark.value
  return dashboardTheme.value === 'dark'
})
const dashboardThemeClass = computed(() => effectiveDark.value ? 'dashboard-dark' : 'dashboard-light')

// ============================================
// 대시보드 관리
// ============================================
const handleSelectDashboard = async (dashboardId) => {
  await store.dispatch('dashboard/selectDashboard', dashboardId)
  // URL 업데이트 (기본 대시보드가 아닌 경우)
  const defaultDb = myDashboards.value.find(d => d.is_default)
  if (defaultDb && dashboardId === defaultDb.dashboard_id) {
    router.replace({ query: {} })
  } else {
    router.replace({ query: { id: dashboardId } })
  }
}

const handleRenameDashboard = () => {
  editingDashboard.value = currentDashboard.value
  showManageModal.value = true
}

const handleSetDefault = async () => {
  if (!currentDashboardId.value) return
  try {
    await store.dispatch('dashboard/setDefaultDashboard', currentDashboardId.value)
    ElMessage.success('기본 대시보드가 변경되었습니다')
  } catch (err) {
    ElMessage.error('기본 대시보드 변경에 실패했습니다')
  }
}

const handleDeleteDashboard = async () => {
  if (!currentDashboard.value) return
  try {
    await ElMessageBox.confirm(
      `"${currentDashboard.value.name}" 대시보드를 삭제하시겠습니까?\n포함된 위젯도 모두 삭제됩니다.`,
      '대시보드 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await store.dispatch('dashboard/deleteDashboard', currentDashboardId.value)
    await store.dispatch('dashboard/fetchDashboards')
    router.replace({ query: {} })
    ElMessage.success('대시보드가 삭제되었습니다')
  } catch {
    // 취소
  }
}

const handleDashboardManageSaved = async () => {
  await store.dispatch('dashboard/fetchDashboards')
  // 대시보드가 없었다면 새로 생성된 기본 대시보드 자동 선택
  if (!currentDashboardId.value) {
    const defaultDb = myDashboards.value.find(d => d.is_default)
    if (defaultDb) {
      await store.dispatch('dashboard/selectDashboard', defaultDb.dashboard_id)
    }
  }
}

const handleDashboardShareSaved = async () => {
  await store.dispatch('dashboard/fetchDashboards')
}

const handleCreateFirstDashboard = () => {
  editingDashboard.value = null
  showManageModal.value = true
}

// ============================================
// 편집 모드
// ============================================
const handleEnterEdit = () => {
  if (isMobile.value) {
    ElMessage.warning('모바일에서는 편집 모드를 지원하지 않습니다')
    return
  }
  store.dispatch('dashboard/enterEditMode')
}

const handleAddWidgetFromEmpty = () => {
  store.dispatch('dashboard/enterEditMode')
  showAddModal.value = true
}

const handleCancelEdit = () => { store.dispatch('dashboard/cancelEditMode') }

const handleSaveEdit = () => {
  store.dispatch('dashboard/saveEditMode')
  ElMessage.success('레이아웃이 저장되었습니다')
}

// ============================================
// 위젯 관리
// ============================================
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
const handleWidgetSaved = () => {
  store.dispatch('dashboard/fetchWidgets')
  store.dispatch('dashboard/fetchDashboards')
}

// 테마 설정
const handleSetTheme = (theme) => {
  store.dispatch('dashboard/setDashboardTheme', theme)
}

// PNG 내보내기
const handleExportPng = async () => {
  if (!dashboardContentRef.value) return
  exporting.value = true
  try {
    const name = currentDashboard.value?.name || 'BI_대시보드'
    const filename = `${name}_${formatTimestamp()}.png`
    await captureElementPng(dashboardContentRef.value, filename)
    ElMessage.success('이미지가 저장되었습니다')
  } catch (err) {
    console.error('[Dashboard] PNG export failed:', err)
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
    const name = currentDashboard.value?.name || 'BI 대시보드'
    const filename = `${name}_${formatTimestamp()}.pdf`
    await exportElementPdf(dashboardContentRef.value, name, filename)
    ElMessage.success('PDF가 저장되었습니다')
  } catch (err) {
    console.error('[Dashboard] PDF export failed:', err)
    ElMessage.error('PDF 내보내기에 실패했습니다')
  } finally {
    exporting.value = false
  }
}

// 네비게이션
const goToChat = () => { router.push('/chat') }
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
