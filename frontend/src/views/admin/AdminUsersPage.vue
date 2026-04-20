<template>
  <div class="admin-users-page">
    <h1>用户管理</h1>
    <div>
      <input
        v-model="search"
        type="text"
        placeholder="搜索用户"
        data-testid="user-mgmt-inp-search"
      />
      <button data-testid="user-mgmt-btn-create" @click="showCreateDialog = true">创建用户</button>
    </div>
    <table data-testid="user-mgmt-tbl-users">
      <thead>
        <tr>
          <th>ID</th>
          <th>邮箱</th>
          <th>昵称</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
      </tbody>
    </table>
    <div data-testid="user-mgmt-pag-list">分页</div>
    <dialog :open="showCreateDialog" data-testid="user-mgmt-dlg-create">
      <div>创建用户对话框</div>
      <button @click="showCreateDialog = false">关闭</button>
    </dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const search = ref('')
const showCreateDialog = ref(false)
</script>

<style scoped>
</style>
