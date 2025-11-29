<template>
  <el-dialog
    :model-value="visible"
    :title="mode === 'create' ? '새 문서 등록' : '문서 수정'"
    width="700px"
    @update:model-value="$emit('update:visible', $event)"
    @closed="resetForm"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
      label-position="top"
    >
      <el-form-item label="제목" prop="title">
        <el-input v-model="form.title" placeholder="문서 제목을 입력하세요" />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="문서 유형" prop="docType">
            <el-select v-model="form.docType" placeholder="유형 선택" style="width: 100%">
              <el-option label="정책" value="policy" />
              <el-option label="가이드" value="guide" />
              <el-option label="FAQ" value="faq" />
              <el-option label="채용공고" value="job_posting" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="언어" prop="language">
            <el-select v-model="form.language" style="width: 100%">
              <el-option label="한국어" value="ko" />
              <el-option label="English" value="en" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="내용" prop="content">
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="10"
          placeholder="문서 내용을 입력하세요..."
        />
        <div class="content-info">
          <span>{{ form.content?.length || 0 }}자</span>
          <el-button
            v-if="form.content?.length > 500"
            type="primary"
            link
            size="small"
            @click="previewChunks"
          >
            청킹 미리보기
          </el-button>
        </div>
      </el-form-item>

      <!-- 청킹 설정 (생성 시에만) -->
      <el-collapse v-if="mode === 'create'" v-model="activeCollapse">
        <el-collapse-item title="고급 설정 (청킹)" name="chunking">
          <el-row :gutter="20">
            <el-col :span="12">
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
            </el-col>
            <el-col :span="12">
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
            </el-col>
          </el-row>
        </el-collapse-item>
      </el-collapse>
    </el-form>

    <!-- 청킹 미리보기 결과 -->
    <ChunkPreview
      v-if="chunkPreviewData"
      :data="chunkPreviewData"
      @close="chunkPreviewData = null"
    />

    <template #footer>
      <el-button @click="$emit('update:visible', false)">취소</el-button>
      <el-button type="primary" :loading="isSaving" @click="handleSubmit">
        {{ mode === 'create' ? '저장' : '수정' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import ChunkPreview from './ChunkPreview.vue'

const props = defineProps({
  visible: Boolean,
  document: Object,
  mode: {
    type: String,
    default: 'create' // 'create' | 'edit'
  }
})

const emit = defineEmits(['update:visible', 'saved'])

const store = useStore()
const formRef = ref(null)
const activeCollapse = ref([])
const chunkPreviewData = ref(null)

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

// 문서 데이터 로드
watch(() => props.document, (doc) => {
  if (doc && props.mode === 'edit') {
    form.value = {
      title: doc.title || '',
      docType: doc.doc_type || 'policy',
      language: doc.language || 'ko',
      content: doc.content || '',
      chunkSize: 1000,
      chunkOverlap: 100
    }
  }
}, { immediate: true })

// 폼 리셋
const resetForm = () => {
  form.value = {
    title: '',
    docType: 'policy',
    language: 'ko',
    content: '',
    chunkSize: 1000,
    chunkOverlap: 100
  }
  chunkPreviewData.value = null
  activeCollapse.value = []
  formRef.value?.resetFields()
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

    if (props.mode === 'create') {
      await store.dispatch('document/saveDocument', documentData)
    } else {
      await store.dispatch('document/updateDocument', {
        docId: props.document.id,
        documentData
      })
    }

    emit('saved')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('저장에 실패했습니다.')
    }
  }
}
</script>

<style lang="scss" scoped>
.content-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.el-collapse {
  margin-top: 20px;
  border: none;

  :deep(.el-collapse-item__header) {
    font-weight: 500;
  }
}
</style>
