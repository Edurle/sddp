<template>
  <div class="team-detail-page">
    <h1>团队详情</h1>
    <div>
      <button @click="activeTab = 'members'">成员</button>
      <button @click="activeTab = 'roles'">角色</button>
      <button @click="activeTab = 'settings'">设置</button>
    </div>
    <TeamMembersTab v-if="activeTab === 'members'" />
    <TeamRolesTab v-if="activeTab === 'roles'" />
    <TeamSettingsTab v-if="activeTab === 'settings'" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import TeamMembersTab from './TeamMembersTab.vue'
import TeamRolesTab from './TeamRolesTab.vue'
import TeamSettingsTab from './TeamSettingsTab.vue'

const activeTab = ref<'members' | 'roles' | 'settings'>('members')
</script>

<style scoped>
</style>
