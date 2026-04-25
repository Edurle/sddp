# E2E 测试 CRUD 补全 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 补全端到端测试中缺失的 CRUD 操作（重点是 create），包括更新测试规范文档、补全测试代码、根据测试结果完善前端实现。

**Architecture:** 按模块分批补全：先更新 spec 文档定义缺失用例，再补全测试代码，最后根据测试结果修复前端页面。每个模块（auth、dashboard、team）独立处理。

**Tech Stack:** Playwright + TypeScript + Vue 3 + FastAPI

---

## 缺失分析总结

### 规范文档 vs 测试代码 vs 前端实现 对照表

| 模块 | 用例编号 | 规范文档 | 测试代码 | 前端 data-testid | 缺失类型 |
|------|---------|---------|---------|-----------------|---------|
| Auth | E2E-AUTH-003 确认密码不一致 | 有描述但无 `register-inp-confirm-password` | 测试未验证确认密码 | 注册页无确认密码字段 | **前端缺字段，测试缺用例** |
| Dashboard | E2E-DASH-002 创建团队 | 有描述 | 无测试代码 | Dashboard 无创建团队 UI（需导航到 /teams） | **规范与实现不匹配，测试需调整** |
| Dashboard | E2E-DASH-005 接受邀请 | 有描述 | 部分测试（只检查空状态） | 有 `dashboard-btn-accept-invitation-{id}` | **测试不完整** |
| Dashboard | E2E-DASH-006 拒绝邀请 | 有描述 | 无测试代码 | 无 `dashboard-btn-reject-invitation-{id}` | **前端缺按钮，测试缺代码** |
| Dashboard | E2E-DASH-007 修改个人信息 | 有描述 | 无测试代码 | 只有 link，无编辑表单 | **前端缺实现，测试缺代码** |
| Dashboard | E2E-DASH-008 修改密码成功 | 有描述 | 无测试代码 | 只有 link，无密码弹窗 | **前端缺实现，测试缺代码** |
| Dashboard | E2E-DASH-009 修改密码-旧密码错误 | 有描述 | 无测试代码 | 同上 | **前端缺实现，测试缺代码** |
| Dashboard | E2E-DASH-003 查看待审核 | 有描述 | 部分测试（只检查可见） | 有 `dashboard-list-pending-reviews` | **测试不完整** |
| Dashboard | E2E-DASH-004 查看待执行任务 | 有描述 | 部分测试（只检查可见） | 有 `dashboard-list-pending-tasks` | **测试不完整** |

### 关键发现

1. **Dashboard 页面最不完整** — 缺少创建团队、修改个人信息、修改密码、拒绝邀请的前端实现和测试
2. **注册页面缺少确认密码字段** — 规范要求但前端未实现，测试也未覆盖
3. **Dashboard 创建团队** 实际上在 `/teams` 页面而非 Dashboard，规范 E2E-DASH-002 描述不准确

---

## File Structure

**需要修改的文件：**

```
docs/superpowers/specs/design/
  12-test-cases-e2e-auth.md          # 更新：补充确认密码相关用例描述
  13-test-cases-e2e-dashboard-admin.md # 更新：调整 DASH-002 描述，补充缺失细节

frontend/src/views/
  auth/RegisterPage.vue               # 添加确认密码字段
  dashboard/DashboardPage.vue         # 添加拒绝邀请按钮、修改个人信息、修改密码功能

frontend/tests/
  auth.spec.ts                        # 补充 E2E-AUTH-003 确认密码测试
  dashboard.spec.ts                   # 大幅补全：创建团队、个人信息、密码修改、邀请处理
```

---

## Task 1: 更新 Auth 规范文档 — 补充确认密码用例

**Files:**
- Modify: `docs/superpowers/specs/design/12-test-cases-e2e-auth.md`

- [ ] **Step 1: 在注册成功用例 E2E-AUTH-001 中补充确认密码步骤**

当前规范在 E2E-AUTH-001 步骤中没有提到 `register-inp-confirm-password`，但 E2E-AUTH-003 引用了它。需要在 E2E-AUTH-001 的测试步骤中补充第 5 步：

在 `register-inp-password` 和 `register-inp-nickname` 之间增加确认密码步骤。更新后的 E2E-AUTH-001 测试步骤应为：

```
1. 访问 /register 页面
2. 在 `register-inp-email` 输入 test@example.com
3. 在 `register-inp-nickname` 输入 测试用户
4. 在 `register-inp-password` 输入 Password123
5. 在 `register-inp-confirm-password` 输入 Password123
6. 点击 `register-btn-submit`
```

- [ ] **Step 2: 确认 E2E-AUTH-003 的描述已经引用 `register-inp-confirm-password`**

确认当前 E2E-AUTH-003 已经正确引用了 `register-inp-confirm-password`。无需修改。

---

## Task 2: 更新 Dashboard/Admin 规范文档

**Files:**
- Modify: `docs/superpowers/specs/design/13-test-cases-e2e-dashboard-admin.md`

- [ ] **Step 1: 调整 E2E-DASH-002 创建团队的描述**

当前描述让用户在 Dashboard 页面操作，但实际创建团队功能在 `/teams` 页面。更新为：

```markdown
### 创建团队

- **用例编号**: E2E-DASH-002
- **前置条件**: 用户已登录
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击我的团队区域的创建链接或导航到 /teams
  3. 点击 `team-list-btn-create`
  4. 在 `team-list-dlg-create` 弹窗中：
     - `team-list-dlg-create-inp-name` 输入团队名称
     - `team-list-dlg-create-txtarea-desc` 输入描述
  5. 点击 `team-list-dlg-create-btn-submit`
- **验证方式**: 团队列表中出现新创建的团队，用户角色为"团队所有者"
```

- [ ] **Step 2: 更新 E2E-DASH-005/006 的 data-testid**

当前 `DashboardPage.vue` 只有接受邀请按钮 `dashboard-btn-accept-invitation-{id}`，需要补充拒绝邀请的 `dashboard-btn-reject-invitation-{id}`。

确认规范中 E2E-DASH-006 已有 `dashboard-btn-reject-invitation-{id}` 的引用。无需修改规范。

---

## Task 3: 前端 — 注册页添加确认密码字段

**Files:**
- Modify: `frontend/src/views/auth/RegisterPage.vue`

- [ ] **Step 1: 在注册表单中添加确认密码输入框**

在 `register-inp-password` 的 form-group 后面，`register-inp-nickname` 之前，添加确认密码字段：

```html
<div class="form-group">
  <label for="confirm-password">确认密码</label>
  <input
    id="confirm-password"
    v-model="confirmPassword"
    type="password"
    data-testid="register-inp-confirm-password"
  />
  <div v-if="errors.confirmPassword" class="error-message">{{ errors.confirmPassword }}</div>
</div>
```

- [ ] **Step 2: 添加确认密码验证逻辑**

在 `<script setup>` 中：
1. 添加 `const confirmPassword = ref('')`
2. 在 `errors` reactive 中添加 `confirmPassword: ''`
3. 在 `validate()` 函数中添加确认密码校验：

```typescript
errors.confirmPassword = ''
if (password.value !== confirmPassword.value) {
  errors.confirmPassword = '两次输入的密码不一致'
  valid = false
}
```

---

## Task 4: 前端 — Dashboard 补全拒绝邀请功能

**Files:**
- Modify: `frontend/src/views/dashboard/DashboardPage.vue`

- [ ] **Step 1: 在邀请列表中添加拒绝按钮**

在模板的邀请列表中，在 `dashboard-btn-accept-invitation-{id}` 按钮后面添加：

```html
<button :data-testid="`dashboard-btn-reject-invitation-${item.id}`" @click="rejectInvitation(item.id)">拒绝</button>
```

- [ ] **Step 2: 添加 rejectInvitation 方法**

在 `<script setup>` 中添加：

```typescript
async function rejectInvitation(id: number) {
  try {
    await apiClient.post(`/api/v1/invitations/${id}/reject`)
    pendingInvitations.value = pendingInvitations.value.filter(i => i.id !== id)
  } catch {
    // ignore
  }
}
```

---

## Task 5: 前端 — Dashboard 补全修改个人信息功能

**Files:**
- Modify: `frontend/src/views/dashboard/DashboardPage.vue`

规范 E2E-DASH-007 要求在 Dashboard 页面直接修改昵称。当前只有一个 link 到 `/edit-profile`。需要将 Dashboard 改为包含 tab 结构（按规范要求有 `dashboard-tab-teams`、`dashboard-tab-pending`、`dashboard-tab-profile`）。

但考虑到当前 Dashboard 已经有数据展示，需要先确认：
- 规范要求有 `dashboard-tab-teams`、`dashboard-tab-pending`、`dashboard-tab-profile` 等 tab
- 当前 Dashboard 是平铺展示

- [ ] **Step 1: 为 Dashboard 添加 tab 结构**

添加 3 个 tab：团队、待办、个人资料。用 `dashboard-tab-teams`、`dashboard-tab-pending`、`dashboard-tab-profile` 作为 data-testid。

```html
<div class="tabs">
  <button data-testid="dashboard-tab-teams" :class="{ active: activeTab === 'teams' }" @click="activeTab = 'teams'">我的团队</button>
  <button data-testid="dashboard-tab-pending" :class="{ active: activeTab === 'pending' }" @click="activeTab = 'pending'">待办事项</button>
  <button data-testid="dashboard-tab-profile" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">个人资料</button>
</div>
```

- [ ] **Step 2: 将待办事项放入 pending tab 下**

添加 pending 子 tab：

```html
<div v-if="activeTab === 'pending'">
  <div class="sub-tabs">
    <button data-testid="dashboard-tab-pending-reviews" :class="{ active: pendingSubTab === 'reviews' }" @click="pendingSubTab = 'reviews'">待审核</button>
    <button data-testid="dashboard-tab-pending-tasks" :class="{ active: pendingSubTab === 'tasks' }" @click="pendingSubTab = 'tasks'">待执行任务</button>
    <button data-testid="dashboard-tab-pending-invitations" :class="{ active: pendingSubTab === 'invitations' }" @click="pendingSubTab = 'invitations'">待处理邀请</button>
  </div>
  <!-- ... reviews/tasks/invitations 内容 -->
</div>
```

- [ ] **Step 3: 添加个人资料 tab**

```html
<div v-if="activeTab === 'profile'">
  <div class="form-group">
    <label>昵称</label>
    <input v-model="profileNickname" data-testid="dashboard-inp-nickname" />
  </div>
  <button data-testid="dashboard-btn-save-profile" @click="saveProfile">保存</button>
  <button data-testid="dashboard-btn-change-password" @click="showPasswordDialog = true">修改密码</button>
  
  <div v-if="showPasswordDialog" class="dialog-overlay" @click.self="showPasswordDialog = false">
    <div data-testid="dashboard-dlg-password" class="dialog">
      <h3>修改密码</h3>
      <div class="form-group">
        <label>旧密码</label>
        <input v-model="passwordForm.old" type="password" data-testid="dashboard-dlg-password-inp-old" />
      </div>
      <div class="form-group">
        <label>新密码</label>
        <input v-model="passwordForm.newPassword" type="password" data-testid="dashboard-dlg-password-inp-new" />
      </div>
      <div class="form-group">
        <label>确认新密码</label>
        <input v-model="passwordForm.confirm" type="password" data-testid="dashboard-dlg-password-inp-confirm" />
      </div>
      <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
      <div v-if="passwordSuccess" class="success-message">{{ passwordSuccess }}</div>
      <button data-testid="dashboard-dlg-password-btn-submit" @click="changePassword">确认修改</button>
      <button @click="showPasswordDialog = false">取消</button>
    </div>
  </div>
</div>
```

- [ ] **Step 4: 添加个人资料和修改密码的 script 逻辑**

```typescript
const activeTab = ref('teams')
const pendingSubTab = ref('reviews')
const profileNickname = ref('')
const showPasswordDialog = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordForm = reactive({ old: '', newPassword: '', confirm: '' })

watch(() => user.value, (u) => {
  if (u) profileNickname.value = (u as any).nickname || ''
}, { immediate: true })

async function saveProfile() {
  try {
    await apiClient.put('/api/v1/users/me', { nickname: profileNickname.value })
    await authStore.fetchUser()
    // 可选：显示成功提示
  } catch {
    // ignore
  }
}

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.newPassword !== passwordForm.confirm) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  try {
    await apiClient.put('/api/v1/users/me/password', {
      old_password: passwordForm.old,
      new_password: passwordForm.newPassword,
    })
    passwordSuccess.value = '密码修改成功'
    passwordForm.old = ''
    passwordForm.newPassword = ''
    passwordForm.confirm = ''
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '修改失败'
    if (msg.includes('旧密码') || msg.includes('old password')) {
      passwordError.value = '旧密码错误'
    } else {
      passwordError.value = msg
    }
  }
}
```

---

## Task 6: 测试 — 补全 auth.spec.ts 确认密码测试

**Files:**
- Modify: `frontend/tests/auth.spec.ts`

- [ ] **Step 1: 添加 E2E-AUTH-003 确认密码不一致测试**

在 Registration Page describe 块中添加：

```typescript
test('should show validation error when passwords do not match', async ({ page }) => {
  await page.getByTestId('register-inp-email').fill('test@example.com')
  await page.getByTestId('register-inp-nickname').fill('测试用户')
  await page.getByTestId('register-inp-password').fill('Password123')
  await page.getByTestId('register-inp-confirm-password').fill('Different456')
  await page.getByTestId('register-btn-submit').click()
  await expect(page.getByText(/密码.*一致|密码.*相同/)).toBeVisible()
})
```

---

## Task 7: 测试 — 大幅补全 dashboard.spec.ts

**Files:**
- Modify: `frontend/tests/dashboard.spec.ts`

当前 dashboard.spec.ts 只有 7 个简单的可见性检查测试。需要补全到覆盖规范中 E2E-DASH-001 到 E2E-DASH-009 的所有用例。

- [ ] **Step 1: 补全 E2E-DASH-001 查看团队列表**

```typescript
test('E2E-DASH-001: should display my teams list', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-teams').click()
  await expect(page.getByTestId('dashboard-list-my-teams')).toBeVisible()
})
```

- [ ] **Step 2: 补全 E2E-DASH-002 创建团队（导航到 /teams 页面）**

```typescript
test('E2E-DASH-002: should create team from teams page', async ({ authenticatedPage: page }) => {
  await page.goto('/teams')
  await page.getByTestId('team-list-btn-create').click()

  const dialog = page.getByTestId('team-list-dlg-create')
  await expect(dialog).toBeVisible()

  const teamName = `E2E Team ${Date.now()}`
  await dialog.getByTestId('team-list-dlg-create-inp-name').fill(teamName)
  await dialog.getByTestId('team-list-dlg-create-txtarea-desc').fill('E2E test team description')
  await dialog.getByTestId('team-list-dlg-create-btn-submit').click()

  await expect(dialog).not.toBeVisible()
  await expect(page.getByTestId('team-list-card-txt-name').first()).toContainText(teamName)
})
```

- [ ] **Step 3: 补全 E2E-DASH-003 查看待审核事项**

```typescript
test('E2E-DASH-003: should display pending reviews', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-pending').click()
  await page.getByTestId('dashboard-tab-pending-reviews').click()
  await expect(page.getByTestId('dashboard-list-pending-reviews')).toBeVisible()
})
```

- [ ] **Step 4: 补全 E2E-DASH-004 查看待执行任务**

```typescript
test('E2E-DASH-004: should display pending tasks', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-pending').click()
  await page.getByTestId('dashboard-tab-pending-tasks').click()
  await expect(page.getByTestId('dashboard-list-pending-tasks')).toBeVisible()
})
```

- [ ] **Step 5: 补全 E2E-DASH-005 接受团队邀请**

```typescript
test('E2E-DASH-005: should accept invitation', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-pending').click()
  await page.getByTestId('dashboard-tab-pending-invitations').click()

  const acceptBtn = page.getByTestId(/dashboard-btn-accept-invitation-/).first()
  if (await acceptBtn.isVisible()) {
    await acceptBtn.click()
    await expect(acceptBtn).not.toBeVisible()
  }
})
```

- [ ] **Step 6: 补全 E2E-DASH-006 拒绝团队邀请**

```typescript
test('E2E-DASH-006: should reject invitation', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-pending').click()
  await page.getByTestId('dashboard-tab-pending-invitations').click()

  const rejectBtn = page.getByTestId(/dashboard-btn-reject-invitation-/).first()
  if (await rejectBtn.isVisible()) {
    await rejectBtn.click()
    await expect(rejectBtn).not.toBeVisible()
  }
})
```

- [ ] **Step 7: 补全 E2E-DASH-007 修改个人信息**

```typescript
test('E2E-DASH-007: should update nickname', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-profile').click()

  const nicknameInput = page.getByTestId('dashboard-inp-nickname')
  await nicknameInput.clear()
  await nicknameInput.fill('新昵称')

  await page.getByTestId('dashboard-btn-save-profile').click()

  await expect(page.getByTestId('dashboard-txt-nickname')).toContainText('新昵称')
})
```

- [ ] **Step 8: 补全 E2E-DASH-008 修改密码成功**

```typescript
test('E2E-DASH-008: should change password successfully', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-profile').click()
  await page.getByTestId('dashboard-btn-change-password').click()

  await expect(page.getByTestId('dashboard-dlg-password')).toBeVisible()

  await page.getByTestId('dashboard-dlg-password-inp-old').fill('Admin1234!')
  await page.getByTestId('dashboard-dlg-password-inp-new').fill('NewPassword567!')
  await page.getByTestId('dashboard-dlg-password-inp-confirm').fill('NewPassword567!')
  await page.getByTestId('dashboard-dlg-password-btn-submit').click()

  await expect(page.getByText(/密码修改成功/)).toBeVisible()
})
```

- [ ] **Step 9: 补全 E2E-DASH-009 修改密码-旧密码错误**

```typescript
test('E2E-DASH-009: should show error for wrong old password', async ({ authenticatedPage: page }) => {
  await page.getByTestId('dashboard-tab-profile').click()
  await page.getByTestId('dashboard-btn-change-password').click()

  await page.getByTestId('dashboard-dlg-password-inp-old').fill('WrongOldPassword')
  await page.getByTestId('dashboard-dlg-password-inp-new').fill('NewPassword567!')
  await page.getByTestId('dashboard-dlg-password-inp-confirm').fill('NewPassword567!')
  await page.getByTestId('dashboard-dlg-password-btn-submit').click()

  await expect(page.getByText(/旧密码错误/)).toBeVisible()
})
```

---

## Task 8: 运行测试并修复

- [ ] **Step 1: 运行所有测试**

```bash
cd /home/dzj/file/sdd/frontend && npx playwright test --reporter=list 2>&1 | head -100
```

- [ ] **Step 2: 分析失败结果，修复前端实现**

根据测试失败的具体原因修复：
- 如果缺少 API 端点，检查后端路由
- 如果 data-testid 不匹配，修复前端模板
- 如果 API 路径不对，修复测试中的路径

- [ ] **Step 3: 重新运行失败的测试直到通过**

```bash
npx playwright test dashboard auth --reporter=list
```

---

## 执行顺序

1. Task 1-2: 更新规范文档（无风险，只是文档）
2. Task 3: 注册页添加确认密码字段
3. Task 4: Dashboard 添加拒绝邀请
4. Task 5: Dashboard 添加 tab 结构和个人资料/密码修改
5. Task 6: 补全 auth 测试
6. Task 7: 补全 dashboard 测试
7. Task 8: 运行测试、修复、验证
