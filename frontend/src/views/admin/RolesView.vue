<template>
  <div class="roles-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>역할 관리</h2>
        <p class="subtitle">역할을 생성, 수정하고 기본 메뉴 권한 템플릿을 확인합니다.</p>
      </div>
    </div>

    <div class="content-card">
      <!-- 툴바 -->
      <div class="toolbar">
        <el-button :icon="Refresh" @click="loadRoles" :loading="isLoading">새로고침</el-button>
        <div class="flex-1" />
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">새 역할</el-button>
      </div>

      <!-- 역할 테이블 -->
      <el-table
        v-loading="isLoading"
        :data="roles"
        style="width: 100%; margin-top: 16px"
        :default-sort="{ prop: 'sort_order', order: 'ascending' }"
      >
        <el-table-column prop="role_code" label="역할 코드" min-width="180" sortable>
          <template #default="{ row }">
            <span>{{ row.role_code }}</span>
            <el-tag v-if="row.is_system" type="info" size="small" style="margin-left: 6px">시스템</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="role_name" label="역할명" width="120" sortable />

        <el-table-column prop="scope_type" label="데이터 범위" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="scopeTagType(row.scope_type)" size="small">
              {{ scopeLabel(row.scope_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="landing_page" label="랜딩 페이지" width="150" show-overflow-tooltip />

        <el-table-column prop="user_count" label="사용자수" width="120" align="center" sortable>
          <template #default="{ row }">
            <el-tag size="small" :type="row.user_count > 0 ? '' : 'info'">{{ row.user_count }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="설명" min-width="160" show-overflow-tooltip />

        <el-table-column label="동작" width="190" align="center">
          <template #default="{ row }">
            <span class="action-cell">
              <el-button link type="primary" size="small" :icon="View" @click="openDefaultMenus(row)">메뉴</el-button>
              <el-button link type="primary" size="small" :icon="Edit" @click="openEditDialog(row)">수정</el-button>
              <el-button link type="danger" size="small" :icon="Delete" @click="handleDelete(row)" :disabled="row.is_system">삭제</el-button>
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 빈 상태 -->
      <div v-if="roles.length === 0 && !isLoading" class="empty-state">
        <p>등록된 역할이 없습니다.</p>
      </div>
    </div>

    <!-- 역할 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '새 역할 추가' : '역할 수정'"
      width="560px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
      >
        <el-form-item label="역할 코드" prop="role_code">
          <el-input
            v-model="formData.role_code"
            placeholder="예: MANAGER"
            :disabled="dialogMode === 'edit'"
          />
          <div class="form-help">영문 대문자, 숫자, _ 만 사용 (생성 후 변경 불가)</div>
        </el-form-item>

        <el-form-item label="역할명" prop="role_name">
          <el-input v-model="formData.role_name" placeholder="예: 매니저" />
        </el-form-item>

        <el-form-item label="설명" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="역할에 대한 설명 (선택사항)"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="데이터 범위" prop="scope_type">
              <el-select
                v-model="formData.scope_type"
                placeholder="범위 선택"
                style="width: 100%"
                :disabled="isSystemRole"
              >
                <el-option label="전체 (GLOBAL)" value="GLOBAL" />
                <el-option label="테넌트 (TENANT)" value="TENANT" />
                <el-option label="본인 (USER)" value="USER" />
              </el-select>
              <div v-if="isSystemRole" class="form-help">시스템 역할의 범위는 변경할 수 없습니다</div>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="랜딩 페이지" prop="landing_page">
              <el-select v-model="formData.landing_page" style="width: 100%">
                <el-option label="/admin/dashboard" value="/admin/dashboard" />
                <el-option label="/admin/chat" value="/admin/chat" />
                <el-option label="/chat" value="/chat" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">취소</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="isSaving">
          {{ dialogMode === 'create' ? '생성' : '수정' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 기본 메뉴 권한 다이얼로그 -->
    <el-dialog
      v-model="menuDialogVisible"
      :title="`기본 메뉴 권한 — ${menuDialogRole}`"
      width="780px"
    >
      <p class="menu-dialog-desc">이 역할로 사용자를 생성할 때 자동으로 할당되는 기본 메뉴 권한입니다.</p>

      <el-table
        v-loading="isLoadingMenus"
        :data="defaultMenus"
        style="width: 100%"
        size="small"
      >
        <el-table-column prop="menu_name" label="메뉴명" min-width="140">
          <template #default="{ row }">
            <span :style="{ paddingLeft: (row.depth || 0) * 16 + 'px' }">{{ row.menu_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="menu_code" label="코드" width="130" />

        <el-table-column prop="menu_type" label="유형" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.menu_type === 'PAGE' ? '' : 'warning'" size="small">
              {{ row.menu_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="조회" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.can_read" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#dcdfe6"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="생성" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.can_create" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#dcdfe6"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="수정" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.can_update" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#dcdfe6"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="삭제" width="60" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.can_delete" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#dcdfe6"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="내보내기" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.can_export" color="#67c23a"><Check /></el-icon>
            <el-icon v-else color="#dcdfe6"><Close /></el-icon>
          </template>
        </el-table-column>
      </el-table>

      <template #footer>
        <el-button @click="menuDialogVisible = false">닫기</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete, View, Check, Close } from '@element-plus/icons-vue'
import rolesApi from '@/api/roles'

// 상태
const isLoading = ref(false)
const isSaving = ref(false)
const roles = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref(null)
const currentRoleId = ref(null)

// 기본 메뉴 다이얼로그
const menuDialogVisible = ref(false)
const menuDialogRole = ref('')
const isLoadingMenus = ref(false)
const defaultMenus = ref([])

// 폼 데이터
const formData = reactive({
  role_code: '',
  role_name: '',
  description: '',
  scope_type: 'USER',
  landing_page: '/chat'
})

// 시스템 역할 여부 (수정 시)
const isSystemRole = ref(false)

// scope_type 라벨 및 태그 타입
const scopeLabel = (scope) => {
  const labels = { GLOBAL: '전체', TENANT: '테넌트', USER: '본인' }
  return labels[scope] || scope
}

const scopeTagType = (scope) => {
  const types = { GLOBAL: 'danger', TENANT: 'warning', USER: '' }
  return types[scope] || 'info'
}

// 폼 검증 규칙
const formRules = {
  role_code: [
    { required: true, message: '역할 코드를 입력하세요', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '영문 대문자, 숫자, _ 만 사용 가능합니다', trigger: 'blur' }
  ],
  role_name: [
    { required: true, message: '역할명을 입력하세요', trigger: 'blur' }
  ],
  scope_type: [
    { required: true, message: '데이터 범위를 선택하세요', trigger: 'change' }
  ]
}

// 역할 목록 로드
const loadRoles = async () => {
  isLoading.value = true
  try {
    const result = await rolesApi.list()
    roles.value = result.items || []
  } catch {
    ElMessage.error('역할 목록 로드 실패')
  } finally {
    isLoading.value = false
  }
}

// 생성 다이얼로그
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentRoleId.value = null
  isSystemRole.value = false
  resetForm()
  dialogVisible.value = true
}

// 수정 다이얼로그
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentRoleId.value = row.role_id
  isSystemRole.value = row.is_system

  formData.role_code = row.role_code
  formData.role_name = row.role_name
  formData.description = row.description || ''
  formData.scope_type = row.scope_type
  formData.landing_page = row.landing_page || '/chat'
  dialogVisible.value = true

  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 폼 초기화
const resetForm = () => {
  formData.role_code = ''
  formData.role_name = ''
  formData.description = ''
  formData.scope_type = 'USER'
  formData.landing_page = '/chat'
  if (formRef.value) formRef.value.clearValidate()
}

// 폼 제출
const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  isSaving.value = true
  try {
    if (dialogMode.value === 'create') {
      await rolesApi.create({
        role_code: formData.role_code,
        role_name: formData.role_name,
        description: formData.description || undefined,
        scope_type: formData.scope_type,
        landing_page: formData.landing_page
      })
      ElMessage.success('역할이 생성되었습니다')
    } else {
      await rolesApi.update(currentRoleId.value, {
        role_name: formData.role_name,
        description: formData.description || undefined,
        scope_type: isSystemRole.value ? undefined : formData.scope_type,
        landing_page: formData.landing_page
      })
      ElMessage.success('역할이 수정되었습니다')
    }
    dialogVisible.value = false
    await loadRoles()
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
  } finally {
    isSaving.value = false
  }
}

// 삭제 처리
const handleDelete = async (row) => {
  if (row.is_system) {
    ElMessage.warning('시스템 기본 역할은 삭제할 수 없습니다')
    return
  }
  if (row.user_count > 0) {
    ElMessage.warning(`이 역할에 ${row.user_count}명의 사용자가 할당되어 있습니다. 먼저 사용자의 역할을 변경하세요.`)
    return
  }

  try {
    await ElMessageBox.confirm(
      `"${row.role_name}" 역할을 삭제하시겠습니까?`,
      '역할 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await rolesApi.delete(row.role_id)
    ElMessage.success('역할이 삭제되었습니다')
    await loadRoles()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// 기본 메뉴 권한 보기
const openDefaultMenus = async (row) => {
  menuDialogRole.value = `${row.role_name} (${row.role_code})`
  menuDialogVisible.value = true
  isLoadingMenus.value = true

  try {
    const menus = await rolesApi.getDefaultMenus(row.role_code)
    defaultMenus.value = menus || []
  } catch {
    ElMessage.error('기본 메뉴 권한 조회 실패')
    defaultMenus.value = []
  } finally {
    isLoadingMenus.value = false
  }
}

// 마운트
onMounted(() => {
  loadRoles()
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.roles-view {
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

  .menu-dialog-desc {
    margin: 0 0 12px;
    color: var(--text-color-secondary);
    font-size: 13px;
  }
}
</style>
