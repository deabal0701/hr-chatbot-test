<template>
  <el-dialog
    v-model="visible"
    title="대시보드 공유 설정"
    width="480px"
    :class="themeClass"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <div v-if="dashboard" class="share-content">
      <div class="share-dashboard-name">
        <span class="label">대시보드</span>
        <span class="name">{{ dashboard.name }}</span>
      </div>

      <el-form label-position="top">
        <el-form-item label="공유 여부">
          <el-switch
            v-model="form.isShared"
            active-text="공유"
            inactive-text="비공유"
          />
        </el-form-item>

        <el-form-item v-if="form.isShared" label="공유 범위">
          <el-radio-group v-model="form.shareScope" class="scope-radio-group">
            <div class="radio-option">
              <el-radio value="all" :disabled="!canShareAll">전체 공유</el-radio>
              <span class="scope-desc">모든 사용자가 볼 수 있습니다</span>
            </div>
            <div class="radio-option">
              <el-radio value="tenant">테넌트 공유</el-radio>
              <span class="scope-desc">같은 테넌트 소속만 볼 수 있습니다</span>
            </div>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="form.isShared"
        title="공유 대시보드는 다른 사용자에게 읽기 전용으로 표시됩니다."
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <template #footer>
      <el-button @click="visible = false">취소</el-button>
      <el-button type="primary" :loading="submitting" :disabled="!canSubmit" @click="handleSubmit">
        저장
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  dashboard: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const store = useStore()
const themeClass = computed(() => store.getters['dashboard/dashboardThemeClass'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const submitting = ref(false)

const form = ref({
  isShared: false,
  shareScope: 'tenant'
})

const roleCode = computed(() => store.state.auth?.user?.role_code || '')
const canShareAll = computed(() => roleCode.value === 'GLOBAL')

watch(visible, (val) => {
  if (val && props.dashboard) {
    form.value.isShared = props.dashboard.is_shared || false
    form.value.shareScope = props.dashboard.share_scope || 'tenant'
  }
})

const canSubmit = computed(() => {
  if (!form.value.isShared) return true
  return !!form.value.shareScope
})

const handleSubmit = async () => {
  if (submitting.value) return
  submitting.value = true
  try {
    await store.dispatch('dashboard/shareDashboard', {
      dashboardId: props.dashboard.dashboard_id,
      data: {
        is_shared: form.value.isShared,
        share_scope: form.value.isShared ? form.value.shareScope : null
      }
    })
    ElMessage.success(form.value.isShared ? '대시보드가 공유되었습니다' : '공유가 해제되었습니다')
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error(err?.response?.data?.error?.detail || '공유 설정에 실패했습니다')
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.share-content {
  .share-dashboard-name {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background: var(--el-fill-color-light);
    border-radius: 6px;
    margin-bottom: 20px;

    .label {
      font-size: 13px;
      color: var(--el-text-color-secondary);
    }

    .name {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  :deep(.scope-radio-group) {
    display: flex;
    width: 100%;
  }

  .radio-option {
    flex: 1;
  }

  .scope-desc {
    display: block;
    font-size: 12px;
    color: var(--el-text-color-secondary);
    margin-top: -12px;
    padding-left: 24px;
  }
}
</style>
