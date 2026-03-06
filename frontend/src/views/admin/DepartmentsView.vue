<template>
  <div class="departments-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>조직 관리</h2>
        <p class="subtitle">부서 트리를 관리하고 조직 구조를 설정합니다.</p>
      </div>
      <!-- GLOBAL 사용자: 테넌트 필터 -->
      <el-select
        v-if="isGlobal"
        v-model="selectedTenantId"
        placeholder="테넌트 선택"
        clearable
        style="width: 200px"
        @change="handleTenantChange"
      >
        <el-option
          v-for="t in tenantOptions"
          :key="t.tenant_id"
          :label="t.tenant_name"
          :value="t.tenant_id"
        />
      </el-select>
    </div>

    <div class="dept-layout">
      <!-- 왼쪽: 부서 트리 패널 -->
      <div class="dept-tree-panel">
        <div class="panel-card content-card">
          <!-- 트리 툴바 -->
          <div class="tree-toolbar">
            <el-button type="primary" :icon="Plus" size="small" @click="handleAddRoot">추가</el-button>
            <div class="toolbar-spacer" />
            <el-button-group size="small">
              <el-tooltip content="모두 펼치기" placement="top" :show-after="400">
                <el-button :icon="ArrowDown" @click="handleExpandAll" />
              </el-tooltip>
              <el-tooltip content="모두 접기" placement="top" :show-after="400">
                <el-button :icon="ArrowUp" @click="handleCollapseAll" />
              </el-tooltip>
            </el-button-group>
            <el-tooltip content="새로고침" placement="top" :show-after="400">
              <el-button :icon="Refresh" size="small" circle @click="loadDeptTree" :loading="isLoading" />
            </el-tooltip>
          </div>
          <el-divider class="tree-divider" />

          <!-- 부서 트리 -->
          <el-tree
            :key="treeVersion"
            ref="treeRef"
            v-loading="isLoading"
            :data="deptTree"
            node-key="dept_id"
            :props="treeProps"
            draggable
            :allow-drop="handleAllowDrop"
            :allow-drag="handleAllowDrag"
            highlight-current
            :expand-on-click-node="false"
            default-expand-all
            @node-click="handleNodeClick"
            @node-drop="handleNodeDrop"
            @node-contextmenu="handleContextMenu"
          >
            <template #default="{ data }">
              <span
                class="tree-node"
                :class="{ 'is-inactive': !data.is_active }"
              >
                <el-icon class="node-icon" :size="14">
                  <OfficeBuilding />
                </el-icon>
                <span class="node-label">{{ data.dept_name }}</span>
                <el-tag size="small" type="info" class="node-count">{{ data.user_count ?? 0 }}명</el-tag>
                <el-tag v-if="!data.is_active" size="small" type="info" class="node-tag">비활성</el-tag>
                <el-button
                  class="node-add-btn"
                  :icon="Plus"
                  size="small"
                  link
                  @click.stop="handleAddChild(data)"
                />
              </span>
            </template>
          </el-tree>

          <!-- 빈 상태 -->
          <div v-if="deptTree.length === 0 && !isLoading" class="empty-state">
            등록된 부서가 없습니다.
          </div>
        </div>
      </div>

      <!-- 오른쪽: 상세설정 패널 -->
      <div class="dept-detail-panel">
        <div class="panel-card content-card">
          <!-- 미선택 상태 -->
          <div v-if="!panelMode" class="empty-state">
            <p class="empty-guide">왼쪽 트리에서 부서를 선택하거나<br/>[추가]를 클릭하세요</p>
          </div>

          <!-- 생성/수정 폼 -->
          <template v-else>
            <div class="panel-header">
              <h3>{{ panelMode === 'create' ? '새 부서 추가' : formData.dept_name }}</h3>
              <el-tag :type="panelMode === 'create' ? 'success' : 'primary'" size="small">
                {{ panelMode === 'create' ? '생성' : '수정' }}
              </el-tag>
            </div>

            <el-form
              ref="formRef"
              :model="formData"
              :rules="formRules"
              label-position="top"
              class="detail-form"
            >
              <el-row :gutter="16">
                <el-col :span="12">
                  <el-form-item label="부서 코드" prop="dept_code">
                    <el-input
                      v-model="formData.dept_code"
                      placeholder="영문 대문자, 숫자, _"
                      :disabled="panelMode === 'edit'"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="부서명" prop="dept_name">
                    <el-input v-model="formData.dept_name" placeholder="부서 표시명" />
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="상위 부서" prop="parent_dept_id">
                <el-tree-select
                  v-model="formData.parent_dept_id"
                  :data="parentDeptOptions"
                  node-key="dept_id"
                  :props="{ label: 'dept_name', children: 'children' }"
                  placeholder="최상위 (루트)"
                  clearable
                  check-strictly
                  :render-after-expand="false"
                  style="width: 100%"
                />
              </el-form-item>

              <el-row :gutter="16">
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
            </el-form>

            <div class="panel-actions">
              <el-button
                v-if="panelMode === 'edit'"
                type="danger"
                plain
                @click="handleDelete"
              >삭제</el-button>
              <div class="spacer" />
              <el-button v-if="panelMode === 'create'" @click="handleCancel">취소</el-button>
              <el-button type="primary" @click="handleSubmit" :loading="isSaving">
                {{ panelMode === 'create' ? '생성' : '저장' }}
              </el-button>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 우클릭 컨텍스트 메뉴 -->
    <div
      v-show="contextMenu.visible"
      ref="contextMenuRef"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
    >
      <div class="context-menu-item" @click="ctxAddChild">
        <el-icon><Plus /></el-icon>
        <span>하위 부서 추가</span>
      </div>
      <div class="context-menu-divider" />
      <div
        class="context-menu-item"
        :class="{ disabled: !canMoveUp }"
        @click="ctxMoveUp"
      >
        <el-icon><Top /></el-icon>
        <span>위로 이동</span>
      </div>
      <div
        class="context-menu-item"
        :class="{ disabled: !canMoveDown }"
        @click="ctxMoveDown"
      >
        <el-icon><Bottom /></el-icon>
        <span>아래로 이동</span>
      </div>
      <div class="context-menu-divider" />
      <div
        class="context-menu-item danger"
        :class="{ disabled: hasChildren }"
        @click="ctxDelete"
      >
        <el-icon><Delete /></el-icon>
        <span>삭제</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Delete, Top, Bottom,
  ArrowDown, ArrowUp, OfficeBuilding
} from '@element-plus/icons-vue'
import departmentsApi from '@/api/departments'
import usersApi from '@/api/users'
import { useAuth } from '@/composables/useAuth'
import { filterTree, flattenTree } from '@/composables/useTreeUtils'

const { roleCode, currentUser } = useAuth()

// ===== 상태 =====
const isLoading = ref(false)
const isSaving = ref(false)
const deptTree = ref([])
const treeVersion = ref(0)
const treeRef = ref(null)
const formRef = ref(null)
const contextMenuRef = ref(null)

// panelMode: null(미선택) | 'create' | 'edit'
const panelMode = ref(null)
const selectedDeptId = ref(null)

// 테넌트 필터 (GLOBAL 사용자용)
const tenantOptions = ref([])
const selectedTenantId = ref(null)

// 트리 props
const treeProps = { children: 'children', label: 'dept_name' }

// 폼 데이터
const formData = reactive({
  dept_code: '',
  dept_name: '',
  parent_dept_id: null,
  tenant_id: null,
  sort_order: 0,
  is_active: true,
})

// 폼 검증 규칙
const formRules = {
  dept_code: [
    { required: true, message: '부서 코드를 입력하세요', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '영문 대문자, 숫자, _ 만 사용 가능', trigger: 'blur' }
  ],
  dept_name: [
    { required: true, message: '부서명을 입력하세요', trigger: 'blur' }
  ]
}

// 우클릭 컨텍스트 메뉴
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  data: null,
  node: null
})

// ===== Computed =====

const isGlobal = computed(() => {
  return currentUser.value?.is_superuser || roleCode.value === 'GLOBAL'
})

// 생성 시 사용할 tenant_id (GLOBAL이면 선택된 테넌트, 아니면 본인 테넌트)
const currentTenantId = computed(() => {
  if (isGlobal.value) return selectedTenantId.value
  return currentUser.value?.tenant_id
})

// 트리에서 자기 자신과 하위 제외한 부서 목록 (상위 부서 선택용)
const parentDeptOptions = computed(() => {
  return filterTree(deptTree.value, selectedDeptId.value)
})

// 컨텍스트 메뉴: 위로 이동 가능 여부
const canMoveUp = computed(() => {
  if (!contextMenu.node) return false
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  return idx > 0
})

// 컨텍스트 메뉴: 아래로 이동 가능 여부
const canMoveDown = computed(() => {
  if (!contextMenu.node) return false
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  return idx >= 0 && idx < siblings.length - 1
})

// 컨텍스트 메뉴: 하위 부서 존재 여부
const hasChildren = computed(() => {
  if (!contextMenu.data) return false
  return (contextMenu.data.children?.length || 0) > 0
})

// ===== 부서 트리 로드 =====
const loadDeptTree = async () => {
  isLoading.value = true
  try {
    const params = {}
    if (selectedTenantId.value) params.tenant_id = selectedTenantId.value
    const result = await departmentsApi.getTree(params)
    deptTree.value = result.items || []
    treeVersion.value++
  } catch {
    ElMessage.error('부서 트리 로드 실패')
  } finally {
    isLoading.value = false
  }
}

// 테넌트 변경 시
const handleTenantChange = () => {
  panelMode.value = null
  selectedDeptId.value = null
  resetForm()
  loadDeptTree()
}

// 테넌트 옵션 로드 (GLOBAL용)
const loadTenantOptions = async () => {
  try {
    const result = await usersApi.getTenantOptions()
    tenantOptions.value = (result.items || []).filter(t => !t.is_system)
  } catch {
    // 무시 (GLOBAL이 아니면 호출하지 않음)
  }
}

// ===== 폼 초기화 =====
const resetForm = () => {
  formData.dept_code = ''
  formData.dept_name = ''
  formData.parent_dept_id = null
  formData.tenant_id = null
  formData.sort_order = 0
  formData.is_active = true
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

const fillForm = (data) => {
  formData.dept_code = data.dept_code
  formData.dept_name = data.dept_name
  formData.parent_dept_id = data.parent_dept_id
  formData.tenant_id = data.tenant_id
  formData.sort_order = data.sort_order
  formData.is_active = data.is_active
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// ===== 트리 이벤트 핸들러 =====

const handleNodeClick = (data) => {
  closeContextMenu()
  panelMode.value = 'edit'
  selectedDeptId.value = data.dept_id
  fillForm(data)
}

const handleAddRoot = () => {
  if (!currentTenantId.value) {
    ElMessage.warning('테넌트를 먼저 선택하세요')
    return
  }
  closeContextMenu()
  panelMode.value = 'create'
  selectedDeptId.value = null
  resetForm()
  formData.tenant_id = currentTenantId.value
  if (treeRef.value) treeRef.value.setCurrentKey(null)
}

const handleAddChild = (parentData) => {
  closeContextMenu()
  panelMode.value = 'create'
  selectedDeptId.value = null
  resetForm()
  formData.parent_dept_id = parentData.dept_id
  formData.tenant_id = parentData.tenant_id
  if (treeRef.value) treeRef.value.setCurrentKey(null)
}

const handleCancel = () => {
  panelMode.value = null
  selectedDeptId.value = null
  resetForm()
  if (treeRef.value) treeRef.value.setCurrentKey(null)
}

// ===== 폼 제출 (생성/수정) =====
const handleSubmit = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  isSaving.value = true
  try {
    if (panelMode.value === 'create') {
      const result = await departmentsApi.create({
        dept_code: formData.dept_code,
        dept_name: formData.dept_name,
        parent_dept_id: formData.parent_dept_id,
        tenant_id: formData.tenant_id,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
      })
      ElMessage.success('부서가 생성되었습니다')
      await loadDeptTree()
      const newId = result.dept_id
      if (newId) {
        nextTick(() => {
          if (treeRef.value) treeRef.value.setCurrentKey(newId)
          panelMode.value = 'edit'
          selectedDeptId.value = newId
          fillForm(result)
        })
      }
    } else {
      const payload = {
        dept_name: formData.dept_name,
        parent_dept_id: formData.parent_dept_id,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
      }
      await departmentsApi.update(selectedDeptId.value, payload)
      ElMessage.success('부서가 수정되었습니다')
      const savedId = selectedDeptId.value
      await loadDeptTree()
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(savedId)
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
  } finally {
    isSaving.value = false
  }
}

// ===== 삭제 =====
const handleDelete = async () => {
  if (!selectedDeptId.value) return
  try {
    await ElMessageBox.confirm(
      `"${formData.dept_name}" 부서를 삭제하시겠습니까?`,
      '부서 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await departmentsApi.delete(selectedDeptId.value)
    ElMessage.success('부서가 삭제되었습니다')
    panelMode.value = null
    selectedDeptId.value = null
    resetForm()
    await loadDeptTree()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// ===== 드래그앤드롭 =====

const handleAllowDrag = () => true

const handleAllowDrop = (draggingNode, dropNode, type) => {
  // 최대 depth 10 제한
  if (type === 'inner') {
    const targetDepth = (dropNode.data.depth || 0) + 1
    const draggingMaxDepth = getMaxChildDepth(draggingNode.data)
    if (targetDepth + draggingMaxDepth > 10) return false
  }
  return true
}

const getMaxChildDepth = (data) => {
  if (!data.children || data.children.length === 0) return 0
  let max = 0
  for (const child of data.children) {
    const d = 1 + getMaxChildDepth(child)
    if (d > max) max = d
  }
  return max
}


const handleNodeDrop = async (draggingNode, dropNode, dropType) => {
  try {
    const dragId = draggingNode.data.dept_id
    const dropId = dropNode.data.dept_id
    const oldParentId = draggingNode.data.parent_dept_id ?? null

    // 1. 새 parent_dept_id 결정
    let newParentId = null
    if (dropType === 'inner') {
      newParentId = dropId
    } else {
      newParentId = dropNode.data.parent_dept_id ?? null
    }

    const parentChanged = oldParentId !== newParentId

    // 2. parent 변경 시 update 호출
    if (parentChanged) {
      await departmentsApi.update(dragId, { parent_dept_id: newParentId })
    }

    // 3. 서버에서 최신 트리 조회
    const params = {}
    if (selectedTenantId.value) params.tenant_id = selectedTenantId.value
    const freshTree = await departmentsApi.getTree(params)
    const allDepts = flattenTree(freshTree.items || [])

    // 4. 새 부모의 형제 목록 (드래그 항목 제외)
    const siblings = allDepts
      .filter(d => (d.parent_dept_id ?? null) === newParentId && d.dept_id !== dragId)
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))

    // 5. 드롭 위치에 따라 삽입 인덱스 계산
    let insertIdx
    if (dropType === 'inner') {
      insertIdx = siblings.length
    } else {
      const dropIdx = siblings.findIndex(s => s.dept_id === dropId)
      insertIdx = dropIdx === -1
        ? siblings.length
        : dropType === 'before' ? dropIdx : dropIdx + 1
    }

    // 6. 드래그 항목을 계산된 위치에 삽입
    siblings.splice(insertIdx, 0, { dept_id: dragId })

    // 7. sort_order 일괄 업데이트
    const reorderItems = siblings.map((s, idx) => ({
      dept_id: s.dept_id,
      sort_order: idx + 1
    }))
    await departmentsApi.reorder(reorderItems)

    // 8. parent 변경 시 이전 부모의 남은 형제도 재정렬
    if (parentChanged) {
      const oldSiblings = allDepts
        .filter(d => (d.parent_dept_id ?? null) === oldParentId && d.dept_id !== dragId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      if (oldSiblings.length > 0) {
        const oldReorderItems = oldSiblings.map((s, idx) => ({
          dept_id: s.dept_id,
          sort_order: idx + 1
        }))
        await departmentsApi.reorder(oldReorderItems)
      }
    }

    // 9. 트리 리로드
    await loadDeptTree()

    if (selectedDeptId.value === dragId) {
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(dragId)
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '부서 이동 실패')
    await loadDeptTree()
  }
}

// ===== 펼치기/접기 =====
const handleExpandAll = () => setAllExpanded(true)
const handleCollapseAll = () => setAllExpanded(false)

const setAllExpanded = (expanded) => {
  const tree = treeRef.value
  if (!tree) return
  const nodes = tree.store._getAllNodes()
  nodes.forEach(node => { node.expanded = expanded })
}

// ===== 컨텍스트 메뉴 =====
const handleContextMenu = (event, data, node) => {
  event.preventDefault()
  contextMenu.visible = true
  contextMenu.x = event.clientX
  contextMenu.y = event.clientY
  contextMenu.data = data
  contextMenu.node = node
}

const closeContextMenu = () => {
  contextMenu.visible = false
}

const ctxAddChild = () => {
  if (!contextMenu.data) return
  handleAddChild(contextMenu.data)
}

const ctxMoveUp = async () => {
  if (!canMoveUp.value || !contextMenu.node) return
  closeContextMenu()
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  if (idx <= 0) return
  await swapSortOrder(siblings, idx, idx - 1)
}

const ctxMoveDown = async () => {
  if (!canMoveDown.value || !contextMenu.node) return
  closeContextMenu()
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  if (idx < 0 || idx >= siblings.length - 1) return
  await swapSortOrder(siblings, idx, idx + 1)
}

const swapSortOrder = async (siblings, idxA, idxB) => {
  try {
    const reorderItems = siblings.map((sib, idx) => {
      let newIdx = idx
      if (idx === idxA) newIdx = idxB
      else if (idx === idxB) newIdx = idxA
      return { dept_id: sib.data.dept_id, sort_order: newIdx + 1 }
    })
    await departmentsApi.reorder(reorderItems)
    await loadDeptTree()
    if (selectedDeptId.value) {
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(selectedDeptId.value)
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '부서 이동 실패')
  }
}

const ctxDelete = async () => {
  if (hasChildren.value || !contextMenu.data) return
  const data = contextMenu.data
  closeContextMenu()
  try {
    await ElMessageBox.confirm(
      `"${data.dept_name}" 부서를 삭제하시겠습니까?`,
      '부서 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await departmentsApi.delete(data.dept_id)
    ElMessage.success('부서가 삭제되었습니다')
    if (selectedDeptId.value === data.dept_id) {
      panelMode.value = null
      selectedDeptId.value = null
      resetForm()
    }
    await loadDeptTree()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

const onDocumentClick = () => closeContextMenu()

// ===== 라이프사이클 =====
onMounted(async () => {
  // GLOBAL 사용자: 테넌트 옵션 로드 + 첫 번째 테넌트 자동 선택
  if (isGlobal.value) {
    await loadTenantOptions()
    if (tenantOptions.value.length > 0 && !selectedTenantId.value) {
      selectedTenantId.value = tenantOptions.value[0].tenant_id
    }
  }
  await loadDeptTree()
  // 첫 로드 시 최상위 부서 자동 선택
  if (deptTree.value.length > 0) {
    const root = deptTree.value[0]
    nextTick(() => {
      if (treeRef.value) treeRef.value.setCurrentKey(root.dept_id)
      handleNodeClick(root)
    })
  }
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.departments-view {
  position: relative;

  // 2-패널 레이아웃
  .dept-layout {
    display: flex;
    gap: 16px;
    align-items: flex-start;

    @include mx.mobile {
      flex-direction: column;
    }
  }

  .dept-tree-panel {
    flex: 0 0 40%;
    max-width: 40%;
  }

  .dept-detail-panel {
    flex: 1;
    min-width: 0;
  }

  .panel-card {
    min-height: 500px;
  }

  // 트리 툴바
  .tree-toolbar {
    display: flex;
    gap: 8px;
    align-items: center;

    .toolbar-spacer {
      flex: 1;
    }
  }

  .tree-divider {
    margin: 12px 0;
  }

  // 트리 노드 커스텀
  .tree-node {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    flex: 1;
    min-width: 0;
    line-height: 1.5;

    .node-icon {
      flex-shrink: 0;
      color: var(--text-color-secondary);
    }

    .node-label {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .node-count {
      flex-shrink: 0;
      margin-left: 4px;
      font-size: 11px;
    }

    .node-tag {
      flex-shrink: 0;
      margin-left: 4px;
    }

    .node-add-btn {
      opacity: 0;
      flex-shrink: 0;
      margin-left: auto;
      font-size: 12px;
      transition: opacity 0.15s;
    }

    &:hover .node-add-btn {
      opacity: 1;
    }

    &.is-inactive {
      .node-label {
        color: var(--text-color-secondary);
        text-decoration: line-through;
      }
    }
  }

  // 상세 패널 헤더
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color-light);

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color-primary);
    }
  }

  // 패널 하단 액션
  .panel-actions {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-top: 16px;
    border-top: 1px solid var(--border-color-light);
    margin-top: 8px;

    .spacer {
      flex: 1;
    }
  }

  .empty-guide {
    text-align: center;
    color: var(--text-color-secondary);
    font-size: 14px;
    line-height: 1.8;
    padding: 60px 0;
    margin: 0;
  }

}

// 우클릭 컨텍스트 메뉴
.context-menu {
  position: fixed;
  z-index: 3000;
  background: var(--bg-color-card);
  border: 1px solid var(--border-color-light);
  border-radius: 4px;
  box-shadow: var(--box-shadow);
  padding: 4px 0;
  min-width: 160px;

  .context-menu-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-color-primary);
    transition: background-color 0.15s;

    &:hover:not(.disabled) {
      background-color: var(--bg-color-hover);
    }

    &.disabled {
      color: var(--text-color-secondary);
      cursor: not-allowed;
      opacity: 0.5;
    }

    &.danger:not(.disabled) {
      color: var(--color-danger);

      &:hover {
        background-color: rgba(var(--color-danger-rgb), 0.1);
      }
    }
  }

  .context-menu-divider {
    height: 1px;
    background-color: var(--border-color-light);
    margin: 4px 0;
  }
}
</style>
