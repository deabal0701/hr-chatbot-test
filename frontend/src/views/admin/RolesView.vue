<template>
  <div class="roles-view">
    <div class="page-header">
      <div>
        <h2>역할 관리</h2>
        <p class="subtitle">역할을 생성, 수정하고 권한을 할당합니다.</p>
      </div>
    </div>
    <div class="content-card">
      <el-empty description="Step 5에서 구현 예정입니다." />
    </div>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.roles-view {
  .page-header {
    @include mx.page-header;
  }
}
</style>
