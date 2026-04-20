# 后端接口测试用例 - 认证、用户、管理员用户管理

> 基于 `02-api-auth-user-team-role.md` 编写，覆盖认证模块、用户模块、管理员用户管理模块。

---

## 1. 认证模块 (Auth)

### 1.1 注册

**接口**: `POST /api/v1/auth/register`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AUTH-001 | 注册成功 | 无 | `{"email":"new@example.com","password":"12345678","nickname":"新用户"}` | 0 | data 为 null，message 为"注册成功，请查收验证邮件" |
| TC-AUTH-002 | 缺少 email 字段 | 无 | `{"password":"12345678","nickname":"新用户"}` | 40001 | 参数校验失败 |
| TC-AUTH-003 | 缺少 password 字段 | 无 | `{"email":"new@example.com","nickname":"新用户"}` | 40001 | 参数校验失败 |
| TC-AUTH-004 | 缺少 nickname 字段 | 无 | `{"email":"new@example.com","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-AUTH-005 | 邮箱格式错误 | 无 | `{"email":"invalid-email","password":"12345678","nickname":"新用户"}` | 40001 | 参数校验失败，邮箱格式不合法 |
| TC-AUTH-006 | 邮箱为空字符串 | 无 | `{"email":"","password":"12345678","nickname":"新用户"}` | 40001 | 参数校验失败 |
| TC-AUTH-007 | 密码长度不足（7位） | 无 | `{"email":"new@example.com","password":"1234567","nickname":"新用户"}` | 40001 | 参数校验失败，密码需 8-64 位 |
| TC-AUTH-008 | 密码长度超限（65位） | 无 | `{"email":"new@example.com","password":"a".repeat(65),"nickname":"新用户"}` | 40001 | 参数校验失败，密码需 8-64 位 |
| TC-AUTH-009 | 昵称长度不足（1位） | 无 | `{"email":"new@example.com","password":"12345678","nickname":"A"}` | 40001 | 参数校验失败，昵称需 2-32 位 |
| TC-AUTH-010 | 昵称长度超限（33位） | 无 | `{"email":"new@example.com","password":"12345678","nickname":"A".repeat(33)}` | 40001 | 参数校验失败，昵称需 2-32 位 |
| TC-AUTH-011 | 邮箱已注册 | 数据库中已存在该邮箱用户 | `{"email":"exist@example.com","password":"12345678","nickname":"用户"}` | 40002 | 邮箱已注册 |
| TC-AUTH-012 | 请求 Body 为空 | 无 | `{}` | 40001 | 参数校验失败，所有必填字段缺失 |

---

### 1.2 验证邮箱

**接口**: `POST /api/v1/auth/verify-email`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AUTH-013 | 验证成功 | 用户已注册，持有有效验证 Token | `{"token":"valid-verify-token"}` | 0 | data 为 null，message 为"邮箱验证成功" |
| TC-AUTH-014 | Token 为空字符串 | 无 | `{"token":""}` | 40001 | 参数校验失败 |
| TC-AUTH-015 | Token 无效（随机字符串） | 无 | `{"token":"invalid-random-token"}` | 40400 | 验证令牌不存在或已过期 |
| TC-AUTH-016 | Token 已过期 | 持有已过期的验证 Token | `{"token":"expired-verify-token"}` | 40400 | 验证令牌不存在或已过期 |
| TC-AUTH-017 | 重复验证（使用已使用过的 Token） | 同一 Token 已成功验证过 | `{"token":"used-verify-token"}` | 40400 | 验证令牌不存在或已过期 |
| TC-AUTH-018 | 缺少 token 字段 | 无 | `{}` | 40001 | 参数校验失败 |

---

### 1.3 登录

**接口**: `POST /api/v1/auth/login`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AUTH-019 | 登录成功 | 用户已注册且邮箱已验证 | `{"email":"user@example.com","password":"12345678"}` | 0 | data 包含 token 和 user 对象（含 id, email, nickname, avatar, is_admin） |
| TC-AUTH-020 | 密码错误 | 用户已注册且邮箱已验证 | `{"email":"user@example.com","password":"wrongpass1"}` | 40003 | 邮箱或密码错误 |
| TC-AUTH-021 | 用户不存在（邮箱未注册） | 无 | `{"email":"nobody@example.com","password":"12345678"}` | 40003 | 邮箱或密码错误（不暴露用户是否存在） |
| TC-AUTH-022 | 邮箱未验证 | 用户已注册但邮箱未验证 | `{"email":"unverified@example.com","password":"12345678"}` | 40004 | 邮箱未验证 |
| TC-AUTH-023 | 带记住登录参数（remember=true） | 用户已注册且邮箱已验证 | `{"email":"user@example.com","password":"12345678","remember":true}` | 0 | data.token 有效期为 30 天 |
| TC-AUTH-024 | 带记住登录参数（remember=false） | 用户已注册且邮箱已验证 | `{"email":"user@example.com","password":"12345678","remember":false}` | 0 | data.token 有效期为 24 小时 |
| TC-AUTH-025 | 缺少 email 字段 | 无 | `{"password":"12345678"}` | 40001 | 参数校验失败 |
| TC-AUTH-026 | 缺少 password 字段 | 无 | `{"email":"user@example.com"}` | 40001 | 参数校验失败 |
| TC-AUTH-027 | 邮箱格式错误 | 无 | `{"email":"not-an-email","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-AUTH-028 | 请求 Body 为空 | 无 | `{}` | 40001 | 参数校验失败 |

---

### 1.4 忘记密码

**接口**: `POST /api/v1/auth/forgot-password`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AUTH-029 | 发送重置邮件成功 | 该邮箱已注册用户 | `{"email":"user@example.com"}` | 0 | data 为 null，message 为"重置邮件已发送" |
| TC-AUTH-030 | 邮箱不存在也返回成功 | 该邮箱未注册 | `{"email":"nobody@example.com"}` | 0 | data 为 null，防止邮箱枚举攻击 |
| TC-AUTH-031 | 邮箱格式错误 | 无 | `{"email":"invalid-email"}` | 40001 | 参数校验失败 |
| TC-AUTH-032 | 缺少 email 字段 | 无 | `{}` | 40001 | 参数校验失败 |

---

### 1.5 重置密码

**接口**: `POST /api/v1/auth/reset-password`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AUTH-033 | 重置密码成功 | 持有有效的重置 Token | `{"token":"valid-reset-token","new_password":"newpass123"}` | 0 | data 为 null，message 为"密码重置成功" |
| TC-AUTH-034 | Token 无效（随机字符串） | 无 | `{"token":"invalid-token","new_password":"newpass123"}` | 40400 | 重置令牌不存在或已过期 |
| TC-AUTH-035 | Token 已过期 | 持有已过期的重置 Token | `{"token":"expired-reset-token","new_password":"newpass123"}` | 40400 | 重置令牌不存在或已过期 |
| TC-AUTH-036 | 新密码太短（7位） | 持有有效的重置 Token | `{"token":"valid-reset-token","new_password":"1234567"}` | 40001 | 参数校验失败，密码需 8-64 位 |
| TC-AUTH-037 | 新密码太长（65位） | 持有有效的重置 Token | `{"token":"valid-reset-token","new_password":"a".repeat(65)}` | 40001 | 参数校验失败，密码需 8-64 位 |
| TC-AUTH-038 | Token 为空字符串 | 无 | `{"token":"","new_password":"newpass123"}` | 40001 | 参数校验失败 |
| TC-AUTH-039 | 缺少 token 字段 | 无 | `{"new_password":"newpass123"}` | 40001 | 参数校验失败 |
| TC-AUTH-040 | 缺少 new_password 字段 | 无 | `{"token":"valid-reset-token"}` | 40001 | 参数校验失败 |

---

## 2. 用户模块 (User)

### 2.1 获取当前用户信息

**接口**: `GET /api/v1/users/me`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-USER-001 | 成功获取用户信息 | 已登录用户，携带有效 Token | 无（Header: `Authorization: Bearer <token>`） | 0 | data 包含 id, email, nickname, avatar, is_admin, teams 数组 |
| TC-USER-002 | 未登录（无 Authorization 头） | 无 | 无 | 40100 | 未登录 |
| TC-USER-003 | Token 过期 | 携带已过期的 Token | 无（Header: `Authorization: Bearer <expired-token>`） | 40101 | Token 过期 |
| TC-USER-004 | Token 无效（随机字符串） | 无 | 无（Header: `Authorization: Bearer invalid-token`） | 40100 | 未登录 |

---

### 2.2 修改用户信息

**接口**: `PUT /api/v1/users/me`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-USER-005 | 修改昵称成功 | 已登录用户 | `{"nickname":"新昵称"}` | 0 | data 包含更新后的用户信息（nickname 为"新昵称"） |
| TC-USER-006 | 修改头像成功 | 已登录用户 | `{"avatar":"https://example.com/new.jpg"}` | 0 | data 包含更新后的用户信息（avatar 为新 URL） |
| TC-USER-007 | 同时修改昵称和头像 | 已登录用户 | `{"nickname":"昵称","avatar":"https://example.com/new.jpg"}` | 0 | data 包含更新后的用户信息 |
| TC-USER-008 | 昵称为空字符串 | 已登录用户 | `{"nickname":""}` | 40001 | 参数校验失败，昵称需 2-32 位 |
| TC-USER-009 | 昵称长度不足（1位） | 已登录用户 | `{"nickname":"A"}` | 40001 | 参数校验失败 |
| TC-USER-010 | 昵称长度超限（33位） | 已登录用户 | `{"nickname":"A".repeat(33)}` | 40001 | 参数校验失败 |
| TC-USER-011 | 未提供任何字段 | 已登录用户 | `{}` | 40001 | 参数校验失败，至少提供一个字段 |
| TC-USER-012 | 未登录 | 无 Token | `{"nickname":"昵称"}` | 40100 | 未登录 |
| TC-USER-013 | Token 过期 | 携带已过期的 Token | `{"nickname":"昵称"}` | 40101 | Token 过期 |

---

### 2.3 修改密码

**接口**: `PUT /api/v1/users/me/password`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-USER-014 | 修改密码成功 | 已登录用户 | `{"old_password":"12345678","new_password":"newpass12"}` | 0 | data 为 null，message 为"密码修改成功" |
| TC-USER-015 | 旧密码错误 | 已登录用户 | `{"old_password":"wrongpass1","new_password":"newpass12"}` | 40003 | 原密码错误 |
| TC-USER-016 | 新密码太短（7位） | 已登录用户 | `{"old_password":"12345678","new_password":"1234567"}` | 40001 | 参数校验失败，密码需 8-64 位 |
| TC-USER-017 | 新密码太长（65位） | 已登录用户 | `{"old_password":"12345678","new_password":"a".repeat(65)}` | 40001 | 参数校验失败 |
| TC-USER-018 | 缺少 old_password 字段 | 已登录用户 | `{"new_password":"newpass12"}` | 40001 | 参数校验失败 |
| TC-USER-019 | 缺少 new_password 字段 | 已登录用户 | `{"old_password":"12345678"}` | 40001 | 参数校验失败 |
| TC-USER-020 | 未登录 | 无 Token | `{"old_password":"12345678","new_password":"newpass12"}` | 40100 | 未登录 |
| TC-USER-021 | Token 过期 | 携带已过期的 Token | `{"old_password":"12345678","new_password":"newpass12"}` | 40101 | Token 过期 |

---

### 2.4 获取待处理事项

**接口**: `GET /api/v1/users/me/pending`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-USER-022 | 成功获取待处理事项 | 已登录用户，存在待评审需求、待办任务、团队邀请 | 无（Header: `Authorization: Bearer <token>`） | 0 | data 包含 pending_reviews、pending_tasks、pending_invitations 数组 |
| TC-USER-023 | 无待处理事项时返回空列表 | 已登录用户，无任何待处理数据 | 无（Header: `Authorization: Bearer <token>`） | 0 | data 中三个数组均为空 |
| TC-USER-024 | 未登录 | 无 Token | 无 | 40100 | 未登录 |
| TC-USER-025 | Token 过期 | 携带已过期的 Token | 无（Header: `Authorization: Bearer <expired-token>`） | 40101 | Token 过期 |

---

## 3. 管理员用户管理 (Admin User)

### 3.1 用户列表

**接口**: `GET /api/v1/admin/users`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-ADMIN-001 | 成功获取用户列表 | 管理员已登录，数据库中有用户数据 | 无（默认分页） | 0 | data 包含 total, page=1, page_size=20, items 数组（每项含 id, email, nickname, is_active, is_admin, created_at） |
| TC-ADMIN-002 | 分页查询第2页 | 管理员已登录，用户数 > 20 | `?page=2&page_size=20` | 0 | data.page=2，items 长度 ≤ 20 |
| TC-ADMIN-003 | 自定义每页数量 | 管理员已登录 | `?page=1&page_size=10` | 0 | data.page_size=10，items 长度 ≤ 10 |
| TC-ADMIN-004 | 按关键词搜索（邮箱） | 管理员已登录，存在匹配用户 | `?search=user@example.com` | 0 | data.items 中包含匹配邮箱的用户 |
| TC-ADMIN-005 | 按关键词搜索（昵称） | 管理员已登录，存在匹配用户 | `?search=张三` | 0 | data.items 中包含匹配昵称的用户 |
| TC-ADMIN-006 | 搜索无结果 | 管理员已登录，无匹配用户 | `?search=不存在的用户` | 0 | data.items 为空数组，data.total=0 |
| TC-ADMIN-007 | 非管理员拒绝访问 | 普通用户已登录（is_admin=false） | 无 | 40300 | 无权限（非管理员） |
| TC-ADMIN-008 | 未登录 | 无 Token | 无 | 40100 | 未登录 |
| TC-ADMIN-009 | Token 过期 | 携带已过期的管理员 Token | 无 | 40101 | Token 过期 |

---

### 3.2 创建用户

**接口**: `POST /api/v1/admin/users`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-ADMIN-010 | 创建用户成功 | 管理员已登录 | `{"email":"newuser@example.com","nickname":"新用户","password":"12345678"}` | 0 | data 包含 id, email, nickname, is_active=true, is_admin=false, created_at；用户自动完成邮箱验证 |
| TC-ADMIN-011 | 邮箱已存在 | 管理员已登录，该邮箱已被注册 | `{"email":"exist@example.com","nickname":"用户","password":"12345678"}` | 40002 | 邮箱已注册 |
| TC-ADMIN-012 | 缺少 email 字段 | 管理员已登录 | `{"nickname":"用户","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-ADMIN-013 | 缺少 nickname 字段 | 管理员已登录 | `{"email":"new@example.com","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-ADMIN-014 | 缺少 password 字段 | 管理员已登录 | `{"email":"new@example.com","nickname":"用户"}` | 40001 | 参数校验失败 |
| TC-ADMIN-015 | 邮箱格式错误 | 管理员已登录 | `{"email":"invalid","nickname":"用户","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-ADMIN-016 | 密码太短（7位） | 管理员已登录 | `{"email":"new@example.com","nickname":"用户","password":"1234567"}` | 40001 | 参数校验失败 |
| TC-ADMIN-017 | 昵称太短（1位） | 管理员已登录 | `{"email":"new@example.com","nickname":"A","password":"12345678"}` | 40001 | 参数校验失败 |
| TC-ADMIN-018 | 昵称太长（33位） | 管理员已登录 | `{"email":"new@example.com","nickname":"A".repeat(33),"password":"12345678"}` | 40001 | 参数校验失败 |
| TC-ADMIN-019 | 非管理员拒绝访问 | 普通用户已登录（is_admin=false） | `{"email":"new@example.com","nickname":"用户","password":"12345678"}` | 40300 | 无权限（非管理员） |
| TC-ADMIN-020 | 未登录 | 无 Token | `{"email":"new@example.com","nickname":"用户","password":"12345678"}` | 40100 | 未登录 |
| TC-ADMIN-021 | 请求 Body 为空 | 管理员已登录 | `{}` | 40001 | 参数校验失败 |

---

### 3.3 启用/禁用用户

**接口**: `PUT /api/v1/admin/users/{id}/status`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-ADMIN-022 | 禁用用户成功 | 管理员已登录，目标用户处于启用状态 | `{"is_active":false}`（路径 {id}=目标用户ID） | 0 | data 包含 id, is_active=false |
| TC-ADMIN-023 | 启用用户成功 | 管理员已登录，目标用户处于禁用状态 | `{"is_active":true}`（路径 {id}=目标用户ID） | 0 | data 包含 id, is_active=true |
| TC-ADMIN-024 | 用户不存在 | 管理员已登录，传入不存在的用户 ID | `{"is_active":false}`（路径 {id}=99999） | 40400 | 用户不存在 |
| TC-ADMIN-025 | 管理员禁用自己 | 管理员已登录，传入自身用户 ID | `{"is_active":false}`（路径 {id}=当前管理员ID） | 40001 | 管理员不可禁用自己 |
| TC-ADMIN-026 | 缺少 is_active 字段 | 管理员已登录 | `{}`（路径 {id}=目标用户ID） | 40001 | 参数校验失败 |
| TC-ADMIN-027 | is_active 为非布尔值 | 管理员已登录 | `{"is_active":"yes"}`（路径 {id}=目标用户ID） | 40001 | 参数校验失败 |
| TC-ADMIN-028 | 非管理员拒绝访问 | 普通用户已登录（is_admin=false） | `{"is_active":false}`（路径 {id}=目标用户ID） | 40300 | 无权限（非管理员） |
| TC-ADMIN-029 | 未登录 | 无 Token | `{"is_active":false}`（路径 {id}=目标用户ID） | 40100 | 未登录 |
| TC-ADMIN-030 | Token 过期 | 携带已过期的管理员 Token | `{"is_active":false}`（路径 {id}=目标用户ID） | 40101 | Token 过期 |

---

## 测试场景覆盖汇总

| 场景类型 | 覆盖用例 |
|----------|----------|
| 正常流程（成功） | TC-AUTH-001, TC-AUTH-013, TC-AUTH-019, TC-AUTH-023, TC-AUTH-024, TC-AUTH-029, TC-AUTH-030, TC-AUTH-033, TC-USER-001, TC-USER-005, TC-USER-006, TC-USER-007, TC-USER-014, TC-USER-022, TC-USER-023, TC-ADMIN-001~006, TC-ADMIN-010, TC-ADMIN-022, TC-ADMIN-023 |
| 参数校验失败 | TC-AUTH-002~004, TC-AUTH-006~010, TC-AUTH-012, TC-AUTH-014, TC-AUTH-018, TC-AUTH-025~028, TC-AUTH-031~032, TC-AUTH-036~040, TC-USER-008~011, TC-USER-016~019, TC-ADMIN-012~018, TC-ADMIN-021, TC-ADMIN-026, TC-ADMIN-027 |
| 重复操作 | TC-AUTH-011（邮箱已注册）, TC-ADMIN-011（邮箱已存在） |
| 权限不足 | TC-USER-002, TC-USER-004, TC-USER-012, TC-USER-020, TC-USER-024, TC-ADMIN-007~008, TC-ADMIN-019~020, TC-ADMIN-028~029 |
| 业务规则违反 | TC-AUTH-015~017（Token 无效/过期/已使用）, TC-AUTH-020~021（密码错误/用户不存在）, TC-AUTH-022（邮箱未验证）, TC-AUTH-034~035（重置 Token 无效/过期）, TC-USER-015（旧密码错误）, TC-ADMIN-024（用户不存在）, TC-ADMIN-025（管理员禁用自己） |
| Token 过期 | TC-USER-003, TC-USER-013, TC-USER-021, TC-USER-025, TC-ADMIN-009, TC-ADMIN-030 |
