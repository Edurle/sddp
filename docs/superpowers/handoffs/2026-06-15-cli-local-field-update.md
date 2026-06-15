# 交接：CLI 局部字段更新 — 执行实现计划

> 面向新会话/新执行者。本文档汇总执行 `docs/superpowers/plans/2026-06-15-cli-local-field-update.md` 所需的全部上下文，无需阅读历史对话。

## 一句话目标

让 CLI 通过"点号路径 + 文件取值"局部更新 JSON 内部字段（spec 草稿 / 需求 type_detail / test_case 长文本），绕开 Windows cmd ~8191 字符限制，无需重发整个大 JSON。

## 要执行的文件

- **计划（逐任务 TDD 步骤）：** `docs/superpowers/plans/2026-06-15-cli-local-field-update.md`
- **设计（背景与契约）：** `docs/superpowers/specs/2026-06-15-cli-local-field-update-design.md`

## 执行方式（建议）

新会话执行者请先阅读上面两个文件，然后：

> 使用 executing-plans（或 subagent-driven-development）技能，执行计划 `docs/superpowers/plans/2026-06-15-cli-local-field-update.md`。先切到分支 `feat/cli-local-field-update`。TDD bite-sized 任务，按 Task 1→9 顺序，每任务"写测试→确认失败→实现→确认通过→提交"。

## 分支与提交状态

- **功能分支：** `feat/cli-local-field-update`（已 `git push -u origin`，已设上游）。
- 该分支基于当前 `main`，**计划尚未实现**，分支内容与 main 相同（仅多了设计文档和计划文件本身）。
- `main` 上已有与本次无关的改动：project list 500 bug 修复（commit `d489d4e`）、设计文档、计划文件、本交接文档。

## ⚠️ 关键上下文（不读会踩坑）

### 1. 测试库是 PostgreSQL `obr_test`，不是 SQLite
- `TEST_DATABASE_URL=postgresql+asyncpg://obr_sdd:...@60.217.227.76:35432/obr_test`（见 `.env`）。
- conftest 用 `TRUNCATE ... RESTART IDENTITY CASCADE` 清理（不是 in-memory SQLite）。`AGENTS.md` 里写的 SQLite 描述已过时，以实际为准。
- 草稿两列用 `JSONB` / `INTEGER`。

### 2. 没有 alembic 迁移
- schema 由 `backend/app/database.py` 的 `init_db()` → `Base.metadata.create_all` 创建。
- `backend/alembic/` 目录不存在（`AGENTS.md` 提到 alembic，但实际没有）。
- **Task 2 给现有 `obr_test` 和生产库加两列需手动执行 SQL：**
  ```sql
  ALTER TABLE spec_documents ADD COLUMN IF NOT EXISTS draft_content JSONB;
  ALTER TABLE spec_documents ADD COLUMN IF NOT EXISTS draft_base_version INTEGER;
  ```
  新库通过 `init_db()` 自动建出，无需手动。

### 3. conda 环境
- 后端用 `conda run -n sdd python ...`，`sdd` 环境已装好后端依赖。
- CLI 测试需确认能 import `sdd_cli`：可能需 `conda run -n sdd pip install -e cli`（先验证）。

### 4. spec content 的真实结构
- spec content 是 **section-name-keyed dict**：
  ```python
  {
    "entity_definition": {"description": "...", "fields": [{"name":..., "type":..., "constraints":[...]}]},
    "table_design": {"tables": [...]},
    "page_structure": {"pages": [{"name":..., "code":..., "elements":[...]}]},
    "api_design": {"endpoints": [{"method":..., "path":..., "description":...}]},
    "constraints": {},
  }
  ```
- **路径从 section 名直接开始**，例如 `entity_definition.fields[0].constraints`，**不是** `sections[name=...].fields...`。
- 计划与设计文档均已按此修正；路径工具测试样例也用正确结构。

### 5. 预先存在的测试失败（与本次无关，不算回归）
- `backend/tests` 中 7 个 `*_no_permission` / `*_not_found` 用例在改动前就失败（`permissions=[]` fixture 仍被 `check_team_permission` 当成成员）。已用 `git stash` 在干净 checkout 上验证过。
- 执行 Task 9 全量回归时，这些失败可忽略，**只关注本次新增/相关测试**。

### 6. 后端现有能力（已在设计阶段核实）
- `PATCH /requirements/{id}` 已支持局部更新；`PatchRequirementRequest`（`backend/app/api/requirements.py:121`）**已含 `prototype_html`**，inline 逻辑也已应用（311-312 行）。Task 5 只需加 `type_detail_path`/`value` 字段和下钻分支，prototype_html 后端无需改。
- `PUT /test-cases/{id}` 已存在（`backend/app/api/test_cases.py:53`），test_case 后端零改动。
- `update_requirement` 服务（`backend/app/services/requirement.py`）要求 `status == "drafting_req"`；但 `PATCH /{id}` API 用 `EDITABLE_STATUSES = {"drafting_req"}`（`requirement.py:41`）。

### 7. 错误码（已核实）
- `ERR_VALIDATION = 40001`，`ERR_NOT_FOUND = 40400`，`ERR_REQUIREMENT_STATUS = 40204`。
- 计划新增的可读常量（`ERR_FIELD_PATH_*`、`ERR_NO_DRAFT`）码值复用 40001/40404，不引入新码值。

## 任务概览（9 个）

| Task | 内容 | 文件 |
|---|---|---|
| 1 | 路径工具 `path_utils.py`（纯函数，可操作错误信息） | `backend/app/services/path_utils.py` + test |
| 2 | 错误码常量 + `SpecDocument` 加 `draft_content`/`draft_base_version` 两列 | `exceptions.py`, `models/spec.py` |
| 3 | spec 草稿服务层（set-field/commit/discard） | `services/specification.py` |
| 4 | spec 草稿 API 端点 + commit/discard 测试 | `api/requirements.py` |
| 5 | 需求 `type_detail` 路径下钻（最小改动） | `api/requirements.py` |
| 6 | CLI 文件取值工具（json 自动 parse 回退原文） | `cli/sdd_cli/file_loader.py` |
| 7 | CLI 需求命令（set-spec-field/commit-spec/discard-spec-draft/set-field） | `cli/sdd_cli/requirements.py` |
| 8 | CLI test_case set-field | `cli/sdd_cli/test_cases.py` |
| 9 | 全量回归 + 端到端联调 | 仅验证 |

## 完成标准
- 路径工具单测全绿（Task 1）
- spec 草稿 set/commit/discard 端点+服务测试全绿（Task 3-4）
- 需求 type_detail 下钻测试全绿（Task 5）
- CLI 5 个新命令测试全绿（Task 6-8）
- 端到端联调通过（Task 9）
- 错误信息对 Agent 可操作（含现有键/长度/有效下标）
- 无回归（预先存在的 no_permission 失败除外）
