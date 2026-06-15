# SDD CLI 使用指南

> `sdd-cli` 当前版本：**0.3.0**
> 适用：通过命令行/脚本操作 SDD 平台，尤其面向 Agent 自动化场景。

---

## 安装与配置

### 安装

```bash
# 从源码安装（开发）
pip install -e cli

# 或从 PyPI 安装
pip install sdd-cli
```

### 配置连接

首次使用需配置后端地址和认证凭据：

```bash
sdd config set-url http://<后端地址>:8000/api/v1

# 方式一：账号密码登录（生成 token）
sdd config login --email you@example.com --password <密码>

# 方式二：直接设置 API Key（在平台个人设置页生成）
sdd config set-api-key <你的 api key>
```

配置存储在用户目录，后续命令自动读取。验证配置：

```bash
sdd me
```

---

## 核心概念

SDD 的研发流程围绕以下对象流转，CLI 命令按此组织：

```
团队 Team
  └─ 项目 Project
       └─ 迭代/模块 Iteration   （一个项目可同时有多个 in_progress 迭代）
            └─ 需求 Requirement
                 ├─ 规范 Specification（多版本 + 草稿）
                 ├─ 测试用例 TestCase
                 └─ 任务 Task
                      └─ 测试执行 TestExecution
```

命令以子命令组形式组织：`sdd <组> <命令>`，例如 `sdd requirements list`。

---

## 局部字段更新（v0.3.0 新增）

> **解决的核心问题**：长文本（HTML 原型、规范 JSON、测试步骤）作为命令行参数会触发 cmd ~8191 字符限制被截断；Agent 改 JSON 内部某字段时被迫重发整个大 JSON。
>
> **方案**：以"点号路径 + 文件取值"局部更新，绕开长度限制，无需重发整份内容。值**只从文件读取**，CLI 自动尝试 JSON 解析（失败则当字符串原文）。

### 路径语法

```
点号分隔 key：     type_detail.reproduce_steps
数组下标：         api_design.endpoints[0].description
负数下标：         api_design.endpoints[-1]          （-1 = 末元素）
键值匹配数组元素：  page_structure.pages[name=user-list].elements[2].type
```

错误信息对 Agent 可操作：包含出错位置、现状（现有键/数组长度/有效下标）、修正方向。

### Spec 规范草稿编辑

Spec content 是 section-name-keyed dict，路径从 section 名直接开始：

```bash
# 1. 先有一份正式版本（草稿基于它）
sdd requirements save-spec <id> --content '<整份 JSON>'

# 2. 局部改草稿某字段（自动建草稿基线，可多次累积）
sdd requirements set-spec-field <id> entity_definition.description --file desc.md
sdd requirements set-spec-field <id> api_design.endpoints[0].description --file api.md

# 3. 查看草稿（默认返回草稿，含 is_draft / base_version）
sdd requirements spec <id>

# 4a. 定版：草稿 → 新正式版本（version+1），清空草稿
sdd requirements commit-spec <id>

# 4b. 或丢弃草稿，回到当前正式版本
sdd requirements discard-spec-draft <id>
```

**草稿机制要点：**
- `set-spec-field` 首次调用时自动从当前正式版本拷贝草稿基线；后续调用在草稿上累积修改。
- 每次局部写都做整份 Schema 校验，失败则不落库（草稿不被污染）。
- 只有需求处于 `drafting_spec` 状态才能编辑草稿/定版。
- `commit` 产生新版本（version+1）；`discard` 回到定版前状态。

### 需求字段局部更新

```bash
# prototype_html 整体替换（绕开 cmd 限制）
sdd requirements set-field <id> prototype_html --file proto.html

# type_detail 内部某子字段局部更新（不重发整个 type_detail）
sdd requirements set-field <id> type_detail.reproduce_steps --file steps.json
```

> `set-field` 仅支持 `prototype_html` 与 `type_detail.<子路径>`。其他顶层字段（title/description 等）用 `sdd requirements patch`。

### 测试用例字段更新

```bash
# 长文本字段（steps/expected/precondition）从文件读取
sdd test-cases set-field <id> steps --file steps.txt
sdd test-cases set-field <id> expected --file expected.md
sdd test-cases set-field <id> precondition --file precondition.md
```

支持的字段：`title` `type` `precondition` `steps` `expected` `related_api` `related_element`。

---

## 取值文件的 JSON 自动解析规则

`--file` 指定的文件内容会先尝试 `json.loads`：
- 解析成功 → 作为结构化值（对象/数组/数字/布尔）发送
- 解析失败 → 作为字符串原文发送

| 文件内容 | 发送的值 |
|---|---|
| `["s1","s2"]` | 数组 `["s1","s2"]` |
| `{"k":"v"}` | 对象 `{"k":"v"}` |
| `# 标题\n正文` | 字符串 `"# 标题\n正文"` |
| `<div>html</div>` | 字符串 `"<div>html</div>"` |

**经验法则**：想让字段是结构化值就传 `.json`，想让字段是字符串就传 `.md`/`.html`/`.txt`。

---

## 命令索引（按组）

### `sdd me` — 个人

| 命令 | 说明 |
|---|---|
| `me` | 当前用户信息 |
| `me pending` | 待处理事项 |
| `me pending-reviews` | 待我评审 |
| `me my-work` | 我的工作 |
| `me update-profile` | 更新资料 |
| `me change-password` | 改密码 |
| `me projects-tree` | 项目树 |

### `sdd teams` — 团队

| 命令 | 说明 |
|---|---|
| `teams list` | 团队列表 |
| `teams create` | 创建团队 |
| `teams get <id>` | 团队详情 |
| `teams update <id>` | 更新团队 |
| `teams delete <id>` | 删除团队 |
| `teams members` | 成员列表 |
| `teams invite` | 邀请成员 |
| `teams remove-member` | 移除成员 |
| `teams assign-role` | 分配角色 |
| `teams roles` | 角色列表 |
| `teams create-role` | 创建角色 |
| `teams transfer <id>` | 转让所有权 |
| `teams spec-template` | 查看 spec 模板 |
| `teams agent-guide` | Agent 指南 |
| `teams update-spec-template` | 更新 spec 模板 |

### `sdd invitations` — 邀请

| 命令 | 说明 |
|---|---|
| `invitations pending` | 待处理邀请 |
| `invitations handle` | 接受/拒绝邀请 |

### `sdd projects` — 项目

| 命令 | 说明 |
|---|---|
| `projects list` | 项目列表 |
| `projects get <id>` | 项目详情 |
| `projects create` | 创建项目 |
| `projects update <id>` | 更新项目 |
| `projects archive <id>` | 归档项目 |
| `projects delete <id>` | 删除项目 |
| `projects test-stats <id>` | 测试统计 |

### `sdd iterations` — 迭代/模块

| 命令 | 说明 |
|---|---|
| `iterations list` | 迭代列表 |
| `iterations get <id>` | 迭代详情 |
| `iterations create` | 创建迭代 |
| `iterations update <id>` | 更新迭代 |
| `iterations start <id>` | 启动迭代 |
| `iterations complete <id>` | 完成迭代 |
| `iterations kanban <id>` | 看板 |
| `iterations statistics <id>` | 统计 |
| `iterations test-stats <id>` | 测试统计 |

### `sdd requirements` — 需求

**基础：**

| 命令 | 说明 |
|---|---|
| `requirements list` | 列表（支持 `--status` `--iteration`） |
| `requirements get <id>` | 详情 |
| `requirements create` | 创建（`--title` `--type` `--iteration` 等） |
| `requirements update <id>` | 整体更新 |
| `requirements patch <id>` | 局部更新（title/description/type_detail/prototype_html） |
| `requirements delete <id>` | 删除 |
| `requirements approve <id>` | 直接通过 |
| `requirements full-context <id>` | 完整上下文 |
| `requirements guide` | 需求编写指南 |

**评审流转：**

| 命令 | 说明 |
|---|---|
| `requirements submit-review <id> --reviewer <uid>` | 提交需求评审 |
| `requirements review <id> --action <approve\|reject> [--comment]` | 评审 |
| `requirements submit-spec-review <id> --reviewer <uid>` | 提交规范评审 |
| `requirements approve-spec <id>` | 通过规范 |
| `requirements submit-tests-review <id> --reviewer <uid>` | 提交测试用例评审 |
| `requirements review-comments <id>` | 评审意见 |

**规范（含 v0.3.0 草稿机制）：**

| 命令 | 说明 |
|---|---|
| `requirements spec <id>` | 查看规范（默认返回草稿） |
| `requirements save-spec <id> --content '<JSON>'` | 整份覆盖保存（定版） |
| `requirements spec-versions <id>` | 版本列表 |
| `requirements spec-version <id> <ver>` | 某版本详情 |
| `requirements set-spec-field <id> <path> --file <f>` | **v0.3.0** 局部改草稿 |
| `requirements commit-spec <id>` | **v0.3.0** 草稿定版 |
| `requirements discard-spec-draft <id>` | **v0.3.0** 丢弃草稿 |
| `requirements set-field <id> <path> --file <f>` | **v0.3.0** 需求字段局部更新（prototype_html / type_detail.*） |

**测试用例：**

| 命令 | 说明 |
|---|---|
| `requirements test-cases <id>` | 用例列表 |
| `requirements create-test-case <id>` | 创建用例 |
| `requirements test-stats <id>` | 测试统计 |

**任务：**

| 命令 | 说明 |
|---|---|
| `requirements tasks <id>` | 任务列表 |
| `requirements create-task <id> --title` | 创建任务 |
| `requirements generate-tasks <id>` | 生成任务 |
| `requirements generate-test-cases <id>` | 生成用例 |

**关联：**

| 命令 | 说明 |
|---|---|
| `requirements links <id>` | 关联列表 |
| `requirements link <id> --target <tid> [--type]` | 建立关联 |
| `requirements unlink <id> --link-id` | 解除关联 |
| `requirements supersede <id>` | 取代需求 |
| `requirements commits <id>` | 提交记录 |

### `sdd tasks` — 任务

| 命令 | 说明 |
|---|---|
| `tasks get <id>` | 任务详情 |
| `tasks create` | 创建任务 |
| `tasks update <id>` | 更新任务 |
| `tasks delete <id>` | 删除任务 |
| `tasks patch <id>` | 局部更新 |
| `tasks start-coding <id>` | 开始编码 |
| `tasks start-testing <id>` | 开始测试 |
| `tasks complete <id>` | 完成任务 |
| `tasks git-info <id>` | Git 信息 |
| `tasks commits <id>` | 提交记录 |
| `tasks test-executions <id>` | 测试执行 |
| `tasks create-test-record` | 创建测试记录 |
| `tasks create-test-round` | 创建测试轮次 |

### `sdd test-cases` — 测试用例（独立组）

| 命令 | 说明 |
|---|---|
| `test-cases create --requirement <id> --title --type` | 创建用例 |
| `test-cases update <id>` | 更新用例（行内选项） |
| `test-cases set-field <id> <field> --file <f>` | **v0.3.0** 单字段从文件更新 |
| `test-cases delete <id>` | 删除用例 |
| `test-cases execution-results --requirement <id>` | 执行结果 |

### `sdd test-executions` — 测试执行

| 命令 | 说明 |
|---|---|
| `test-executions records` | 执行记录 |
| `test-executions batch` | 批量执行 |
| `test-executions update-record` | 更新记录 |

### `sdd admin` — 管理

| 命令 | 说明 |
|---|---|
| `admin users` | 用户列表 |
| `admin create-user` | 创建用户 |
| `admin toggle-user` | 启用/禁用用户 |
| `admin create-api-key` | 创建 API Key |
| `admin list-api-keys` | API Key 列表 |
| `admin revoke-api-key` | 吊销 API Key |

### `sdd webhooks` — Webhook

| 命令 | 说明 |
|---|---|
| `webhooks list` | 列表 |
| `webhooks create` | 创建 |
| `webhooks update` | 更新 |
| `webhooks delete` | 删除 |
| `webhooks deliveries` | 投递记录 |

### `sdd users`

| 命令 | 说明 |
|---|---|
| `users list` | 用户列表 |

---

## 典型工作流

### Agent 编写并提交规范（草稿模式）

```bash
# 1. 整体保存初始规范（建立版本基线）
sdd requirements save-spec 42 --content '@spec-v1.json'
# 或用文件避免命令行长度（save-spec 目前接收字符串，超大时用管道或脚本）

# 2. 局部迭代修改（每次只发改动的字段）
echo "用户实体，含 id/email/role" > desc.md
sdd requirements set-spec-field 42 entity_definition.description --file desc.md

echo '[{"name":"id","type":"BIGINT"},{"name":"email","type":"VARCHAR(255)"}]' > fields.json
sdd requirements set-spec-field 42 entity_definition.fields --file fields.json

# 3. 确认草稿内容
sdd requirements spec 42

# 4. 满意后定版
sdd requirements commit-spec 42

# 5. 提交评审
sdd requirements submit-spec-review 42 --reviewer 3
```

### Agent 修改需求原型（绕开 cmd 限制）

```bash
# 整页 HTML 原型直接从文件读，不受命令行长度限制
sdd requirements set-field 42 prototype_html --file prototype.html
```

### Agent 更新测试用例长步骤

```bash
sdd test-cases set-field 17 steps --file detailed-steps.md
sdd test-cases set-field 17 expected --file expected-result.md
```

---

## 常见问题

### 命令行参数太长被截断？
使用 v0.3.0 的 `--file` 系列命令（`set-field` / `set-spec-field` / `test-cases set-field`），从文件取值，彻底绕开 cmd ~8191 字符限制。

### 路径报错说"键不存在"？
错误信息会列出**现有键**，据此修正路径。例如：
```
路径不存在：'type_detail.reproduce_steps' 中 'reproduce_steps' 键不存在。现有键：[severity, environment]
```

### 草稿和正式版本的关系？
- 草稿独立于正式版本存在，可多次局部修改累积。
- `commit-spec` 把草稿固化为新正式版本（version+1），草稿清空。
- `discard-spec-draft` 丢弃草稿，回到当前正式版本，不影响版本号。
- `requirements spec <id>` 默认返回草稿（若有），响应里 `is_draft` 标识。

### 想看清完整参数？
任何命令加 `--help`：`sdd requirements set-spec-field --help`。
