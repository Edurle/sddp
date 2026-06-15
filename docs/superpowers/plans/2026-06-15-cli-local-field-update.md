# CLI 局部字段更新 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 CLI 能通过"点号路径 + 文件取值"局部更新 JSON 内部字段（spec 草稿 / 需求 type_detail / test_case 长文本），绕开 cmd 长度限制，无需重发整个大 JSON。

**Architecture:** 三层：① 纯函数路径工具 `path_utils.py`（解析 `a.b[0].c[name=x]` 并定位到父节点+键）；② spec 草稿机制（`SpecDocument` 加两列，patch-field 写草稿、commit 定版）；③ CLI `set-field` 命令（`--file` 取值 + json 自动 parse 回退原文）。需求字段复用现有 PATCH，test_case 复用现有 PUT，二者仅加 CLI 命令。

**Tech Stack:** Python 3.12 / FastAPI / SQLAlchemy async / Pydantic / PostgreSQL(JSONB) / Typer(CLI)。测试用 `obr_test`（pg）+ pytest-asyncio。

**参考设计：** `docs/superpowers/specs/2026-06-15-cli-local-field-update-design.md`

---

## 文件结构

**新建：**
- `backend/app/services/path_utils.py` — 纯函数路径解析（三类内容复用）
- `backend/tests/test_path_utils.py` — 路径工具单元测试

**修改：**
- `backend/app/models/spec.py` — `SpecDocument` 加 `draft_content` / `draft_base_version` 两列
- `backend/app/services/specification.py` — 草稿读写/commit/discard + `get_spec_document` 返回草稿
- `backend/app/schemas/spec.py`(若不存在则建) — 草稿端点请求体 schema
- `backend/app/api/requirements.py` — 3 个草稿端点；`PATCH /{id}` schema 加 `type_detail_path`/`value` 并插入下钻分支（prototype_html 后端已支持，仅 CLI 暴露）
- `backend/app/exceptions.py` — 加路径相关错误码（复用 40001/40404，新增语义常量）
- `backend/tests/test_specifications.py` — 草稿用例
- `backend/tests/test_requirements.py` — type_detail 下钻用例
- `cli/sdd_cli/file_loader.py`(新建) — 文件读取 + json 自动 parse 回退原文
- `cli/sdd_cli/requirements.py` — `set-field` / `set-spec-field` / `commit-spec` / `discard-spec-draft`
- `cli/sdd_cli/test_cases.py` — `set-field`
- `cli/tests/test_file_loader.py`(新建) — 文件取值测试
- `cli/tests/test_requirements.py` — set-field 命令测试
- `cli/tests/test_test_cases.py` — set-field 命令测试

**SQL 迁移（无 alembic，手动 ALTER）：**
- 现有 `obr_test`/生产库需执行 `ALTER TABLE spec_documents ADD COLUMN draft_content JSONB, ADD COLUMN draft_base_version INTEGER`。新库通过 `init_db()`/`create_all` 自动建出。

---

## Task 1: 路径工具 `path_utils.py`

**Files:**
- Create: `backend/app/services/path_utils.py`
- Test: `backend/tests/test_path_utils.py`

- [ ] **Step 1: 写失败测试 — 解析点号路径**

Create `backend/tests/test_path_utils.py`:

```python
import pytest

from app.services.path_utils import (
    PathSyntaxError,
    PathNotFoundError,
    MultipleMatchError,
    set_by_path,
)


class TestParseAndNavigate:
    def test_dot_key(self):
        doc = {"a": {"b": 1}}
        result = set_by_path(doc, "a.b", 99)
        assert result == {"a": {"b": 99}}

    def test_array_index(self):
        doc = {"a": [10, 20, 30]}
        result = set_by_path(doc, "a[1]", 99)
        assert result == {"a": [10, 99, 30]}

    def test_negative_index(self):
        doc = {"a": [10, 20, 30]}
        result = set_by_path(doc, "a[-1]", 99)
        assert result == {"a": [10, 20, 99]}

    def test_nested_array_in_dict(self):
        doc = {"sections": [{"name": "x", "v": 1}, {"name": "y", "v": 2}]}
        result = set_by_path(doc, "sections[0].v", 99)
        assert result["sections"][0]["v"] == 99

    def test_name_match(self):
        doc = {"pages": [{"name": "list", "v": 1}, {"name": "detail", "v": 2}]}
        result = set_by_path(doc, "pages[name=list].v", 99)
        assert result["pages"][0]["v"] == 99

    def test_deep_path(self):
        doc = {"a": {"b": [{"c": {"d": 1}}]}}
        result = set_by_path(doc, "a.b[0].c.d", 99)
        assert result == {"a": {"b": [{"c": {"d": 99}}]}}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest backend/tests/test_path_utils.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.path_utils'`

- [ ] **Step 3: 写失败测试 — 错误情况（可操作错误信息）**

Append to `backend/tests/test_path_utils.py`:

```python
class TestErrors:
    def test_syntax_empty_brackets(self):
        doc = {"a": [1, 2]}
        with pytest.raises(PathSyntaxError) as e:
            set_by_path(doc, "a[]", 99)
        assert "[]" in str(e.value)
        assert "缺少下标或键值" in str(e.value)

    def test_syntax_double_dot(self):
        doc = {"a": {"b": 1}}
        with pytest.raises(PathSyntaxError) as e:
            set_by_path(doc, "a..b", 99)
        assert "a..b" in str(e.value)

    def test_missing_key_includes_existing_keys(self):
        doc = {"type_detail": {"severity": "high", "env": "prod"}}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "type_detail.reproduce_steps", 99)
        msg = str(e.value)
        assert "reproduce_steps" in msg
        assert "severity" in msg  # existing keys shown
        assert "env" in msg

    def test_array_out_of_range_includes_length(self):
        doc = {"a": [10, 20, 30]}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "a[5]", 99)
        msg = str(e.value)
        assert "a[5]" in msg
        assert "3" in msg  # length

    def test_name_match_zero_includes_existing(self):
        doc = {"pages": [{"name": "list"}, {"name": "detail"}]}
        with pytest.raises(PathNotFoundError) as e:
            set_by_path(doc, "pages[name=nope].v", 99)
        msg = str(e.value)
        assert "nope" in msg
        assert "list" in msg and "detail" in msg

    def test_name_match_multiple(self):
        doc = {"pages": [{"name": "x"}, {"name": "x"}]}
        with pytest.raises(MultipleMatchError) as e:
            set_by_path(doc, "pages[name=x].v", 99)
        msg = str(e.value)
        assert "2" in msg
        assert "pages[0]" in msg

    def test_empty_path(self):
        doc = {"a": 1}
        with pytest.raises(PathSyntaxError):
            set_by_path(doc, "", 99)
```

- [ ] **Step 4: 实现 `path_utils.py`**

Create `backend/app/services/path_utils.py`:

```python
import re
from typing import Any

_TOKEN_RE = re.compile(r"([^.\[\]]+)|\[(.+?)\]")


class PathSyntaxError(Exception):
    pass


class PathNotFoundError(Exception):
    pass


class MultipleMatchError(Exception):
    pass


def _tokenize(path: str) -> list[tuple[str, str | int]]:
    if not path or not path.strip():
        raise PathSyntaxError(
            f"路径语法非法：'{path}' 为空。路径不能为空。"
        )
    tokens: list[tuple[str, str | int]] = []
    pos = 0
    n = len(path)
    expect_key = True
    while pos < n:
        if path[pos] == ".":
            pos += 1
            expect_key = True
            continue
        if path[pos] == "[":
            end = path.find("]", pos)
            if end == -1:
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 中 '[...] 缺少右括号 ']'。"
                )
            inner = path[pos + 1:end].strip()
            if inner == "":
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 中 '[]' 缺少下标或键值。"
                    f"用法：a[0] / a[-1] / a[name=xxx]"
                )
            if "=" in inner:
                key, _, val = inner.partition("=")
                key = key.strip()
                val = val.strip()
                if not key:
                    raise PathSyntaxError(
                        f"路径语法非法：'{path}' 中 '[{inner}]' 键名缺失。用法：[name=xxx]"
                    )
                tokens.append(("match", (key, val)))
            else:
                try:
                    idx = int(inner)
                except ValueError:
                    raise PathSyntaxError(
                        f"路径语法非法：'{path}' 中 '[{inner}]' 既非整数下标也非键值匹配。"
                        f"用法：a[0] / a[-1] / a[name=xxx]"
                    )
                tokens.append(("index", idx))
            pos = end + 1
            expect_key = False
        else:
            m = re.match(r"[^.\[\]]+", path[pos:])
            if not m:
                raise PathSyntaxError(
                    f"路径语法非法：'{path}' 在位置 {pos} 处无法解析。"
                )
            key = m.group(0)
            if not expect_key and tokens:
                last_kind = tokens[-1][0]
                if last_kind == "key":
                    raise PathSyntaxError(
                        f"路径语法非法：'{path}' 中 '{tokens[-1][1]}{key}' 相邻键缺少点号分隔。"
                    )
            tokens.append(("key", key))
            pos += len(key)
            expect_key = False
    if not tokens:
        raise PathSyntaxError(f"路径语法非法：'{path}' 没有有效段。")
    return tokens


def _navigate_to_parent(doc: Any, tokens: list[tuple[str, Any]]) -> tuple[Any, Any]:
    cur = doc
    for i, (kind, key) in enumerate(tokens[:-1]):
        cur, _ = _descend(cur, kind, key, full_tokens=tokens[:i + 1])
    last_kind, last_key = tokens[-1]
    return cur, (last_kind, last_key)


def _descend(cur: Any, kind: str, key: Any, full_tokens: list) -> tuple[Any, Any]:
    path_so_far = _tokens_to_str(full_tokens)
    if kind == "key":
        if not isinstance(cur, dict):
            raise PathNotFoundError(
                f"路径不存在：'{path_so_far}' 中 '{key}' 要求对象，但当前节点不是对象。"
            )
        if key not in cur:
            existing = list(cur.keys())
            raise PathNotFoundError(
                f"路径不存在：'{path_so_far}' 中 '{key}' 键不存在。"
                f"现有键：{existing}"
            )
        return cur[key], key
    if kind == "index":
        if not isinstance(cur, list):
            raise PathNotFoundError(
                f"路径不存在：'{path_so_far}' 要求数组，但当前节点不是数组。"
            )
        length = len(cur)
        actual = key if key >= 0 else length + key
        if actual < 0 or actual >= length:
            raise PathNotFoundError(
                f"路径不存在：'{path_so_far}' 越界，该数组当前长度 {length}"
                f"（有效下标 0..{length - 1} 或用 [-1] 取末元素）。"
            )
        return cur[actual], actual
    # match
    if not isinstance(cur, list):
        raise PathNotFoundError(
            f"路径不存在：'{path_so_far}' 要求数组，但当前节点不是数组。"
        )
    mk, mv = key
    matches = [item for item in cur if isinstance(item, dict) and item.get(mk) == mv]
    if len(matches) == 0:
        existing_vals = [item.get(mk) for item in cur if isinstance(item, dict)]
        raise PathNotFoundError(
            f"路径不存在：{path_so_far}[{mk}={mv}] 无匹配。"
            f"现有 {mk} 值：{existing_vals}"
        )
    if len(matches) > 1:
        raise MultipleMatchError(
            f"路径匹配到多个节点：{path_so_far}[{mk}={mv}] 命中 {len(matches)} 条，"
            f"请改用下标精确定位（如 {path_so_far}[0]/{path_so_far}[1]）。"
        )
    idx = cur.index(matches[0])
    return cur[idx], idx


def _tokens_to_str(tokens: list) -> str:
    parts = []
    for kind, key in tokens:
        if kind == "key":
            parts.append(str(key))
        elif kind == "index":
            parts.append(f"[{key}]")
        else:
            mk, mv = key
            parts.append(f"[{mk}={mv}]")
    out = ""
    for p in parts:
        if p.startswith("[") or out == "":
            out += p
        else:
            out += "." + p if not p.startswith("[") else p
    return out


def set_by_path(doc: Any, path: str, value: Any) -> Any:
    import copy
    doc = copy.deepcopy(doc)
    tokens = _tokenize(path)
    parent, (last_kind, last_key) = _navigate_to_parent(doc, tokens)
    path_so_far = _tokens_to_str(tokens[:-1])
    if last_kind == "key":
        if not isinstance(parent, dict):
            raise PathNotFoundError(
                f"路径不存在：'{path}' 的目标节点不是对象，无法设置键 '{last_key}'。"
            )
        if last_key not in parent:
            existing = list(parent.keys())
            raise PathNotFoundError(
                f"路径不存在：'{path}' 中 '{last_key}' 键不存在。现有键：{existing}"
            )
        parent[last_key] = value
    elif last_kind == "index":
        if not isinstance(parent, list):
            raise PathNotFoundError(
                f"路径不存在：'{path}' 的目标节点不是数组。"
            )
        length = len(parent)
        actual = last_key if last_key >= 0 else length + last_key
        if actual < 0 or actual >= length:
            raise PathNotFoundError(
                f"路径不存在：'{path}' 越界，该数组当前长度 {length}"
                f"（有效下标 0..{length - 1} 或用 [-1] 取末元素）。"
            )
        parent[actual] = value
    else:
        mk, mv = last_key
        matches = [item for item in parent if isinstance(item, dict) and item.get(mk) == mv]
        if len(matches) == 0:
            existing_vals = [item.get(mk) for item in parent if isinstance(item, dict)]
            raise PathNotFoundError(
                f"路径不存在：{path_so_far}[{mk}={mv}] 无匹配。现有 {mk} 值：{existing_vals}"
            )
        if len(matches) > 1:
            raise MultipleMatchError(
                f"路径匹配到多个节点：{path_so_far}[{mk}={mv}] 命中 {len(matches)} 条，"
                f"请改用下标精确定位（如 {path_so_far}[0]/{path_so_far}[1]）。"
            )
        idx = parent.index(matches[0])
        parent[idx] = value
    return doc
```

- [ ] **Step 5: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest backend/tests/test_path_utils.py -v`
Expected: 所有测试 PASS。修复实现细节直到全绿。

- [ ] **Step 6: 提交**

```bash
git add backend/app/services/path_utils.py backend/tests/test_path_utils.py
git commit -m "feat: add path_utils for JSON path-based field updates"
```

---

## Task 2: 错误码常量与 SpecDocument 草稿列

**Files:**
- Modify: `backend/app/exceptions.py`
- Modify: `backend/app/models/spec.py`

- [ ] **Step 1: 加错误码常量（复用 40001/40404 语义，新增可读常量）**

Read `backend/app/exceptions.py`，确认已有 `ERR_VALIDATION = 40001` 和 `ERR_NOT_FOUND = 40400`。在合适位置追加：

```python
ERR_FIELD_PATH_SYNTAX = 40001   # 路径语法非法，复用 40001
ERR_FIELD_PATH_NOT_FOUND = 40404  # 路径节点不存在（用 40404，对齐 not-found 语义）
ERR_FIELD_PATH_MULTIPLE = 40001  # 路径匹配多个
ERR_NO_DRAFT = 40404              # 无草稿可 commit/discard
```

> 注：这些常量仅用于可读性，码值与现有 40001/40404 一致，不引入新码值。

- [ ] **Step 2: 给 SpecDocument 加两列**

Modify `backend/app/models/spec.py` 的 `SpecDocument` 类，在 `versions` 之后加：

```python
    draft_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    draft_base_version: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
```

- [ ] **Step 3: 为现有库执行 ALTER（手动，一次性）**

对 `obr_test` 和生产库执行（在 pg 客户端中）：

```sql
ALTER TABLE spec_documents ADD COLUMN IF NOT EXISTS draft_content JSONB;
ALTER TABLE spec_documents ADD COLUMN IF NOT EXISTS draft_base_version INTEGER;
```

新库通过 `init_db()` 自动建出这两列，无需手动执行。

- [ ] **Step 4: 确认测试仍通过（无回归）**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py -v -k "TestGetSpecDocument or TestSaveSpecDocument"`
Expected: PASS（草稿列 nullable，不影响现有读写）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/exceptions.py backend/app/models/spec.py
git commit -m "feat: add draft columns to SpecDocument and path error constants"
```

---

## Task 3: Spec 草稿服务层

**Files:**
- Modify: `backend/app/services/specification.py`

- [ ] **Step 1: 写失败测试 — set-spec-field 建草稿基线并局部写**

Append to `backend/tests/test_specifications.py` 末尾新增类：

```python
class TestSpecDraftSetField:
    @pytest.mark.asyncio
    async def test_set_field_creates_draft_from_current_version(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])

        # 先存一份正式版本
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "old", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )

        # 局部改 entity_definition.description
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "new desc"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["is_draft"] is True
        assert body["data"]["base_version"] == 1

        # GET 默认返回草稿
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["is_draft"] is True
        assert gdata["content"]["entity_definition"]["description"] == "new desc"
        # 其余字段保留
        assert gdata["content"]["table_design"] == {"tables": []}

    @pytest.mark.asyncio
    async def test_set_field_multiple_writes_accumulate(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "d1", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": [{"method": "GET", "path": "/a", "description": "a"}]},
                "constraints": {},
            }},
            headers=headers,
        )

        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "d2"},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "api_design.endpoints[0].description", "value": "updated"},
            headers=headers,
        )
        assert resp.json()["code"] == 0

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        content = get_resp.json()["data"]["content"]
        assert content["entity_definition"]["description"] == "d2"
        assert content["api_design"]["endpoints"][0]["description"] == "updated"

    @pytest.mark.asyncio
    async def test_set_field_status_not_drafting_spec(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "x"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40204

    @pytest.mark.asyncio
    async def test_set_field_path_not_found_actionable(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "d", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.nonexistent", "value": "x"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "description" in body["message"]  # existing key shown

    @pytest.mark.asyncio
    async def test_set_field_schema_validation_fails_rolls_back(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "d", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )
        # 把 fields 改成非法类型（应为数组）
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.fields", "value": "not_an_array"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001
        # 草稿未被污染：GET 仍是原内容（或无草稿）
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        # 草稿要么不存在（is_draft False），要么仍是空 fields
        assert get_resp.json()["code"] == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py::TestSpecDraftSetField -v`
Expected: FAIL — 端点不存在（404）。

- [ ] **Step 3: 实现草稿服务函数**

在 `backend/app/services/specification.py` 顶部 import 区加：

```python
from app.services.path_utils import (
    PathSyntaxError,
    PathNotFoundError,
    MultipleMatchError,
    set_by_path,
)
```

在 `save_spec_document` 函数之后追加：

```python
async def set_spec_draft_field(
    db: AsyncSession, req_id: int, user_id: int, path: str, value
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_spec":
        raise BusinessError(
            ERR_REQUIREMENT_STATUS,
            f"当前需求状态为 {req.status}，不允许编辑草稿。需处于 drafting_spec 状态。",
        )

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None or doc.current_version == 0:
        raise BusinessError(ERR_NOT_FOUND, "尚无正式 spec 版本，无法局部更新草稿。请先用 save-spec 提交初始版本。")

    if doc.draft_content is None:
        latest_version_entry = (doc.versions or [])[-1]
        doc.draft_content = latest_version_entry.get("content")
        doc.draft_base_version = doc.current_version

    try:
        new_draft = set_by_path(doc.draft_content, path, value)
    except PathSyntaxError as e:
        raise BusinessError(ERR_VALIDATION, str(e))
    except MultipleMatchError as e:
        raise BusinessError(ERR_VALIDATION, str(e))
    except PathNotFoundError as e:
        raise BusinessError(ERR_NOT_FOUND, str(e))

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors, suggestions = await _validate_spec_content(new_draft, db, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "草稿校验失败", errors=errors)

    doc.draft_content = new_draft
    await db.commit()
    return {
        "is_draft": True,
        "base_version": doc.draft_base_version,
        "errors": [],
        "suggestions": suggestions,
    }


async def commit_spec_draft(db: AsyncSession, req_id: int, user_id: int) -> dict:
    from datetime import datetime, timezone
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_spec":
        raise BusinessError(
            ERR_REQUIREMENT_STATUS,
            f"当前需求状态为 {req.status}，不允许定版草稿。需处于 drafting_spec 状态。",
        )

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None or doc.draft_content is None:
        raise BusinessError(ERR_NOT_FOUND, "无草稿可定版：当前 spec 无未提交草稿。用 set-spec-field 开始编辑草稿。")

    new_version_num = doc.current_version + 1
    new_entry = {
        "version": new_version_num,
        "content": doc.draft_content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
    }
    versions = list(doc.versions or [])
    versions.append(new_entry)
    doc.versions = versions
    doc.current_version = new_version_num
    doc.draft_content = None
    doc.draft_base_version = None
    await db.commit()
    return {"version": new_version_num, "committed_from_base": True}


async def discard_spec_draft(db: AsyncSession, req_id: int) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None or doc.draft_content is None:
        raise BusinessError(ERR_NOT_FOUND, "无草稿可丢弃：当前 spec 无未提交草稿。")
    doc.draft_content = None
    doc.draft_base_version = None
    await db.commit()
    return {"discarded": True, "current_version": doc.current_version}
```

修改 `get_spec_document`，在返回前判断草稿：

```python
async def get_spec_document(
    db: AsyncSession, req_id: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is not None and doc.draft_content is not None:
        return {
            "current_version": doc.current_version,
            "content": doc.draft_content,
            "is_draft": True,
            "base_version": doc.draft_base_version,
        }

    if doc is None or doc.current_version == 0:
        return {"current_version": 0, "content": None, "is_draft": False}

    versions = doc.versions or []
    content = versions[-1].get("content") if versions else None
    return {
        "current_version": doc.current_version,
        "content": content,
        "is_draft": False,
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py::TestSpecDraftSetField -v`
Expected: 全 PASS。修复实现直到全绿。

- [ ] **Step 5: 提交**

```bash
git add backend/app/services/specification.py backend/tests/test_specifications.py
git commit -m "feat: add spec draft set-field/commit/discard services"
```

---

## Task 4: Spec 草稿 API 端点 + commit/discard 测试

**Files:**
- Modify: `backend/app/api/requirements.py`

- [ ] **Step 1: 写失败测试 — commit 与 discard**

Append to `backend/tests/test_specifications.py`:

```python
class TestSpecDraftCommitDiscard:
    @pytest.mark.asyncio
    async def test_commit_creates_new_version_clears_draft(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])

        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "v1", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "v2-draft"},
            headers=headers,
        )

        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/specification/commit",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["version"] == 2

        # GET 不再是草稿
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["is_draft"] is False
        assert gdata["content"]["entity_definition"]["description"] == "v2-draft"
        assert gdata["current_version"] == 2

    @pytest.mark.asyncio
    async def test_commit_no_draft(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "v1", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )
        resp = await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/specification/commit",
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "无草稿" in body["message"]

    @pytest.mark.asyncio
    async def test_discard_returns_to_committed(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit", "specification:edit"])
        await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": {
                "entity_definition": {"description": "committed", "fields": []},
                "table_design": {"tables": []},
                "page_structure": {"pages": []},
                "api_design": {"endpoints": []},
                "constraints": {},
            }},
            headers=headers,
        )
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft/field",
            json={"path": "entity_definition.description", "value": "drafted"},
            headers=headers,
        )

        resp = await client.delete(
            f"/api/v1/requirements/{sample_requirement.id}/specification/draft",
            headers=headers,
        )
        assert resp.json()["code"] == 0

        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            headers=auth_headers(normal_user.id),
        )
        gdata = get_resp.json()["data"]
        assert gdata["is_draft"] is False
        assert gdata["content"]["entity_definition"]["description"] == "committed"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py::TestSpecDraftCommitDiscard -v`
Expected: FAIL — 路由不存在（404）。

- [ ] **Step 3: 加 API 端点**

在 `backend/app/api/requirements.py`，先在顶部 import 区确认有 `from app.services import specification as spec_svc`（参考现有 spec 端点）。在 `update_specification`（PUT /specification）端点之后追加：

```python
class SetSpecDraftFieldRequest(BaseModel):
    path: str
    value: Any = None


@router.patch("/{reqId}/specification/draft/field")
async def set_spec_draft_field(
    reqId: int,
    body: SetSpecDraftFieldRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.set_spec_draft_field(
        db, reqId, int(user["sub"]), body.path, body.value
    )
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/specification/commit")
async def commit_spec_draft(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.commit_spec_draft(db, reqId, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{reqId}/specification/draft")
async def discard_spec_draft(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.discard_spec_draft(db, reqId)
    return {"code": 0, "message": "success", "data": data}
```

> 确认 `Any` 已 import：在 requirements.py 顶部 `from typing import Annotated, Any`（若没有则补）。

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py -v`
Expected: 全部 PASS（含原有 + 新增草稿类）。

- [ ] **Step 5: 提交**

```bash
git add backend/app/api/requirements.py backend/tests/test_specifications.py
git commit -m "feat: add spec draft field/commit/discard API endpoints"
```

---

## Task 5: 需求 type_detail 路径下钻 + prototype_html

**Files:**
- Modify: `backend/app/api/requirements.py`
- Test: `backend/tests/test_requirements.py`

- [ ] **Step 1: 写失败测试 — type_detail 下钻**

Append to `backend/tests/test_requirements.py`（确认有 `auth_headers` import 与 `sample_requirement` fixture，参考现有类）：

```python
class TestPatchRequirementTypeDetailPath:
    @pytest.mark.asyncio
    async def test_type_detail_path_partial_update(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        sample_requirement.type_detail = {"severity": "low", "reproduce_steps": ["old"]}
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail_path": "reproduce_steps", "value": ["step1", "step2"]},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        # GET 验证只改了 reproduce_steps，severity 不变
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=auth_headers(normal_user.id),
        )
        td = get_resp.json()["data"]["type_detail"]
        assert td["severity"] == "low"
        assert td["reproduce_steps"] == ["step1", "step2"]

    @pytest.mark.asyncio
    async def test_type_detail_path_and_type_detail_mutually_exclusive(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail": {"a": 1}, "type_detail_path": "a", "value": 2},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001
        assert "type_detail_path" in body["message"]

    @pytest.mark.asyncio
    async def test_type_detail_path_not_found_actionable(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        sample_requirement.type_detail = {"severity": "low"}
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"type_detail_path": "nonexistent", "value": 1},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40404
        assert "severity" in body["message"]

    @pytest.mark.asyncio
    async def test_patch_prototype_html(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_req"
        db.add(sample_requirement)
        await db.commit()
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"prototype_html": "<div>proto</div>"},
            headers=headers,
        )
        assert resp.json()["code"] == 0
        get_resp = await client.get(
            f"/api/v1/requirements/{sample_requirement.id}",
            headers=auth_headers(normal_user.id),
        )
        assert get_resp.json()["data"]["prototype_html"] == "<div>proto</div>"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py::TestPatchRequirementTypeDetailPath -v`
Expected: FAIL — schema 不接受 `type_detail_path`/`value`。

- [ ] **Step 3: 扩展 schema + API 端点（最小改动，复用现有 inline 逻辑）**

现状（`backend/app/api/requirements.py`）：
- `PatchRequirementRequest`（121 行）**已含 `prototype_html`**，但**缺** `type_detail_path` / `value`。
- `patch_requirement`（277 行）inline 处理 status 转换 + title/description/type_detail/prototype_html 整体替换。**已正确应用 prototype_html（311-312 行）**，所以 prototype_html 仅需 CLI 暴露（Task 7），后端无需改这部分。

**改动 A — 扩展 schema**（121 行 `PatchRequirementRequest`）：

```python
class PatchRequirementRequest(BaseModel):
    status: str | None = None
    title: str | None = None
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None
    type_detail_path: str | None = None
    value: Any = None
```

确认顶部 `from typing import Annotated, Any`（若无 `Any` 则补）。

**改动 B — 在 `patch_requirement` 函数体内，于 `has_field_edits` 检查之后、`if body.title` 块之前，插入路径下钻分支**：

把 293-297 行的 `has_field_edits` 改为也包含 `type_detail_path`，并在互斥校验后插入分支：

```python
    has_field_edits = any(v is not None for v in [
        body.title, body.description, body.type_detail,
        body.prototype_html, body.type_detail_path,
    ])
    if has_field_edits and req.status not in EDITABLE_STATUSES:
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑")

    if body.type_detail is not None and body.type_detail_path is not None:
        raise BusinessError(
            ERR_VALIDATION,
            "type_detail_path 与 type_detail 不可同时提供，二选一。",
        )

    if body.type_detail_path is not None:
        from app.services.path_utils import (
            PathSyntaxError, PathNotFoundError, MultipleMatchError, set_by_path,
        )
        base = req.type_detail if isinstance(req.type_detail, dict) else {}
        if not base:
            raise BusinessError(
                ERR_NOT_FOUND,
                "路径不存在：type_detail 当前为空，无法下钻。请先用 type_detail 整体设置初始结构。",
            )
        full_path = f"type_detail.{body.type_detail_path}"
        try:
            new_td = set_by_path({"type_detail": base}, full_path, body.value)["type_detail"]
        except PathSyntaxError as e:
            raise BusinessError(ERR_VALIDATION, str(e))
        except MultipleMatchError as e:
            raise BusinessError(ERR_VALIDATION, str(e))
        except PathNotFoundError as e:
            raise BusinessError(ERR_NOT_FOUND, str(e))
        req.type_detail = new_td
        await db.commit()
        await db.refresh(req)
        return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}
```

> 现有 305-312 行（title/description/type_detail/prototype_html 整体替换）**保持不变**。`type_detail_path` 分支在它之前 return，不会冲突。

- [ ] **Step 4: 运行测试确认通过**

- [ ] **Step 5: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py -v`
Expected: 新增类 PASS，原有测试无回归。

- [ ] **Step 6: 提交**

```bash
git add backend/app/api/requirements.py backend/tests/test_requirements.py
git commit -m "feat: add type_detail path drill-down to PATCH requirement"
```

---

## Task 6: CLI 文件取值工具 `file_loader.py`

**Files:**
- Create: `cli/sdd_cli/file_loader.py`
- Create: `cli/tests/test_file_loader.py`

- [ ] **Step 1: 写失败测试**

Create `cli/tests/test_file_loader.py`:

```python
import json
from pathlib import Path

from sdd_cli.file_loader import load_value_from_file


class TestLoadValueFromFile:
    def test_json_file_parsed(self, tmp_path):
        f = tmp_path / "x.json"
        f.write_text(json.dumps(["a", "b"]), encoding="utf-8")
        assert load_value_from_file(str(f)) == ["a", "b"]

    def test_plain_text_kept_as_string(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("# 标题\n正文", encoding="utf-8")
        assert load_value_from_file(str(f)) == "# 标题\n正文"

    def test_html_kept_as_string(self, tmp_path):
        f = tmp_path / "x.html"
        f.write_text("<div>hi</div>", encoding="utf-8")
        assert load_value_from_file(str(f)) == "<div>hi</div>"

    def test_invalid_json_falls_back_to_string(self, tmp_path):
        f = tmp_path / "x.txt"
        f.write_text("{not valid json", encoding="utf-8")
        assert load_value_from_file(str(f)) == "{not valid json"

    def test_utf8_content(self, tmp_path):
        f = tmp_path / "x.md"
        f.write_text("中文内容", encoding="utf-8")
        assert load_value_from_file(str(f)) == "中文内容"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest cli/tests/test_file_loader.py -v`（若 cli 用单独 env 则用对应 env；先确认 sdd env 能 import sdd_cli——可能需 `pip install -e cli`）
Expected: FAIL — module not found。

- [ ] **Step 3: 实现 `file_loader.py`**

Create `cli/sdd_cli/file_loader.py`:

```python
import json


def load_value_from_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest cli/tests/test_file_loader.py -v`
Expected: 全 PASS。

- [ ] **Step 5: 提交**

```bash
git add cli/sdd_cli/file_loader.py cli/tests/test_file_loader.py
git commit -m "feat: add file_loader for CLI value-from-file with json auto-parse"
```

---

## Task 7: CLI 需求 set-field / set-spec-field / commit-spec / discard-spec-draft

**Files:**
- Modify: `cli/sdd_cli/requirements.py`
- Test: `cli/tests/test_requirements.py`

- [ ] **Step 1: 写失败测试 — set-spec-field**

先确认现有 `cli/tests/test_requirements.py` 的测试风格（如何 mock client）。参考其现有测试，append：

```python
from unittest.mock import patch


class TestSetSpecField:
    def test_set_spec_field_reads_file(self, tmp_path):
        f = tmp_path / "desc.md"
        f.write_text("新描述", encoding="utf-8")
        with patch("sdd_cli.requirements.get_client") as gc:
            gc.return_value.patch.return_value = {"is_draft": True, "base_version": 1}
            from typer.testing import CliRunner
            from sdd_cli.requirements import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "set-spec-field", "5", "entity_definition.description",
                "--file", str(f),
            ])
            assert result.exit_code == 0
            called = gc.return_value.patch.call_args
            assert called.args[0] == "/requirements/5/specification/draft/field"
            assert called.kwargs["json"]["path"] == "entity_definition.description"
            assert called.kwargs["json"]["value"] == "新描述"


class TestCommitSpec:
    def test_commit_spec(self):
        with patch("sdd_cli.requirements.get_client") as gc:
            gc.return_value.post.return_value = {"version": 2}
            from typer.testing import CliRunner
            from sdd_cli.requirements import app
            runner = CliRunner()
            result = runner.invoke(app, ["commit-spec", "5"])
            assert result.exit_code == 0
            gc.return_value.post.assert_called_with("/requirements/5/specification/commit")


class TestDiscardSpecDraft:
    def test_discard_spec_draft(self):
        with patch("sdd_cli.requirements.get_client") as gc:
            gc.return_value.delete.return_value = {"discarded": True}
            from typer.testing import CliRunner
            from sdd_cli.requirements import app
            runner = CliRunner()
            result = runner.invoke(app, ["discard-spec-draft", "5"])
            assert result.exit_code == 0
            gc.return_value.delete.assert_called_with("/requirements/5/specification/draft")


class TestReqSetField:
    def test_set_field_prototype_html(self, tmp_path):
        f = tmp_path / "proto.html"
        f.write_text("<div>x</div>", encoding="utf-8")
        with patch("sdd_cli.requirements.get_client") as gc:
            gc.return_value.patch.return_value = {"id": 5, "status": "drafting_req"}
            from typer.testing import CliRunner
            from sdd_cli.requirements import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "set-field", "5", "prototype_html", "--file", str(f),
            ])
            assert result.exit_code == 0
            called = gc.return_value.patch.call_args
            assert called.args[0] == "/requirements/5"
            assert called.kwargs["json"]["prototype_html"] == "<div>x</div>"

    def test_set_field_type_detail_path(self, tmp_path):
        f = tmp_path / "steps.json"
        import json as _json
        f.write_text(_json.dumps(["s1", "s2"]), encoding="utf-8")
        with patch("sdd_cli.requirements.get_client") as gc:
            gc.return_value.patch.return_value = {"id": 5, "status": "drafting_req"}
            from typer.testing import CliRunner
            from sdd_cli.requirements import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "set-field", "5", "type_detail.reproduce_steps", "--file", str(f),
            ])
            assert result.exit_code == 0
            called = gc.return_value.patch.call_args
            assert called.kwargs["json"]["type_detail_path"] == "type_detail.reproduce_steps"
            assert called.kwargs["json"]["value"] == ["s1", "s2"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest cli/tests/test_requirements.py -v -k "SetSpecField or CommitSpec or DiscardSpecDraft or ReqSetField"`
Expected: FAIL — 命令不存在。

- [ ] **Step 3: 实现 CLI 命令**

在 `cli/sdd_cli/requirements.py` 顶部 import 区加：

```python
from sdd_cli.file_loader import load_value_from_file
```

在文件末尾追加命令：

```python
@app.command("set-spec-field")
def set_spec_field(
    id: int,
    path: str = typer.Argument(...),
    file: str = typer.Option(..., "--file", "-f"),
) -> None:
    try:
        value = load_value_from_file(file)
        client = get_client()
        data = client.patch(
            f"/requirements/{id}/specification/draft/field",
            json={"path": path, "value": value},
        )
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("commit-spec")
def commit_spec(id: int) -> None:
    try:
        client = get_client()
        data = client.post(f"/requirements/{id}/specification/commit")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("discard-spec-draft")
def discard_spec_draft(id: int) -> None:
    try:
        client = get_client()
        data = client.delete(f"/requirements/{id}/specification/draft")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("set-field")
def set_requirement_field(
    id: int,
    path: str = typer.Argument(...),
    file: str = typer.Option(..., "--file", "-f"),
) -> None:
    try:
        value = load_value_from_file(file)
        client = get_client()
        body: dict = {}
        if path == "prototype_html":
            body["prototype_html"] = value
        elif path.startswith("type_detail."):
            body["type_detail_path"] = path[len("type_detail."):]
            body["value"] = value
        else:
            typer.echo(
                f"Error: 不支持的字段路径 '{path}'。支持 prototype_html 或 type_detail.<subpath>",
                err=True,
            )
            raise typer.Exit(code=1)
        data = client.patch(f"/requirements/{id}", json=body)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest cli/tests/test_requirements.py -v -k "SetSpecField or CommitSpec or DiscardSpecDraft or ReqSetField"`
Expected: 全 PASS。

- [ ] **Step 5: 提交**

```bash
git add cli/sdd_cli/requirements.py cli/tests/test_requirements.py
git commit -m "feat: add CLI set-field/set-spec-field/commit-spec/discard-spec-draft"
```

---

## Task 8: CLI test_case set-field

**Files:**
- Modify: `cli/sdd_cli/test_cases.py`
- Test: `cli/tests/test_test_cases.py`

- [ ] **Step 1: 写失败测试**

先读 `cli/tests/test_test_cases.py` 确认现有 mock 风格，append：

```python
from unittest.mock import patch


class TestTcSetField:
    def test_set_field_steps(self, tmp_path):
        f = tmp_path / "steps.txt"
        f.write_text("1. 步骤一\n2. 步骤二", encoding="utf-8")
        with patch("sdd_cli.test_cases.get_client") as gc:
            gc.return_value.put.return_value = {"id": 9}
            from typer.testing import CliRunner
            from sdd_cli.test_cases import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "set-field", "9", "steps", "--file", str(f),
            ])
            assert result.exit_code == 0
            called = gc.return_value.put.call_args
            assert called.args[0] == "/test-cases/9"
            assert called.kwargs["json"]["steps"] == "1. 步骤一\n2. 步骤二"

    def test_set_field_expected(self, tmp_path):
        f = tmp_path / "expected.md"
        f.write_text("预期结果", encoding="utf-8")
        with patch("sdd_cli.test_cases.get_client") as gc:
            gc.return_value.put.return_value = {"id": 9}
            from typer.testing import CliRunner
            from sdd_cli.test_cases import app
            runner = CliRunner()
            result = runner.invoke(app, [
                "set-field", "9", "expected", "--file", str(f),
            ])
            assert result.exit_code == 0
            assert gc.return_value.put.call_args.kwargs["json"]["expected_result"] == "预期结果"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `conda run -n sdd python -m pytest cli/tests/test_test_cases.py -v -k TestTcSetField`
Expected: FAIL — 命令不存在。

- [ ] **Step 3: 实现 set-field 命令**

在 `cli/sdd_cli/test_cases.py` 顶部 import 区加：

```python
from sdd_cli.file_loader import load_value_from_file
```

在 `update_test_case` 之后追加：

```python
_FIELD_MAP = {
    "title": "title",
    "type": "case_type",
    "precondition": "precondition",
    "steps": "steps",
    "expected": "expected_result",
    "related_api": "related_api",
    "related_element": "related_element",
}


@app.command("set-field")
def set_test_case_field(
    id: int,
    field: str = typer.Argument(...),
    file: str = typer.Option(..., "--file", "-f"),
) -> None:
    try:
        if field not in _FIELD_MAP:
            typer.echo(
                f"Error: 不支持的字段 '{field}'。支持：{list(_FIELD_MAP.keys())}",
                err=True,
            )
            raise typer.Exit(code=1)
        value = load_value_from_file(file)
        client = get_client()
        data = client.put(f"/test-cases/{id}", json={_FIELD_MAP[field]: value})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `conda run -n sdd python -m pytest cli/tests/test_test_cases.py -v -k TestTcSetField`
Expected: 全 PASS。

- [ ] **Step 5: 提交**

```bash
git add cli/sdd_cli/test_cases.py cli/tests/test_test_cases.py
git commit -m "feat: add CLI test-case set-field command"
```

---

## Task 9: 全量回归 + 联调验证

**Files:** 无（仅运行验证）

- [ ] **Step 1: 后端全量测试**

Run: `conda run -n sdd python -m pytest backend/tests/ -v`
Expected: 所有相关测试 PASS（已知预先存在的 `*_no_permission` 用例失败与本次无关，记录但不算回归）。

- [ ] **Step 2: CLI 全量测试**

Run: `conda run -n sdd python -m pytest cli/tests/ -v`
Expected: 全 PASS。

- [ ] **Step 3: 手动联调（端到端）**

启动服务（先 stop 再 start）：

```bash
./scripts/services.sh stop
./scripts/services.sh start
```

用真实 token 走一遍草稿流程（替换 `<id>` 与 token）：

```bash
# 1. 建草稿基线（需 requirement 处于 drafting_spec 且已有正式版本）
sdd requirements set-spec-field <id> entity_definition.description --file desc.md
# 2. 再改一处
sdd requirements set-spec-field <id> api_design.endpoints[0].description --file api.md
# 3. 确认 GET 返回草稿
sdd requirements get-spec <id>
# 4. 定版
sdd requirements commit-spec <id>
# 5. 确认定版后无草稿
sdd requirements get-spec <id>
```

验证：每步返回 `code: 0`，GET 第 3 步 `is_draft: true`、第 5 步 `is_draft: false`。

- [ ] **Step 4: 验证错误信息可操作性**

故意触发路径错误，确认 Agent 可读：

```bash
echo "x" > /tmp/bad.md
sdd requirements set-spec-field <id> entity_definition.nonexistent --file /tmp/bad.md
```

Expected: 错误信息含"现有键：[description, fields]"，Agent 据此知道改路径。

- [ ] **Step 5: 提交（如有文档/脚本调整）**

```bash
git add -A
git commit -m "test: end-to-end verification of local field updates" --allow-empty
```

---

## 完成标准

- 路径工具单测全绿（Task 1）
- spec 草稿 set/commit/discard 端点+服务测试全绿（Task 3-4）
- 需求 type_detail 下钻 + prototype_html 测试全绿（Task 5）
- CLI 5 个新命令测试全绿（Task 6-8）
- 端到端联调通过（Task 9）
- 错误信息对 Agent 可操作（含现有键/长度/有效下标）
- 无回归（预先存在的 no_permission 失败除外）
