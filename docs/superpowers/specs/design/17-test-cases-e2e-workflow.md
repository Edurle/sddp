# 端到端测试用例 — 完整业务流程

> 本文档描述一个串行执行的完整业务流程 E2E 测试，覆盖从团队创建到迭代完成的全链路。

## 测试角色

| 角色 | 邮箱 | 昵称 | 密码 |
|------|------|------|------|
| 创建者 (creator) | workflow_creator_{ts}@test.com | 创建者 | Test1234! |
| 产品经理 (pm) | workflow_pm_{ts}@test.com | 产品经理 | Test1234! |
| 开发 (dev) | workflow_dev_{ts}@test.com | 开发 | Test1234! |
| 测试 (tester) | workflow_tester_{ts}@test.com | 测试 | Test1234! |

---

## 流程步骤

### 阶段一：团队准备

#### WF-001 注册所有用户
- **操作用户**: 浏览器直接操作
- **测试步骤**:
  1. 访问 /register 页面
  2. 依次注册 4 个用户（创建者、产品经理、开发、测试）
  3. 每次注册填写邮箱、昵称、密码、确认密码
  4. 点击 `register-btn-submit` 提交
  5. 等待跳转到 /login
- **验证方式**: 4 个用户全部注册成功

#### WF-002 创建者登录
- **操作用户**: creator
- **测试步骤**:
  1. 访问 /login 页面
  2. 在 `login-inp-email` 输入创建者邮箱
  3. 在 `login-inp-password` 输入密码
  4. 点击 `login-btn-submit`
- **验证方式**: 跳转到 /dashboard，页面显示用户信息

#### WF-003 创建者创建团队
- **操作用户**: creator
- **测试步骤**:
  1. 访问 /teams 页面
  2. 点击 `team-list-btn-create`
  3. 在 `team-list-dlg-create` 弹窗中：
     - `team-list-dlg-create-inp-name` 输入"流程测试团队"
     - `team-list-dlg-create-txtarea-desc` 输入"端到端流程测试团队"
  4. 点击 `team-list-dlg-create-btn-submit`
- **验证方式**: 弹窗关闭，团队卡片出现在列表中

#### WF-004 创建者邀请成员
- **操作用户**: creator
- **测试步骤**:
  1. 点击进入团队详情页
  2. 点击 `team-detail-tab-members`
  3. 对每个成员（产品经理、开发、测试）重复：
     a. 点击 `team-members-btn-invite`
     b. 在 `team-members-dlg-invite` 弹窗的 `team-members-dlg-invite-inp-identifier` 输入成员邮箱
     c. 点击 `team-members-dlg-invite-btn-submit`
- **验证方式**: 每次邀请后显示"邀请已发送"

#### WF-005 成员接受邀请
- **操作用户**: pm / dev / tester（依次）
- **测试步骤**:
  1. 切换登录态到对应成员
  2. 访问 /dashboard
  3. 点击 `dashboard-tab-pending` → `dashboard-tab-pending-invitations`
  4. 点击 `dashboard-btn-accept-invitation-{id}`
- **验证方式**: 邀请消失

#### WF-006 创建者创建自定义角色
- **操作用户**: creator
- **测试步骤**:
  1. 进入团队详情页，点击 `team-detail-tab-roles`
  2. 点击 `team-roles-btn-create`
  3. 创建"产品经理"角色：
     - `team-roles-dlg-edit-inp-name` 输入"产品经理"
     - `team-roles-dlg-edit-txtarea-desc` 输入"管理需求和迭代"
     - 勾选权限：requirement:create, requirement:edit, task:create
     - 点击 `team-roles-dlg-edit-btn-save`
  4. 创建"开发工程师"角色：
     - 名称"开发工程师"，权限：task:create, task:edit
  5. 创建"测试工程师"角色：
     - 名称"测试工程师"，权限：task:create, task:edit
- **验证方式**: 角色列表中出现 3 个新角色

#### WF-007 创建者给成员分配角色
- **操作用户**: creator
- **测试步骤**:
  1. 在成员 tab 中，点击 `team-members-btn-roles-user-{userId}` 给每个成员分配角色
  2. 在 `team-members-dlg-roles` 弹窗中勾选对应角色
  3. 点击 `team-members-dlg-roles-btn-save`
- **验证方式**: 成员列表显示对应角色名

#### WF-008 创建者创建项目
- **操作用户**: creator
- **测试步骤**:
  1. 在团队详情页点击 `team-detail-tab-projects`
  2. 点击 `project-list-btn-create`
  3. 填写项目名称和描述
  4. 点击 `project-list-dlg-create-btn-submit`
- **验证方式**: 项目列表中出现新项目

---

### 阶段二：需求阶段

#### WF-009 产品经理登录并创建迭代
- **操作用户**: pm
- **测试步骤**:
  1. 切换登录态到产品经理
  2. 进入项目详情页
  3. 点击 `project-detail-tab-iterations`
  4. 点击 `iteration-list-btn-create`
  5. 填写迭代名称、目标、开始/结束日期
  6. 点击 `iteration-list-dlg-create-btn-submit`
- **验证方式**: 迭代列表中出现新迭代，状态为"计划中"

#### WF-010 产品经理创建需求
- **操作用户**: pm
- **测试步骤**:
  1. 进入迭代看板页（点击 `iteration-list-btn-kanban-{id}`）
  2. 点击 `iteration-kanban-btn-add-req`
  3. 填写需求标题、类型、优先级、描述
  4. 点击 `iteration-kanban-dlg-create-req-btn-submit`
- **验证方式**: 看板中出现新需求卡片

#### WF-011 产品经理提交需求审核
- **操作用户**: pm
- **测试步骤**:
  1. 点击需求卡片进入详情页
  2. 点击 `req-detail-btn-submit-req-review`
  3. 在弹窗中选择审核人（开发）
  4. 点击确认
- **验证方式**: 步骤条进入审核状态

#### WF-012 开发审核通过需求
- **操作用户**: dev
- **测试步骤**:
  1. 切换登录态到开发
  2. 访问需求详情页
  3. 点击 `req-detail-btn-approve`
- **验证方式**: 步骤条进入"编写规范"步骤

#### WF-013 开发编写规范
- **操作用户**: dev
- **测试步骤**:
  1. 点击 `req-detail-tab-spec`
  2. 在 `req-detail-txtarea-spec-content` 中编写规范文档
  3. 点击 `req-detail-btn-save-spec`
- **验证方式**: 显示保存成功

#### WF-014 开发提交规范审核
- **操作用户**: dev
- **测试步骤**:
  1. 点击 `req-detail-btn-submit-spec-review`
  2. 选择审核人（产品经理）
  3. 点击确认
- **验证方式**: 步骤条进入规范审核状态

#### WF-015 产品经理审核通过规范
- **操作用户**: pm
- **测试步骤**:
  1. 切换登录态到产品经理
  2. 通过 API approve spec
- **验证方式**: 需求状态变为 drafting_tests

#### WF-016 测试编写测试用例
- **操作用户**: tester
- **测试步骤**:
  1. 切换登录态到测试
  2. 访问需求详情页
  3. 点击 `req-detail-btn-add-test-case`
  4. 在弹窗中填写用例标题、类型、前置条件、步骤、预期结果
  5. 点击 `req-detail-dlg-test-case-btn-save`
- **验证方式**: 测试用例列表中出现新用例

#### WF-017 测试提交测试用例审核
- **操作用户**: tester
- **测试步骤**:
  1. 点击 `req-detail-btn-submit-tests-review`
  2. 选择审核人（产品经理）
  3. 点击确认
- **验证方式**: 步骤条进入测试用例审核状态

#### WF-018 产品经理审核通过测试用例
- **操作用户**: pm
- **测试步骤**:
  1. 切换登录态到产品经理
  2. 通过 API approve（reviewing_tests → approved）
- **验证方式**: 需求状态变为 approved

---

### 阶段三：任务与完成

#### WF-019 开发创建开发任务
- **操作用户**: dev
- **测试步骤**:
  1. 切换登录态到开发
  2. 访问需求详情页
  3. 点击 `req-detail-tab-tasks`
  4. 点击 `req-detail-btn-add-task`
  5. 填写任务标题、描述、选择指派人（自己）
  6. 点击 `req-detail-dlg-add-task-btn-submit`
- **验证方式**: 任务列表中出现新任务

#### WF-020 开发执行任务（编码）
- **操作用户**: dev
- **测试步骤**:
  1. 点击任务进入详情页
  2. 点击 `task-detail-btn-start`（pending → coding）
- **验证方式**: 任务状态变为"编码中"

#### WF-021 开发进入测试阶段
- **操作用户**: dev
- **测试步骤**:
  1. 点击 `task-detail-btn-start-testing`（coding → testing）
- **验证方式**: 状态变为"测试中"，出现测试执行 tab

#### WF-022 测试填写测试结果
- **操作用户**: tester
- **测试步骤**:
  1. 切换登录态到测试
  2. 访问任务详情页
  3. 在 `task-detail-tbl-test-records` 中点击 `task-detail-btn-record-{id}`
  4. 选择状态"通过"，填写实际结果
  5. 点击 `task-detail-dlg-record-btn-save`
- **验证方式**: 测试记录状态更新为"通过"

#### WF-023 完成任务
- **操作用户**: dev
- **测试步骤**:
  1. 切换登录态到开发
  2. 访问任务详情页
  3. 点击 `task-detail-btn-complete`
- **验证方式**: 任务状态变为"已完成"

#### WF-024 产品经理启动迭代
- **操作用户**: pm
- **测试步骤**:
  1. 切换登录态到产品经理
  2. 进入项目详情的迭代 tab
  3. 点击 `iteration-list-btn-start-{id}`
  4. 确认启动
- **验证方式**: 迭代状态变为"进行中"

#### WF-025 产品经理完成迭代
- **操作用户**: pm
- **测试步骤**:
  1. 点击 `iteration-list-btn-complete-{id}`
  2. 确认完成
- **验证方式**: 迭代状态变为"已完成"
