<template>
  <div class="tenants-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>테넌트 관리</h2>
        <p class="subtitle">테넌트(조직)를 생성하고 관리합니다.</p>
      </div>
    </div>

    <div class="content-card">
      <!-- 툴바 -->
      <div class="toolbar">
        <el-button :icon="Refresh" @click="loadTenants" :loading="isLoading">새로고침</el-button>
        <div class="flex-1" />
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">새 테넌트</el-button>
      </div>

      <!-- 테넌트 테이블 -->
      <el-table
        v-loading="isLoading"
        :data="tenants"
        style="width: 100%; margin-top: 16px"
        :default-sort="{ prop: 'tenant_id', order: 'ascending' }"
      >
        <el-table-column prop="tenant_id" label="ID" width="60" sortable />

        <el-table-column prop="tenant_code" label="테넌트 코드" width="160" sortable />

        <el-table-column prop="tenant_name" label="테넌트명" min-width="180" sortable />

        <el-table-column prop="user_count" label="사용자 수" width="100" align="center" sortable>
          <template #default="{ row }">
            <el-tag size="small" :type="row.user_count > 0 ? '' : 'info'">{{ row.user_count }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="상태" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '활성' : '비활성' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="메타데이터" width="100" align="center">
          <template #default="{ row }">
            <el-button
              v-if="row.metadata && Object.keys(row.metadata).length > 0"
              link type="primary" size="small"
              @click="viewMetadata(row)"
            >
              보기
            </el-button>
            <span v-else style="color: var(--text-color-secondary)">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="생성일" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="동작" width="120" fixed="right">
          <template #default="{ row }">
            <span class="action-cell">
              <el-button link type="primary" size="small" :icon="Edit" @click="openEditDialog(row)">수정</el-button>
              <el-button link type="danger" size="small" :icon="Delete" @click="handleDelete(row)">삭제</el-button>
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 빈 상태 -->
      <div v-if="tenants.length === 0 && !isLoading" class="empty-state">
        <p>등록된 테넌트가 없습니다.</p>
      </div>
    </div>

    <!-- 테넌트 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '새 테넌트 추가' : '테넌트 수정'"
      width="560px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
      >
        <el-form-item label="테넌트 코드" prop="tenant_code">
          <el-input
            v-model="formData.tenant_code"
            placeholder="예: COMPANY_A"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-help">영문 대문자, 숫자, _ 만 사용 (생성 후 변경 불가)</div>
        </el-form-item>

        <el-form-item label="테넌트명" prop="tenant_name">
          <el-input v-model="formData.tenant_name" placeholder="예: A 주식회사" />
        </el-form-item>

        <el-form-item label="활성화 여부">
          <el-switch v-model="formData.is_active" />
        </el-form-item>

        <el-form-item label="메타데이터 (JSON)">
          <el-input
            v-model="metadataJson"
            type="textarea"
            :rows="4"
            placeholder='{"industry": "IT", "contract_type": "enterprise"}'
          />
          <div class="form-help">JSON 형식으로 추가 속성 입력 (업종, 계약정보 등)</div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">취소</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isSaving">
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import tenantsApi from '@/api/tenants'

// 상태
const isLoading = ref(false)
const isSaving = ref(false)
const tenants = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref(null)
const currentTenantId = ref(null)

// 메타데이터 보기
const metadataDialogVisible = ref(false)
const selectedMetadata = ref(null)

// 폼 데이터
const formData = reactive({
  tenant_code: '',
  tenant_name: '',
  is_active: true
})
const metadataJson = ref('')

// 날짜 포맷
const formatDateTime = (dt) => {
  if (!dt) return '-'
  return new Date(dt).toLocaleString('ko-KR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// 폼 검증 규칙
const formRules = {
  tenant_code: [
    { required: true, message: '테넌트 코드를 입력하세요', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '영문 대문자, 숫자, _ 만 사용 가능합니다', trigger: 'blur' }
  ],
  tenant_name: [
    { required: true, message: '테넌트명을 입력하세요', trigger: 'blur' }
  ]
}

// 테넌트 목록 로드
const loadTenants = async () => {
  isLoading.value = true
  try {
    const result = await tenantsApi.list()
    tenants.value = result.items || []
  } catch {
    ElMessage.error('테넌트 목록 로드 실패')
  } finally {
    isLoading.value = false
  }
}

// 생성 다이얼로그
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentTenantId.value = null
  resetForm()
  dialogVisible.value = true
}

// 수정 다이얼로그
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentTenantId.value = row.tenant_id

  formData.tenant_code = row.tenant_code
  formData.tenant_name = row.tenant_name
  formData.is_active = row.is_active
  metadataJson.value = row.metadata ? JSON.stringify(row.metadata, null, 2) : ''
  dialogVisible.value = true

  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 폼 초기화
const resetForm = () => {
  formData.tenant_code = ''
  formData.tenant_name = ''
  formData.is_active = true
  metadataJson.value = ''
  if (formRef.value) formRef.value.clearValidate()
}

// 폼 제출
const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  // 메타데이터 JSON 파싱
  let metadata = null
  if (metadataJson.value.trim()) {
    try {
      metadata = JSON.parse(metadataJson.value)
    } catch {
      ElMessage.error('메타데이터 JSON 형식이 올바르지 않습니다')
      return
    }
  }

  isSaving.value = true
  try {
    if (dialogMode.value === 'create') {
      await tenantsApi.create({
        tenant_code: formData.tenant_code,
        tenant_name: formData.tenant_name,
        is_active: formData.is_active,
        metadata
      })
      ElMessage.success('테넌트가 생성되었습니다')
    } else {
      await tenantsApi.update(currentTenantId.value, {
        tenant_name: formData.tenant_name,
        is_active: formData.is_active,
        metadata
      })
      ElMessage.success('테넌트가 수정되었습니다')
    }
    dialogVisible.value = false
    await loadTenants()
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
  } finally {
    isSaving.value = false
  }
}

// 삭제 처리
const handleDelete = async (row) => {
  const hasUsers = row.user_count > 0
  const message = hasUsers
    ? `"${row.tenant_name}"에 ${row.user_count}명의 사용자가 소속되어 있습니다.\n삭제 시 비활성화 처리됩니다. 계속하시겠습니까?`
    : `"${row.tenant_name}" 테넌트를 삭제하시겠습니까?`
  const title = hasUsers ? '테넌트 비활성화' : '테넌트 삭제'

  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: hasUsers ? '비활성화' : '삭제',
      cancelButtonText: '취소',
      type: 'warning'
    })
    await tenantsApi.delete(row.tenant_id)
    ElMessage.success(hasUsers ? '테넌트가 비활성화되었습니다' : '테넌트가 삭제되었습니다')
    await loadTenants()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// 메타데이터 보기
const viewMetadata = (row) => {
  selectedMetadata.value = row.metadata
  metadataDialogVisible.value = true
}

// 마운트
onMounted(() => {
  loadTenants()
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.tenants-view {
  .page-header {
    @include mx.page-header;
  }

  .toolbar {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
  }

  .flex-1 {
    flex: 1;
  }

  .action-cell {
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }

  .empty-state {
    @include mx.empty-state;
  }

  .form-help {
    @include mx.form-help;
  }

  .metadata-viewer {
    background-color: var(--bg-color-hover);
    padding: 16px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.6;
    overflow-x: auto;
    max-height: 400px;
  }
}
</style>
