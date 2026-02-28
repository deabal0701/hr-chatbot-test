<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '대시보드 수정' : '새 대시보드'"
    width="420px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-form label-position="top" :model="form">
      <el-form-item label="대시보드 이름" required>
        <el-input
          v-model="form.name"
          placeholder="대시보드 이름을 입력하세요"
          maxlength="100"
          show-word-limit
          @keydown.enter.prevent="handleSubmit"
        />
      </el-form-item>
      <el-form-item label="설명">
        <el-input
          v-model="form.description"
          type="textarea"
          placeholder="대시보드 설명 (선택)"
          maxlength="500"
          show-word-limit
          :rows="3"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">취소</el-button>
      <el-button type="primary" :disabled="!canSubmit" :loading="submitting" @click="handleSubmit">
        {{ isEdit ? '수정' : '생성' }}
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

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const isEdit = computed(() => !!props.dashboard)
const submitting = ref(false)

const form = ref({
  name: '',
  description: ''
})

watch(visible, (val) => {
  if (val && props.dashboard) {
    form.value.name = props.dashboard.name || ''
    form.value.description = props.dashboard.description || ''
  } else if (val) {
    form.value.name = ''
    form.value.description = ''
  }
})

const canSubmit = computed(() => form.value.name.trim().length > 0)

const handleSubmit = async () => {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  try {
    if (isEdit.value) {
      await store.dispatch('dashboard/updateDashboard', {
        dashboardId: props.dashboard.dashboard_id,
        data: { name: form.value.name.trim(), description: form.value.description?.trim() || null }
      })
      ElMessage.success('대시보드가 수정되었습니다')
    } else {
      await store.dispatch('dashboard/createDashboard', {
        name: form.value.name.trim(),
        description: form.value.description?.trim() || null
      })
      ElMessage.success('대시보드가 생성되었습니다')
    }
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error(err?.response?.data?.error?.detail || '처리에 실패했습니다')
  } finally {
    submitting.value = false
  }
}

const handleClose = () => {
  visible.value = false
}
</script>
