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
                <el-descriptions-item label="제목">{{ document.title }}</el-descriptions-item>
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
                <el-descriptions-item label="내용 길이">
                  {{ formatNumber(document.content_length) }}자
                </el-descriptions-item>
                <el-descriptions-item label="청크 수">
                  {{ document.total_chunks || '-' }}
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

              <!-- 임베딩 실행 버튼 -->
              <div class="action-section" v-if="!document.indexed">
                <el-button
                  type="success"
                  :icon="Upload"
                  :loading="isEmbedding"
                  style="width: 100%"
                  @click="executeEmbedding"
                >
                  임베딩 실행
                </el-button>
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
              <div class="content-body">
                {{ document.content || '(내용 없음)' }}
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
import { ArrowLeft, Edit, Delete, Upload, CopyDocument } from '@element-plus/icons-vue'

const store = useStore()
const router = useRouter()
const route = useRoute()

const document = ref(null)
const isLoading = ref(false)
const isEmbedding = ref(false)

const docId = computed(() => route.params.id)

// 문서 로드
onMounted(async () => {
  if (docId.value) {
    isLoading.value = true
    try {
      document.value = await store.dispatch('document/fetchDocument', docId.value)
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
    `"${document.value.title}" 문서를 삭제하시겠습니까?`,
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

// 임베딩 실행
const executeEmbedding = async () => {
  isEmbedding.value = true
  try {
    const result = await store.dispatch('document/executeEmbedding', { docIds: [docId.value] })
    ElMessage.success(result.message || '임베딩이 완료되었습니다.')
    // 문서 새로고침
    document.value = await store.dispatch('document/fetchDocument', docId.value)
  } catch (error) {
    ElMessage.error('임베딩 실행에 실패했습니다.')
  } finally {
    isEmbedding.value = false
  }
}

// 내용 복사
const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(document.value.content)
    ElMessage.success('내용이 클립보드에 복사되었습니다.')
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

const formatNumber = (num) => {
  return num?.toLocaleString() || '0'
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('ko-KR')
}
</script>

<style lang="scss" scoped>
.document-detail-view {
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

  .detail-container {
    flex: 1;
    overflow: auto;
  }

  .meta-section {
    h3 {
      margin: 0 0 20px;
      font-size: 16px;
      font-weight: 600;
      color: var(--text-color-primary);
    }

    .action-section {
      margin-top: 20px;
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
        color: var(--text-color-primary);
      }
    }

    .content-body {
      flex: 1;
      padding: 20px;
      background-color: var(--bg-color-hover);
      border-radius: 8px;
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 14px;
      line-height: 1.8;
      color: var(--text-color-primary);
      overflow-y: auto;
      max-height: calc(100vh - 280px);
      transition: var(--theme-transition);
    }
  }
}
</style>
