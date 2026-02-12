<template>
  <div class="tenants-view">
    <div class="page-header">
      <div>
        <h2>테넌트 관리</h2>
        <p class="subtitle">테넌트(조직)를 생성하고 관리합니다.</p>
      </div>
    </div>
    <div class="content-card">
      <el-empty description="Step 6에서 구현 예정입니다." />
    </div>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.tenants-view {
  .page-header {
    @include mx.page-header;
  }
}
</style>
