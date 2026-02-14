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
    width="700px"
    class="source-detail-dialog"
    :show-close="true"
    append-to-body
  >
    <template #header>
      <div class="dialog-header">
        <span class="dialog-title">{{ source.title }}</span>
      </div>
    </template>

    <div class="source-detail">
      <div class="detail-meta">
        <el-tag type="info" effect="plain">{{ source.doc_type }}</el-tag>
        <span v-if="source.similarity_score" class="similarity">
          유사도: {{ (source.similarity_score * 100).toFixed(1) }}%
        </span>
      </div>
      <div class="detail-content-wrap">
        <el-tooltip :content="copied ? '복사됨!' : '내용 복사'" placement="top">
          <el-icon class="copy-icon" :class="{ copied }" @click.stop="copyContent">
            <Check v-if="copied" />
            <DocumentCopy v-else />
          </el-icon>
        </el-tooltip>
        <div class="detail-content">
          {{ source.content }}
        </div>
      </div>
      <div v-if="source.context_data" class="detail-context">
        <h4>컨텍스트 데이터</h4>
        <pre class="context-pre">{{ source.context_data }}</pre>
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
import { DocumentCopy, Check } from '@element-plus/icons-vue'

const props = defineProps({
  source: {
    type: Object,
    required: true
  }
})

const showDetail = ref(false)
const copied = ref(false)

const truncate = (text, maxLength) => {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}

const copyContent = async () => {
  try {
    await navigator.clipboard.writeText(props.source.content || '')
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback
    const textarea = document.createElement('textarea')
    textarea.value = props.source.content || ''
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}
</script>

<style lang="scss" scoped>
.source-card {
  padding: 10px 12px;
  background-color: var(--bg-color-page);
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s;
  border: 1px solid var(--border-color-light);

  &:hover {
    background-color: var(--bg-color-overlay);
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
    color: var(--text-color-primary);
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
  color: var(--text-color-regular);
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

  .detail-content-wrap {
    position: relative;

    .copy-icon {
      position: absolute;
      top: 10px;
      right: 10px;
      font-size: 28px;
      color: var(--text-color-secondary);
      cursor: pointer;
      padding: 8px;
      border-radius: 6px;
      transition: all 0.2s;
      z-index: 1;

      &:hover {
        color: var(--color-primary);
        background-color: var(--bg-color-overlay);
      }

      &.copied {
        color: #67c23a;
      }
    }

    .detail-content {
      padding: 16px 36px 16px 16px;
      background-color: var(--bg-color-page);
      border-radius: 6px;
      font-size: 14px;
      line-height: 1.8;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--text-color-primary);
      max-height: 400px;
      overflow-y: auto;
    }
  }

  .detail-context {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-color-primary);
    }

    .context-pre {
      padding: 12px;
      background-color: var(--bg-color-page);
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--text-color-regular);
      max-height: 200px;
      overflow-y: auto;
    }
  }

  .detail-metadata {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px;
      font-size: 14px;
      font-weight: 500;
      color: var(--text-color-primary);
    }
  }
}
</style>

<!-- 다이얼로그 전역 스타일 (scoped 밖에서 적용) -->
<style lang="scss">
.source-detail-dialog {
  .el-dialog {
    background-color: var(--bg-color) !important;

    .el-dialog__header {
      background-color: var(--bg-color);
      border-bottom: 1px solid var(--border-color-light);
      padding: 16px 20px;

      .dialog-header {
        .dialog-title {
          font-size: 16px;
          font-weight: 600;
          color: var(--text-color-primary);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }

      .el-dialog__headerbtn .el-dialog__close {
        color: var(--text-color-regular);
      }
    }

    .el-dialog__body {
      background-color: var(--bg-color);
      color: var(--text-color-primary);
      padding: 20px;
    }
  }
}
</style>
