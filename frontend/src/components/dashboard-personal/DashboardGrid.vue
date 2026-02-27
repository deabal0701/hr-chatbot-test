<template>
  <div ref="gridContainer" class="dashboard-grid">
    <grid-layout
      v-if="gridReady"
      :layout="layoutModel"
      @update:layout="layoutModel = $event"
      @layout-updated="handleLayoutUpdated"
      :col-num="colNum"
      :row-height="30"
      :margin="[16, 16]"
      :is-draggable="editMode"
      :is-resizable="editMode"
      :vertical-compact="true"
      :use-css-transforms="true"
    >
      <grid-item
        v-for="item in layoutModel"
        :key="item.i"
        :i="item.i"
        :x="item.x"
        :y="item.y"
        :w="item.w"
        :h="item.h"
        :min-w="item.minW || 2"
        :min-h="item.minH || 3"
        drag-allow-from=".widget-header.drag-handle"
      >
        <DashboardWidget
          :widget="getWidget(item.i)"
          :edit-mode="editMode"
          :is-refreshing="isWidgetRefreshing(item.i)"
          :content-height="(item.h * 30) - 60"
          :dark-mode="darkMode"
          @edit="$emit('edit-widget', $event)"
          @delete="$emit('delete-widget', $event)"
          @refresh="$emit('refresh-widget', $event)"
        />
      </grid-item>
    </grid-layout>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import DashboardWidget from './DashboardWidget.vue'

const props = defineProps({
  editMode: { type: Boolean, default: false },
  colNum: { type: Number, default: 12 },
  darkMode: { type: Boolean, default: false }
})

defineEmits(['edit-widget', 'delete-widget', 'refresh-widget', 'layout-changed'])

// vue3-grid-layout-next 초기화 타이밍 이슈 보정
// ResizeObserver로 컨테이너가 실제 너비를 가질 때까지 대기 후 grid-layout 마운트
const gridContainer = ref(null)
const gridReady = ref(false)
let resizeObserver = null

onMounted(() => {
  const el = gridContainer.value
  if (!el) return

  // 이미 너비가 있으면 nextTick 후 마운트 (CSS 레이아웃 안정화 대기)
  if (el.offsetWidth > 0) {
    nextTick(() => { gridReady.value = true })
    return
  }

  // 너비가 0이면 ResizeObserver로 대기
  resizeObserver = new ResizeObserver((entries) => {
    for (const entry of entries) {
      if (entry.contentRect.width > 0) {
        gridReady.value = true
        resizeObserver.disconnect()
        resizeObserver = null
        break
      }
    }
  })
  resizeObserver.observe(el)
})

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})

const store = useStore()

const layoutModel = ref([])

// store의 gridLayout을 watch하여 동기화
// 편집 모드: 위젯 추가/삭제(개수 변경) 시에만 동기화 (드래그 위치 변경은 무시)
// 일반 모드: 항상 동기화
watch(
  () => store.getters['dashboard/gridLayout'],
  (newLayout) => {
    if (!props.editMode || newLayout.length !== layoutModel.value.length) {
      layoutModel.value = JSON.parse(JSON.stringify(newLayout))
    }
  },
  { immediate: true, deep: true }
)

// 편집 모드 진입 시 현재 레이아웃 스냅샷
watch(
  () => props.editMode,
  (isEdit) => {
    if (isEdit) {
      layoutModel.value = JSON.parse(JSON.stringify(store.getters['dashboard/gridLayout']))
    }
  }
)

// 드래그/리사이즈 완료 시 store 업데이트
const handleLayoutUpdated = (newLayout) => {
  if (props.editMode) {
    const items = newLayout.map(item => ({
      widget_id: Number(item.i),
      x: item.x,
      y: item.y,
      w: item.w,
      h: item.h
    }))
    store.commit('dashboard/UPDATE_LAYOUT', items)
  }
}

const getWidget = (id) => {
  return store.getters['dashboard/widgetById'](Number(id)) || {}
}

const isWidgetRefreshing = (id) => {
  return store.getters['dashboard/isWidgetRefreshing'](Number(id))
}
</script>

<style lang="scss" scoped>
.dashboard-grid {
  width: 100%;
  min-height: 400px;
}

// vue3-grid-layout 기본 스타일 오버라이드
:deep(.vue-grid-item) {
  transition: all 0.2s ease;

  &.vue-grid-placeholder {
    background: var(--el-color-primary-light-8) !important;
    border: 2px dashed var(--el-color-primary) !important;
    border-radius: 8px;
    opacity: 0.6;
  }
}

// 리사이즈 핸들 스타일
:deep(.vue-resizable-handle) {
  width: 20px;
  height: 20px;
  bottom: 2px;
  right: 2px;
  background: none;

  &::after {
    content: '';
    position: absolute;
    right: 4px;
    bottom: 4px;
    width: 8px;
    height: 8px;
    border-right: 2px solid var(--dashboard-text-muted);
    border-bottom: 2px solid var(--dashboard-text-muted);
    opacity: 0.5;
  }
}
</style>
