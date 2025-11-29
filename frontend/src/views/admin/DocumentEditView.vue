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

              <el-form-item label="문서 유형" prop="docType">
                <el-select v-model="form.docType" placeholder="유형 선택" style="width: 100%">
                  <el-option label="정책" value="policy" />
                  <el-option label="가이드" value="guide" />
                  <el-option label="FAQ" value="faq" />
                  <el-option label="채용공고" value="job_posting" />
                </el-select>
              </el-form-item>

              <el-form-item label="언어" prop="language">
                <el-select v-model="form.language" style="width: 100%">
                  <el-option label="한국어" value="ko" />
                  <el-option label="English" value="en" />
                </el-select>
              </el-form-item>

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
                  <el-descriptions-item label="청크 수">{{ documentInfo.total_chunks || '-' }}</el-descriptions-item>
                  <el-descriptions-item label="생성일">{{ formatDate(documentInfo.created_at) }}</el-descriptions-item>
                </el-descriptions>
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

const store = useStore()
const router = useRouter()
const route = useRoute()

const formRef = ref(null)
const documentInfo = ref(null)
const chunkPreviewVisible = ref(false)
const chunkPreviewData = ref(null)
const isLoading = ref(false)

// 모드 판단
const isEditMode = computed(() => route.name === 'AdminDocumentEdit')
const docId = computed(() => route.params.id)
const isSaving = computed(() => store.state.document.isSaving)

// 폼 데이터
const form = ref({
  title: '',
  docType: 'policy',
  language: 'ko',
  content: '',
  chunkSize: 1000,
  chunkOverlap: 100
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

// 문서 데이터 로드 (수정 모드)
onMounted(async () => {
  if (isEditMode.value && docId.value) {
    isLoading.value = true
    try {
      const doc = await store.dispatch('document/fetchDocument', docId.value)
      documentInfo.value = doc
      form.value = {
        title: doc.title || '',
        docType: doc.doc_type || 'policy',
        language: doc.language || 'ko',
        content: doc.content || '',
        chunkSize: 1000,
        chunkOverlap: 100
      }
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
    await formRef.value.validate()

    const documentData = {
      title: form.value.title,
      docType: form.value.docType,
      language: form.value.language,
      content: form.value.content
    }

    if (isEditMode.value) {
      await store.dispatch('document/updateDocument', {
        docId: docId.value,
        documentData
      })
      ElMessage.success('문서가 수정되었습니다.')
    } else {
      await store.dispatch('document/saveDocument', documentData)
      ElMessage.success('문서가 생성되었습니다.')
    }

    router.push({ name: 'AdminDocuments' })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('저장에 실패했습니다.')
    }
  }
}

// 유틸리티
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ko-KR')
}
</script>

<style lang="scss" scoped>
.document-edit-view {
  height: 100%;
  display: flex;
  flex-direction: column;

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-left {
      display: flex;
      align-items: center;
      gap: 16px;

      h2 {
        margin: 0;
      }
    }

    .header-right {
      display: flex;
      gap: 8px;
    }
  }

  .form-container {
    flex: 1;
    overflow: auto;
  }

  .meta-section {
    h3 {
      margin: 0 0 20px;
      font-size: 16px;
      font-weight: 600;
      color: #303133;
    }

    h4 {
      margin: 0 0 16px;
      font-size: 14px;
      font-weight: 500;
      color: #606266;
    }

    .form-tip {
      font-size: 12px;
      color: #909399;
      margin-top: 4px;
    }
  }

  .content-section {
    height: 100%;
    display: flex;
    flex-direction: column;

    .content-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
      }

      .char-count {
        font-size: 14px;
        color: #909399;
      }
    }

    .content-form-item {
      flex: 1;

      :deep(.el-textarea__inner) {
        font-family: 'Pretendard', sans-serif;
        font-size: 14px;
        line-height: 1.8;
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
    background-color: #f5f7fa;
    border-radius: 6px;

    .chunk-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 12px;

      .chunk-number {
        font-weight: 600;
        color: #409eff;
      }

      .chunk-length {
        color: #909399;
      }
    }

    .chunk-content {
      font-size: 13px;
      line-height: 1.6;
      color: #606266;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}
</style>
