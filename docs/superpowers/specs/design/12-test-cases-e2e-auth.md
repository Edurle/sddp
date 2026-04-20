# 端到端测试用例 — 认证页面

> Playwright E2E 测试用例，使用前端页面元素编码描述交互。
> 元素编码格式：`{页面编码}-{类型}-{名称}`

## 元素编码前缀说明

| 前缀    | 页面         | 路由            |
|---------|-------------|-----------------|
| login   | 登录页       | /login          |
| register| 注册页       | /register       |
| forgot  | 忻记密码页   | /forgot-password|
| reset   | 重置密码页   | /reset-password |

---

## 1. 注册页面 /register

### 成功注册

- **用例编号**: E2E-AUTH-001
- **前置条件**: 数据库中不存在邮箱 test@example.com
- **测试步骤**:
  1. 访问 /register 页面
  2. 在 `register-inp-email` 输入 test@example.com
  3. 在 `register-inp-nickname` 输入 测试用户
  4. 在 `register-inp-password` 输入 Password123
  5. 在 `register-inp-confirm-password` 输入 Password123
  6. 点击 `register-btn-submit`
- **验证方式**: 页面跳转到登录页，显示"注册成功，请查收验证邮件"提示

### 注册 - 邮箱格式错误

- **用例编号**: E2E-AUTH-002
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /register 页面
  2. 在 `register-inp-email` 输入 invalid-email
  3. 填写其他必填项
  4. 点击 `register-btn-submit`
- **验证方式**: 邮箱输入框显示格式错误提示，未提交

### 注册 - 密码不一致

- **用例编号**: E2E-AUTH-003
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /register 页面
  2. 填写邮箱和昵称
  3. 在 `register-inp-password` 输入 Password123
  4. 在 `register-inp-confirm-password` 输入 Different456
  5. 点击 `register-btn-submit`
- **验证方式**: 确认密码框显示不一致提示，未提交

### 注册 - 邮箱已注册

- **用例编号**: E2E-AUTH-004
- **前置条件**: 数据库已存在 exist@example.com
- **测试步骤**:
  1. 访问 /register 页面
  2. 填写所有字段，邮箱为 exist@example.com
  3. 点击 `register-btn-submit`
- **验证方式**: 页面显示"邮箱已注册"错误提示

### 注册 - 跳转登录

- **用例编号**: E2E-AUTH-005
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /register 页面
  2. 点击 `register-btn-login`
- **验证方式**: 页面跳转到 /login

---

## 2. 登录页面 /login

### 成功登录

- **用例编号**: E2E-AUTH-006
- **前置条件**: 用户 test@example.com 已注册且邮箱已验证
- **测试步骤**:
  1. 访问 /login 页面
  2. 在 `login-inp-email` 输入 test@example.com
  3. 在 `login-inp-password` 输入 Password123
  4. 点击 `login-btn-submit`
- **验证方式**: 页面跳转到 /dashboard，显示用户昵称

### 登录 - 密码错误

- **用例编号**: E2E-AUTH-007
- **前置条件**: 用户 test@example.com 已注册
- **测试步骤**:
  1. 访问 /login 页面
  2. 在 `login-inp-email` 输入 test@example.com
  3. 在 `login-inp-password` 输入 WrongPassword
  4. 点击 `login-btn-submit`
- **验证方式**: 页面显示"邮箱或密码错误"提示

### 登录 - 邮箱未验证

- **用例编号**: E2E-AUTH-008
- **前置条件**: 用户 unverified@example.com 已注册但未验证邮箱
- **测试步骤**:
  1. 访问 /login 页面
  2. 在 `login-inp-email` 输入 unverified@example.com
  3. 在 `login-inp-password` 输入正确密码
  4. 点击 `login-btn-submit`
- **验证方式**: 页面显示"邮箱未验证"提示

### 登录 - 记住登录状态

- **用例编号**: E2E-AUTH-009
- **前置条件**: 用户已注册且验证
- **测试步骤**:
  1. 访问 /login 页面
  2. 在 `login-inp-email` 输入邮箱
  3. 在 `login-inp-password` 输入密码
  4. 勾选 `login-chk-remember`
  5. 点击 `login-btn-submit`
  6. 关闭浏览器重新打开
- **验证方式**: 重新打开后仍然登录状态，无需重新登录

### 登录 - 跳转注册

- **用例编号**: E2E-AUTH-010
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /login 页面
  2. 点击 `login-btn-register`
- **验证方式**: 页面跳转到 /register

### 登录 - 跳转忘记密码

- **用例编号**: E2E-AUTH-011
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /login 页面
  2. 点击 `login-btn-forgot`
- **验证方式**: 页面跳转到 /forgot-password

---

## 3. 忘记密码页 /forgot-password

### 发送重置邮件成功

- **用例编号**: E2E-AUTH-012
- **前置条件**: 用户 test@example.com 已注册
- **测试步骤**:
  1. 访问 /forgot-password 页面
  2. 在 `forgot-inp-email` 输入 test@example.com
  3. 点击 `forgot-btn-submit`
- **验证方式**: 页面显示"重置邮件已发送"提示

### 重置邮件 - 用户不存在也应成功

- **用例编号**: E2E-AUTH-013
- **前置条件**: 邮箱 nobody@example.com 不存在
- **测试步骤**:
  1. 访问 /forgot-password 页面
  2. 在 `forgot-inp-email` 输入 nobody@example.com
  3. 点击 `forgot-btn-submit`
- **验证方式**: 页面同样显示"重置邮件已发送"（不暴露用户是否存在）

---

## 4. 重置密码页 /reset-password

### 重置密码成功

- **用例编号**: E2E-AUTH-014
- **前置条件**: 通过重置邮件获取有效Token
- **测试步骤**:
  1. 访问 /reset-password?token=有效Token
  2. 在 `reset-inp-password` 输入 NewPassword456
  3. 在 `reset-inp-confirm` 输入 NewPassword456
  4. 点击 `reset-btn-submit`
- **验证方式**: 页面显示"密码重置成功"并跳转到登录页

### 重置密码 - Token无效

- **用例编号**: E2E-AUTH-015
- **前置条件**: 无
- **测试步骤**:
  1. 访问 /reset-password?token=invalid-token
  2. 在 `reset-inp-password` 输入 NewPassword456
  3. 在 `reset-inp-confirm` 输入 NewPassword456
  4. 点击 `reset-btn-submit`
- **验证方式**: 页面显示"链接无效或已过期"提示

### 重置密码 - 新密码不一致

- **用例编号**: E2E-AUTH-016
- **前置条件**: 有效Token
- **测试步骤**:
  1. 访问 /reset-password?token=有效Token
  2. 在 `reset-inp-password` 输入 NewPassword456
  3. 在 `reset-inp-confirm` 输入 Different789
  4. 点击 `reset-btn-submit`
- **验证方式**: 确认密码框显示不一致提示，未提交
