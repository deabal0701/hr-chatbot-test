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

        <el-table-column prop="scope_level" label="Scope" width="130" align="center" sortable>
          <template #default="{ row }">
            <el-tag :type="scopeLevelTag(row.scope_level)" size="small">{{ scopeLevelLabel(row.scope_level) }}</el-tag>
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

        <el-form-item label="Scope" prop="scope_level">
          <el-select v-model="formData.scope_level" style="width: 100%">
            <el-option :value="0" label="GLOBAL(전체) - 모든 데이터 접근" />
            <el-option :value="1" label="TENANT(테넌트) - 소속 테넌트" />
            <el-option :value="2" label="DEPT(부서) - 소속 부서 + 하위" />
            <el-option :value="3" label="USER(본인) - 본인만" />
          </el-select>
          <div class="form-help">역할에 할당된 사용자가 접근할 수 있는 데이터 범위</div>
        </el-form-item>

        <el-form-item label="랜딩 페이지" prop="landing_page">
          <el-select v-model="formData.landing_page" style="width: 100%">
            <el-option label="/admin/dashboard" value="/admin/dashboard" />
            <el-option label="/admin/chat" value="/admin/chat" />
            <el-option label="/chat" value="/chat" />
          </el-select>
        </el-form-item>
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
        :row-class-name="({ row }) => row.is_directory ? 'directory-row' : ''"
      >
        <el-table-column prop="menu_name" label="메뉴명" min-width="140">
          <template #default="{ row }">
            <span :style="{
              paddingLeft: ((row.depth || 0) - 1) * 20 + 'px',
              fontWeight: row.is_directory ? 'bold' : 'normal'
            }">{{ row.menu_name }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="menu_code" label="코드" width="130" />

        <el-table-column prop="menu_type" label="유형" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.menu_type === 'PAGE' ? '' : row.menu_type === 'DIRECTORY' ? 'info' : 'warning'" size="small">
              {{ row.menu_type }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="조회" width="60" align="center">
          <template #default="{ row }">
            <span v-if="row.is_directory" class="dir-placeholder">—</span>
            <el-icon v-else-if="row.can_read" class="perm-check"><Check /></el-icon>
            <el-icon v-else class="perm-close"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="생성" width="60" align="center">
          <template #default="{ row }">
            <span v-if="row.is_directory" class="dir-placeholder">—</span>
            <el-icon v-else-if="row.can_create" class="perm-check"><Check /></el-icon>
            <el-icon v-else class="perm-close"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="수정" width="60" align="center">
          <template #default="{ row }">
            <span v-if="row.is_directory" class="dir-placeholder">—</span>
            <el-icon v-else-if="row.can_update" class="perm-check"><Check /></el-icon>
            <el-icon v-else class="perm-close"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="삭제" width="60" align="center">
          <template #default="{ row }">
            <span v-if="row.is_directory" class="dir-placeholder">—</span>
            <el-icon v-else-if="row.can_delete" class="perm-check"><Check /></el-icon>
            <el-icon v-else class="perm-close"><Close /></el-icon>
          </template>
        </el-table-column>

        <el-table-column label="내보내기" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.is_directory" class="dir-placeholder">—</span>
            <el-icon v-else-if="row.can_export" class="perm-check"><Check /></el-icon>
            <el-icon v-else class="perm-close"><Close /></el-icon>
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
import { getErrorMessage } from '@/utils/error'

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
  landing_page: '/chat',
  scope_level: 3
})

// 폼 검증 규칙
const formRules = {
  role_code: [
    { required: true, message: '역할 코드를 입력하세요', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '영문 대문자, 숫자, _ 만 사용 가능합니다', trigger: 'blur' }
  ],
  role_name: [
    { required: true, message: '역할명을 입력하세요', trigger: 'blur' }
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
  resetForm()
  dialogVisible.value = true
}

// 수정 다이얼로그
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentRoleId.value = row.role_id

  formData.role_code = row.role_code
  formData.role_name = row.role_name
  formData.description = row.description || ''
  formData.landing_page = row.landing_page || '/chat'
  formData.scope_level = row.scope_level ?? 3
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
  formData.landing_page = '/chat'
  formData.scope_level = 3
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
        landing_page: formData.landing_page,
        scope_level: formData.scope_level
      })
      ElMessage.success('역할이 생성되었습니다')
    } else {
      await rolesApi.update(currentRoleId.value, {
        role_name: formData.role_name,
        description: formData.description || undefined,
        landing_page: formData.landing_page,
        scope_level: formData.scope_level
      })
      ElMessage.success('역할이 수정되었습니다')
    }
    dialogVisible.value = false
    await loadRoles()
  } catch (error) {
    const msg = getErrorMessage(error, '역할 저장에 실패하였습니다')
    if (msg) ElMessage.error(msg)
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
    const msg = getErrorMessage(error, '역할 삭제에 실패하였습니다')
    if (msg) ElMessage.error(msg)
  }
}

// 기본 메뉴 권한 보기
const openDefaultMenus = async (row) => {
  menuDialogRole.value = `${row.role_name} (${row.role_code})`
  menuDialogVisible.value = true
  isLoadingMenus.value = true

  try {
    const response = await rolesApi.getDefaultMenus(row.role_code)
    defaultMenus.value = response?.items || []
  } catch {
    ElMessage.error('기본 메뉴 권한 조회 실패')
    defaultMenus.value = []
  } finally {
    isLoadingMenus.value = false
  }
}

// scope_level 표시 헬퍼 (시스템 상수 — Role과 무관)
const SCOPE_LABELS = { 0: 'GLOBAL', 1: 'TENANT', 2: 'DEPT', 3: 'USER' }
const SCOPE_TAGS = { 0: 'danger', 1: 'warning', 2: '', 3: 'info' }
const scopeLevelLabel = (level) => SCOPE_LABELS[level] ?? `Level ${level}`
const scopeLevelTag = (level) => SCOPE_TAGS[level] ?? 'info'

// 마운트
onMounted(() => {
  loadRoles()
})
</script>

<style lang="scss" scoped>
.roles-view {
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

  .menu-dialog-desc {
    margin: 0 0 12px;
    color: var(--text-color-secondary);
    font-size: 13px;
  }

  .perm-check {
    color: var(--color-success);
  }

  .perm-close {
    color: var(--text-color-placeholder);
  }

  .dir-placeholder {
    color: var(--el-text-color-placeholder);
  }

  :deep(.directory-row) {
    background-color: var(--el-fill-color-light);
  }
}
</style>
