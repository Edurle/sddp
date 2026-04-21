<template>
  <div class="team-detail-page">
    <h1>团队详情</h1>
    <div class="team-info" v-if="team">
      <h2 data-testid="team-detail-txt-name">{{ team.name }}</h2>
      <p data-testid="team-detail-txt-owner">创建者: {{ team.owner_name || team.owner_nickname || team.owner_id }}</p>
      <p data-testid="team-detail-txt-desc">{{ team.description || '' }}</p>
      <p data-testid="team-detail-txt-member-count">成员数: {{ team.member_count ?? memberCount }}</p>
    </div>
    <div class="tab-buttons">
      <button
        :data-testid="'team-detail-tab-members'"
        :class="{ active: activeTab === 'members' }"
        @click="activeTab = 'members'"
      >成员</button>
      <button
        :data-testid="'team-detail-tab-roles'"
        :class="{ active: activeTab === 'roles' }"
        @click="activeTab = 'roles'"
      >角色</button>
      <button
        :data-testid="'team-detail-tab-settings'"
        :class="{ active: activeTab === 'settings' }"
        @click="activeTab = 'settings'"
      >设置</button>
      <button
        :data-testid="'team-detail-tab-projects'"
        :class="{ active: activeTab === 'projects' }"
        @click="activeTab = 'projects'"
      >项目</button>
    </div>
    <TeamMembersTab v-if="activeTab === 'members'" :team-id="teamId" />
    <TeamRolesTab v-if="activeTab === 'roles'" :team-id="teamId" />
    <TeamSettingsTab v-if="activeTab === 'settings'" :team-id="teamId" :team="team" @team-updated="fetchTeam" />
    <div v-if="activeTab === 'projects'" data-testid="team-detail-projects-list">
      <ProjectListTab :team-id="teamId" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { apiClient } from '@/api/client'
import TeamMembersTab from './TeamMembersTab.vue'
import TeamRolesTab from './TeamRolesTab.vue'
import TeamSettingsTab from './TeamSettingsTab.vue'
import ProjectListTab from '../project/ProjectListTab.vue'

const route = useRoute()
const teamId = computed(() => route.params.id as string)

interface TeamInfo {
  id: number
  name: string
  description: string
  owner_id: number
  owner_name?: string
  owner_nickname?: string
  member_count?: number
}

const team = ref<TeamInfo | null>(null)
const memberCount = ref(0)
const activeTab = ref<'members' | 'roles' | 'settings' | 'projects'>('members')

async function fetchTeam() {
  try {
    const res = await apiClient.get(`/api/v1/teams/${teamId.value}`)
    team.value = res.data?.data || res.data
  } catch {
    // ignore
  }
}

onMounted(() => fetchTeam())
</script>
