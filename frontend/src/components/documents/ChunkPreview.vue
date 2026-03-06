<template>
  <div class="chunk-preview">
    <div class="preview-header">
      <h4>청킹 미리보기</h4>
      <el-button text :icon="Close" @click="$emit('close')" />
    </div>

    <div class="preview-summary">
      <el-tag type="info">원본: {{ formatNumber(data.original_length) }}자</el-tag>
      <el-tag type="success">청크: {{ data.total_chunks }}개</el-tag>
    </div>

    <div class="chunk-list">
      <div
        v-for="chunk in data.chunks"
        :key="chunk.index"
        class="chunk-item"
      >
        <div class="chunk-header">
          <span class="chunk-index">청크 #{{ chunk.index + 1 }}</span>
          <span class="chunk-length">{{ chunk.length }}자</span>
        </div>
        <div class="chunk-content">
          {{ chunk.preview }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Close } from '@element-plus/icons-vue'

defineProps({
  data: {
    type: Object,
    required: true
  }
})

defineEmits(['close'])

const formatNumber = (num) => {
  return num?.toLocaleString() || '0'
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.chunk-preview {
  margin-top: 20px;
  padding: 16px;
  background-color: var(--bg-color-hover);
  border-radius: 6px;
  transition: var(--theme-transition);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;

  h4 {
    margin: 0;
    font-size: 14px;
    font-weight: 500;
    color: var(--text-color-primary);
  }
}

.preview-summary {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.chunk-list {
  max-height: 300px;
  overflow-y: auto;
}

.chunk-item {
  padding: 12px;
  background-color: var(--bg-color-card);
  border-radius: 4px;
  margin-bottom: 8px;
  transition: var(--theme-transition);

  &:last-child {
    margin-bottom: 0;
  }
}

.chunk-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;

  .chunk-index {
    font-size: 12px;
    font-weight: 500;
    color: var(--color-primary);
  }

  .chunk-length {
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}

.chunk-content {
  font-size: 13px;
  color: var(--text-color-regular);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
