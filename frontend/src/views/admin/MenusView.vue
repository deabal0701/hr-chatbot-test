<template>
  <div class="menus-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>메뉴 관리</h2>
        <p class="subtitle">메뉴 트리를 관리하고 구조를 설정합니다.</p>
      </div>
      <el-button type="success" :icon="Check" @click="applySidebar" :loading="isApplying">
        사이드바 적용
      </el-button>
    </div>

    <div class="menu-layout">
      <!-- 왼쪽: 메뉴 트리 패널 -->
      <div class="menu-tree-panel">
        <div class="panel-card">
          <!-- 트리 툴바 -->
          <div class="tree-toolbar">
            <el-button type="primary" :icon="Plus" size="small" @click="handleAddRoot">메뉴추가</el-button>
            <el-button size="small" @click="handleExpandAll">펼치기</el-button>
            <el-button size="small" @click="handleCollapseAll">접기</el-button>
            <el-button :icon="Refresh" size="small" circle @click="loadMenuTree" :loading="isLoading" />
          </div>

          <!-- 메뉴 트리 -->
          <el-tree
            ref="treeRef"
            v-loading="isLoading"
            :data="menuTree"
            node-key="menu_id"
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
                  <Folder v-if="data.menu_type === 'DIRECTORY'" />
                  <Link v-else-if="data.menu_type === 'API'" />
                  <component v-else :is="resolveIcon(data.icon)" />
                </el-icon>
                <span class="node-label">{{ data.menu_name }}</span>
                <el-tag v-if="!data.is_active" size="small" type="info" class="node-tag">비활성</el-tag>
                <el-button
                  v-if="data.menu_type !== 'API'"
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
          <div v-if="menuTree.length === 0 && !isLoading" class="empty-state">
            등록된 메뉴가 없습니다.
          </div>
        </div>
      </div>

      <!-- 오른쪽: 상세설정 패널 -->
      <div class="menu-detail-panel">
        <div class="panel-card">
          <!-- 미선택 상태 -->
          <div v-if="!panelMode" class="empty-state">
            <el-empty description="왼쪽 트리에서 메뉴를 선택하거나&#10;[메뉴추가]를 클릭하세요" :image-size="80" />
          </div>

          <!-- 생성/수정 폼 -->
          <template v-else>
            <div class="panel-header">
              <h3>{{ panelMode === 'create' ? '새 메뉴 추가' : formData.menu_name }}</h3>
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
                  <el-form-item label="메뉴 코드" prop="menu_code">
                    <el-input
                      v-model="formData.menu_code"
                      placeholder="영문 대문자, 숫자, _"
                      :disabled="panelMode === 'edit'"
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
                      check-strictly
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
                        :key="opt.value"
                        :label="opt.label"
                        :value="opt.value"
                      >
                        <span class="icon-option">
                          <el-icon :size="16"><component :is="opt.component" /></el-icon>
                          <span>{{ opt.label }}</span>
                        </span>
                      </el-option>
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
      <div
        v-if="contextMenu.data?.menu_type !== 'API'"
        class="context-menu-item"
        @click="ctxAddChild"
      >
        <el-icon><Plus /></el-icon>
        <span>하위 메뉴 추가</span>
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
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Refresh, Delete, Top, Bottom, Link, Folder, Check,
  ChatDotSquare, Document, Setting, Grid, Histogram,
  User, Key, OfficeBuilding, Odometer,
  Menu as MenuIcon, List, DataLine
} from '@element-plus/icons-vue'
import menusApi from '@/api/menus'

const store = useStore()

// ===== 아이콘 매핑 (AppSidebar ICON_MAP 동기화) =====
const ICON_MAP = {
  dashboard: Odometer,
  chat: ChatDotSquare,
  document: Document,
  users: User,
  menu: MenuIcon,
  role: Key,
  tenant: OfficeBuilding,
  settings: Setting,
  code: Grid,
  history: Histogram,
  search: DataLine,
  folder: Folder
}

const resolveIcon = (iconName) => ICON_MAP[iconName] || Document

const iconOptions = Object.entries(ICON_MAP).map(([value, component]) => ({
  value,
  label: value,
  component
}))

// ===== 상태 =====
const isLoading = ref(false)
const isSaving = ref(false)
const isApplying = ref(false)
const menuTree = ref([])
const treeRef = ref(null)
const formRef = ref(null)
const contextMenuRef = ref(null)

// panelMode: null(미선택) | 'create' | 'edit'
const panelMode = ref(null)
const selectedMenuId = ref(null)

// 트리 props
const treeProps = { children: 'children', label: 'menu_name' }

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

// 우클릭 컨텍스트 메뉴
const contextMenu = reactive({
  visible: false,
  x: 0,
  y: 0,
  data: null,
  node: null
})

// ===== Computed =====

// 트리에서 특정 menu_id와 그 하위를 제외 (순환 참조 방지)
const filterMenuTree = (items, excludeId) => {
  return items
    .filter(item => item.menu_id !== excludeId)
    .map(item => ({
      ...item,
      children: item.children?.length ? filterMenuTree(item.children, excludeId) : []
    }))
}

// 상위 메뉴 선택 옵션
const parentMenuOptions = computed(() => {
  if (!selectedMenuId.value) return menuTree.value
  return filterMenuTree(menuTree.value, selectedMenuId.value)
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

// 컨텍스트 메뉴: 하위 메뉴 존재 여부
const hasChildren = computed(() => {
  if (!contextMenu.data) return false
  return (contextMenu.data.children?.length || 0) > 0
})

// ===== 메뉴 트리 로드 =====
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

// ===== 폼 초기화 =====
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
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// 폼에 메뉴 데이터 채우기
const fillForm = (data) => {
  formData.menu_code = data.menu_code
  formData.menu_name = data.menu_name
  formData.menu_type = data.menu_type
  formData.parent_menu_id = data.parent_menu_id
  formData.menu_path = data.menu_path || ''
  formData.api_pattern = data.api_pattern || ''
  formData.icon = data.icon || ''
  formData.sort_order = data.sort_order
  formData.is_active = data.is_active
  formData.description = data.description || ''
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}

// ===== 트리 이벤트 핸들러 =====

// 노드 클릭 → 우측 패널 수정 모드
const handleNodeClick = (data) => {
  closeContextMenu()
  panelMode.value = 'edit'
  selectedMenuId.value = data.menu_id
  fillForm(data)
}

// 루트 메뉴 추가
const handleAddRoot = () => {
  closeContextMenu()
  panelMode.value = 'create'
  selectedMenuId.value = null
  resetForm()
  // 트리 선택 해제
  if (treeRef.value) treeRef.value.setCurrentKey(null)
}

// 하위 메뉴 추가 (hover 버튼 또는 컨텍스트 메뉴)
const handleAddChild = (parentData) => {
  closeContextMenu()
  panelMode.value = 'create'
  selectedMenuId.value = null
  resetForm()
  formData.parent_menu_id = parentData.menu_id
  if (treeRef.value) treeRef.value.setCurrentKey(null)
}

// 취소 (생성 모드 → 미선택)
const handleCancel = () => {
  panelMode.value = null
  selectedMenuId.value = null
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
      const result = await menusApi.create({
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
      await loadMenuTree()
      // 생성된 메뉴 자동 선택
      const newId = result.menu_id
      if (newId) {
        nextTick(() => {
          if (treeRef.value) treeRef.value.setCurrentKey(newId)
          panelMode.value = 'edit'
          selectedMenuId.value = newId
          fillForm(result)
        })
      }
    } else {
      const payload = {
        menu_name: formData.menu_name,
        menu_type: formData.menu_type,
        parent_menu_id: formData.parent_menu_id,
        menu_path: formData.menu_type === 'PAGE' ? formData.menu_path : null,
        api_pattern: formData.menu_type === 'API' ? formData.api_pattern : null,
        icon: formData.icon || null,
        sort_order: formData.sort_order,
        is_active: formData.is_active,
        description: formData.description || null
      }
      await menusApi.update(selectedMenuId.value, payload)
      ElMessage.success('메뉴가 수정되었습니다')
      const savedId = selectedMenuId.value
      await loadMenuTree()
      // 수정된 메뉴 재선택
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
  if (!selectedMenuId.value) return
  try {
    await ElMessageBox.confirm(
      `"${formData.menu_name}" 메뉴를 삭제하시겠습니까?`,
      '메뉴 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await menusApi.delete(selectedMenuId.value)
    ElMessage.success('메뉴가 삭제되었습니다')
    panelMode.value = null
    selectedMenuId.value = null
    resetForm()
    await loadMenuTree()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// ===== 드래그앤드롭 =====

// 드래그 가능 여부
const handleAllowDrag = () => true

// 드롭 가능 여부
const handleAllowDrop = (draggingNode, dropNode, type) => {
  // API 타입은 하위 메뉴를 가질 수 없음
  if (type === 'inner' && dropNode.data.menu_type === 'API') return false
  // 최대 depth 5 제한
  if (type === 'inner') {
    const targetDepth = (dropNode.data.depth || 0) + 1
    const draggingMaxDepth = getMaxChildDepth(draggingNode.data)
    if (targetDepth + draggingMaxDepth > 5) return false
  }
  return true
}

// 드래그 노드의 최대 하위 depth 계산
const getMaxChildDepth = (data) => {
  if (!data.children || data.children.length === 0) return 0
  let max = 0
  for (const child of data.children) {
    const d = 1 + getMaxChildDepth(child)
    if (d > max) max = d
  }
  return max
}

// 드롭 완료 처리
const handleNodeDrop = async (draggingNode, dropNode, dropType) => {
  try {
    const dragData = draggingNode.data

    // 1. parent_menu_id 결정
    let newParentId = null
    if (dropType === 'inner') {
      newParentId = dropNode.data.menu_id
    } else {
      // before/after → 대상 노드의 부모
      newParentId = dropNode.data.parent_menu_id || null
    }

    // 2. parent 변경이 필요하면 update 호출
    if (dragData.parent_menu_id !== newParentId) {
      await menusApi.update(dragData.menu_id, { parent_menu_id: newParentId })
    }

    // 3. 같은 부모의 형제들 sort_order 재계산
    const siblings = getSiblings(draggingNode)
    if (siblings.length > 0) {
      const reorderItems = siblings.map((sib, idx) => ({
        menu_id: sib.data.menu_id,
        sort_order: idx + 1
      }))
      await menusApi.reorder(reorderItems)
    }

    await loadMenuTree()

    // 이동된 메뉴 재선택
    if (selectedMenuId.value === dragData.menu_id) {
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(dragData.menu_id)
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '메뉴 이동 실패')
    await loadMenuTree()
  }
}

// 노드의 형제 목록 가져오기
const getSiblings = (node) => {
  const parent = node.parent
  return parent?.childNodes || []
}

// ===== 펼치기/접기 =====
const handleExpandAll = () => {
  setAllExpanded(true)
}

const handleCollapseAll = () => {
  setAllExpanded(false)
}

const setAllExpanded = (expanded) => {
  const tree = treeRef.value
  if (!tree) return
  const nodes = tree.store._getAllNodes()
  nodes.forEach(node => {
    node.expanded = expanded
  })
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

// 하위 메뉴 추가
const ctxAddChild = () => {
  if (!contextMenu.data) return
  handleAddChild(contextMenu.data)
}

// 위로 이동
const ctxMoveUp = async () => {
  if (!canMoveUp.value || !contextMenu.node) return
  closeContextMenu()
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  if (idx <= 0) return
  await swapSortOrder(siblings, idx, idx - 1)
}

// 아래로 이동
const ctxMoveDown = async () => {
  if (!canMoveDown.value || !contextMenu.node) return
  closeContextMenu()
  const parent = contextMenu.node.parent
  const siblings = parent?.childNodes || []
  const idx = siblings.indexOf(contextMenu.node)
  if (idx < 0 || idx >= siblings.length - 1) return
  await swapSortOrder(siblings, idx, idx + 1)
}

// 두 형제의 sort_order 교환
const swapSortOrder = async (siblings, idxA, idxB) => {
  try {
    const reorderItems = siblings.map((sib, idx) => {
      let newIdx = idx
      if (idx === idxA) newIdx = idxB
      else if (idx === idxB) newIdx = idxA
      return { menu_id: sib.data.menu_id, sort_order: newIdx + 1 }
    })
    await menusApi.reorder(reorderItems)
    await loadMenuTree()
    // 이동된 메뉴 재선택
    if (selectedMenuId.value) {
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(selectedMenuId.value)
      })
    }
  } catch (error) {
    ElMessage.error(error.message || '메뉴 이동 실패')
  }
}

// 컨텍스트 삭제
const ctxDelete = async () => {
  if (hasChildren.value || !contextMenu.data) return
  const data = contextMenu.data
  closeContextMenu()
  try {
    await ElMessageBox.confirm(
      `"${data.menu_name}" 메뉴를 삭제하시겠습니까?`,
      '메뉴 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )
    await menusApi.delete(data.menu_id)
    ElMessage.success('메뉴가 삭제되었습니다')
    if (selectedMenuId.value === data.menu_id) {
      panelMode.value = null
      selectedMenuId.value = null
      resetForm()
    }
    await loadMenuTree()
  } catch (error) {
    if (error === 'cancel') return
    ElMessage.error(error.message || '삭제 실패')
  }
}

// 문서 클릭 시 컨텍스트 메뉴 닫기
const onDocumentClick = () => closeContextMenu()

// ===== 사이드바 적용 =====
const applySidebar = async () => {
  isApplying.value = true
  try {
    await store.dispatch('auth/fetchMe')
    ElMessage.success('사이드바 메뉴가 적용되었습니다')
  } catch {
    ElMessage.error('사이드바 적용 실패')
  } finally {
    isApplying.value = false
  }
}

// ===== 라이프사이클 =====
onMounted(() => {
  loadMenuTree()
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.menus-view {
  position: relative;

  .page-header {
    @include mx.page-header;
  }

  // 2-패널 레이아웃
  .menu-layout {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }

  .menu-tree-panel {
    flex: 0 0 40%;
    max-width: 40%;
  }

  .menu-detail-panel {
    flex: 1;
    min-width: 0;
  }

  .panel-card {
    @include mx.content-card;
    min-height: 500px;
  }

  // 트리 툴바
  .tree-toolbar {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 12px;
    flex-wrap: wrap;
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
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-color-light);

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color-primary);
    }
  }

  // 상세 폼
  .detail-form {
    .icon-option {
      display: inline-flex;
      align-items: center;
      gap: 8px;
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

  .empty-state {
    @include mx.empty-state;
  }

  .form-help {
    @include mx.form-help;
  }
}

// 우클릭 컨텍스트 메뉴
.context-menu {
  position: fixed;
  z-index: 3000;
  background: var(--bg-color-card, #fff);
  border: 1px solid var(--border-color-light, #e4e7ed);
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
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
      background-color: var(--el-fill-color-light, #f5f7fa);
    }

    &.disabled {
      color: var(--text-color-secondary);
      cursor: not-allowed;
      opacity: 0.5;
    }

    &.danger:not(.disabled) {
      color: var(--el-color-danger);

      &:hover {
        background-color: var(--el-color-danger-light-9, #fef0f0);
      }
    }
  }

  .context-menu-divider {
    height: 1px;
    background-color: var(--border-color-light, #e4e7ed);
    margin: 4px 0;
  }
}
</style>
