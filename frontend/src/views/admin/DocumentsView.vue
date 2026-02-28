<template>
  <div class="documents-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>문서 관리</h2>
        <p class="subtitle">AI 어시스턴트에서 사용할 문서를 관리합니다.</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="showCreateForm">
        새 문서
      </el-button>
    </div>

    <!-- 필터 및 액션 -->
    <div class="content-card filter-section">
      <div class="filter-row">
        <!-- 테넌트 필터 (GLOBAL 역할만 표시) -->
        <el-select
          v-if="isGlobal"
          v-model="tenantFilter"
          placeholder="테넌트"
          clearable
          style="width: 150px"
          @change="handleTenantFilterChange"
          :loading="tenantsLoading"
        >
          <el-option label="공용" value="1" />
          <el-option
            v-for="tenant in tenantOptions"
            :key="tenant.tenant_id"
            :label="tenant.tenant_name"
            :value="String(tenant.tenant_id)"
          />
        </el-select>

        <el-select
          v-model="filters.usageType"
          placeholder="문서 용도"
          clearable
          style="width: 150px"
          @change="handleFilterChange"
          :loading="usageTypesLoading"
        >
          <el-option
            v-for="usageType in usageTypes"
            :key="usageType.code_value"
            :label="usageType.code_name"
            :value="usageType.code_value"
          />
        </el-select>

        <el-select
          v-model="filters.docType"
          placeholder="문서 유형"
          clearable
          style="width: 150px"
          @change="handleFilterChange"
          :loading="docTypesLoading"
        >
          <el-option
            v-for="docType in filteredDocTypes"
            :key="docType.code_value"
            :label="docType.code_name"
            :value="docType.code_value"
          />
        </el-select>

        <el-select
          v-model="filters.indexed"
          placeholder="임베딩 상태"
          clearable
          style="width: 150px"
          @change="handleFilterChange"
        >
          <el-option label="임베딩 완료" :value="true" />
          <el-option label="임베딩 대기" :value="false" />
        </el-select>

        <el-button :icon="Refresh" @click="resetFilters">
          필터 초기화
        </el-button>

        <div class="flex-1" />

        <!-- 선택된 항목 액션 -->
        <template v-if="selectedCount > 0">
          <span class="selected-info">{{ selectedCount }}개 선택됨</span>
          <el-button
            type="success"
            plain
            :icon="Upload"
            @click="executeEmbeddingSelected"
          >
            임베딩 실행
          </el-button>
          <el-button
            type="danger"
            plain
            :icon="Delete"
            @click="deleteSelected"
          >
            삭제
          </el-button>
        </template>
      </div>
    </div>

    <!-- 문서 목록 -->
    <div class="content-card">
      <el-table
        v-loading="isLoading"
        :data="documents"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="45" />

        <el-table-column prop="id" label="ID" width="70" />

        <el-table-column prop="title" label="제목" min-width="200">
          <template #default="{ row }">
            <span class="title-link" :title="row.title" @click="showDetail(row)">
              {{ row.title }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="doc_type" label="유형" width="100">
          <template #default="{ row }">
            <el-tag size="small" :type="getDocTypeTag(row.doc_type)">
              {{ getDocTypeLabel(row.doc_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="usage_type" label="용도" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.usage_type === 'rag_action' ? 'warning' : 'primary'">
              {{ row.usage_type === 'rag_action' ? 'Action' : '지식' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="original_length" label="길이" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.original_length || row.content_length) }}자
          </template>
        </el-table-column>

        <el-table-column prop="indexed" label="임베딩" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.indexed" type="success" size="small">완료</el-tag>
            <el-tag v-else type="warning" size="small">대기</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="total_chunks" label="청크" width="80" align="center">
          <template #default="{ row }">
            {{ row.total_chunks || '-' }}
          </template>
        </el-table-column>

        <el-table-column prop="tenant_id" label="테넌트" width="100" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.tenant_id === '1' ? 'info' : ''">
              {{ getTenantLabel(row.tenant_id) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="생성일" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="작업" width="150">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                v-if="canEditDoc(row)"
                size="small" text :icon="Edit" @click="showEditForm(row)"
              >
                수정
              </el-button>
              <el-button
                v-if="canDeleteDoc(row)"
                size="small" text type="danger" :icon="Delete" @click="confirmDelete(row)"
              >
                삭제
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

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

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Delete, Edit, Upload } from '@element-plus/icons-vue'
import codesApi from '@/api/codes'
import usersApi from '@/api/users'
import { formatDate, formatNumber } from '@/utils/format'

const store = useStore()
const router = useRouter()

// 사용자 역할 정보
const roleCode = computed(() => store.getters['auth/roleCode'])
const isGlobal = computed(() => roleCode.value === 'GLOBAL')
const currentUser = computed(() => store.getters['auth/currentUser'])

// 테넌트 필터 (GLOBAL 역할 전용)
const tenantFilter = ref(null)
const tenantOptions = ref([])
const tenantsLoading = ref(false)

// 문서 용도 코드 (DB에서 동적 로드)
const usageTypes = ref([])
const usageTypesLoading = ref(false)

// 문서 유형 코드 (DB에서 동적 로드)
const docTypes = ref([])
const docTypesLoading = ref(false)

// Computed
const documents = computed(() => store.state.document.documents)
const isLoading = computed(() => store.state.document.isLoading)
const selectedCount = computed(() => store.getters['document/selectedCount'])
const filters = computed(() => store.state.document.filters)
const total = computed(() => store.state.document.pagination.total)
const pageSize = computed(() => store.state.document.pagination.limit)
const currentPage = computed(() => store.state.document.pagination.page)

// 테넌트 옵션 로드 (GLOBAL 역할만)
const loadTenantOptions = async () => {
  if (!isGlobal.value) return
  tenantsLoading.value = true
  try {
    const response = await usersApi.getTenantOptions()
    // tenant_id=1(공용)은 드롭다운에 직접 추가했으므로 제외
    tenantOptions.value = (response.items || []).filter(t => t.tenant_id !== 1)
  } catch (error) {
    console.error('테넌트 옵션 로드 실패:', error)
  } finally {
    tenantsLoading.value = false
  }
}

// 테넌트 필터 변경
const handleTenantFilterChange = () => {
  store.dispatch('document/setTenantFilter', tenantFilter.value)
}

// 문서 용도 코드 로드
const loadUsageTypes = async () => {
  usageTypesLoading.value = true
  try {
    const response = await codesApi.lookup('USAGE_TYPE')
    usageTypes.value = response.items
  } catch (error) {
    console.error('문서 용도 로드 실패:', error)
  } finally {
    usageTypesLoading.value = false
  }
}

// 문서 유형 코드 로드
const loadDocTypes = async () => {
  docTypesLoading.value = true
  try {
    const response = await codesApi.lookup('DOC_TYPE')
    docTypes.value = response.items
  } catch (error) {
    console.error('문서 유형 로드 실패:', error)
  } finally {
    docTypesLoading.value = false
  }
}

// 문서 용도에 따른 문서 유형 필터링
// - RAG (sort_order 1-9): policy, guide, faq, job_posting 등
// - Cortex (sort_order 10+): schema, query_example, glossary
// - 미선택: 전체 표시
const filteredDocTypes = computed(() => {
  if (!docTypes.value.length) return []

  const usageType = filters.value.usageType
  if (!usageType) return docTypes.value  // 전체 표시

  const isRagKnowledge = usageType === 'rag_knowledge'
  return docTypes.value.filter(dt => {
    const sortOrder = dt.sort_order || 0
    return isRagKnowledge ? sortOrder < 10 : sortOrder >= 10
  })
})

// 문서 용도 변경 시 문서 유형 필터 초기화
watch(() => filters.value.usageType, (newUsageType) => {
  if (newUsageType && filters.value.docType) {
    // 현재 선택된 docType이 새 usageType에서 유효한지 확인
    const validDocTypes = filteredDocTypes.value.map(dt => dt.code_value)
    if (!validDocTypes.includes(filters.value.docType)) {
      // 유효하지 않으면 docType 필터 초기화
      store.dispatch('document/setFilters', { ...filters.value, docType: null })
    }
  }
})

// 초기 로드
onMounted(() => {
  loadTenantOptions()
  loadUsageTypes()
  loadDocTypes()
  store.dispatch('document/fetchDocuments')
})

// 필터 변경
const handleFilterChange = () => {
  store.dispatch('document/setFilters', filters.value)
}

const resetFilters = () => {
  tenantFilter.value = null
  store.dispatch('document/resetFilters')
}

// 페이지 변경
const handlePageChange = (page) => {
  store.dispatch('document/setPage', page)
}

// 페이지 사이즈 변경
const handleSizeChange = (size) => {
  store.dispatch('document/setPageSize', size)
}

// 선택 변경
const handleSelectionChange = (selection) => {
  store.commit('document/SET_SELECTED', selection.map(doc => doc.id))
}

// 새 문서 페이지로 이동
const showCreateForm = () => {
  // 현재 필터된 용도가 있으면 쿼리 파라미터로 전달
  const query = filters.value.usageType ? { usageType: filters.value.usageType } : {}
  router.push({ name: 'AdminDocumentNew', query })
}

// 문서 수정 페이지로 이동
const showEditForm = (doc) => {
  router.push({ name: 'AdminDocumentEdit', params: { id: doc.id } })
}

// 문서 상세 페이지로 이동
const showDetail = (doc) => {
  router.push({ name: 'AdminDocumentDetail', params: { id: doc.id } })
}

// 단일 삭제
const confirmDelete = (doc) => {
  ElMessageBox.confirm(
    `"${doc.title}" 문서를 삭제하시겠습니까?`,
    '문서 삭제',
    {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await store.dispatch('document/deleteDocument', doc.id)
      ElMessage.success('문서가 삭제되었습니다.')
    } catch (error) {
      ElMessage.error('문서 삭제에 실패했습니다.')
    }
  }).catch(() => {})
}

// 선택 삭제
const deleteSelected = () => {
  ElMessageBox.confirm(
    `선택한 ${selectedCount.value}개 문서를 삭제하시겠습니까?`,
    '일괄 삭제',
    {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await store.dispatch('document/deleteSelected')
      ElMessage.success('문서가 삭제되었습니다.')
    } catch (error) {
      ElMessage.error('일괄 삭제에 실패했습니다.')
    }
  }).catch(() => {})
}

// 선택 임베딩 실행
const executeEmbeddingSelected = async () => {
  const selectedIds = store.state.document.selectedIds
  try {
    const result = await store.dispatch('document/executeEmbedding', { docIds: selectedIds })
    ElMessage.success(result.message || '임베딩이 완료되었습니다.')
    store.commit('document/CLEAR_SELECTED')
  } catch (error) {
    ElMessage.error('임베딩 실행에 실패했습니다.')
  }
}

// 테넌트 라벨
const getTenantLabel = (tenantId) => {
  if (!tenantId || tenantId === '1') return '공용'
  const found = tenantOptions.value.find(t => String(t.tenant_id) === String(tenantId))
  return found ? found.tenant_name : `T${tenantId}`
}

// 문서 수정/삭제 권한 (TENANT 역할은 공용 문서 수정/삭제 불가)
const canEditDoc = (row) => {
  if (isGlobal.value) return true
  return row.tenant_id !== '1'
}

const canDeleteDoc = (row) => {
  if (isGlobal.value) return true
  return row.tenant_id !== '1'
}

// 유틸리티
const getDocTypeLabel = (type) => {
  const found = docTypes.value.find(dt => dt.code_value === type)
  return found ? found.code_name : type
}

const getDocTypeTag = (type) => {
  const found = docTypes.value.find(dt => dt.code_value === type)
  return found?.metadata?.tag_type || 'info'
}

</script>

<style lang="scss" scoped>
.documents-view {
  .filter-section {
    margin-bottom: 12px;
  }

  .filter-row {
    .selected-info {
      font-size: 14px;
      color: var(--text-color-regular);
      font-weight: 500;
    }
  }

}
</style>
