# 前端页面结构与元素编码

技术栈: Vue 3

页面中的每个可交互元素和展示信息的元素都需要一个唯一编码，用于编写端到端测试用例。

编码格式: `{页面编码}-{元素类型}-{名称}`

元素类型:
| 类型 | 说明 |
|------|------|
| btn | 按钮 |
| inp | 输入框 |
| sel | 下拉选择 |
| tbl | 表格 |
| frm | 表单 |
| dlg | 弹窗 |
| txt | 文本展示 |
| tab | tab页签 |
| card | 卡片 |
| pag | 分页器 |
| chk | 复选框 |
| rd | 单选 |
| txtarea | 文本域 |
| upload | 上传 |
| tag | 标签 |
| badge | 徽章 |
| breadcrumb | 面包屑 |
| step | 步骤条 |
| list | 列表 |

---

## 1. 登录页 /login

页面编码: `login`

布局: 居中卡片式登录表单

| 编码 | 类型 | 说明 |
|------|------|------|
| login-inp-email | inp | 邮箱输入框 |
| login-inp-password | inp | 密码输入框 |
| login-chk-remember | chk | 记住登录 |
| login-btn-submit | btn | 登录按钮 |
| login-btn-register | btn | 去注册链接 |
| login-btn-forgot | btn | 忘记密码链接 |

---

## 2. 注册页 /register

页面编码: `register`

| 编码 | 类型 | 说明 |
|------|------|------|
| register-inp-email | inp | 邮箱 |
| register-inp-nickname | inp | 昵称 |
| register-inp-password | inp | 密码 |
| register-inp-confirm-password | inp | 确认密码 |
| register-btn-submit | btn | 注册按钮 |
| register-btn-login | btn | 去登录链接 |

---

## 3. 忘记密码页 /forgot-password

页面编码: `forgot`

| 编码 | 类型 | 说明 |
|------|------|------|
| forgot-inp-email | inp | 邮箱 |
| forgot-btn-submit | btn | 发送重置邮件 |

---

## 4. 重置密码页 /reset-password

页面编码: `reset`

| 编码 | 类型 | 说明 |
|------|------|------|
| reset-inp-password | inp | 新密码 |
| reset-inp-confirm | inp | 确认新密码 |
| reset-btn-submit | btn | 重置密码 |

---

## 5. 个人中心 /dashboard

页面编码: `dashboard`

布局: 左侧导航 + 右侧内容区

### 左侧导航

| 编码 | 类型 | 说明 |
|------|------|------|
| dashboard-tab-teams | tab | 我的团队 |
| dashboard-tab-pending | tab | 待处理事项 |
| dashboard-tab-profile | tab | 个人信息 |

### 我的团队内容

| 编码 | 类型 | 说明 |
|------|------|------|
| dashboard-list-teams | list | 团队列表，每项显示团队名称、角色 |
| dashboard-btn-create-team | btn | 创建团队按钮 |

### 待处理事项

| 编码 | 类型 | 说明 |
|------|------|------|
| dashboard-tab-pending-reviews | tab | 待审核 |
| dashboard-tab-pending-tasks | tab | 待执行任务 |
| dashboard-tab-pending-invitations | tab | 待处理邀请 |
| dashboard-list-reviews | list | 待审核列表（需求标题、审核类型） |
| dashboard-list-tasks | list | 待执行任务列表 |
| dashboard-list-invitations | list | 邀请列表 |
| dashboard-btn-accept-invitation-{id} | btn | 接受邀请 |
| dashboard-btn-reject-invitation-{id} | btn | 拒绝邀请 |

### 个人信息

| 编码 | 类型 | 说明 |
|------|------|------|
| dashboard-txt-email | txt | 邮箱展示 |
| dashboard-inp-nickname | inp | 昵称 |
| dashboard-upload-avatar | upload | 头像上传 |
| dashboard-btn-save-profile | btn | 保存信息 |
| dashboard-btn-change-password | btn | 修改密码（弹出弹窗） |
| dashboard-dlg-password | dlg | 修改密码弹窗 |
| dashboard-dlg-password-inp-old | inp | 旧密码 |
| dashboard-dlg-password-inp-new | inp | 新密码 |
| dashboard-dlg-password-inp-confirm | inp | 确认新密码 |
| dashboard-dlg-password-btn-submit | btn | 确认修改 |

---

## 6. 团队详情页 /teams/:teamId

页面编码: `team-detail`

布局: 顶部团队信息 + tab切换（项目/成员/角色/设置）

| 编码 | 类型 | 说明 |
|------|------|------|
| team-detail-txt-name | txt | 团队名称 |
| team-detail-txt-description | txt | 团队描述 |
| team-detail-txt-owner | txt | 团队所有者 |
| team-detail-tab-projects | tab | 项目tab |
| team-detail-tab-members | tab | 成员tab |
| team-detail-tab-roles | tab | 角色tab |
| team-detail-tab-settings | tab | 设置tab |

---

## 7. 团队成员管理（team-detail 的成员tab）

页面编码: `team-members`

| 编码 | 类型 | 说明 |
|------|------|------|
| team-members-btn-invite | btn | 邀请成员按钮 |
| team-members-dlg-invite | dlg | 邀请成员弹窗 |
| team-members-dlg-invite-inp-identifier | inp | 用户名/用户ID输入框 |
| team-members-dlg-invite-btn-submit | btn | 发送邀请 |
| team-members-sel-role-filter | sel | 按角色筛选下拉 |
| team-members-tbl-members | tbl | 成员列表表格（列: 昵称、邮箱、角色、加入时间、操作） |
| team-members-btn-remove-{userId} | btn | 移出成员 |
| team-members-btn-roles-{userId} | btn | 分配角色（弹出弹窗） |
| team-members-dlg-roles | dlg | 角色分配弹窗 |
| team-members-dlg-roles-chk-role-{roleId} | chk | 角色复选框 |
| team-members-dlg-roles-btn-save | btn | 保存 |

---

## 8. 团队角色管理（team-detail 的角色tab）

页面编码: `team-roles`

| 编码 | 类型 | 说明 |
|------|------|------|
| team-roles-btn-create | btn | 创建角色按钮 |
| team-roles-tbl-roles | tbl | 角色列表表格（列: 角色名、权限数、是否内置、操作） |
| team-roles-btn-edit-{roleId} | btn | 编辑角色 |
| team-roles-btn-delete-{roleId} | btn | 删除角色 |
| team-roles-dlg-edit | dlg | 创建/编辑角色弹窗 |
| team-roles-dlg-edit-inp-name | inp | 角色名称 |
| team-roles-dlg-edit-txtarea-desc | txtarea | 角色描述 |
| team-roles-dlg-edit-chk-permission-{perm} | chk | 权限复选框（按分组显示） |
| team-roles-dlg-edit-btn-save | btn | 保存 |

### 权限分组

| 分组 | 权限编码 |
|------|----------|
| 项目管理 | `project:create`, `project:edit`, `project:archive`, `project:delete` |
| 迭代管理 | `iteration:create`, `iteration:edit`, `iteration:start`, `iteration:complete` |
| 需求管理 | `requirement:create`, `requirement:edit`, `requirement:delete` |
| 需求审核 | `requirement:review_req`, `requirement:review_spec`, `requirement:review_tests` |
| 任务管理 | `task:create`, `task:edit`, `task:delete`, `task:test`, `task:complete` |
| 成员管理 | `member:invite`, `member:remove`, `member:assign_role` |
| 规范模板 | `spec_template:edit` |

---

## 9. 团队设置（team-detail 的设置tab）

页面编码: `team-settings`

| 编码 | 类型 | 说明 |
|------|------|------|
| team-settings-inp-name | inp | 团队名称 |
| team-settings-txtarea-desc | txtarea | 团队描述 |
| team-settings-btn-save | btn | 保存修改 |
| team-settings-btn-transfer | btn | 转让团队（弹出弹窗） |
| team-settings-dlg-transfer | dlg | 转让团队弹窗 |
| team-settings-dlg-transfer-sel-owner | sel | 选择新所有者 |
| team-settings-dlg-transfer-btn-confirm | btn | 确认转让 |
| team-settings-btn-dissolve | btn | 解散团队（弹出确认弹窗） |
| team-settings-dlg-dissolve | dlg | 解散确认弹窗 |
| team-settings-dlg-dissolve-btn-confirm | btn | 确认解散 |

---

## 10. 项目列表（team-detail 的项目tab）

页面编码: `project-list`

| 编码 | 类型 | 说明 |
|------|------|------|
| project-list-btn-create | btn | 创建项目按钮 |
| project-list-sel-status | sel | 状态筛选（活跃/归档） |
| project-list-tbl-projects | tbl | 项目列表表格（列: 名称、描述、开始日期、结束日期、状态、当前迭代、操作） |
| project-list-btn-archive-{id} | btn | 归档 |
| project-list-btn-delete-{id} | btn | 删除 |

---

## 11. 项目详情 /projects/:projectId

页面编码: `project-detail`

| 编码 | 类型 | 说明 |
|------|------|------|
| project-detail-txt-name | txt | 项目名称 |
| project-detail-txt-description | txt | 项目描述 |
| project-detail-txt-start-date | txt | 开始日期 |
| project-detail-txt-end-date | txt | 结束日期 |
| project-detail-txt-status | txt | 状态 |
| project-detail-txt-stat-req | txt | 需求完成统计 |
| project-detail-txt-stat-task | txt | 任务完成统计 |
| project-detail-txt-stat-test | txt | 测试通过率 |
| project-detail-tab-iterations | tab | 迭代tab |
| project-detail-btn-edit | btn | 编辑项目（弹出弹窗） |
| project-detail-btn-archive | btn | 归档项目 |
| project-detail-dlg-edit | dlg | 编辑项目弹窗 |
| project-detail-dlg-edit-inp-name | inp | 项目名称 |
| project-detail-dlg-edit-txtarea-desc | txtarea | 项目描述 |
| project-detail-dlg-edit-inp-start-date | inp | 开始日期 |
| project-detail-dlg-edit-btn-save | btn | 保存 |

---

## 12. 迭代列表（project-detail 的迭代tab）

页面编码: `iteration-list`

| 编码 | 类型 | 说明 |
|------|------|------|
| iteration-list-btn-create | btn | 创建迭代按钮 |
| iteration-list-sel-status | sel | 状态筛选 |
| iteration-list-tbl-iterations | tbl | 迭代列表表格（列: 名称、目标、开始日期、截止日期、状态、需求数、任务数、操作） |
| iteration-list-btn-start-{id} | btn | 启动迭代 |
| iteration-list-btn-complete-{id} | btn | 完成迭代 |
| iteration-list-btn-kanban-{id} | btn | 查看看板 |
| iteration-list-btn-edit-{id} | btn | 编辑迭代 |
| iteration-list-dlg-create | dlg | 创建迭代弹窗 |
| iteration-list-dlg-create-inp-name | inp | 迭代名称 |
| iteration-list-dlg-create-txtarea-goal | txtarea | 迭代目标 |
| iteration-list-dlg-create-inp-start-date | inp | 开始日期 |
| iteration-list-dlg-create-inp-end-date | inp | 截止日期 |
| iteration-list-dlg-create-btn-submit | btn | 提交 |

---

## 13. 迭代看板 /iterations/:iterationId/kanban

页面编码: `iteration-kanban`

布局: 顶部迭代信息 + 看板视图（多列，每列一个需求状态）

### 顶部迭代信息

| 编码 | 类型 | 说明 |
|------|------|------|
| iteration-kanban-txt-name | txt | 迭代名称 |
| iteration-kanban-txt-goal | txt | 迭代目标 |
| iteration-kanban-txt-stat | txt | 统计信息 |

### 看板列

| 编码 | 类型 | 说明 |
|------|------|------|
| iteration-kanban-col-drafting-req | card | 编写需求列 |
| iteration-kanban-col-reviewing-req | card | 需求审核列 |
| iteration-kanban-col-drafting-spec | card | 编写规范列 |
| iteration-kanban-col-reviewing-spec | card | 规范审核列 |
| iteration-kanban-col-drafting-tests | card | 编写测试用例列 |
| iteration-kanban-col-reviewing-tests | card | 测试用例审核列 |
| iteration-kanban-col-approved | card | 已通过列 |

### 需求卡片

| 编码 | 类型 | 说明 |
|------|------|------|
| iteration-kanban-card-req-{id} | card | 需求卡片（显示: 标题、类型标签、优先级） |
| iteration-kanban-btn-req-{id} | btn | 点击需求卡片进入详情 |
| iteration-kanban-btn-add-req | btn | 添加需求按钮（弹出创建弹窗） |

### 创建需求弹窗

| 编码 | 类型 | 说明 |
|------|------|------|
| iteration-kanban-dlg-create-req | dlg | 创建需求弹窗 |
| iteration-kanban-dlg-create-req-inp-title | inp | 需求标题 |
| iteration-kanban-dlg-create-req-sel-type | sel | 需求类型（功能/优化/缺陷） |
| iteration-kanban-dlg-create-req-inp-priority | inp | 优先级（数字） |
| iteration-kanban-dlg-create-req-txtarea-desc | txtarea | 描述 |
| iteration-kanban-dlg-create-req-txtarea-type-detail | txtarea | 类型详情（根据类型动态变化标签） |
| iteration-kanban-dlg-create-req-btn-submit | btn | 提交 |

---

## 14. 需求详情 /requirements/:reqId

页面编码: `req-detail`

布局: 顶部需求信息 + 左侧步骤导航 + 右侧步骤内容

### 顶部需求信息

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-txt-title | txt | 需求标题 |
| req-detail-tag-type | tag | 类型标签（功能/优化/缺陷） |
| req-detail-txt-priority | txt | 优先级 |
| req-detail-txt-status | txt | 当前状态 |
| req-detail-txt-created-by | txt | 创建者 |
| req-detail-txt-description | txt | 需求描述 |
| req-detail-txt-type-detail | txt | 类型详情 |

### 步骤导航

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-step-nav | step | 步骤导航条（编写需求→编写规范→编写测试用例→已通过） |
| req-detail-step-nav-step-req | step | 第1步: 编写需求 |
| req-detail-step-nav-step-spec | step | 第2步: 编写规范 |
| req-detail-step-nav-step-tests | step | 第3步: 编写测试用例 |
| req-detail-step-nav-step-approved | step | 第4步: 已通过 |

### 编写需求步骤内容

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-btn-edit-req | btn | 编辑需求按钮 |
| req-detail-btn-delete-req | btn | 删除需求按钮 |
| req-detail-btn-submit-req-review | btn | 提交审核按钮 |
| req-detail-dlg-submit-review | dlg | 提交审核弹窗 |
| req-detail-dlg-submit-review-sel-reviewer | sel | 选择审核人 |
| req-detail-dlg-submit-review-btn-confirm | btn | 确认提交 |

### 审核中状态内容

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-txt-reviewer | txt | 审核人 |
| req-detail-txt-review-status | txt | 审核状态（待审核/已通过/已驳回） |
| req-detail-txt-review-comment | txt | 审核意见 |
| req-detail-btn-approve | btn | 通过按钮（仅审核人可见） |
| req-detail-btn-reject | btn | 驳回按钮（仅审核人可见） |
| req-detail-dlg-reject | dlg | 驳回弹窗 |
| req-detail-dlg-reject-txtarea-comment | txtarea | 驳回理由 |
| req-detail-dlg-reject-btn-confirm | btn | 确认驳回 |

### 编写规范步骤内容

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-tab-spec | tab | 规范文档tab |
| req-detail-tab-spec-versions | tab | 版本历史tab |
| req-detail-txtarea-spec-content | txtarea | 规范内容编辑器（结构化，按模板分节） |
| req-detail-btn-save-spec | btn | 保存规范 |
| req-detail-btn-submit-spec-review | btn | 提交规范审核 |
| req-detail-list-spec-versions | list | 版本列表 |
| req-detail-btn-spec-version-{v} | btn | 查看历史版本 |

### 编写测试用例步骤内容

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-btn-add-test-case | btn | 添加测试用例 |
| req-detail-tbl-test-cases | tbl | 测试用例列表表格（列: 用例编号、标题、类型、关联API/元素、操作） |
| req-detail-btn-edit-test-case-{id} | btn | 编辑用例 |
| req-detail-btn-delete-test-case-{id} | btn | 删除用例 |
| req-detail-dlg-test-case | dlg | 创建/编辑测试用例弹窗 |
| req-detail-dlg-test-case-inp-title | inp | 用例标题 |
| req-detail-dlg-test-case-sel-type | sel | 用例类型（api/e2e） |
| req-detail-dlg-test-case-txtarea-precondition | txtarea | 前置条件 |
| req-detail-dlg-test-case-txtarea-steps | txtarea | 操作步骤 |
| req-detail-dlg-test-case-txtarea-expected | txtarea | 预期结果 |
| req-detail-dlg-test-case-inp-related-api | inp | 关联API路径 |
| req-detail-dlg-test-case-inp-related-element | inp | 关联元素编码 |
| req-detail-dlg-test-case-btn-save | btn | 保存用例 |
| req-detail-btn-submit-tests-review | btn | 提交测试用例审核 |

### 已通过状态内容

| 编码 | 类型 | 说明 |
|------|------|------|
| req-detail-tab-tasks | tab | 任务tab |
| req-detail-tab-test-stats | tab | 测试统计tab |
| req-detail-btn-add-task | btn | 创建任务 |
| req-detail-tbl-tasks | tbl | 任务列表表格（列: 标题、指派人、状态、操作） |
| req-detail-dlg-add-task | dlg | 创建任务弹窗 |
| req-detail-dlg-add-task-inp-title | inp | 任务标题 |
| req-detail-dlg-add-task-txtarea-desc | txtarea | 任务描述 |
| req-detail-dlg-add-task-sel-assignee | sel | 指派人（下拉选团队成员） |
| req-detail-dlg-add-task-btn-submit | btn | 提交 |
| req-detail-txt-test-stats | txt | 测试用例统计（总数、通过、失败、跳过、通过率） |

---

## 15. 任务详情 /tasks/:taskId

页面编码: `task-detail`

### 基本信息

| 编码 | 类型 | 说明 |
|------|------|------|
| task-detail-txt-title | txt | 任务标题 |
| task-detail-txt-description | txt | 任务描述 |
| task-detail-txt-status | txt | 任务状态 |
| task-detail-txt-assignee | txt | 指派人 |
| task-detail-txt-requirement | txt | 关联需求（可点击跳转） |
| task-detail-btn-start | btn | 开始编码（仅pending状态） |
| task-detail-btn-edit | btn | 编辑任务（仅pending/coding状态） |
| task-detail-btn-delete | btn | 删除任务（仅pending/coding状态） |
| task-detail-btn-start-testing | btn | 开始测试（仅coding状态） |
| task-detail-btn-complete | btn | 完成任务（仅testing状态且测试全通过） |

### 规范文档参考区域

| 编码 | 类型 | 说明 |
|------|------|------|
| task-detail-tab-spec | tab | 规范文档tab |
| task-detail-txt-spec-content | txt | 规范文档内容（只读） |

### 测试执行区域（仅testing状态显示）

| 编码 | 类型 | 说明 |
|------|------|------|
| task-detail-tab-test-exec | tab | 测试执行tab |
| task-detail-tbl-test-records | tbl | 测试执行记录表格（列: 用例编号、标题、状态、实际结果、失败原因、操作） |
| task-detail-btn-record-{id} | btn | 填写/编辑执行结果 |
| task-detail-dlg-record | dlg | 填写执行结果弹窗 |
| task-detail-dlg-record-sel-status | sel | 执行状态（通过/失败/跳过） |
| task-detail-dlg-record-txtarea-result | txtarea | 实际结果 |
| task-detail-dlg-record-txtarea-reason | txtarea | 失败原因（失败时必填） |
| task-detail-dlg-record-btn-save | btn | 保存 |
| task-detail-txt-test-summary | txt | 本轮测试汇总（总数、通过、失败、跳过） |

### 历史执行记录

| 编码 | 类型 | 说明 |
|------|------|------|
| task-detail-list-exec-history | list | 历史执行轮次列表 |
| task-detail-btn-exec-round-{id} | btn | 查看某轮详情 |

---

## 16. 管理员用户管理 /admin/users

页面编码: `admin-users`

| 编码 | 类型 | 说明 |
|------|------|------|
| admin-users-btn-create | btn | 创建用户按钮 |
| admin-users-inp-search | inp | 搜索框 |
| admin-users-tbl-users | tbl | 用户列表表格（列: ID、邮箱、昵称、是否激活、是否管理员、创建时间、操作） |
| admin-users-btn-toggle-status-{id} | btn | 启用/禁用切换 |
| admin-users-pag-list | pag | 分页器 |
| admin-users-dlg-create | dlg | 创建用户弹窗 |
| admin-users-dlg-create-inp-email | inp | 邮箱 |
| admin-users-dlg-create-inp-nickname | inp | 昵称 |
| admin-users-dlg-create-inp-password | inp | 初始密码 |
| admin-users-dlg-create-btn-submit | btn | 创建 |

---

## 17. 团队规范模板（team-detail 的设置tab中）

页面编码: `team-spec-template`

| 编码 | 类型 | 说明 |
|------|------|------|
| team-spec-template-btn-edit | btn | 编辑模板按钮 |
| team-spec-template-txt-sections | txt | 模板结构展示（分节列表） |
| team-spec-template-dlg-edit | dlg | 编辑模板弹窗 |
| team-spec-template-dlg-edit-list-sections | list | 节列表（可添加/删除/排序） |
| team-spec-template-dlg-edit-btn-save | btn | 保存模板 |
