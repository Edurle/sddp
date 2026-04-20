# 端到端测试用例 — 个人中心、管理员用户管理

> 元素编码前缀：`dashboard`（个人中心）、`admin-users`（管理员用户管理）

---

## 1. 个人中心 /dashboard

### 查看我的团队列表

- **用例编号**: E2E-DASH-001
- **前置条件**: 用户已登录，已加入1个团队
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-teams`
- **验证方式**: `dashboard-list-teams` 显示已加入的团队名称和角色

### 创建团队

- **用例编号**: E2E-DASH-002
- **前置条件**: 用户已登录
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-teams`
  3. 点击 `dashboard-btn-create-team`
  4. 在弹窗中填写团队名称和描述
  5. 点击确认
- **验证方式**: 团队列表中出现新创建的团队，用户角色为"团队所有者"

### 查看待审核事项

- **用例编号**: E2E-DASH-003
- **前置条件**: 用户被指定为某个需求的审核人，该需求已提交审核
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-pending`
  3. 点击 `dashboard-tab-pending-reviews`
- **验证方式**: `dashboard-list-reviews` 显示待审核需求，含需求标题和审核类型

### 查看待执行任务

- **用例编号**: E2E-DASH-004
- **前置条件**: 用户被分配了任务
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-pending`
  3. 点击 `dashboard-tab-pending-tasks`
- **验证方式**: `dashboard-list-tasks` 显示被分配的任务

### 接受团队邀请

- **用例编号**: E2E-DASH-005
- **前置条件**: 用户收到一个团队邀请
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-pending`
  3. 点击 `dashboard-tab-pending-invitations`
  4. 在邀请列表中点击 `dashboard-btn-accept-invitation-{id}`
- **验证方式**: 邀请消失，我的团队列表中出现该团队

### 拒绝团队邀请

- **用例编号**: E2E-DASH-006
- **前置条件**: 用户收到一个团队邀请
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-pending`
  3. 点击 `dashboard-tab-pending-invitations`
  4. 点击 `dashboard-btn-reject-invitation-{id}`
- **验证方式**: 邀请消失，团队列表不出现该团队

### 修改个人信息

- **用例编号**: E2E-DASH-007
- **前置条件**: 用户已登录
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-profile`
  3. 在 `dashboard-inp-nickname` 修改昵称为"新昵称"
  4. 点击 `dashboard-btn-save-profile`
- **验证方式**: 页面显示保存成功，昵称更新

### 修改密码

- **用例编号**: E2E-DASH-008
- **前置条件**: 用户已登录
- **测试步骤**:
  1. 访问 /dashboard
  2. 点击 `dashboard-tab-profile`
  3. 点击 `dashboard-btn-change-password`
  4. 在 `dashboard-dlg-password` 弹窗中：
     - `dashboard-dlg-password-inp-old` 输入旧密码
     - `dashboard-dlg-password-inp-new` 输入新密码
     - `dashboard-dlg-password-inp-confirm` 输入确认新密码
  5. 点击 `dashboard-dlg-password-btn-submit`
- **验证方式**: 弹窗关闭，显示"密码修改成功"

### 修改密码 - 旧密码错误

- **用例编号**: E2E-DASH-009
- **前置条件**: 用户已登录
- **测试步骤**:
  1. 同 E2E-DASH-008 步骤，但 `dashboard-dlg-password-inp-old` 输入错误旧密码
  2. 点击 `dashboard-dlg-password-btn-submit`
- **验证方式**: 弹窗不关闭，显示"旧密码错误"

---

## 2. 管理员用户管理 /admin/users

### 查看用户列表

- **用例编号**: E2E-ADMIN-001
- **前置条件**: 以管理员身份登录，数据库有用户数据
- **测试步骤**:
  1. 访问 /admin/users
  2. 查看 `admin-users-tbl-users` 表格
- **验证方式**: 表格显示用户列表（邮箱、昵称、状态等列）

### 搜索用户

- **用例编号**: E2E-ADMIN-002
- **前置条件**: 同 E2E-ADMIN-001
- **测试步骤**:
  1. 在 `admin-users-inp-search` 输入 test@example
  2. 等待表格刷新
- **验证方式**: `admin-users-tbl-users` 仅显示匹配的用户

### 创建用户

- **用例编号**: E2E-ADMIN-003
- **前置条件**: 管理员已登录
- **测试步骤**:
  1. 点击 `admin-users-btn-create`
  2. 在 `admin-users-dlg-create` 弹窗中：
     - `admin-users-dlg-create-inp-email` 输入 new@example.com
     - `admin-users-dlg-create-inp-nickname` 输入 新用户
     - `admin-users-dlg-create-inp-password` 输入 InitPass123
  3. 点击 `admin-users-dlg-create-btn-submit`
- **验证方式**: 弹窗关闭，用户列表中出现新用户

### 创建用户 - 邮箱已存在

- **用例编号**: E2E-ADMIN-004
- **前置条件**: 数据库已存在 exist@example.com
- **测试步骤**:
  1. 同 E2E-ADMIN-003，但邮箱输入 exist@example.com
  2. 点击提交
- **验证方式**: 弹窗显示"邮箱已注册"错误

### 禁用用户

- **用例编号**: E2E-ADMIN-005
- **前置条件**: 管理员已登录，有活跃用户
- **测试步骤**:
  1. 在 `admin-users-tbl-users` 中找到目标用户
  2. 点击 `admin-users-btn-toggle-status-{id}`
  3. 确认操作
- **验证方式**: 该用户状态列变为"已禁用"

### 启用用户

- **用例编号**: E2E-ADMIN-006
- **前置条件**: 有已禁用用户
- **测试步骤**:
  1. 找到已禁用用户
  2. 点击 `admin-users-btn-toggle-status-{id}`
  3. 确认操作
- **验证方式**: 用户状态变为"已启用"

### 翻页

- **用例编号**: E2E-ADMIN-007
- **前置条件**: 用户数超过每页数量
- **测试步骤**:
  1. 点击 `admin-users-pag-list` 下一页按钮
- **验证方式**: 表格显示第二页数据

### 非管理员无权访问

- **用例编号**: E2E-ADMIN-008
- **前置条件**: 以普通用户登录
- **测试步骤**:
  1. 访问 /admin/users
- **验证方式**: 页面显示无权限提示或跳转
