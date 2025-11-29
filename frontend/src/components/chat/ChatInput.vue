<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      :autosize="{ minRows: 2, maxRows: 6 }"
      placeholder="HR 관련 질문을 입력하세요..."
      :disabled="disabled"
      @keydown.enter.exact.prevent="handleSend"
    />
    <el-button
      type="primary"
      :icon="Promotion"
      :disabled="disabled || !inputText.trim()"
      @click="handleSend"
    >
      전송
    </el-button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send'])

const inputText = ref('')

const handleSend = () => {
  const text = inputText.value.trim()
  if (text && !props.disabled) {
    emit('send', text)
    inputText.value = ''
  }
}
</script>

<style lang="scss" scoped>
.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;

  .el-input {
    flex: 1;
  }

  .el-button {
    flex-shrink: 0;
  }
}
</style>
