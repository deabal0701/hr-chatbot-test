<template>
  <div class="menus-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>메뉴 관리</h2>
        <p class="subtitle">메뉴 트리를 관리하고 권한을 설정합니다.</p>
      </div>
    </div>

    <div class="content-card">
      <!-- 툴바 -->
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">새 메뉴 추가</el-button>
        <el-button @click="toggleExpandAll">
          {{ expandAll ? '전체 접기' : '전체 펼치기' }}
        </el-button>
        <el-button :icon="Refresh" @click="loadMenuTree" :loading="isLoading">새로고침</el-button>
      </div>

      <!-- 메뉴 트리 테이블 -->
      <el-table
        :key="tableKey"
        v-loading="isLoading"
        :data="menuTree"
        row-key="menu_id"
        :tree-props="{ children: 'children' }"
        :default-expand-all="expandAll"
        style="width: 100%; margin-top: 16px"
      >
        <el-table-column prop="menu_name" label="메뉴명" min-width="180" />

        <el-table-column prop="menu_code" label="코드" min-width="130" show-overflow-tooltip />

        <el-table-column prop="menu_type" label="타입" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="menuTypeTag(row.menu_type)" size="small">
              {{ menuTypeLabel(row.menu_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="경로" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.menu_path || row.api_pattern || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="icon" label="아이콘" width="80" align="center">
          <template #default="{ row }">
            <span v-if="row.icon" class="icon-text">{{ row.icon }}</span>
            <span v-else class="text-secondary">-</span>
          </template>
        </el-table-column>

        <el-table-column prop="sort_order" label="순서" width="60" align="center" />

        <el-table-column prop="is_active" label="상태" width="70" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '활성' : '비활성' }}
            </el-tag>
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
      <div v-if="menuTree.length === 0 && !isLoading" class="empty-state">
        <p>등록된 메뉴가 없습니다.</p>
      </div>
    </div>

    <!-- 메뉴 생성/수정 다이얼로그 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '새 메뉴 추가' : '메뉴 수정'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-position="top"
      >
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="메뉴 코드" prop="menu_code">
              <el-input
                v-model="formData.menu_code"
                placeholder="영문 대문자, 숫자, _"
                :disabled="dialogMode === 'edit'"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="메뉴명" prop="menu_name">
              <el-input v-model="formData.menu_name" placeholder="메뉴 표시명" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="메뉴 타입" prop="menu_type">
              <el-select
                v-model="formData.menu_type"
                placeholder="타입 선택"
                style="width: 100%"
                :disabled="dialogMode === 'edit'"
              >
                <el-option label="폴더 (DIRECTORY)" value="DIRECTORY" />
                <el-option label="화면 (PAGE)" value="PAGE" />
                <el-option label="API" value="API" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="상위 메뉴" prop="parent_menu_id">
              <el-tree-select
                v-model="formData.parent_menu_id"
                :data="parentMenuOptions"
                node-key="menu_id"
                :props="{ label: 'menu_name', children: 'children' }"
                placeholder="최상위 (루트)"
                clearable
                :render-after-expand="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="formData.menu_type === 'PAGE'" label="프론트엔드 경로" prop="menu_path">
          <el-input v-model="formData.menu_path" placeholder="/admin/example" />
          <div class="form-help">프론트엔드 라우트 경로 (PAGE 타입)</div>
        </el-form-item>

        <el-form-item v-if="formData.menu_type === 'API'" label="API 경로 패턴" prop="api_pattern">
          <el-input v-model="formData.api_pattern" placeholder="/api/admin/v1/example" />
          <div class="form-help">API 접근 제어용 경로 패턴 (API 타입)</div>
        </el-form-item>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="아이콘" prop="icon">
              <el-select
                v-model="formData.icon"
                placeholder="선택"
                clearable
                style="width: 100%"
              >
                <el-option
                  v-for="opt in iconOptions"
                  :key="opt"
                  :label="opt"
                  :value="opt"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="정렬 순서" prop="sort_order">
              <el-input-number
                v-model="formData.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="활성화">
              <el-switch v-model="formData.is_active" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="설명" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="메뉴 설명 (선택)"
          />
        </el-form-item>
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Edit, Delete } from '@element-plus/icons-vue'
import menusApi from '@/api/menus'

// 상태
const isLoading = ref(false)
const isSaving = ref(false)
const menuTree = ref([])
const dialogVisible = ref(false)
const dialogMode = ref('create')
const formRef = ref(null)
const currentMenuId = ref(null)
const expandAll = ref(true)
const tableKey = ref(0)

// 아이콘 옵션 (AppSidebar ICON_MAP 키와 동기화)
const iconOptions = [
  'dashboard', 'chat', 'document', 'users', 'menu',
  'role', 'tenant', 'settings', 'code', 'history',
  'search', 'folder'
]

// 폼 데이터
const formData = reactive({
  menu_code: '',
  menu_name: '',
  menu_type: 'PAGE',
  parent_menu_id: null,
  menu_path: '',
  api_pattern: '',
  icon: '',
  sort_order: 0,
  is_active: true,
  description: ''
})

// 폼 검증 규칙
const formRules = {
  menu_code: [
    { required: true, message: '메뉴 코드를 입력하세요', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '영문 대문자, 숫자, _ 만 사용 가능', trigger: 'blur' }
  ],
  menu_name: [
    { required: true, message: '메뉴명을 입력하세요', trigger: 'blur' }
  ],
  menu_type: [
    { required: true, message: '메뉴 타입을 선택하세요', trigger: 'change' }
  ]
}

// 메뉴 타입 태그 색상
const menuTypeTag = (type) => {
  if (type === 'DIRECTORY') return 'warning'
  if (type === 'PAGE') return 'success'
  return 'info'
}

// 메뉴 타입 라벨
const menuTypeLabel = (type) => {
  if (type === 'DIRECTORY') return '폴더'
  if (type === 'PAGE') return '화면'
  return 'API'
}

// 트리에서 특정 menu_id와 그 하위를 제외 (순환 참조 방지)
const filterMenuTree = (items, excludeId) => {
  return items
    .filter(item => item.menu_id !== excludeId)
    .map(item => ({
      ...item,
      children: item.children?.length
        ? filterMenuTree(item.children, excludeId)
        : []
    }))
}

// 상위 메뉴 선택 옵션 (수정 시 자기 자신과 하위 제외)
const parentMenuOptions = computed(() => {
  if (!currentMenuId.value) return menuTree.value
  return filterMenuTree(menuTree.value, currentMenuId.value)
})

// 전체 펼치기/접기 토글
const toggleExpandAll = () => {
  expandAll.value = !expandAll.value
  tableKey.value++
}

// 메뉴 트리 로드
const loadMenuTree = async () => {
  isLoading.value = true
  try {
    const result = await menusApi.getTree()
    menuTree.value = result.items || []
  } catch {
    ElMessage.error('메뉴 트리 로드 실패')
  } finally {
    isLoading.value = false
  }
}

// 생성 다이얼로그 열기
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentMenuId.value = null
  resetForm()
  dialogVisible.value = true
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 수정 다이얼로그 열기
const openEditDialog = (row) => {
  dialogMode.value = 'edit'
  currentMenuId.value = row.menu_id
  formData.menu_code = row.menu_code
  formData.menu_name = row.menu_name
  formData.menu_type = row.menu_type
  formData.parent_menu_id = row.parent_menu_id
  formData.menu_path = row.menu_path || ''
  formData.api_pattern = row.api_pattern || ''
  formData.icon = row.icon || ''
  formData.sort_order = row.sort_order
  formData.is_active = row.is_active
  formData.description = row.description || ''
  dialogVisible.value = true
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 폼 초기화
const resetForm = () => {
  formData.menu_code = ''
  formData.menu_name = ''
  formData.menu_type = 'PAGE'
  formData.parent_menu_id = null
  formData.menu_path = ''
  formData.api_pattern = ''
  formData.icon = ''
  formData.sort_order = 0
  formData.is_active = true
  formData.description = ''
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
      await menusApi.create({
        menu_code: formData.menu_code,
        menu_name: formData.menu_name,
        menu_type: formData.menu_type,
        parent_menu_id: formData.parent_menu_id,
        menu_path: formData.menu_type === 'PAGE' ? formData.menu_path : null,
        api_pattern: formData.menu_type === 'API' ? formData.api_pattern : null,
        icon: formData.icon || null,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        description: formData.description || null
      })
      ElMessage.success('메뉴가 생성되었습니다')
    } else {
      await menusApi.update(currentMenuId.value, {
        menu_name: formData.menu_name,
        menu_path: formData.menu_type === 'PAGE' ? formData.menu_path : null,
        api_pattern: formData.menu_type === 'API' ? formData.api_pattern : null,
        icon: formData.icon || null,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        description: formData.description || null
      })
      ElMessage.success('메뉴가 수정되었습니다')
    }
    dialogVisible.value = false
    await loadMenuTree()
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
  } finally {
    isSaving.value = false
  }
}

// 삭제 처리
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `"${row.menu_name}" 메뉴를 삭제하시겠습니까?`,
      '메뉴 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await menusApi.delete(row.menu_id)
    ElMessage.success('메뉴가 삭제되었습니다')
    await loadMenuTree()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// 마운트
onMounted(() => {
  loadMenuTree()
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.menus-view {
  .page-header {
    @include mx.page-header;
  }

  .toolbar {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .action-cell {
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
  }

  .icon-text {
    font-size: 12px;
    color: var(--text-color-secondary);
  }

  .text-secondary {
    color: var(--text-color-secondary);
  }

  .empty-state {
    @include mx.empty-state;
  }

  .form-help {
    @include mx.form-help;
  }
}
</style>
