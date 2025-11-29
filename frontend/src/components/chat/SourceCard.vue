<template>
  <div class="source-card" @click="showDetail = true">
    <div class="source-header">
      <el-tag size="small" type="info" effect="plain">
        {{ source.doc_type }}
      </el-tag>
      <span class="source-title">{{ source.title }}</span>
      <span v-if="source.similarity_score" class="similarity-score">
        {{ (source.similarity_score * 100).toFixed(1) }}%
      </span>
    </div>
    <div class="source-snippet">
      {{ truncate(source.content_snippet, 150) }}
    </div>
  </div>

  <!-- 상세 다이얼로그 -->
  <el-dialog
    v-model="showDetail"
    :title="source.title"
    width="600px"
  >
    <div class="source-detail">
      <div class="detail-meta">
        <el-tag type="info" effect="plain">{{ source.doc_type }}</el-tag>
        <span v-if="source.similarity_score" class="similarity">
          유사도: {{ (source.similarity_score * 100).toFixed(1) }}%
        </span>
      </div>
      <div class="detail-content">
        {{ source.content_snippet }}
      </div>
      <div v-if="source.metadata && Object.keys(source.metadata).length > 0" class="detail-metadata">
        <h4>메타데이터</h4>
        <el-descriptions :column="2" size="small" border>
          <el-descriptions-item
            v-for="(value, key) in source.metadata"
            :key="key"
            :label="key"
          >
            {{ value }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  source: {
    type: Object,
    required: true
  }
})

const showDetail = ref(false)

const truncate = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}
</script>

<style lang="scss" scoped>
.source-card {
  padding: 10px 12px;
  background-color: #f5f7fa;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;

  &:hover {
    background-color: #ebeef5;
  }
}

.source-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;

  .source-title {
    flex: 1;
    font-size: 13px;
    font-weight: 500;
    color: #303133;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .similarity-score {
    font-size: 12px;
    color: #67c23a;
    font-weight: 500;
  }
}

.source-snippet {
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

.source-detail {
  .detail-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;

    .similarity {
      font-size: 14px;
      color: #67c23a;
    }
  }

  .detail-content {
    padding: 16px;
    background-color: #f5f7fa;
    border-radius: 6px;
    font-size: 14px;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .detail-metadata {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 500;
      color: #303133;
    }
  }
}
</style>
