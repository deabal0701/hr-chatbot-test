<template>
  <div class="dashboard-toolbar">
    <div class="toolbar-left">
      <el-tooltip content="채팅으로 이동" placement="bottom">
        <el-button :icon="ArrowLeft" circle size="small" class="back-btn" @click="$emit('go-chat')" />
      </el-tooltip>
      <el-icon class="toolbar-icon" :size="22"><DataAnalysis /></el-icon>
      <div class="toolbar-title-area">
        <h2>
          BI 대시보드
          <span v-if="widgetCount > 0" class="toolbar-subtitle">(위젯 {{ widgetCount }}개)</span>
        </h2>
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
        <el-button type="primary" plain @click="$emit('edit')">
          <el-icon><Edit /></el-icon>
          <span>편집</span>
        </el-button>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowLeft, DataAnalysis, Refresh, Edit, Sunny, Moon, Monitor, Download, PictureFilled, Document } from '@element-plus/icons-vue'

const props = defineProps({
  editMode: { type: Boolean, default: false },
  widgetCount: { type: Number, default: 0 },
  dashboardTheme: { type: String, default: 'auto' }, // 'auto' | 'light' | 'dark'
  exporting: { type: Boolean, default: false }
})

const emit = defineEmits(['edit', 'cancel', 'save', 'refresh-all', 'go-chat', 'toggle-theme', 'export-png', 'export-pdf'])

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
    h2 {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      color: var(--dashboard-text-primary);
      line-height: 1.4;
    }

    .toolbar-subtitle {
      font-size: 13px;
      font-weight: 400;
      color: var(--dashboard-text-secondary);
      margin-left: 4px;
    }
  }
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 768px) {
  .dashboard-toolbar {
    padding: 12px 16px;
  }

  .toolbar-left {
    .toolbar-title-area h2 { font-size: 16px; }
  }

  .toolbar-right span { display: none; }
}
</style>
