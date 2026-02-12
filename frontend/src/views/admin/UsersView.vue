<template>
  <div class="users-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>사용자 관리</h2>
        <p class="subtitle">사용자 계정을 생성, 수정, 삭제하고 역할을 할당합니다.</p>
      </div>
    </div>

    <div class="content-card">
      <!-- 필터 + 액션 -->
      <div class="toolbar">
        <el-input
          v-model="searchKeyword"
          placeholder="이름 또는 로그인ID 검색"
          :prefix-icon="Search"
          clearable
          style="width: 220px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-select
          v-model="filterActive"
          placeholder="상태 필터"
          clearable
          style="width: 140px"
          @change="handleSearch"
        >
          <el-option label="활성" :value="true" />
          <el-option label="비활성" :value="false" />
        </el-select>
        <el-button :icon="Refresh" @click="resetFilters">필터 초기화</el-button>
        <div class="flex-1" />
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">새 사용자</el-button>
      </div>

      <!-- 사용자 테이블 -->
      <el-table
        v-loading="isLoading"
        :data="users"
        style="width: 100%; margin-top: 16px"
        :default-sort="{ prop: 'user_id', order: 'ascending' }"
      >
        <el-table-column prop="user_id" label="ID" width="60" sortable />

        <el-table-column prop="login_id" label="로그인 ID" min-width="110" sortable />

        <el-table-column prop="display_name" label="이름" min-width="130">
          <template #default="{ row }">
            <span class="name-cell">
              <span>{{ row.display_name || '-' }}</span>
              <el-tag v-if="row.is_superuser" type="danger" size="small">SU</el-tag>
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="email" label="이메일" min-width="170" show-overflow-tooltip />

        <el-table-column label="역할" min-width="130">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role.role_id"
              :type="scopeTagType(role.scope_type)"
              size="small"
              style="margin-right: 4px; margin-bottom: 2px"
            >
              {{ role.role_name }}
            </el-tag>
            <span v-if="!row.roles?.length" style="color: var(--text-color-secondary)">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="tenant_name" label="테넌트" min-width="90">
          <template #default="{ row }">
            {{ row.tenant_name || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="상태" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '활성' : '비활성' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="last_login_at" label="최근 로그인" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_login_at) }}
          </template>
        </el-table-column>

        <el-table-column label="동작" width="120" fixed="right">
          <template #default="{ row }">
            <span class="action-cell">
              <el-button link type="primary" size="small" :icon="Edit" @click="openEditDialog(row)">수정</el-button>
              <el-button link type="danger" size="small" :icon="Delete" @click="handleDelete(row)" :disabled="row.is_superuser">삭제</el-button>
            </span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 빈 상태 -->
      <div v-if="users.length === 0 && !isLoading" class="empty-state">
        <p>등록된 사용자가 없습니다.</p>
      </div>

      <!-- 페이지네이션 -->
      <div class="pagination-wrapper">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 사용자 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '새 사용자 추가' : '사용자 수정'"
      width="560px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
        autocomplete="off"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="로그인 ID" prop="login_id">
              <el-input
                v-model="formData.login_id"
                placeholder="영문, 숫자, 5자 이상"
                :disabled="dialogMode === 'edit'"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="이름" prop="display_name">
              <el-input v-model="formData.display_name" placeholder="표시 이름" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="이메일" prop="email">
          <el-input v-model="formData.email" placeholder="user@example.com" autocomplete="off" />
        </el-form-item>

        <el-form-item v-if="dialogMode === 'create'" label="비밀번호" prop="password">
          <el-input v-model="formData.password" type="password" show-password placeholder="8자 이상 (대소문자, 숫자 포함)" autocomplete="new-password" />
        </el-form-item>

        <el-form-item label="역할" prop="role_ids">
          <el-select
            v-model="formData.role_ids"
            multiple
            placeholder="역할을 선택하세요"
            style="width: 100%"
          >
            <el-option
              v-for="role in allRoles"
              :key="role.role_id"
              :label="`${role.role_name} (${role.scope_type})`"
              :value="role.role_id"
            />
          </el-select>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="테넌트" prop="tenant_id">
              <el-select
                v-model="formData.tenant_id"
                placeholder="테넌트 선택 (선택)"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="t in allTenants"
                  :key="t.tenant_id"
                  :label="t.tenant_name"
                  :value="t.tenant_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="활성화 여부">
              <el-switch v-model="formData.is_active" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete, Search } from '@element-plus/icons-vue'
import usersApi from '@/api/users'
import tenantsApi from '@/api/tenants'
import { formatDateTime } from '@/utils/format'

// 상태
const isLoading = ref(false)
const isSaving = ref(false)
const users = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const filterActive = ref(null)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref(null)
const currentUserId = ref(null)

// 역할/테넌트 목록 (다이얼로그 셀렉트 용)
const allRoles = ref([])
const allTenants = ref([])

// 폼 데이터
const formData = reactive({
  login_id: '',
  email: '',
  display_name: '',
  password: '',
  tenant_id: null,
  is_active: true,
  role_ids: []
})

// 폼 검증 규칙
const formRules = {
  login_id: [
    { required: true, message: '로그인 ID를 입력하세요', trigger: 'blur' },
    { min: 3, message: '3자 이상 입력하세요', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '이메일을 입력하세요', trigger: 'blur' },
    { type: 'email', message: '올바른 이메일 형식이 아닙니다', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '이름을 입력하세요', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '비밀번호를 입력하세요', trigger: 'blur' },
    { min: 8, message: '8자 이상 입력하세요', trigger: 'blur' }
  ]
}

// scope_type에 따른 태그 색상
const scopeTagType = (scope) => {
  if (scope === 'GLOBAL') return 'danger'
  if (scope === 'TENANT') return 'warning'
  return 'info'
}

// 사용자 목록 로드
const loadUsers = async () => {
  isLoading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    }
    if (filterActive.value !== null) params.is_active = filterActive.value
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim()
    const result = await usersApi.list(params)
    users.value = result.items || []
    total.value = result.total || 0
  } catch (error) {
    ElMessage.error('사용자 목록 로드 실패')
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

// 역할 목록 로드
const loadRoles = async () => {
  try {
    const result = await usersApi.listRoles()
    allRoles.value = result.items || []
  } catch (error) {
    console.error('역할 목록 로드 실패:', error)
  }
}

// 테넌트 목록 로드
const loadTenants = async () => {
  try {
    const result = await tenantsApi.list()
    allTenants.value = result.items || result || []
  } catch {
    allTenants.value = []
  }
}

// 검색
const handleSearch = () => {
  currentPage.value = 1
  loadUsers()
}

// 필터 초기화
const resetFilters = () => {
  searchKeyword.value = ''
  filterActive.value = null
  currentPage.value = 1
  loadUsers()
}

// 페이지 변경
const handlePageChange = (page) => {
  currentPage.value = page
  loadUsers()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadUsers()
}

// 생성 다이얼로그 열기
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentUserId.value = null
  resetForm()
  dialogVisible.value = true
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 수정 다이얼로그 열기
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentUserId.value = row.user_id
  formData.login_id = row.login_id
  formData.email = row.email
  formData.display_name = row.display_name || ''
  formData.tenant_id = row.tenant_id
  formData.is_active = row.is_active
  formData.role_ids = (row.roles || []).map(r => r.role_id)
  formData.password = ''
  dialogVisible.value = true
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 폼 초기화
const resetForm = () => {
  formData.login_id = ''
  formData.email = ''
  formData.display_name = ''
  formData.password = ''
  formData.tenant_id = null
  formData.is_active = true
  formData.role_ids = []
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
      await usersApi.create({
        login_id: formData.login_id,
        email: formData.email,
        display_name: formData.display_name,
        password: formData.password,
        tenant_id: formData.tenant_id,
        is_active: formData.is_active,
        role_ids: formData.role_ids
      })
      ElMessage.success('사용자가 생성되었습니다')
    } else {
      await usersApi.update(currentUserId.value, {
        email: formData.email,
        display_name: formData.display_name,
        tenant_id: formData.tenant_id,
        is_active: formData.is_active
      })
      // 역할이 변경된 경우 별도 할당
      if (formData.role_ids.length > 0) {
        await usersApi.assignRoles(currentUserId.value, formData.role_ids)
      }
      ElMessage.success('사용자가 수정되었습니다')
    }
    dialogVisible.value = false
    await loadUsers()
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
    console.error(error)
  } finally {
    isSaving.value = false
  }
}

// 삭제 처리
const handleDelete = async (row) => {
  if (row.is_superuser) {
    ElMessage.warning('슈퍼유저는 삭제할 수 없습니다')
    return
  }
  try {
    await ElMessageBox.confirm(
      `"${row.display_name || row.login_id}" 사용자를 삭제하시겠습니까?`,
      '사용자 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await usersApi.delete(row.user_id)
    ElMessage.success('사용자가 삭제되었습니다')
    await loadUsers()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
    console.error(error)
  }
}

// 마운트
onMounted(async () => {
  await Promise.all([loadUsers(), loadRoles(), loadTenants()])
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.users-view {
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

  .name-cell {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;
  }

  .action-cell {
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }

  .empty-state {
    @include mx.empty-state;
  }

  .pagination-wrapper {
    @include mx.pagination-wrapper;
  }
}
</style>
