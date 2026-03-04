<template>
  <div class="menu-permission-table">
    <div v-if="menus.length === 0" class="empty-state">
      <p>메뉴 정보를 불러오는 중...</p>
    </div>
    <el-table v-else :data="menus" style="width: 100%" size="small" :row-class-name="menuRowClassName">
      <el-table-column label="메뉴" min-width="160">
        <template #default="{ row }">
          <span :style="{ paddingLeft: (row.depth || 0) * 16 + 'px' }" :class="{ 'text-disabled': !row.assignable }">
            {{ row.menu_name }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="조회" width="60" align="center">
        <template #default="{ row }">
          <el-checkbox
            v-model="modelValue[row.menu_id].can_read"
            :disabled="!row.assignable"
            @change="(val) => handlePermChange(row.menu_id, 'can_read', val)"
          />
        </template>
      </el-table-column>
      <el-table-column label="등록" width="60" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="modelValue[row.menu_id].can_create" :disabled="!row.assignable" />
        </template>
      </el-table-column>
      <el-table-column label="수정" width="60" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="modelValue[row.menu_id].can_update" :disabled="!row.assignable" />
        </template>
      </el-table-column>
      <el-table-column label="삭제" width="60" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="modelValue[row.menu_id].can_delete" :disabled="!row.assignable" />
        </template>
      </el-table-column>
      <el-table-column label="내보내기" width="80" align="center">
        <template #default="{ row }">
          <el-checkbox v-model="modelValue[row.menu_id].can_export" :disabled="!row.assignable" />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup>
const props = defineProps({
  menus: { type: Array, required: true },
  modelValue: { type: Object, required: true }
})

defineEmits(['update:modelValue'])

const menuRowClassName = ({ row }) => {
  return row.assignable === false ? 'row-disabled' : ''
}

const handlePermChange = (menuId, field, val) => {
  if (field === 'can_read' && !val) {
    props.modelValue[menuId].can_create = false
    props.modelValue[menuId].can_update = false
    props.modelValue[menuId].can_delete = false
    props.modelValue[menuId].can_export = false
  }
}

const buildMenusPayload = () => {
  const menus = []
  for (const m of props.menus) {
    const perm = props.modelValue[m.menu_id]
    if (perm?.can_read) {
      menus.push({
        menu_id: m.menu_id,
        can_create: perm.can_create,
        can_read: perm.can_read,
        can_update: perm.can_update,
        can_delete: perm.can_delete,
        can_export: perm.can_export
      })
    }
  }
  return menus
}

defineExpose({ buildMenusPayload })
</script>

<style lang="scss" scoped>
.menu-permission-table {
  .text-disabled {
    opacity: 0.4;
  }

  :deep(.row-disabled) {
    background-color: var(--el-fill-color-lighter) !important;
  }
}
</style>
