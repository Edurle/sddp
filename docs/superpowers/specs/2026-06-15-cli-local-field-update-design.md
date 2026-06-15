# CLI 局部字段更新设计

> 通过 CLI 提交需求、原型、规范、测试用例等内容时，长文本作为命令行参数传递会触发 Windows cmd 的 ~8191 字符限制，被截断或产生格式错误；更本质的是，Agent 想局部修改 JSON 内部某个字段时，被迫重新拼装并重发整个大 JSON，影响大且易错。

## 目标

- **JSON 字段级局部更新**：Agent 只需给出"路径 + 值"，即可定位到 JSON 文档内部某个节点就地替换，无需重发整个文档。
- **绕开命令行长度限制**：长文本值统一从文件读取，彻底规避 cmd 截断。
- **不改变现有数据结构与 API 响应格式**：响应仍为 `{code, message, data}`，code `0` = 成功；错误复用现有 numeric code 体系。
- **错误信息对 Agent 可操作**：每条错误包含出错位置、现状、修正方向，Agent 看到后能直接知道怎么改。

## 非目标

- 不引入并发控制/乐观锁（同时修改一份数据的可能性基本没有）。
- 不改变需求状态机（spec 草稿仍受 `drafting_spec` 状态约束）。
- 不做"自动建树"——路径中间节点不存在时报错，不自动创建。

## 现状

| 内容类型 | 后端能力 | CLI 现状 |
|---|---|---|
| 需求字段（title/description/type_detail/prototype_html） | `PATCH /requirements/{id}` 已支持局部更新（`if v is not None`） | CLI `patch` 命令漏了 `prototype_html`；`type_detail` 只能整体替换，无法下钻 |
| specification | `PUT /specification` 整份覆盖，每次 +1 版本；无草稿、无局部更新 | CLI `save-spec` 要传整个 JSON |
| test_case | `PUT /test-cases/{id}` 已支持局部更新；字段均为顶层字符串 | CLI 有 `update` 命令但用 `--steps` 行内选项，长文本仍受 cmd 限制 |

数据库：生产/测试均使用 PostgreSQL。测试库 `obr_test`（`TEST_DATABASE_URL`），conftest 用 `TRUNCATE ... CASCADE` 清理，`spec_documents` 已在清理列表。

## 路径语法

纯函数 `resolve_path(doc, path)` 定位到文档节点。语法：

```
点号分隔 key：     type_detail.reproduce_steps
数组下标：         entity_definition.fields[0]
负数下标：         api_design.endpoints[-1]          （-1 = 末元素）
键值匹配数组元素：  page_structure.pages[name=user-list].elements[2].type
```

> **注意**：spec content 是 **section-name-keyed dict**（`{entity_definition: {...}, table_design: {...}, ...}`），不是 `{sections: [...]}` 数组。路径从 section 名直接开始。`[name=x]` 键值定位用于定位数组里的 dict 元素（如 `pages[name=user-list]`），而非 section 本身。

语义：
- **仅更新已存在节点**：路径中间或叶子不存在时报错，不自动建树。
- **整体替换**：路径指向的叶子或子树被文件内容整体替换。
- **`[name=x]` 键值定位**：用于数组中按某个 key 的值定位 dict 元素（如 `pages[name=user-list]`）。匹配多个时报错。
- **路径合法性校验**：非法语法 → `40001`。

实现位置：`backend/app/services/path_utils.py`，纯函数、无 IO，三类内容复用。

## 草稿数据模型（仅 spec）

在 `SpecDocument` 新增两列：

```
draft_content       JSONB | NULL   # 草稿内容；NULL = 无草稿
draft_base_version  INTEGER | NULL  # 草稿基于哪个正式版本
```

生命周期：
- **`set-spec-field`（局部写草稿）**：若 `draft_content` 为 NULL，先从 `current_version` 对应的正式 content 拷贝一份到 `draft_content`，记 `draft_base_version = current_version`；然后用 `resolve_path` 在 `draft_content` 上局部替换。不碰 `versions`、不 +1。写后对整个 `draft_content` 跑 Schema 校验，失败则不落库。
- **`get-spec`**：默认返回草稿（若有），否则正式版本。响应带 `is_draft`、`base_version`。
- **`commit-spec`（定版）**：草稿通过校验 → `versions` 追加一项（content=草稿，version+1）→ `current_version` +1 → 清空 `draft_content`/`draft_base_version`。
- **`discard-spec-draft`（丢弃）**：清空两列，回到当前正式版本。

迁移：Alembic 新增两列，nullable，默认 NULL。存量数据不受影响。

## API 契约

### Spec 草稿端点（新增）

| 方法 & 路径 | 作用 |
|---|---|
| `GET /requirements/{id}/specification` | 改语义：默认返回草稿（若有），否则正式版本。响应加 `is_draft`、`base_version`。 |
| `PATCH /requirements/{id}/specification/draft/field` | 局部写草稿。body: `{path, value}`。无草稿则从当前正式版本拷贝基线。 |
| `POST /requirements/{id}/specification/commit` | 定版：草稿→新正式版本（version+1），清空草稿。 |
| `DELETE /requirements/{id}/specification/draft` | 丢弃草稿，回到正式版本。 |

状态约束：`set-spec-field` 与 `commit` 沿用现有 `status == "drafting_spec"` 检查。
旧的 `PUT /requirements/{id}/specification`（整份覆盖）保留，视为一次性定版并清空草稿。

### 需求字段端点（扩展）

复用 `PATCH /requirements/{id}`，增强：
- 补全 `prototype_html`。
- `type_detail` 支持路径下钻：body 加可选 `type_detail_path` + `value`，若提供则用 `resolve_path` 在现有 `type_detail` 上局部替换；整体替换仍用原 `type_detail` 字段。
- **优先级**：同一请求中 `type_detail_path` 与 `type_detail` 互斥；若同时传，报 `40001`："`type_detail_path` 与 `type_detail` 不可同时提供，二选一。"

### Test case 端点

后端零改动：`PUT /test-cases/{id}` 已存在，字段均为顶层字符串，无需路径下钻。CLI 新增 `set-field` 命令（`--file` 取值）补充现有 `update`（行内选项），让长文本（steps/expected/precondition）绕开 cmd 限制。

## CLI 命令面

统一 `set-field <id> <path> --file <path>` 模式，值只从文件读。

```
# spec 草稿
sdd req set-spec-field     <id> entity_definition.description --file d.md
sdd req set-spec-field     <id> api_design.endpoints[0].description --file api_desc.md
sdd req commit-spec        <id>
sdd req discard-spec-draft <id>
sdd req get-spec           <id>           # 返回草稿（若有），带 is_draft

# 需求字段（复用 PATCH /{id}）
sdd req set-field          <id> prototype_html --file proto.html
sdd req set-field          <id> type_detail.reproduce_steps --file steps.json

# test_case（复用 PUT /test-cases/{id}）
sdd tc set-field           <id> steps --file steps.txt
```

**取值约定（方案 ii）**：CLI 读取文件后自动尝试 `json.loads`；成功则传结构化值，失败则传字符串原文。Agent 传 `.json` 得结构化值，传 `.md`/`.html` 得字符串，心智负担低。

## 错误处理

所有错误复用现有 `BusinessError(code, message, errors=[...])` 体系，响应格式 `{code, message, data}` 不变。**错误信息必须对 Agent 可操作**：包含出错位置、现状、修正方向。

| 场景 | code | 错误信息样例 |
|---|---|---|
| 路径语法非法 | `40001` | `路径语法非法：'api_design.endpoints[]' 中 '[]' 缺少下标或键值。用法：endpoints[0] / endpoints[-1] / endpoints[path=/x]` |
| 中间/叶子节点不存在 | `40404` | `路径不存在：'type_detail.reproduce_steps' 中 'reproduce_steps' 键不存在。type_detail 现有键：[severity, environment]` |
| 数组越界 | `40404` | `路径不存在：'api_design.endpoints[3]' 越界，该数组当前长度 3（有效下标 0..2 或用 [-1] 取末元素）` |
| `[name=x]` 匹配 0 个 | `40404` | `路径不存在：pages[name=api_design] 无匹配。现有 name 值：[user-list, user-detail]` |
| `[name=x]` 匹配多个 | `40001` | `路径匹配到多个节点：pages[name=x] 命中 2 条，请改用下标 pages[0]/pages[1] 精确定位` |
| 草稿 Schema 校验失败 | `40001` | `草稿校验失败：` + 现有 `_validate_spec_content` 的 errors（含具体 section/field + 期望格式） |
| 无草稿 commit/discard | `40404` | `无草稿可定版：当前 spec 已是正式版本 N，无未提交草稿。用 set-spec-field 开始编辑草稿` |
| 状态非 drafting_spec | `40204`(ERR_REQUIREMENT_STATUS) | `当前需求状态为 drafting_req，不允许编辑草稿。需处于 drafting_spec 状态` |

校验时机：
- **spec 草稿**：每次 `set-spec-field` 局部替换后，对整个 `draft_content` 跑 `_validate_spec_content`；失败则不落库。保证草稿始终合法。
- **需求 `type_detail` 下钻**：无 Schema 约束，仅校验路径合法 + 节点存在。
- **test_case**：字段是顶层字符串，沿用现有行为。

## 测试策略

数据库：测试库 `obr_test`（PostgreSQL），conftest 用 `TRUNCATE ... CASCADE`，草稿两列随 Alembic 迁移自动创建。

| 层 | 覆盖 |
|---|---|
| `path_utils` 单元测试 | 点号、`[0]`、`[-1]`、`[name=x]`、越界、多匹配、空串、非法语法；纯函数、快 |
| spec 草稿服务测试 | 基线拷贝（首次写自动建草稿）、多次局部写累积、commit→version+1+清草稿、discard、无草稿 commit/discard 报错、Schema 校验失败回滚、status 非 drafting_spec 报错、错误信息含现有键/有效范围 |
| 需求字段测试 | `type_detail` 下钻成功/路径不存在（错误信息含现有键）、整体替换、补 prototype_html |
| test_case 测试 | update 端点已存在，补 CLI 层覆盖 |
| CLI 测试 | `set-spec-field`/`commit-spec`/`discard-spec-draft`/`set-field`/`tc set-field`，含 `--file` 读取、json 自动 parse 回退原文、超长文件不再受 cmd 限制 |

## 改动规模小结

| 内容 | 后端改动 |
|---|---|
| 需求字段 | 扩展现有 `PATCH /{id}`：补 `prototype_html`、`type_detail` 加路径下钻 |
| spec | 新增草稿两列 + 3 个草稿端点（patch-field / commit / discard）；`GET` 改返回草稿 |
| test_case | 零后端改动（端点已存在） |
| 公共 | `path_utils.py` 路径工具（三类复用） |
| CLI | 新增 5 个命令，`--file` 取值 + json 自动 parse |
