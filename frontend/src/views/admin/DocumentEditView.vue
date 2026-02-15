<template>
  <div class="document-edit-view">
    <!-- 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">
          목록으로
        </el-button>
        <h2>{{ isEditMode ? '문서 수정' : '새 문서 등록' }}</h2>
      </div>
      <div class="header-right">
        <el-button @click="goBack">취소</el-button>
        <el-button type="primary" :loading="isSaving" @click="handleSubmit">
          {{ isEditMode ? '수정' : '저장' }}
        </el-button>
      </div>
    </div>

    <!-- 폼 영역 -->
    <div class="content-card form-container">
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        label-position="top"
        v-loading="isLoading"
      >
        <el-row :gutter="24">
          <!-- 왼쪽: 메타 정보 -->
          <el-col :span="8">
            <div class="meta-section">
              <h3>문서 정보</h3>

              <el-form-item label="제목" prop="title">
                <el-input v-model="form.title" placeholder="문서 제목을 입력하세요" />
              </el-form-item>

              <el-form-item label="문서 용도" prop="usageType">
                <el-select
                  v-model="form.usageType"
                  style="width: 100%"
                  :loading="usageTypesLoading"
                >
                  <el-option
                    v-for="usageType in usageTypes"
                    :key="usageType.code_value"
                    :label="usageType.code_name"
                    :value="usageType.code_value"
                  />
                </el-select>
                <div class="form-tip">RAG: 문서 기반 답변 / Cortex: SQL 생성 컨텍스트</div>
              </el-form-item>

              <el-form-item label="문서 유형" prop="docType">
                <el-select
                  v-model="form.docType"
                  placeholder="유형 선택"
                  style="width: 100%"
                  :loading="docTypesLoading"
                >
                  <el-option
                    v-for="docType in filteredDocTypes"
                    :key="docType.code_value"
                    :label="docType.code_name"
                    :value="docType.code_value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="언어" prop="language">
                <el-select v-model="form.language" style="width: 100%">
                  <el-option label="한국어" value="ko" />
                  <el-option label="English" value="en" />
                </el-select>
              </el-form-item>

              <!-- 메타데이터 -->
              <el-divider />
              <div class="metadata-section">
                <div class="metadata-header">
                  <h4>메타데이터</h4>
                  <el-button type="primary" link size="small" @click="addMetadataItem">
                    + 추가
                  </el-button>
                </div>
                <div class="form-tip" style="margin-bottom: 8px;">문서 분류 및 검색에 활용되는 추가 정보</div>

                <div v-if="metadataItems.length === 0" class="metadata-empty">
                  메타데이터가 없습니다
                </div>

                <div v-for="(item, index) in metadataItems" :key="index" class="metadata-item">
                  <el-input
                    v-model="item.key"
                    placeholder="키"
                    size="small"
                    style="width: 35%"
                    @change="syncMetadataToForm"
                  />
                  <el-input
                    v-model="item.value"
                    placeholder="값"
                    size="small"
                    style="width: 50%"
                    @change="syncMetadataToForm"
                  />
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="removeMetadataItem(index)"
                  >
                    삭제
                  </el-button>
                </div>
              </div>

              <!-- 청킹 설정 (생성 시에만) -->
              <template v-if="!isEditMode">
                <el-divider />
                <h4>청킹 설정</h4>

                <el-form-item label="청크 크기">
                  <el-input-number
                    v-model="form.chunkSize"
                    :min="100"
                    :max="5000"
                    :step="100"
                    style="width: 100%"
                  />
                  <div class="form-tip">권장: 500~1500자</div>
                </el-form-item>

                <el-form-item label="오버랩">
                  <el-input-number
                    v-model="form.chunkOverlap"
                    :min="0"
                    :max="500"
                    :step="50"
                    style="width: 100%"
                  />
                  <div class="form-tip">청크 간 중복 문자 수</div>
                </el-form-item>

                <el-button
                  v-if="form.content?.length > 500"
                  type="primary"
                  plain
                  style="width: 100%"
                  @click="previewChunks"
                >
                  청킹 미리보기
                </el-button>
              </template>

              <!-- 문서 정보 (수정 시) -->
              <template v-if="isEditMode && documentInfo">
                <el-divider />
                <h4>문서 상태</h4>
                <el-descriptions :column="1" size="small">
                  <el-descriptions-item label="ID">{{ documentInfo.id }}</el-descriptions-item>
                  <el-descriptions-item label="임베딩">
                    <el-tag :type="documentInfo.indexed ? 'success' : 'warning'" size="small">
                      {{ documentInfo.indexed ? '완료' : '대기' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="청크 수">{{ documentInfo.total_chunks || 1 }}</el-descriptions-item>
                  <el-descriptions-item label="전체 길이">{{ formatNumber(documentInfo.original_length || documentInfo.content_length) }}자</el-descriptions-item>
                  <el-descriptions-item label="생성일">{{ formatDate(documentInfo.created_at) }}</el-descriptions-item>
                </el-descriptions>

                <!-- 청크 문서 수정 안내 -->
                <el-alert
                  v-if="documentInfo.total_chunks > 1"
                  type="info"
                  :closable="false"
                  show-icon
                  style="margin-top: 16px"
                >
                  <template #title>
                    청크 문서 수정 안내
                  </template>
                  내용 수정 시 기존 청크가 삭제되고, 저장 후 재임베딩이 필요합니다.
                </el-alert>
              </template>
            </div>
          </el-col>

          <!-- 오른쪽: 내용 편집 -->
          <el-col :span="16">
            <div class="content-section">
              <div class="content-header">
                <h3>문서 내용</h3>
                <span class="char-count">{{ form.content?.length || 0 }}자</span>
              </div>

              <el-form-item prop="content" class="content-form-item">
                <el-input
                  v-model="form.content"
                  type="textarea"
                  placeholder="문서 내용을 입력하세요..."
                  :autosize="{ minRows: 20, maxRows: 40 }"
                />
              </el-form-item>

              <!-- 컨텍스트 데이터 -->
              <div class="context-data-section">
                <div class="content-header">
                  <h3>컨텍스트 데이터</h3>
                  <span class="char-count">{{ form.contextData?.length || 0 }}자</span>
                </div>
                <div class="form-tip context-tip">
                  임베딩되지 않고 스키마, SQL 등 Agent 참조용으로 사용됩니다.
                </div>
                <el-form-item prop="contextData" class="context-form-item">
                  <el-input
                    v-model="form.contextData"
                    type="textarea"
                    placeholder="스키마, SQL 예시 등 Agent가 참조할 컨텍스트 데이터를 입력하세요..."
                    :autosize="{ minRows: 6, maxRows: 15 }"
                  />
                </el-form-item>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 청킹 미리보기 다이얼로그 -->
    <el-dialog
      v-model="chunkPreviewVisible"
      title="청킹 미리보기"
      width="600px"
    >
      <div v-if="chunkPreviewData" class="chunk-preview">
        <div class="preview-summary">
          <el-tag>원본 길이: {{ chunkPreviewData.original_length }}자</el-tag>
          <el-tag type="success">총 {{ chunkPreviewData.total_chunks }}개 청크</el-tag>
        </div>
        <div class="preview-list">
          <div
            v-for="chunk in chunkPreviewData.chunks"
            :key="chunk.index"
            class="preview-item"
          >
            <div class="chunk-header">
              <span class="chunk-number">청크 #{{ chunk.index + 1 }}</span>
              <span class="chunk-length">{{ chunk.length }}자</span>
            </div>
            <div class="chunk-content">{{ chunk.preview }}</div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import codesApi from '@/api/codes'
import { formatDate, formatNumber } from '@/utils/format'

const store = useStore()
const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const documentInfo = ref(null)
const chunkPreviewVisible = ref(false)
const chunkPreviewData = ref(null)
const isLoading = ref(false)

// 문서 용도 코드 (DB에서 동적 로드)
const usageTypes = ref([])
const usageTypesLoading = ref(false)

// 문서 유형 코드 (DB에서 동적 로드)
const docTypes = ref([])
const docTypesLoading = ref(false)

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
const filteredDocTypes = computed(() => {
  if (!docTypes.value.length) return []

  const isRagKnowledge = form.value.usageType === 'rag_knowledge'
  return docTypes.value.filter(dt => {
    const sortOrder = dt.sort_order || 0
    return isRagKnowledge ? sortOrder < 10 : sortOrder >= 10
  })
})

// 기본 문서 유형 반환
const getDefaultDocType = (usageType) => {
  return usageType === 'rag_knowledge' ? 'policy' : 'schema'
}

// 모드 판단
const isEditMode = computed(() => route.name === 'AdminDocumentEdit')
const docId = computed(() => route.params.id)
const isSaving = computed(() => store.state.document.isSaving)

// 폼 데이터
const form = ref({
  title: '',
  docType: 'policy',
  language: 'ko',
  usageType: 'rag_knowledge',
  content: '',
  contextData: '',
  chunkSize: 1000,
  chunkOverlap: 100,
  metadata: {}
})

// 메타데이터 키-값 쌍 관리
const metadataItems = ref([])

// 메타데이터 항목 추가
const addMetadataItem = () => {
  metadataItems.value.push({ key: '', value: '' })
}

// 메타데이터 항목 삭제
const removeMetadataItem = (index) => {
  metadataItems.value.splice(index, 1)
  syncMetadataToForm()
}

// 메타데이터 배열 → 객체 동기화
const syncMetadataToForm = () => {
  const metadata = {}
  metadataItems.value.forEach(item => {
    if (item.key && item.key.trim()) {
      metadata[item.key.trim()] = item.value
    }
  })
  form.value.metadata = metadata
}

// 메타데이터 객체 → 배열 변환
const loadMetadataItems = (metadata) => {
  if (!metadata || typeof metadata !== 'object') {
    metadataItems.value = []
    return
  }
  metadataItems.value = Object.entries(metadata).map(([key, value]) => ({
    key,
    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
  }))
}

// 문서 용도 변경 시 문서 유형 초기화
watch(() => form.value.usageType, (newUsageType) => {
  // 현재 선택된 docType이 새 usageType에서 유효한지 확인
  const validDocTypes = filteredDocTypes.value.map(dt => dt.code_value)
  if (!validDocTypes.includes(form.value.docType)) {
    form.value.docType = getDefaultDocType(newUsageType)
  }
})

// 유효성 검사 규칙
const rules = {
  title: [
    { required: true, message: '제목을 입력하세요', trigger: 'blur' },
    { max: 500, message: '제목은 500자 이하여야 합니다', trigger: 'blur' }
  ],
  docType: [
    { required: true, message: '문서 유형을 선택하세요', trigger: 'change' }
  ],
  content: [
    { required: true, message: '내용을 입력하세요', trigger: 'blur' }
  ]
}

// 문서 데이터 로드
onMounted(async () => {
  // 코드 로드
  loadUsageTypes()
  loadDocTypes()

  // 새 문서 생성 모드: 쿼리 파라미터에서 usageType 읽기
  if (!isEditMode.value) {
    const queryUsageType = route.query.usageType
    if (queryUsageType && ['rag_knowledge', 'rag_action'].includes(queryUsageType)) {
      form.value.usageType = queryUsageType
      form.value.docType = getDefaultDocType(queryUsageType)
    }
  }

  // 수정 모드인 경우 문서 데이터 로드
  if (isEditMode.value && docId.value) {
    isLoading.value = true
    try {
      const doc = await store.dispatch('document/fetchDocument', docId.value)

      // 자식 청크 문서인 경우 부모 문서로 리다이렉트
      if (doc.redirect_to_parent) {
        router.replace({ name: 'AdminDocumentEdit', params: { id: doc.redirect_to_parent } })
        return
      }

      documentInfo.value = doc

      // 제목에서 청크 번호 제거
      const originalTitle = doc.title?.replace(/\s*\(\d+\/\d+\)$/, '') || ''

      // full_content가 있으면 사용 (청크된 문서의 경우), 없으면 content 사용
      const fullContent = doc.full_content || doc.content || ''

      form.value = {
        title: originalTitle,
        docType: doc.doc_type || 'policy',
        language: doc.language || 'ko',
        usageType: doc.usage_type || 'rag_knowledge',
        content: fullContent,
        contextData: doc.context_data || '',
        chunkSize: 1000,
        chunkOverlap: 100,
        metadata: doc.metadata || {}
      }

      // 메타데이터 UI에 로드
      loadMetadataItems(doc.metadata)
    } catch (error) {
      ElMessage.error('문서를 불러올 수 없습니다.')
      router.push({ name: 'AdminDocuments' })
    } finally {
      isLoading.value = false
    }
  }
})

// 목록으로 돌아가기
const goBack = () => {
  router.push({ name: 'AdminDocuments' })
}

// 청킹 미리보기
const previewChunks = async () => {
  if (!form.value.content) return

  try {
    const result = await store.dispatch('document/previewChunks', {
      content: form.value.content,
      chunkSize: form.value.chunkSize,
      chunkOverlap: form.value.chunkOverlap
    })
    chunkPreviewData.value = result
    chunkPreviewVisible.value = true
  } catch (error) {
    ElMessage.error('청킹 미리보기 실패')
  }
}

// 폼 제출
const handleSubmit = async () => {
  try {
    // formRef 유효성 체크
    if (!formRef.value) {
      console.error('formRef가 null입니다')
      ElMessage.error('폼을 초기화할 수 없습니다.')
      return
    }

    await formRef.value.validate()

    const documentData = {
      title: form.value.title,
      docType: form.value.docType,
      language: form.value.language,
      usageType: form.value.usageType,
      content: form.value.content,
      contextData: form.value.contextData || null,
      metadata: form.value.metadata || {}
    }

    console.log('저장할 데이터:', documentData)

    if (isEditMode.value) {
      await store.dispatch('document/updateDocument', {
        docId: docId.value,
        documentData
      })

      // 청크가 있었던 문서의 내용이 변경된 경우 안내
      if (documentInfo.value?.total_chunks > 1) {
        ElMessage.success('문서가 수정되었습니다. 재임베딩이 필요합니다.')
      } else {
        ElMessage.success('문서가 수정되었습니다.')
      }
    } else {
      await store.dispatch('document/saveDocument', documentData)
      ElMessage.success('문서가 생성되었습니다.')
    }

    router.push({ name: 'AdminDocuments' })
  } catch (error) {
    console.error('문서 저장 오류:', error)
    if (error !== 'cancel') {
      // 유효성 검사 실패 시 error는 false
      if (error === false) {
        ElMessage.error('입력값을 확인해주세요.')
      } else {
        const message = error?.response?.data?.detail || error?.message || '저장에 실패했습니다.'
        ElMessage.error(message)
      }
    }
  }
}

</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.document-edit-view {
  height: 100%;
  display: flex;
  flex-direction: column;

  .page-header {
    @include mx.page-header($align: center);

    .header-left {
      @include mx.page-header-left;
    }

    .header-right {
      @include mx.page-header-right;
    }
  }

  .form-container {
    flex: 1;
    overflow: auto;
  }

  .meta-section {
    h3 {
      @include mx.section-title;
    }

    h4 {
      margin: 0 0 16px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-color-regular);
    }

    .form-tip {
      @include mx.form-help;
    }

    .metadata-section {
      .metadata-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;

        h4 {
          margin: 0;
          font-size: 14px;
          font-weight: 500;
          color: var(--text-color-regular);
        }
      }

      .metadata-empty {
        font-size: 12px;
        color: var(--text-color-secondary);
        padding: 12px;
        text-align: center;
        background-color: var(--bg-color);
        border-radius: 4px;
      }

      .metadata-item {
        display: flex;
        gap: 8px;
        align-items: center;
        margin-bottom: 8px;
      }
    }
  }

  .content-section {
    height: 100%;
    display: flex;
    flex-direction: column;

    .content-header {
      @include mx.content-header;

      .char-count {
        font-size: 14px;
        color: var(--text-color-secondary);
      }
    }

    .content-form-item {
      flex: 1;

      :deep(.el-textarea__inner) {
        font-size: 14px;
        line-height: 1.8;
      }
    }

    .context-data-section {
      margin-top: 24px;
      padding-top: 20px;
      border-top: 1px solid var(--border-color-light);

      .context-tip {
        margin-bottom: 12px;
        color: var(--text-color-secondary);
        font-size: 12px;
      }

      .context-form-item {
        :deep(.el-textarea__inner) {
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 13px;
          line-height: 1.6;
          background-color: var(--bg-color-hover);
        }
      }
    }
  }
}

.chunk-preview {
  .preview-summary {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
  }

  .preview-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .preview-item {
    margin-bottom: 16px;
    padding: 12px;
    background-color: var(--bg-color-hover);
    border-radius: 6px;
    transition: var(--theme-transition);

    .chunk-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 12px;

      .chunk-number {
        font-weight: 600;
        color: var(--color-primary);
      }

      .chunk-length {
        color: var(--text-color-secondary);
      }
    }

    .chunk-content {
      font-size: 13px;
      line-height: 1.6;
      color: var(--text-color-regular);
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}
</style>
