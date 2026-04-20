# 端到端测试用例 — 团队详情、成员、角色、设置

元素编码前缀：
- `team-detail` — 团队详情
- `team-members` — 成员管理
- `team-roles` — 角色管理
- `team-settings` — 团队设置
- `team-spec-template` — 规范模板

---

## 1. 团队详情页 /teams/:teamId

### 查看团队基本信息
- **用例编号**: E2E-TEAM-001
- **前置条件**: 已登录且为团队成员
- **测试步骤**:
  1. 访问 /teams/{teamId}
  2. 查看团队信息区域
- **验证方式**: `team-detail-txt-name` 显示团队名称，`team-detail-txt-owner` 显示所有者昵称

### Tab切换
- **用例编号**: E2E-TEAM-002
- **前置条件**: 同上
- **测试步骤**:
  1. 点击 `team-detail-tab-projects` → 显示项目列表
  2. 点击 `team-detail-tab-members` → 显示成员列表
  3. 点击 `team-detail-tab-roles` → 显示角色列表
  4. 点击 `team-detail-tab-settings` → 显示设置页面
- **验证方式**: 每次点击后内容区域切换到对应tab

---

## 2. 成员管理

### 邀请成员成功
- **用例编号**: E2E-MEMBER-001
- **前置条件**: 有 member:invite 权限，目标用户存在
- **测试步骤**:
  1. 在团队详情点击 `team-detail-tab-members`
  2. 点击 `team-members-btn-invite`
  3. 在 `team-members-dlg-invite` 弹窗中 `team-members-dlg-invite-inp-identifier` 输入目标用户名
  4. 点击 `team-members-dlg-invite-btn-submit`
- **验证方式**: 弹窗关闭，显示"邀请已发送"

### 邀请 - 用户已在团队中
- **用例编号**: E2E-MEMBER-002
- **前置条件**: 目标用户已是团队成员
- **测试步骤**:
  1. 同 E2E-MEMBER-001 步骤，输入已有成员的用户名
- **验证方式**: 弹窗显示"用户已在团队中"错误

### 按角色筛选成员
- **用例编号**: E2E-MEMBER-003
- **前置条件**: 团队有多个角色和成员
- **测试步骤**:
  1. 在 `team-members-sel-role-filter` 选择某个角色
- **验证方式**: `team-members-tbl-members` 仅显示该角色的成员

### 移出成员
- **用例编号**: E2E-MEMBER-004
- **前置条件**: 有 member:remove 权限
- **测试步骤**:
  1. 在 `team-members-tbl-members` 找到目标成员
  2. 点击 `team-members-btn-remove-{userId}`
  3. 确认操作
- **验证方式**: 该成员从列表中消失

### 分配角色
- **用例编号**: E2E-MEMBER-005
- **前置条件**: 有 member:assign_role 权限
- **测试步骤**:
  1. 在成员表格点击 `team-members-btn-roles-{userId}`
  2. 在 `team-members-dlg-roles` 弹窗中勾选 `team-members-dlg-roles-chk-role-{roleId}`
  3. 点击 `team-members-dlg-roles-btn-save`
- **验证方式**: 弹窗关闭，成员表格中该成员角色列更新

---

## 3. 角色管理

### 查看角色列表
- **用例编号**: E2E-ROLE-001
- **前置条件**: 团队成员
- **测试步骤**:
  1. 点击 `team-detail-tab-roles`
- **验证方式**: `team-roles-tbl-roles` 显示内置角色（团队所有者、团队管理员）和自定义角色

### 创建角色
- **用例编号**: E2E-ROLE-002
- **前置条件**: 有 member:assign_role 权限
- **测试步骤**:
  1. 点击 `team-roles-btn-create`
  2. 在 `team-roles-dlg-edit` 弹窗中：
     - `team-roles-dlg-edit-inp-name` 输入"开发者"
     - `team-roles-dlg-edit-txtarea-desc` 输入"开发团队成员"
     - 勾选权限：`team-roles-dlg-edit-chk-permission-task:create`、`team-roles-dlg-edit-chk-permission-task:edit`
  3. 点击 `team-roles-dlg-edit-btn-save`
- **验证方式**: 弹窗关闭，角色列表中出现新角色

### 创建角色 - 名称重复
- **用例编号**: E2E-ROLE-003
- **前置条件**: 同上，已有"开发者"角色
- **测试步骤**:
  1. 点击 `team-roles-btn-create`
  2. 名称输入已存在的"开发者"
  3. 点击保存
- **验证方式**: 弹窗显示"角色名称已存在"错误

### 编辑角色
- **用例编号**: E2E-ROLE-004
- **前置条件**: 有权限，有自定义角色
- **测试步骤**:
  1. 在 `team-roles-tbl-roles` 点击 `team-roles-btn-edit-{roleId}`
  2. 修改角色名称和权限
  3. 点击 `team-roles-dlg-edit-btn-save`
- **验证方式**: 角色列表中信息更新

### 内置角色不可编辑
- **用例编号**: E2E-ROLE-005
- **前置条件**: 查看内置角色
- **测试步骤**:
  1. 在角色列表中查看内置角色的操作列
- **验证方式**: 内置角色无编辑和删除按钮（或按钮禁用）

### 删除角色
- **用例编号**: E2E-ROLE-006
- **前置条件**: 有权限，有自定义角色
- **测试步骤**:
  1. 点击 `team-roles-btn-delete-{roleId}`
  2. 确认删除
- **验证方式**: 角色从列表中消失

---

## 4. 团队设置

### 修改团队信息
- **用例编号**: E2E-SET-001
- **前置条件**: 团队所有者或管理员
- **测试步骤**:
  1. 点击 `team-detail-tab-settings`
  2. 在 `team-settings-inp-name` 修改团队名称
  3. 在 `team-settings-txtarea-desc` 修改描述
  4. 点击 `team-settings-btn-save`
- **验证方式**: 显示保存成功，团队名称和描述更新

### 转让团队
- **用例编号**: E2E-SET-002
- **前置条件**: 团队所有者
- **测试步骤**:
  1. 点击 `team-settings-btn-transfer`
  2. 在 `team-settings-dlg-transfer` 弹窗的 `team-settings-dlg-transfer-sel-owner` 选择新所有者
  3. 点击 `team-settings-dlg-transfer-btn-confirm`
- **验证方式**: 页面刷新后所有者变更，当前用户不再是所有者

### 解散团队
- **用例编号**: E2E-SET-003
- **前置条件**: 团队所有者
- **测试步骤**:
  1. 点击 `team-settings-btn-dissolve`
  2. 在 `team-settings-dlg-dissolve` 弹窗中点击 `team-settings-dlg-dissolve-btn-confirm`
- **验证方式**: 页面跳转到个人中心，团队列表中不再显示该团队
