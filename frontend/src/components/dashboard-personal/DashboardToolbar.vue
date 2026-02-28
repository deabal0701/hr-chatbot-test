<template>
  <div class="dashboard-toolbar">
    <div class="toolbar-left">
      <el-tooltip content="대화로 이동" placement="bottom">
        <el-button :icon="ArrowLeft" circle size="small" class="back-btn" @click="$emit('go-chat')" />
      </el-tooltip>
      <el-icon class="toolbar-icon" :size="22"><DataAnalysis /></el-icon>

      <!-- 대시보드 선택 드롭다운 -->
      <div class="toolbar-title-area">
        <el-dropdown trigger="click" @command="handleDashboardCommand">
          <h2 class="dashboard-selector">
            {{ currentTitle }}
            <el-icon class="dropdown-arrow"><ArrowDown /></el-icon>
            <el-tag v-if="isReadOnly" size="small" type="info" class="shared-tag">공유됨</el-tag>
            <el-tag v-if="currentDashboard?.is_shared" size="small" type="success" class="shared-tag">공유중</el-tag>
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
                <el-dropdown-item divided disabled>
                  <div class="dropdown-section-title">공유 대시보드</div>
                </el-dropdown-item>
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
      <template v-else>
        <el-tooltip :content="themeTooltip" placement="bottom">
          <el-button circle size="small" @click="$emit('toggle-theme')">
            <el-icon :size="16"><component :is="themeIcon" /></el-icon>
          </el-button>
        </el-tooltip>

        <!-- 내보내기 (readOnly에서도 허용) -->
        <el-dropdown trigger="click" @command="handleExportCommand">
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

        <!-- 편집/공유/관리 버튼: readOnly일 때 숨김 -->
        <template v-if="!isReadOnly">
          <!-- 공유 버튼 (GLOBAL/TENANT만) -->
          <el-tooltip v-if="canShare" content="공유 설정" placement="bottom">
            <el-button :icon="Share" @click="$emit('share')" />
          </el-tooltip>

          <!-- 대시보드 관리 드롭다운 -->
          <el-dropdown trigger="click" @command="handleManageCommand">
            <el-button :icon="Setting" />
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="rename">
                  <el-icon><Edit /></el-icon>
                  대시보드 이름 변경
                </el-dropdown-item>
                <el-dropdown-item command="set-default" :disabled="currentDashboard?.is_default">
                  <el-icon><Star /></el-icon>
                  기본 대시보드로 설정
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided :disabled="currentDashboard?.is_default">
                  <el-icon><Delete /></el-icon>
                  <span class="text-danger">대시보드 삭제</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <el-button type="primary" plain @click="$emit('edit')">
            <el-icon><Edit /></el-icon>
            <span>편집</span>
          </el-button>
        </template>
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
  'edit', 'cancel', 'save', 'refresh-all', 'go-chat', 'toggle-theme',
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
  if (cmd === 'rename') emit('rename-dashboard')
  else if (cmd === 'set-default') emit('set-default')
  else if (cmd === 'delete') emit('delete-dashboard')
}

const handleExportCommand = (command) => {
  if (command === 'png') emit('export-png')
  else if (command === 'pdf') emit('export-pdf')
}

const themeIcon = computed(() => {
  const map = { auto: Monitor, light: Sunny, dark: Moon }
  return map[props.dashboardTheme] || Monitor
})

const themeTooltip = computed(() => {
  const map = { auto: '테마: 자동 (클릭하여 변경)', light: '테마: 라이트 (클릭하여 변경)', dark: '테마: 다크 (클릭하여 변경)' }
  return map[props.dashboardTheme] || '테마 변경'
})
</script>

<style lang="scss" scoped>
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

  .back-btn {
    margin-right: 4px;
  }

  .toolbar-icon {
    color: var(--el-color-primary);
  }

  .toolbar-title-area {
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

      &:hover {
        color: var(--el-color-primary);
      }

      .dropdown-arrow {
        font-size: 14px;
        transition: transform 0.2s;
      }
    }

    .toolbar-subtitle {
      font-size: 13px;
      font-weight: 400;
      color: var(--dashboard-text-secondary);
    }

    .shared-tag {
      font-weight: 400;
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
    padding: 12px 16px;
  }

  .toolbar-left {
    .toolbar-title-area .dashboard-selector { font-size: 16px; }
  }

  .toolbar-right span { display: none; }
}
</style>
