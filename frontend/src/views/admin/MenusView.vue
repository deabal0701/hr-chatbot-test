<template>
  <div class="menus-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>메뉴 관리</h2>
        <p class="subtitle">메뉴 트리를 관리하고 구조를 설정합니다.</p>
      </div>
      <el-button type="primary" plain :icon="Refresh" @click="applySidebar" :loading="isApplying">
        메뉴 적용
      </el-button>
    </div>

    <div class="menu-layout">
      <!-- 왼쪽: 메뉴 트리 패널 -->
      <div class="menu-tree-panel">
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
              <el-button :icon="Refresh" size="small" circle @click="loadMenuTree" :loading="isLoading" />
            </el-tooltip>
          </div>
          <el-divider class="tree-divider" />

          <!-- 메뉴 트리 -->
          <el-tree
            :key="treeVersion"
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
                  <component v-else :is="resolveIcon(data.icon)" />
                </el-icon>
                <span class="node-label">{{ data.menu_name }}</span>
                <el-tag v-if="!data.is_active" size="small" type="info" class="node-tag">비활성</el-tag>
                <el-button
                  v-if="data.menu_type === 'DIRECTORY'"
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
        <div class="panel-card content-card">
          <!-- 미선택 상태 -->
          <div v-if="!panelMode" class="empty-state">
            <p class="empty-guide">왼쪽 트리에서 메뉴를 선택하거나<br/>[메뉴추가]를 클릭하세요</p>
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

              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="아이콘" prop="icon">
                    <div class="icon-select-wrap">
                      <el-icon v-if="formData.icon" class="icon-preview" :size="18">
                        <component :is="resolveIcon(formData.icon)" />
                      </el-icon>
                      <el-select
                        v-model="formData.icon"
                        placeholder="선택"
                        clearable
                        filterable
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
                    </div>
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
        v-if="contextMenu.data?.menu_type === 'DIRECTORY'"
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
  Plus, Refresh, Delete, Top, Bottom, Folder, Check,
  ArrowDown, ArrowUp,
  ChatDotSquare, Document, Setting, Grid, Histogram,
  User, Key, OfficeBuilding, Odometer,
  Menu as MenuIcon, List, DataLine,
  SetUp, Tools, HomeFilled, Monitor, Connection, Bell,
  Calendar, Clock, Search, Lock, Unlock, Star, Flag,
  PieChart, TrendCharts, Tickets, Briefcase, Suitcase,
  House, Platform, Service, Management, Operation,
  DataAnalysis, DataBoard, Notebook, Reading,
  ShoppingCart, Goods, Wallet, CreditCard, Money,
  Message, ChatRound, Comment, Notification,
  Picture, Files, FolderOpened, DocumentAdd,
  Edit as EditIcon, EditPen, Download, Upload,
  CircleCheck, Warning, InfoFilled, QuestionFilled
} from '@element-plus/icons-vue'
import menusApi from '@/api/menus'
import { filterTree, flattenTree } from '@/composables/useTreeUtils'
import { getErrorMessage } from '@/utils/error'

const store = useStore()

// ===== 아이콘 매핑 (AppSidebar ICON_MAP 동기화) =====
const ICON_MAP = {
  // 기본 (사이드바 사용)
  dashboard: Odometer,
  chat: ChatDotSquare,
  document: Document,
  users: User,
  menu: MenuIcon,
  role: Key,
  tenant: OfficeBuilding,
  settings: Setting,
  setup: SetUp,
  tools: Tools,
  code: Grid,
  history: Histogram,
  search: DataLine,
  folder: Folder,
  // 추가 아이콘
  home: HomeFilled,
  monitor: Monitor,
  connection: Connection,
  bell: Bell,
  calendar: Calendar,
  clock: Clock,
  lock: Lock,
  unlock: Unlock,
  star: Star,
  flag: Flag,
  piechart: PieChart,
  trendcharts: TrendCharts,
  tickets: Tickets,
  briefcase: Briefcase,
  suitcase: Suitcase,
  house: House,
  platform: Platform,
  service: Service,
  management: Management,
  operation: Operation,
  dataanalysis: DataAnalysis,
  databoard: DataBoard,
  notebook: Notebook,
  reading: Reading,
  cart: ShoppingCart,
  goods: Goods,
  wallet: Wallet,
  creditcard: CreditCard,
  money: Money,
  message: Message,
  chatround: ChatRound,
  comment: Comment,
  notification: Notification,
  picture: Picture,
  files: Files,
  folderopened: FolderOpened,
  documentadd: DocumentAdd,
  edit: EditIcon,
  editpen: EditPen,
  download: Download,
  upload: Upload,
  circlecheck: CircleCheck,
  warning: Warning,
  info: InfoFilled,
  question: QuestionFilled,
  list: List,
  department: Management,
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
const treeVersion = ref(0)
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

// 상위 메뉴 선택 옵션 — DIRECTORY 타입만 표시 (자기 자신과 하위 제외)
const parentMenuOptions = computed(() => {
  return filterTree(menuTree.value, selectedMenuId.value, {
    idKey: 'menu_id',
    filterFn: item => item.menu_type === 'DIRECTORY'
  })
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
    treeVersion.value++
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
    const msg = getErrorMessage(error, '메뉴 저장에 실패하였습니다')
    if (msg) ElMessage.error(msg)
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
    const msg = getErrorMessage(error, '메뉴 삭제에 실패하였습니다')
    if (msg) ElMessage.error(msg)
  }
}

// ===== 드래그앤드롭 =====

// 드래그 가능 여부
const handleAllowDrag = () => true

// 드롭 가능 여부
const handleAllowDrop = (draggingNode, dropNode, type) => {
  // inner(하위 편입)는 DIRECTORY 타입만 허용 — PAGE는 자식을 가질 수 없음
  if (type === 'inner' && dropNode.data.menu_type !== 'DIRECTORY') return false
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

// 드롭 완료 처리 — 서버 데이터 기반 계산 (el-tree 내부 상태에 의존하지 않음)
const handleNodeDrop = async (draggingNode, dropNode, dropType) => {
  try {
    const dragId = draggingNode.data.menu_id
    const dropId = dropNode.data.menu_id
    const oldParentId = draggingNode.data.parent_menu_id ?? null

    // 1. 새 parent_menu_id 결정
    let newParentId = null
    if (dropType === 'inner') {
      newParentId = dropId
    } else {
      newParentId = dropNode.data.parent_menu_id ?? null
    }

    const parentChanged = oldParentId !== newParentId

    // 2. parent 변경 시 update 호출
    if (parentChanged) {
      await menusApi.update(dragId, { parent_menu_id: newParentId })
    }

    // 3. 서버에서 최신 트리 조회 (el-tree 내부 상태 대신 DB 기준)
    const freshTree = await menusApi.getTree()
    const allMenus = flattenTree(freshTree.items || [])

    // 4. 새 부모의 형제 목록 (드래그 항목 제외) — DB sort_order 순
    const siblings = allMenus
      .filter(m => (m.parent_menu_id ?? null) === newParentId && m.menu_id !== dragId)
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))

    // 5. 드롭 위치에 따라 삽입 인덱스 계산
    let insertIdx
    if (dropType === 'inner') {
      insertIdx = siblings.length
    } else {
      const dropIdx = siblings.findIndex(s => s.menu_id === dropId)
      insertIdx = dropIdx === -1
        ? siblings.length
        : dropType === 'before' ? dropIdx : dropIdx + 1
    }

    // 6. 드래그 항목을 계산된 위치에 삽입
    siblings.splice(insertIdx, 0, { menu_id: dragId })

    // 7. sort_order 1,2,3... 일괄 업데이트
    const reorderItems = siblings.map((s, idx) => ({
      menu_id: s.menu_id,
      sort_order: idx + 1
    }))
    await menusApi.reorder(reorderItems)

    // 8. parent 변경 시 이전 부모의 남은 형제도 재정렬
    if (parentChanged) {
      const oldSiblings = allMenus
        .filter(m => (m.parent_menu_id ?? null) === oldParentId && m.menu_id !== dragId)
        .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
      if (oldSiblings.length > 0) {
        const oldReorderItems = oldSiblings.map((s, idx) => ({
          menu_id: s.menu_id,
          sort_order: idx + 1
        }))
        await menusApi.reorder(oldReorderItems)
      }
    }

    // 9. 트리 리로드
    await loadMenuTree()

    // 이동된 메뉴 재선택
    if (selectedMenuId.value === dragId) {
      nextTick(() => {
        if (treeRef.value) treeRef.value.setCurrentKey(dragId)
      })
    }
  } catch (error) {
    const msg = getErrorMessage(error, '메뉴 이동에 실패하였습니다')
    if (msg) ElMessage.error(msg)
    await loadMenuTree()
  }
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
    const msg = getErrorMessage(error, '메뉴 이동에 실패하였습니다')
    if (msg) ElMessage.error(msg)
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
    const msg = getErrorMessage(error, '메뉴 삭제에 실패하였습니다')
    if (msg) ElMessage.error(msg)
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
onMounted(async () => {
  await loadMenuTree()
  // 첫 로드 시 최상위 루트 메뉴 자동 선택
  if (menuTree.value.length > 0) {
    const root = menuTree.value[0]
    nextTick(() => {
      if (treeRef.value) treeRef.value.setCurrentKey(root.menu_id)
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

.menus-view {
  position: relative;

  // 2-패널 레이아웃
  .menu-layout {
    display: flex;
    gap: 16px;
    align-items: flex-start;

    @include mx.mobile {
      flex-direction: column;
    }
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

  // 상세 폼
  .detail-form {
    .icon-option {
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .icon-select-wrap {
      display: flex;
      align-items: center;
      gap: 8px;
      width: 100%;

      .icon-preview {
        flex-shrink: 0;
        color: var(--color-primary);
      }

      .el-select {
        flex: 1;
      }
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
        background-color: var(--el-color-danger-light-9, rgba(245, 108, 108, 0.1));
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
