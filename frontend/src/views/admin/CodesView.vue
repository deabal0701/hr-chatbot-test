<template>
  <div class="codes-view">
    <div class="page-header">
      <h1>코드 관리</h1>
      <p>LLM 제공자, 모델, 임베딩 모델 등을 동적으로 관리합니다.</p>
    </div>

    <el-card>
      <!-- 코드 그룹 선택 -->
      <div class="group-selector">
        <el-select
          v-model="selectedGroup"
          placeholder="코드 그룹 선택"
          size="large"
          style="width: 300px"
          @change="onGroupChange"
        >
          <el-option
            v-for="group in codeGroups"
            :key="group.value"
            :label="group.label"
            :value="group.value"
          />
        </el-select>

        <el-button
          type="primary"
          :icon="Plus"
          @click="openCreateDialog"
          :disabled="!selectedGroup"
        >
          새 코드 추가
        </el-button>

        <el-button
          :icon="Refresh"
          @click="loadCodes"
          :loading="isLoading"
        >
          새로고침
        </el-button>
      </div>

      <!-- 코드 테이블 -->
      <el-table
        v-loading="isLoading"
        :data="codes"
        style="width: 100%; margin-top: 20px"
        :default-sort="{ prop: 'sort_order', order: 'ascending' }"
      >
        <el-table-column prop="sort_order" label="순서" width="80" sortable />

        <el-table-column prop="code_value" label="코드 값" width="200">
          <template #default="{ row }">
            <el-tag v-if="row.is_system" type="info" size="small">시스템</el-tag>
            <span style="margin-left: 8px">{{ row.code_value }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="code_name" label="표시명" min-width="200" />

        <el-table-column prop="description" label="설명" min-width="250" show-overflow-tooltip />

        <el-table-column label="메타데이터" width="120">
          <template #default="{ row }">
            <el-button
              v-if="row.metadata"
              link
              type="primary"
              size="small"
              @click="viewMetadata(row)"
            >
              보기
            </el-button>
            <span v-else style="color: #999">없음</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="상태" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '활성' : '비활성' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="동작" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              :icon="Edit"
              @click="openEditDialog(row)"
            >
              수정
            </el-button>
            <el-button
              link
              type="danger"
              size="small"
              :icon="Delete"
              @click="handleDelete(row)"
              :disabled="row.is_system"
            >
              삭제
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="codes.length === 0 && !isLoading" class="empty-state">
        <p>코드 그룹을 선택하여 관리할 코드를 확인하세요.</p>
      </div>
    </el-card>

    <!-- 코드 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '새 코드 추가' : '코드 수정'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
      >
        <el-form-item label="코드 그룹" prop="code_group">
          <el-input v-model="formData.code_group" :disabled="true" />
        </el-form-item>

        <el-form-item label="코드 값" prop="code_value">
          <el-input
            v-model="formData.code_value"
            placeholder="예: gpt-4o-mini"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-help">코드의 실제 값 (영문, 숫자, -, _ 만 사용)</div>
        </el-form-item>

        <el-form-item label="표시명" prop="code_name">
          <el-input
            v-model="formData.code_name"
            placeholder="예: GPT-4o Mini"
          />
          <div class="form-help">사용자에게 표시될 이름</div>
        </el-form-item>

        <el-form-item label="설명" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="코드에 대한 설명 (선택사항)"
          />
        </el-form-item>

        <el-form-item label="메타데이터 (JSON)" prop="metadata">
          <el-input
            v-model="metadataJson"
            type="textarea"
            :rows="4"
            placeholder='{"dimension": 1536, "pricing_link": "https://..."}'
          />
          <div class="form-help">JSON 형식으로 추가 속성 입력 (선택사항)</div>
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="정렬 순서" prop="sort_order">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="활성화 여부" prop="is_active">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">취소</el-button>
        <el-button
          type="primary"
          @click="handleSubmit"
          :loading="isSaving"
        >
          {{ dialogMode === 'create' ? '생성' : '수정' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 메타데이터 보기 다이얼로그 -->
    <el-dialog
      v-model="metadataDialogVisible"
      title="메타데이터"
      width="500px"
    >
      <pre class="metadata-viewer">{{ JSON.stringify(selectedMetadata, null, 2) }}</pre>
      <template #footer>
        <el-button @click="metadataDialogVisible = false">닫기</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import codesApi from '@/api/codes'

// 상태
const isLoading = ref(false)
const isSaving = ref(false)
const selectedGroup = ref('')
const codes = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create') // 'create' | 'edit'
const metadataDialogVisible = ref(false)
const selectedMetadata = ref(null)
const formRef = ref(null)

// 코드 그룹 정의 (레이블 매핑)
const codeGroups = [
  { value: 'LLM_PROVIDER', label: 'LLM 제공자' },
  { value: 'LLM_MODEL_OPENAI', label: 'LLM 모델 (OpenAI)' },
  { value: 'LLM_MODEL_ANTHROPIC', label: 'LLM 모델 (Anthropic)' },
  { value: 'EMBEDDING_MODEL', label: '임베딩 모델' }
]

// 폼 데이터
const formData = reactive({
  code_group: '',
  code_value: '',
  code_name: '',
  description: '',
  metadata: null,
  sort_order: 0,
  is_active: true
})

const metadataJson = ref('')
const currentEditId = ref(null)

// 폼 검증 규칙
const formRules = {
  code_value: [
    { required: true, message: '코드 값을 입력하세요', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9\-_]+$/, message: '영문, 숫자, -, _ 만 사용 가능합니다', trigger: 'blur' }
  ],
  code_name: [
    { required: true, message: '표시명을 입력하세요', trigger: 'blur' }
  ]
}

// 코드 그룹 변경 시
const onGroupChange = async () => {
  await loadCodes()
}

// 코드 목록 로드
const loadCodes = async () => {
  if (!selectedGroup.value) return

  isLoading.value = true
  try {
    const response = await codesApi.getByGroup(selectedGroup.value, false)
    codes.value = response.codes
  } catch (error) {
    ElMessage.error('코드 목록 로드 실패')
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

// 생성 다이얼로그 열기
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentEditId.value = null
  resetForm()
  formData.code_group = selectedGroup.value
  dialogVisible.value = true
}

// 수정 다이얼로그 열기
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentEditId.value = row.code_id

  formData.code_group = row.code_group
  formData.code_value = row.code_value
  formData.code_name = row.code_name
  formData.description = row.description || ''
  formData.metadata = row.metadata
  formData.sort_order = row.sort_order
  formData.is_active = row.is_active

  metadataJson.value = row.metadata ? JSON.stringify(row.metadata, null, 2) : ''
  dialogVisible.value = true
}

// 폼 초기화
const resetForm = () => {
  formData.code_group = ''
  formData.code_value = ''
  formData.code_name = ''
  formData.description = ''
  formData.metadata = null
  formData.sort_order = 0
  formData.is_active = true
  metadataJson.value = ''

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 폼 제출
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 메타데이터 파싱
    let metadata = null
    if (metadataJson.value.trim()) {
      try {
        metadata = JSON.parse(metadataJson.value)
      } catch (error) {
        ElMessage.error('메타데이터 JSON 형식이 올바르지 않습니다')
        return
      }
    }

    isSaving.value = true
    try {
      const payload = {
        ...formData,
        metadata: metadata
      }

      if (dialogMode.value === 'create') {
        await codesApi.create(payload)
        ElMessage.success('코드가 생성되었습니다')
      } else {
        const { code_group, code_value, ...updatePayload } = payload
        await codesApi.update(currentEditId.value, updatePayload)
        ElMessage.success('코드가 수정되었습니다')
      }

      dialogVisible.value = false
      await loadCodes()
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '작업 실패'
      ElMessage.error(errorMsg)
      console.error(error)
    } finally {
      isSaving.value = false
    }
  })
}

// 삭제 처리
const handleDelete = async (row) => {
  if (row.is_system) {
    ElMessage.warning('시스템 코드는 삭제할 수 없습니다')
    return
  }

  try {
    await ElMessageBox.confirm(
      `"${row.code_name}" 코드를 삭제하시겠습니까?`,
      '코드 삭제',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    await codesApi.delete(row.code_id)
    ElMessage.success('코드가 삭제되었습니다')
    await loadCodes()
  } catch (error) {
    if (error === 'cancel') return

    const errorMsg = error.response?.data?.detail || '삭제 실패'
    ElMessage.error(errorMsg)
    console.error(error)
  }
}

// 메타데이터 보기
const viewMetadata = (row) => {
  selectedMetadata.value = row.metadata
  metadataDialogVisible.value = true
}

// 마운트 시 첫 번째 그룹 선택
onMounted(() => {
  if (codeGroups.length > 0) {
    selectedGroup.value = codeGroups[0].value
    loadCodes()
  }
})
</script>

<style lang="scss" scoped>
.codes-view {
  padding: 20px;

  .page-header {
    margin-bottom: 24px;

    h1 {
      font-size: 28px;
      font-weight: 600;
      margin: 0 0 8px 0;
      color: #303133;
    }

    p {
      font-size: 14px;
      color: #606266;
      margin: 0;
    }
  }

  .group-selector {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
    color: #909399;
    font-size: 14px;
  }

  .form-help {
    font-size: 12px;
    color: #909399;
    margin-top: 4px;
  }

  .metadata-viewer {
    background-color: #f5f7fa;
    padding: 16px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.6;
    overflow-x: auto;
    max-height: 400px;
  }
}
</style>
