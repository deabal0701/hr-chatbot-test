<template>
  <div class="dashboard-toolbar">
    <div class="toolbar-left">
      <el-tooltip content="대화로 이동" placement="bottom">
        <el-button :icon="ArrowLeft" circle size="small" class="back-btn" @click="$emit('go-chat')" />
      </el-tooltip>
      <img :src="logoMark" alt="win-AI" class="toolbar-logo" />

      <!-- 대시보드 선택 드롭다운 -->
      <div class="toolbar-title-area">
        <el-dropdown trigger="click" :popper-class="popperClass" @command="handleDashboardCommand">
          <h2 class="dashboard-selector">
            <span class="selector-title">{{ currentTitle }}</span>
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            <el-tag v-if="isReadOnly" size="small" type="info" class="shared-tag">공유됨</el-tag>
            <el-tag v-if="currentDashboard?.is_shared" size="small" type="success" effect="plain" class="shared-tag">공유중</el-tag>
            <span v-if="widgetCount > 0" class="toolbar-subtitle">(위젯 {{ widgetCount }}개)</span>
          </h2>
          <template #dropdown>
            <el-dropdown-menu>
              <!-- 내 대시보드 -->
              <div class="dropdown-section-title">내 대시보드</div>
              <el-dropdown-item
                v-for="db in myDashboards"
                :key="db.dashboard_id"
                :command="{ action: 'select', id: db.dashboard_id }"
                :class="{ 'is-active': db.dashboard_id === currentDashboardId }"
              >
                <span class="db-name">{{ db.name }}</span>
                <span class="db-meta">
                  <el-tag v-if="db.is_default" size="small" type="primary" disable-transitions>기본</el-tag>
                  <el-tag v-if="db.is_shared" size="small" type="success" disable-transitions>공유</el-tag>
                  <span class="db-count">{{ db.widget_count || 0 }}</span>
                </span>
              </el-dropdown-item>

              <!-- 공유 대시보드 -->
              <template v-if="sharedDashboards.length > 0">
                <el-dropdown-item divided disabled class="section-divider" />
                <div class="dropdown-section-title">공유 대시보드</div>
                <el-dropdown-item
                  v-for="db in sharedDashboards"
                  :key="db.dashboard_id"
                  :command="{ action: 'select', id: db.dashboard_id }"
                  :class="{ 'is-active': db.dashboard_id === currentDashboardId }"
                >
                  <span class="db-name">{{ db.name }}</span>
                  <span class="db-meta">
                    <span class="db-owner">{{ db.owner_name || db.owner_login_id }}</span>
                    <span class="db-count">{{ db.widget_count || 0 }}</span>
                  </span>
                </el-dropdown-item>
              </template>

              <!-- 대시보드 관리 -->
              <el-dropdown-item divided :command="{ action: 'create' }">
                <el-icon><Plus /></el-icon>
                <span>새 대시보드</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    <div class="toolbar-right">
      <template v-if="editMode">
        <el-button @click="$emit('cancel')">취소</el-button>
        <el-button type="primary" @click="$emit('save')">레이아웃 저장</el-button>
      </template>
      <template v-else-if="currentDashboard">
        <!-- 내보내기 (readOnly에서도 허용) -->
        <el-dropdown trigger="click" :popper-class="popperClass" @command="handleExportCommand">
          <el-button :loading="exporting">
            <el-icon><Download /></el-icon>
            <span>내보내기</span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="png">
                <el-icon><PictureFilled /></el-icon>
                이미지 저장 (PNG)
              </el-dropdown-item>
              <el-dropdown-item command="pdf">
                <el-icon><Document /></el-icon>
                PDF 저장
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <el-tooltip content="전체 새로고침" placement="bottom">
          <el-button :icon="Refresh" @click="$emit('refresh-all')" />
        </el-tooltip>

        <!-- 설정 드롭다운 -->
        <el-dropdown trigger="click" :popper-class="popperClass" @command="handleManageCommand">
          <el-button :icon="Setting" />
          <template #dropdown>
            <el-dropdown-menu>
              <!-- 테마 토글 (클릭 시 auto → light → dark 순환) -->
              <el-dropdown-item command="toggle-theme">
                <el-icon><component :is="themeIcon" /></el-icon>
                테마: {{ themeLabel }}
              </el-dropdown-item>

              <!-- 공유 설정 -->
              <el-dropdown-item v-if="!isReadOnly && canShare" command="share" divided>
                <el-icon><Share /></el-icon>
                공유 설정
              </el-dropdown-item>

              <!-- 대시보드 관리 -->
              <template v-if="!isReadOnly">
                <el-dropdown-item command="rename" divided>
                  <el-icon><Edit /></el-icon>
                  대시보드 이름 변경
                </el-dropdown-item>
                <el-dropdown-item command="set-default" :disabled="currentDashboard?.is_default">
                  <el-icon><Star /></el-icon>
                  기본 대시보드로 설정
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided :disabled="currentDashboard?.is_default && myDashboards.length > 1">
                  <el-icon><Delete /></el-icon>
                  <span class="text-danger">대시보드 삭제</span>
                </el-dropdown-item>
              </template>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <!-- 편집 버튼 -->
        <el-button v-if="!isReadOnly" type="primary" plain @click="$emit('edit')">
          <el-icon><Edit /></el-icon>
          <span>편집</span>
        </el-button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  ArrowLeft, ArrowDown, DataAnalysis, Refresh, Edit, Delete, Sunny, Moon, Monitor,
  Download, PictureFilled, Document, Plus, Share, Setting, Star
} from '@element-plus/icons-vue'
import { useTheme } from '@/composables/useTheme'
import logoMarkLight from '@/assets/logo/winai_logo_mark.png'
import logoMarkDark from '@/assets/logo/winai_logo_mark_dark.png'

const { isDarkMode } = useTheme()
const logoMark = computed(() => isDarkMode.value ? logoMarkDark : logoMarkLight)

// 대시보드 테마에 따른 popper class (텔레포트된 드롭다운에 적용)
const isDashboardDark = computed(() => {
  if (props.dashboardTheme === 'auto') return isDarkMode.value
  return props.dashboardTheme === 'dark'
})
const popperClass = computed(() => isDashboardDark.value ? 'dashboard-popper-dark' : 'dashboard-popper-light')

const props = defineProps({
  editMode: { type: Boolean, default: false },
  widgetCount: { type: Number, default: 0 },
  dashboardTheme: { type: String, default: 'auto' },
  exporting: { type: Boolean, default: false },
  isReadOnly: { type: Boolean, default: false },
  currentDashboard: { type: Object, default: null },
  currentDashboardId: { type: Number, default: null },
  myDashboards: { type: Array, default: () => [] },
  sharedDashboards: { type: Array, default: () => [] },
  canShare: { type: Boolean, default: false }
})

const emit = defineEmits([
  'edit', 'cancel', 'save', 'refresh-all', 'go-chat', 'set-theme',
  'export-png', 'export-pdf', 'select-dashboard', 'create-dashboard',
  'rename-dashboard', 'set-default', 'delete-dashboard', 'share'
])

const currentTitle = computed(() => {
  return props.currentDashboard?.name || 'BI 대시보드'
})

const handleDashboardCommand = (cmd) => {
  if (cmd.action === 'select') {
    emit('select-dashboard', cmd.id)
  } else if (cmd.action === 'create') {
    emit('create-dashboard')
  }
}

const handleManageCommand = (cmd) => {
  if (cmd === 'toggle-theme') {
    const cycle = { auto: 'light', light: 'dark', dark: 'auto' }
    emit('set-theme', cycle[props.dashboardTheme] || 'auto')
  }
  else if (cmd === 'share') emit('share')
  else if (cmd === 'rename') emit('rename-dashboard')
  else if (cmd === 'set-default') emit('set-default')
  else if (cmd === 'delete') emit('delete-dashboard')
}

const themeIcon = computed(() => {
  const map = { auto: Monitor, light: Sunny, dark: Moon }
  return map[props.dashboardTheme] || Monitor
})

const themeLabel = computed(() => {
  const map = { auto: '자동', light: '라이트', dark: '다크' }
  return map[props.dashboardTheme] || '자동'
})

const handleExportCommand = (command) => {
  if (command === 'png') emit('export-png')
  else if (command === 'pdf') emit('export-pdf')
}

</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.dashboard-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  background: var(--dashboard-toolbar-bg);
  border-bottom: 1px solid var(--dashboard-toolbar-border);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
  overflow: hidden;

  .back-btn {
    margin-right: 4px;
    flex-shrink: 0;
  }

  .toolbar-icon {
    color: var(--el-color-primary);
    flex-shrink: 0;
  }

  .toolbar-logo {
    width: 24px;
    height: 24px;
    object-fit: contain;
    flex-shrink: 0;

    [data-theme="dark"] & {
      filter: brightness(2.5);
    }
  }

  .toolbar-title-area {
    min-width: 0;
    overflow: hidden;

    .dashboard-selector {
      display: flex;
      align-items: center;
      gap: 6px;
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      color: var(--dashboard-text-primary);
      line-height: 1.4;
      cursor: pointer;
      user-select: none;
      white-space: nowrap;

      &:hover {
        color: var(--el-color-primary);
      }

      .selector-title {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        min-width: 0;
      }

      .dropdown-arrow {
        font-size: 14px;
        transition: transform 0.2s;
        flex-shrink: 0;
      }
    }

    .toolbar-subtitle {
      font-size: 13px;
      font-weight: 400;
      color: var(--dashboard-text-secondary);
      flex-shrink: 0;
    }

    .shared-tag {
      font-weight: 400;
      flex-shrink: 0;
    }
  }
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;

  .text-danger {
    color: var(--el-color-danger);
  }
}

// 드롭다운 메뉴 스타일
.dropdown-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--el-text-color-secondary);
  padding: 4px 12px;
}

:deep(.el-dropdown-menu__item.section-divider) {
  min-height: 0;
  height: 0;
  padding: 0;
  margin: 0;
  line-height: 0;
}

:deep(.el-dropdown-menu__item) {
  &.is-active {
    color: var(--el-color-primary);
    font-weight: 600;
  }

  .db-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-right: 8px;
  }

  .db-meta {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;

    .db-owner {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    .db-count {
      font-size: 11px;
      color: var(--el-text-color-placeholder);
      background: var(--el-fill-color);
      padding: 0 6px;
      border-radius: 8px;
      min-width: 18px;
      text-align: center;
    }
  }
}

@media (max-width: 768px) {
  .dashboard-toolbar {
    padding: 10px 12px;
    gap: 8px;
  }

  .toolbar-left {
    gap: 6px;

    .toolbar-icon { display: none; }

    .toolbar-title-area .dashboard-selector {
      font-size: 15px;
      gap: 4px;
    }

    .toolbar-title-area .toolbar-subtitle { display: none; }
    .toolbar-title-area .shared-tag { display: none; }
  }

  .toolbar-right {
    flex-shrink: 0;
    gap: 4px;

    span { display: none; }

    // 버튼 크기 축소
    :deep(.el-button) {
      padding: 6px;
      &.is-circle { width: 30px; height: 30px; }
    }
  }
}

@media (max-width: 480px) {
  .toolbar-left {
    .back-btn { display: none; }
  }
}
</style>

