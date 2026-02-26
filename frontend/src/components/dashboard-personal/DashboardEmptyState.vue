<template>
  <div class="dashboard-empty">
    <el-icon class="empty-icon" :size="64"><DataAnalysis /></el-icon>
    <h3>위젯이 없습니다</h3>
    <p>채팅에서 NL2SQL 결과를 대시보드에 추가하거나,<br>아래 버튼으로 데모 위젯을 불러올 수 있습니다.</p>
    <div class="empty-actions">
      <el-button type="primary" @click="$emit('go-chat')">
        <el-icon><ChatDotRound /></el-icon>
        <span>채팅으로 이동</span>
      </el-button>
      <el-button @click="$emit('load-demo')">
        <el-icon><MagicStick /></el-icon>
        <span>데모 위젯 불러오기</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { DataAnalysis, ChatDotRound, MagicStick } from '@element-plus/icons-vue'

defineEmits(['go-chat', 'load-demo'])
</script>

<style lang="scss" scoped>
.dashboard-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
  padding: 60px 20px;
  background: var(--dashboard-card);
  border-radius: 12px;
  border: 1px solid var(--dashboard-border);
  margin: 40px auto;
  max-width: 480px;

  .empty-icon {
    color: var(--dashboard-empty-icon);
    margin-bottom: 20px;
  }

  h3 {
    margin: 0 0 8px;
    font-size: 20px;
    font-weight: 600;
    color: var(--dashboard-text-primary);
  }

  p {
    margin: 0 0 28px;
    font-size: 14px;
    color: var(--dashboard-text-secondary);
    line-height: 1.6;
  }

  .empty-actions {
    display: flex;
    gap: 12px;
  }
}
</style>
