<template>
  <div class="document-detail-view">
    <!-- 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">
          목록으로
        </el-button>
        <h2>문서 상세</h2>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Edit" @click="goEdit">
          수정
        </el-button>
        <el-button type="danger" plain :icon="Delete" @click="confirmDelete">
          삭제
        </el-button>
      </div>
    </div>

    <!-- 내용 -->
    <div class="content-card detail-container" v-loading="isLoading">
      <template v-if="document">
        <el-row :gutter="24">
          <!-- 왼쪽: 메타 정보 -->
          <el-col :span="8">
            <div class="meta-section">
              <h3>문서 정보</h3>

              <el-descriptions :column="1" border>
                <el-descriptions-item label="ID">{{ document.id }}</el-descriptions-item>
                <el-descriptions-item label="제목">{{ getOriginalTitle }}</el-descriptions-item>
                <el-descriptions-item label="유형">
                  <el-tag :type="getDocTypeTag(document.doc_type)">
                    {{ getDocTypeLabel(document.doc_type) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="언어">
                  {{ document.language === 'ko' ? '한국어' : 'English' }}
                </el-descriptions-item>
                <el-descriptions-item label="임베딩 상태">
                  <el-tag :type="document.indexed ? 'success' : 'warning'">
                    {{ document.indexed ? '완료' : '대기' }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="전체 길이">
                  {{ formatNumber(document.original_length || document.content_length) }}자
                </el-descriptions-item>
                <el-descriptions-item label="청크 수">
                  {{ document.total_chunks || 1 }}
                </el-descriptions-item>
                <el-descriptions-item label="소스 타입">
                  {{ document.source_type || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="원본 파일">
                  {{ document.source_file || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="생성일">
                  {{ formatDateTime(document.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="수정일">
                  {{ formatDateTime(document.updated_at) }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 임베딩 섹션 -->
              <div class="embedding-section">
                <h3>임베딩</h3>

                <div class="chunk-settings">
                  <div class="setting-item">
                    <label>청크 크기</label>
                    <el-input-number
                      v-model="chunkSize"
                      :min="100" :max="5000" :step="100"
                      size="small"
                      controls-position="right"
                      style="width: 100%"
                    />
                  </div>
                  <div class="setting-item">
                    <label>청크 오버랩</label>
                    <el-input-number
                      v-model="chunkOverlap"
                      :min="0" :max="500" :step="50"
                      size="small"
                      controls-position="right"
                      style="width: 100%"
                    />
                  </div>
                </div>

                <div class="embedding-actions">
                  <el-button
                    :icon="View"
                    size="small"
                    :loading="isPreviewing"
                    @click="previewChunks"
                    :disabled="!document.content && !document.full_content"
                  >
                    미리보기
                  </el-button>
                  <el-button
                    type="success"
                    :icon="Upload"
                    size="small"
                    :loading="isEmbedding"
                    @click="executeEmbedding"
                  >
                    {{ document.indexed ? '재임베딩' : '임베딩 실행' }}
                  </el-button>
                </div>

                <!-- 청킹 미리보기 결과 -->
                <ChunkPreview
                  v-if="chunkPreviewData"
                  :data="chunkPreviewData"
                  @close="chunkPreviewData = null"
                />
              </div>
            </div>
          </el-col>

          <!-- 오른쪽: 내용 -->
          <el-col :span="16">
            <div class="content-section">
              <div class="content-header">
                <h3>문서 내용</h3>
                <el-button text :icon="CopyDocument" @click="copyContent">
                  복사
                </el-button>
              </div>

              <!-- 청크 네비게이션 (청크가 2개 이상인 경우에만 표시) -->
              <div class="chunk-navigation" v-if="hasMultipleChunks">
                <div class="nav-left">
                  <el-button
                    :type="viewMode === 'full' ? 'primary' : 'default'"
                    size="small"
                    @click="viewMode = 'full'"
                  >
                    전체 보기
                  </el-button>
                  <el-divider direction="vertical" />
                  <span class="chunk-label">청크 보기:</span>
                </div>
                <div class="nav-center" v-if="viewMode === 'chunk'">
                  <el-button
                    :icon="ArrowLeft"
                    size="small"
                    :disabled="currentChunkIndex <= 0"
                    @click="currentChunkIndex--"
                  />
                  <span class="chunk-indicator">
                    {{ currentChunkIndex + 1 }} / {{ document.total_chunks }}
                  </span>
                  <el-button
                    :icon="ArrowRight"
                    size="small"
                    :disabled="currentChunkIndex >= document.total_chunks - 1"
                    @click="currentChunkIndex++"
                  />
                </div>
                <div class="nav-center" v-else>
                  <el-button
                    size="small"
                    @click="viewMode = 'chunk'; currentChunkIndex = 0"
                  >
                    청크별 보기
                  </el-button>
                </div>
                <div class="nav-right" v-if="viewMode === 'chunk'">
                  <el-select
                    v-model="currentChunkIndex"
                    size="small"
                    style="width: 120px"
                    placeholder="청크 선택"
                  >
                    <el-option
                      v-for="(chunk, index) in document.chunks"
                      :key="chunk.id"
                      :label="`청크 ${index + 1} (${formatNumber(chunk.content_length)}자)`"
                      :value="index"
                    />
                  </el-select>
                </div>
              </div>

              <!-- 현재 보기 정보 -->
              <div class="view-info" v-if="hasMultipleChunks">
                <template v-if="viewMode === 'full'">
                  <el-tag type="info" size="small">
                    전체 내용 ({{ formatNumber(document.original_length) }}자)
                  </el-tag>
                </template>
                <template v-else>
                  <el-tag type="success" size="small">
                    청크 {{ currentChunkIndex + 1 }}/{{ document.total_chunks }}
                    ({{ formatNumber(currentChunk?.content_length) }}자)
                  </el-tag>
                </template>
              </div>

              <div class="content-body">
                {{ currentContent || '(내용 없음)' }}
              </div>

              <!-- 청크 페이지네이션 (하단) -->
              <div class="chunk-pagination" v-if="hasMultipleChunks && viewMode === 'chunk'">
                <el-pagination
                  :current-page="chunkPage"
                  :page-size="1"
                  :total="document.total_chunks"
                  layout="prev, pager, next"
                  :pager-count="7"
                  small
                  @current-change="handleChunkPageChange"
                />
              </div>

              <!-- 컨텍스트 데이터 -->
              <div class="context-data-section">
                <div class="content-header">
                  <h3>컨텍스트 데이터</h3>
                  <el-button
                    v-if="document.context_data"
                    text
                    :icon="CopyDocument"
                    @click="copyContextData"
                  >
                    복사
                  </el-button>
                </div>
                <div class="context-tip">
                  임베딩되지 않고 스키마, SQL 등 Agent 참조용으로 사용됩니다.
                </div>
                <div class="context-body">
                  {{ document.context_data || '(컨텍스트 데이터 없음)' }}
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowRight, Edit, Delete, Upload, CopyDocument, View } from '@element-plus/icons-vue'
import { formatDateTime, formatNumber } from '@/utils/format'
import ChunkPreview from '@/components/documents/ChunkPreview.vue'
import settingsApi from '@/api/settings'

const store = useStore()
const router = useRouter()
const route = useRoute()

const document = ref(null)
const isLoading = ref(false)
const isEmbedding = ref(false)
const isPreviewing = ref(false)
const viewMode = ref('full') // 'full' | 'chunk'
const currentChunkIndex = ref(0)
const chunkSize = ref(1000)
const chunkOverlap = ref(100)
const chunkPreviewData = ref(null)

// 서버 청킹 설정 로드
const loadChunkingSettings = async () => {
  try {
    const response = await settingsApi.getCategory('chunking')
    const settingsList = response.settings || response || []
    const sizeItem = settingsList.find(s => s.key === 'default_chunk_size')
    const overlapItem = settingsList.find(s => s.key === 'default_overlap')
    if (sizeItem?.value) chunkSize.value = Number(sizeItem.value)
    if (overlapItem?.value) chunkOverlap.value = Number(overlapItem.value)
  } catch (error) {
    console.error('청킹 설정 로드 실패:', error)
  }
}

const docId = computed(() => route.params.id)

// 청크 페이지 (1부터 시작, el-pagination용)
const chunkPage = computed({
  get: () => currentChunkIndex.value + 1,
  set: (val) => { currentChunkIndex.value = val - 1 }
})

// 청크가 여러 개인지 확인
const hasMultipleChunks = computed(() => {
  return document.value?.chunks?.length > 1
})

// 원본 제목 (청크 번호 제거)
const getOriginalTitle = computed(() => {
  if (!document.value?.title) return ''
  return document.value.title.replace(/\s*\(\d+\/\d+\)$/, '')
})

// 현재 선택된 청크
const currentChunk = computed(() => {
  if (!document.value?.chunks) return null
  return document.value.chunks[currentChunkIndex.value]
})

// 현재 표시할 내용
const currentContent = computed(() => {
  if (!document.value) return ''

  if (viewMode.value === 'full') {
    return document.value.full_content || document.value.content
  }

  return currentChunk.value?.content || document.value.content
})

// 청크 페이지 변경 핸들러
const handleChunkPageChange = (page) => {
  currentChunkIndex.value = page - 1
}

// 문서 로드
onMounted(async () => {
  // 서버 청킹 설정 로드
  loadChunkingSettings()

  if (docId.value) {
    isLoading.value = true
    try {
      const doc = await store.dispatch('document/fetchDocument', docId.value)

      // 자식 청크 문서인 경우 부모 문서로 리다이렉트
      if (doc.redirect_to_parent) {
        router.replace({ name: 'AdminDocumentDetail', params: { id: doc.redirect_to_parent } })
        return
      }

      document.value = doc
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

// 수정 페이지로 이동
const goEdit = () => {
  router.push({ name: 'AdminDocumentEdit', params: { id: docId.value } })
}

// 삭제 확인
const confirmDelete = () => {
  ElMessageBox.confirm(
    `"${getOriginalTitle.value}" 문서를 삭제하시겠습니까?`,
    '문서 삭제',
    {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await store.dispatch('document/deleteDocument', docId.value)
      ElMessage.success('문서가 삭제되었습니다.')
      router.push({ name: 'AdminDocuments' })
    } catch (error) {
      ElMessage.error('문서 삭제에 실패했습니다.')
    }
  }).catch(() => {})
}

// 청킹 미리보기
const previewChunks = async () => {
  const content = document.value?.full_content || document.value?.content
  if (!content) return

  isPreviewing.value = true
  chunkPreviewData.value = null
  try {
    const result = await store.dispatch('document/previewChunks', {
      content,
      chunkSize: chunkSize.value,
      chunkOverlap: chunkOverlap.value,
    })
    chunkPreviewData.value = result
  } catch (error) {
    ElMessage.error('청킹 미리보기에 실패했습니다.')
  } finally {
    isPreviewing.value = false
  }
}

// 임베딩 실행
const executeEmbedding = async () => {
  const action = document.value?.indexed ? '재임베딩' : '임베딩'
  if (document.value?.indexed) {
    try {
      await ElMessageBox.confirm(
        '기존 임베딩 데이터를 덮어씁니다. 계속하시겠습니까?',
        `${action} 확인`,
        { confirmButtonText: '실행', cancelButtonText: '취소', type: 'warning' }
      )
    } catch { return }
  }

  isEmbedding.value = true
  try {
    const result = await store.dispatch('document/executeEmbedding', {
      docIds: [docId.value],
      chunkSize: chunkSize.value,
      chunkOverlap: chunkOverlap.value,
    })
    ElMessage.success(result.message || `${action}이 완료되었습니다.`)
    chunkPreviewData.value = null
    document.value = await store.dispatch('document/fetchDocument', docId.value)
  } catch (error) {
    ElMessage.error(`${action} 실행에 실패했습니다.`)
  } finally {
    isEmbedding.value = false
  }
}

// 내용 복사
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(currentContent.value)
    ElMessage.success('내용이 클립보드에 복사되었습니다.')
  } catch (error) {
    ElMessage.error('복사에 실패했습니다.')
  }
}

// 컨텍스트 데이터 복사
const copyContextData = async () => {
  try {
    await navigator.clipboard.writeText(document.value.context_data || '')
    ElMessage.success('컨텍스트 데이터가 클립보드에 복사되었습니다.')
  } catch (error) {
    ElMessage.error('복사에 실패했습니다.')
  }
}

// 유틸리티
const getDocTypeLabel = (type) => {
  const labels = {
    policy: '정책',
    guide: '가이드',
    faq: 'FAQ',
    job_posting: '채용공고'
  }
  return labels[type] || type
}

const getDocTypeTag = (type) => {
  const types = {
    policy: 'primary',
    guide: 'success',
    faq: 'info',
    job_posting: 'warning'
  }
  return types[type] || 'info'
}

</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.document-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;

  .page-header {
    align-items: center;

  }

  .detail-container {
    flex: 1;
    overflow: auto;
  }


  .embedding-section {
    margin-top: 24px;
    padding-top: 20px;
    border-top: 1px solid var(--border-color-light);

    .chunk-settings {
      display: flex;
      flex-direction: column;
      gap: 12px;
      margin-bottom: 16px;

      .setting-item {
        label {
          display: block;
          font-size: 13px;
          color: var(--text-color-secondary);
          margin-bottom: 4px;
        }
      }
    }

    .embedding-actions {
      display: flex;
      gap: 8px;

      .el-button {
        flex: 1;
      }
    }
  }

  .content-section {
    height: 100%;
    display: flex;
    flex-direction: column;

    .chunk-navigation {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      background-color: var(--bg-color-hover);
      border-radius: 8px;
      margin-bottom: 12px;

      .nav-left {
        display: flex;
        align-items: center;
        gap: 8px;

        .chunk-label {
          font-size: 14px;
          color: var(--text-color-regular);
        }
      }

      .nav-center {
        display: flex;
        align-items: center;
        gap: 12px;

        .chunk-indicator {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-color-primary);
          min-width: 80px;
          text-align: center;
        }
      }

      .nav-right {
        display: flex;
        align-items: center;
      }
    }

    .view-info {
      margin-bottom: 8px;
    }

    .content-body {
      flex: 1;
      padding: 12px;
      background-color: var(--bg-color-hover);
      border-radius: 8px;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 14px;
      line-height: 1.8;
      color: var(--text-color-primary);
      overflow-y: auto;
      max-height: calc(100vh - 400px);
      transition: var(--theme-transition);
    }

    .chunk-pagination {
      display: flex;
      justify-content: center;
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--border-color-light);
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

      .context-body {
        padding: 16px;
        background-color: var(--bg-color-hover);
        border-radius: 8px;
        white-space: pre-wrap;
        word-break: break-word;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 13px;
        line-height: 1.6;
        color: var(--text-color-primary);
        max-height: 300px;
        overflow-y: auto;
        transition: var(--theme-transition);
      }
    }
  }
}
</style>
