# SDD CLI + Agent Skills 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 Python CLI 工具 (`sdd` 命令) 包装全部 96 个 API 端点，并创建 5 个 Agent Skills 引导 AI Agent 完成从需求发现到代码提交的全流程。

**Architecture:** CLI 作为独立 Python 包安装在 conda env `sdd` 中，使用 typer 做命令框架、httpx 做 HTTP 调用、rich 做表格输出。每个命令模块对应一个 API 域，通过共享的 `SDDClient` 调用后端。5 个 Skills 以 markdown 文件形式存放在 `.superpowers/skills/` 下，每个 Skill 描述一个完整的 Agent 工作流。

**Tech Stack:** Python 3.12, typer, httpx, rich, typer.testing.CliRunner (测试)

**测试命令:** `conda run -n sdd python -m pytest cli/tests/ -v`

---

## 依赖图

```
Task 1: CLI Scaffold (config, output, main) ──┐
Task 2: HTTP Client ──────────────────────────┤
                                               ↓
Task 3: Auth + Me Commands ───────────────────┤ (depends on 1, 2)
Task 4: Teams Commands ───────────────────────┤
Task 5: Projects + Iterations Commands ───────┤
Task 6: Requirements Commands ────────────────┤  (all parallel after 1-2)
Task 7: Tasks Commands ───────────────────────┤
Task 8a: Test Cases + Test Executions ────────┤
Task 8b: Admin Commands ──────────────────────┘
                                               ↓
Task 9-13: Skills (depends on CLI complete)
```

---

## File Structure

```
cli/
├── pyproject.toml
├── sdd_cli/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── client.py
│   ├── output.py
│   ├── auth.py
│   ├── me.py
│   ├── teams.py
│   ├── projects.py
│   ├── iterations.py
│   ├── requirements.py
│   ├── tasks.py
│   ├── test_cases.py
│   ├── test_executions.py
│   └── admin.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_config.py
    ├── test_client.py
    ├── test_output.py
    ├── test_auth.py
    ├── test_me.py
    ├── test_teams.py
    ├── test_projects.py
    ├── test_iterations.py
    ├── test_requirements.py
    ├── test_tasks.py
    ├── test_test_cases.py
    ├── test_test_executions.py
    └── test_admin.py

.superpowers/skills/
├── sdd-discover-work/SKILL.md
├── sdd-project-setup/SKILL.md
├── sdd-spec-writing/SKILL.md
├── sdd-task-execution/SKILL.md
└── sdd-review/SKILL.md
```

---

## Phase 1: CLI 基础架构

### Task 1: CLI Scaffold — config + output + main

**Files:**
- Create: `cli/pyproject.toml`
- Create: `cli/sdd_cli/__init__.py`
- Create: `cli/sdd_cli/main.py`
- Create: `cli/sdd_cli/config.py`
- Create: `cli/sdd_cli/output.py`
- Create: `cli/tests/__init__.py`
- Create: `cli/tests/conftest.py`
- Create: `cli/tests/test_config.py`
- Create: `cli/tests/test_output.py`

- [ ] **Step 1: 创建项目骨架**

```bash
mkdir -p cli/sdd_cli cli/tests
```

创建 `cli/pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "sdd-cli"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "httpx>=0.27",
    "rich>=13.0",
]

[project.scripts]
sdd = "sdd_cli.main:app"

[tool.setuptools.packages.find]
where = ["."]
include = ["sdd_cli*"]
```

创建 `cli/sdd_cli/__init__.py`:

```python
```

创建 `cli/tests/__init__.py`:

```python
```

- [ ] **Step 2: 写测试 — config.py**

创建 `cli/tests/test_config.py`:

```python
import json
import os
from unittest.mock import patch
import pytest
from sdd_cli.config import Config, DEFAULT_API_URL


class TestConfigLoad:
    def test_load_from_env(self, tmp_path):
        with patch.dict(os.environ, {"SDD_API_KEY": "sdd_test123", "SDD_API_URL": "http://custom:9000/api/v1"}):
            with patch("sdd_cli.config.CONFIG_FILE", tmp_path / "config.json"):
                cfg = Config.load()
                assert cfg.api_key == "sdd_test123"
                assert cfg.api_url == "http://custom:9000/api/v1"

    def test_load_from_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"api_key": "sdd_from_file", "api_url": "http://file:8000/api/v1"}))
        with patch.dict(os.environ, {"SDD_API_KEY": "", "SDD_API_URL": ""}, clear=False):
            with patch("sdd_cli.config.CONFIG_FILE", config_file):
                cfg = Config.load()
                assert cfg.api_key == "sdd_from_file"
                assert cfg.api_url == "http://file:8000/api/v1"

    def test_defaults_when_no_env_no_file(self, tmp_path):
        with patch.dict(os.environ, {}, clear=True):
            with patch("sdd_cli.config.CONFIG_FILE", tmp_path / "nonexistent.json"):
                cfg = Config.load()
                assert cfg.api_key == ""
                assert cfg.api_url == DEFAULT_API_URL

    def test_env_overrides_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"api_key": "file_key", "api_url": "http://file:8000/api/v1"}))
        with patch.dict(os.environ, {"SDD_API_KEY": "env_key"}, clear=False):
            with patch("sdd_cli.config.CONFIG_FILE", config_file):
                cfg = Config.load()
                assert cfg.api_key == "env_key"


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        config_file = tmp_path / "sdd" / "config.json"
        with patch("sdd_cli.config.CONFIG_FILE", config_file):
            cfg = Config(api_key="sdd_new_key", api_url="http://localhost:8000/api/v1")
            cfg.save()
            assert config_file.exists()
            data = json.loads(config_file.read_text())
            assert data["api_key"] == "sdd_new_key"

    def test_save_overwrites(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({"api_key": "old"}))
        with patch("sdd_cli.config.CONFIG_FILE", config_file):
            cfg = Config(api_key="new")
            cfg.save()
            data = json.loads(config_file.read_text())
            assert data["api_key"] == "new"
```

- [ ] **Step 3: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest cli/tests/test_config.py -v
```

预期：FAIL（`sdd_cli` 模块不存在）

- [ ] **Step 4: 实现 config.py**

创建 `cli/sdd_cli/config.py`:

```python
import json
import os
from pathlib import Path

DEFAULT_API_URL = "http://localhost:8000/api/v1"
CONFIG_DIR = Path.home() / ".sdd"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self, api_url: str = DEFAULT_API_URL, api_key: str = ""):
        self.api_url = api_url
        self.api_key = api_key

    @classmethod
    def load(cls) -> "Config":
        api_url = os.getenv("SDD_API_URL", DEFAULT_API_URL)
        api_key = os.getenv("SDD_API_KEY", "")

        if not api_key and CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                api_key = data.get("api_key", "")
                if not os.getenv("SDD_API_URL"):
                    api_url = data.get("api_url", api_url)
            except (json.JSONDecodeError, OSError):
                pass

        return cls(api_url=api_url, api_key=api_key)

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps({"api_key": self.api_key, "api_url": self.api_url}, indent=2))
```

- [ ] **Step 5: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest cli/tests/test_config.py -v
```

- [ ] **Step 6: 写测试 — output.py**

创建 `cli/tests/test_output.py`:

```python
import json
from sdd_cli.output import print_response


class TestFormatJson:
    def test_simple_dict(self, capsys):
        print_response({"id": 1, "name": "test"}, format="json")
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert data["id"] == 1

    def test_list(self, capsys):
        items = [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}]
        print_response(items, format="json")
        out = capsys.readouterr().out.strip()
        data = json.loads(out)
        assert len(data) == 2

    def test_nested_dict(self, capsys):
        data = {"outer": {"inner": "value"}}
        print_response(data, format="json")
        out = capsys.readouterr().out.strip()
        parsed = json.loads(out)
        assert parsed["outer"]["inner"] == "value"


class TestFormatTable:
    def test_list_table(self, capsys):
        items = [{"id": 1, "title": "Task A"}, {"id": 2, "title": "Task B"}]
        print_response(items, format="table")
        out = capsys.readouterr().out
        assert "id" in out
        assert "Task A" in out
        assert "Task B" in out

    def test_empty_list(self, capsys):
        print_response([], format="table")
        out = capsys.readouterr().out.strip()
        assert "empty" in out.lower() or out == ""

    def test_dict_table(self, capsys):
        data = {"key1": "val1", "key2": "val2"}
        print_response(data, format="table")
        out = capsys.readouterr().out
        assert "key1" in out
        assert "val1" in out
```

- [ ] **Step 7: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest cli/tests/test_output.py -v
```

- [ ] **Step 8: 实现 output.py**

创建 `cli/sdd_cli/output.py`:

```python
import json
import sys


def print_response(data, format: str = "json"):
    if format == "json":
        print(json.dumps(data, ensure_ascii=False, indent=2))
    elif format == "table":
        _print_table(data)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _print_table(data):
    if isinstance(data, list):
        _print_list_table(data)
    elif isinstance(data, dict):
        _print_dict_table(data)
    else:
        print(data)


def _print_list_table(items: list):
    if not items:
        print("(empty)")
        return
    headers = list(items[0].keys())
    col_widths = {h: len(str(h)) for h in headers}
    for item in items:
        for h in headers:
            col_widths[h] = max(col_widths[h], min(len(str(item.get(h, ""))), 40))
    header_line = "  ".join(str(h).ljust(col_widths[h]) for h in headers)
    print(header_line)
    print("-" * len(header_line))
    for item in items:
        row = "  ".join(str(item.get(h, ""))[:col_widths[h]].ljust(col_widths[h]) for h in headers)
        print(row)


def _print_dict_table(data: dict):
    if not data:
        print("(empty)")
        return
    max_key_len = max(len(str(k)) for k in data.keys())
    for k, v in data.items():
        val = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v)
        print(f"{str(k).ljust(max_key_len)}  {val}")
```

- [ ] **Step 9: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest cli/tests/test_output.py -v
```

- [ ] **Step 10: 创建 main.py 骨架**

创建 `cli/sdd_cli/main.py`:

```python
import typer

app = typer.Typer(name="sdd", help="SDD CLI - Agent-driven development tool", no_args_is_help=True)


@app.callback()
def main():
    pass


if __name__ == "__main__":
    app()
```

- [ ] **Step 11: 创建 conftest.py**

创建 `cli/tests/conftest.py`:

```python
from unittest.mock import MagicMock
import pytest
from typer.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.get.return_value = {}
    client.post.return_value = {}
    client.put.return_value = {}
    client.patch.return_value = {}
    client.delete.return_value = {}
    return client
```

- [ ] **Step 12: 安装 CLI 包**

```bash
conda run -n sdd pip install -e ./cli
```

- [ ] **Step 13: 验证 sdd 命令可用**

```bash
conda run -n sdd sdd --help
```

预期：显示帮助信息

- [ ] **Step 14: 跑全部 CLI 测试**

```bash
conda run -n sdd python -m pytest cli/tests/ -v
```

- [ ] **Step 15: 提交**

```bash
git add cli/
git commit -m "feat: scaffold SDD CLI with config and output modules"
```

---

### Task 2: HTTP Client — SDDClient + APIError

**Files:**
- Create: `cli/sdd_cli/client.py`
- Create: `cli/tests/test_client.py`

- [ ] **Step 1: 写测试 — client.py**

创建 `cli/tests/test_client.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from sdd_cli.client import SDDClient, APIError


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {"code": 0, "message": "success", "data": {}}
    return resp


class TestSDDClientInit:
    def test_init_with_config(self):
        from sdd_cli.config import Config
        cfg = Config(api_key="sdd_test", api_url="http://localhost:8000/api/v1")
        client = SDDClient(config=cfg)
        assert client.api_key == "sdd_test"
        assert client.base_url == "http://localhost:8000/api/v1"

    def test_init_loads_config(self):
        with patch("sdd_cli.client.Config.load") as mock_load:
            from sdd_cli.config import Config
            mock_load.return_value = Config(api_key="sdd_auto", api_url="http://auto:8000/api/v1")
            client = SDDClient()
            assert client.api_key == "sdd_auto"


class TestSDDClientHeaders:
    def test_headers_with_api_key(self):
        from sdd_cli.config import Config
        cfg = Config(api_key="sdd_key123")
        client = SDDClient(config=cfg)
        headers = client._headers()
        assert headers["X-API-Key"] == "sdd_key123"

    def test_headers_without_api_key(self):
        from sdd_cli.config import Config
        cfg = Config(api_key="")
        client = SDDClient(config=cfg)
        headers = client._headers()
        assert "X-API-Key" not in headers


class TestSDDClientMethods:
    @pytest.fixture
    def client(self):
        from sdd_cli.config import Config
        cfg = Config(api_key="sdd_test", api_url="http://localhost:8000/api/v1")
        c = SDDClient(config=cfg)
        return c

    def test_get_success(self, client):
        expected = {"id": 1, "name": "test"}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.get = MagicMock(return_value=resp)
        result = client.get("/users/me")
        assert result == expected
        client._client.get.assert_called_once_with("/users/me", params=None)

    def test_get_with_params(self, client):
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": {"items": []}})
        client._client.get = MagicMock(return_value=resp)
        client.get("/requirements", params={"status": "drafting_req"})
        client._client.get.assert_called_once_with("/requirements", params={"status": "drafting_req"})

    def test_post_success(self, client):
        expected = {"token": "jwt_xxx"}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.post = MagicMock(return_value=resp)
        result = client.post("/auth/login", json={"email": "test@test.com", "password": "12345678"})
        assert result == expected
        client._client.post.assert_called_once_with("/auth/login", json={"email": "test@test.com", "password": "12345678"})

    def test_put_success(self, client):
        expected = {"id": 1, "name": "updated"}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.put = MagicMock(return_value=resp)
        result = client.put("/teams/1", json={"name": "updated"})
        assert result == expected

    def test_patch_success(self, client):
        expected = {"id": 1, "status": "coding"}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.patch = MagicMock(return_value=resp)
        result = client.patch("/tasks/1", json={"status": "coding"})
        assert result == expected

    def test_delete_success(self, client):
        expected = {"id": 1}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.delete = MagicMock(return_value=resp)
        result = client.delete("/requirements/1")
        assert result == expected


class TestAPIError:
    def test_raises_on_nonzero_code(self, client):
        resp = _mock_response(json_data={"code": 40100, "message": "Unauthorized", "data": None})
        client._client.get = MagicMock(return_value=resp)
        with pytest.raises(APIError) as exc_info:
            client.get("/users/me")
        assert exc_info.value.code == 40100
        assert "Unauthorized" in str(exc_info.value.message)

    def test_raises_on_validation_error(self, client):
        resp = _mock_response(json_data={"code": 40001, "message": "Validation error", "data": [{"field": "name", "msg": "required"}]})
        client._client.post = MagicMock(return_value=resp)
        with pytest.raises(APIError) as exc_info:
            client.post("/admin/api-keys", json={"user_id": 1, "name": ""})
        assert exc_info.value.code == 40001
        assert exc_info.value.data is not None

    def test_unwrap_returns_data_field(self, client):
        expected = {"key": "value"}
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": expected})
        client._client.get = MagicMock(return_value=resp)
        result = client.get("/test")
        assert result == expected

    def test_unwrap_empty_data(self, client):
        resp = _mock_response(json_data={"code": 0, "message": "success", "data": None})
        client._client.get = MagicMock(return_value=resp)
        result = client.get("/test")
        assert result is None
```

- [ ] **Step 2: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest cli/tests/test_client.py -v
```

预期：FAIL（`sdd_cli.client` 不存在）

- [ ] **Step 3: 实现 client.py**

创建 `cli/sdd_cli/client.py`:

```python
import httpx
from sdd_cli.config import Config


class APIError(Exception):
    def __init__(self, code: int, message: str, data=None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"[{code}] {message}")


class SDDClient:
    def __init__(self, config: Config | None = None):
        if config is None:
            config = Config.load()
        self.base_url = config.api_url.rstrip("/")
        self.api_key = config.api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=self._headers(),
            timeout=30.0,
        )

    def _headers(self) -> dict:
        if self.api_key:
            return {"X-API-Key": self.api_key}
        return {}

    def _unwrap(self, resp: httpx.Response):
        data = resp.json()
        if data.get("code", 0) != 0:
            raise APIError(data["code"], data.get("message", "Unknown error"), data.get("data"))
        return data.get("data")

    def get(self, path: str, params: dict | None = None):
        resp = self._client.get(path, params=params)
        return self._unwrap(resp)

    def post(self, path: str, json: dict | None = None):
        resp = self._client.post(path, json=json)
        return self._unwrap(resp)

    def put(self, path: str, json: dict | None = None):
        resp = self._client.put(path, json=json)
        return self._unwrap(resp)

    def patch(self, path: str, json: dict | None = None):
        resp = self._client.patch(path, json=json)
        return self._unwrap(resp)

    def delete(self, path: str):
        resp = self._client.delete(path)
        return self._unwrap(resp)


def get_client() -> SDDClient:
    return SDDClient()
```

- [ ] **Step 4: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest cli/tests/test_client.py -v
```

- [ ] **Step 5: 提交**

```bash
git add cli/sdd_cli/client.py cli/tests/test_client.py
git commit -m "feat: add SDDClient with API error handling"
```

---

## Phase 2: 命令组

### Task 3: Auth + Me Commands

**Files:**
- Create: `cli/sdd_cli/auth.py`
- Create: `cli/sdd_cli/me.py`
- Create: `cli/tests/test_auth.py`
- Create: `cli/tests/test_me.py`
- Modify: `cli/sdd_cli/main.py`

- [ ] **Step 1: 写测试 — auth.py**

创建 `cli/tests/test_auth.py`:

```python
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import pytest

from sdd_cli.main import app


@pytest.fixture
def runner():
    return CliRunner()


class TestAuthLogin:
    def test_login_success(self, runner, mock_client):
        mock_client.post.return_value = {
            "access_token": "jwt_xxx",
            "token_type": "bearer",
            "user": {"id": 1, "email": "test@test.com", "nickname": "Tester"},
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            with patch("sdd_cli.auth.Config") as mock_cfg:
                mock_cfg.load.return_value = MagicMock(api_url="http://localhost:8000/api/v1")
                result = runner.invoke(app, ["auth", "login", "--email", "test@test.com", "--password", "12345678"])
        assert result.exit_code == 0
        assert "jwt_xxx" in result.output

    def test_login_failure(self, runner, mock_client):
        from sdd_cli.client import APIError
        mock_client.post.side_effect = APIError(40003, "Invalid credentials")
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "login", "--email", "bad@test.com", "--password", "wrong"])
        assert result.exit_code == 1
        assert "Invalid credentials" in result.output

    def test_login_missing_args(self, runner):
        result = runner.invoke(app, ["auth", "login"])
        assert result.exit_code != 0


class TestAuthRegister:
    def test_register_success(self, runner, mock_client):
        mock_client.post.return_value = {
            "user": {"id": 2, "email": "new@test.com", "nickname": "NewUser"},
            "message": "验证邮件已发送",
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, [
                "auth", "register",
                "--email", "new@test.com",
                "--password", "12345678",
                "--nickname", "NewUser",
            ])
        assert result.exit_code == 0


class TestAuthWhoami:
    def test_whoami_with_key(self, runner, mock_client):
        mock_client.get.return_value = {
            "id": 1,
            "email": "test@test.com",
            "nickname": "Tester",
            "permissions": ["project:create"],
        }
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "whoami"])
        assert result.exit_code == 0
        assert "test@test.com" in result.output

    def test_whoami_no_key(self, runner, mock_client):
        from sdd_cli.client import APIError
        mock_client.get.side_effect = APIError(40100, "Not authenticated")
        with patch("sdd_cli.auth.get_client", return_value=mock_client):
            result = runner.invoke(app, ["auth", "whoami"])
        assert result.exit_code == 1


class TestAuthLogout:
    def test_logout(self, runner):
        with patch("sdd_cli.auth.Config") as mock_cfg:
            mock_cfg.load.return_value = MagicMock(api_key="sdd_old", api_url="http://localhost:8000/api/v1", save=MagicMock())
            result = runner.invoke(app, ["auth", "logout"])
        assert result.exit_code == 0
```

- [ ] **Step 2: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest cli/tests/test_auth.py -v
```

- [ ] **Step 3: 实现 auth.py**

创建 `cli/sdd_cli/auth.py`:

```python
import typer
from sdd_cli.client import get_client, APIError
from sdd_cli.config import Config
from sdd_cli.output import print_response

app = typer.Typer(help="Authentication commands")


@app.command()
def login(
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p"),
    remember: bool = typer.Option(False, "--remember"),
):
    try:
        client = get_client()
        data = client.post("/auth/login", json={"email": email, "password": password, "remember": remember})
        token = data.get("access_token", "")
        cfg = Config.load()
        cfg.api_key = ""
        cfg.save()
        print_response({"access_token": token, "user": data.get("user", {})})
        typer.echo("Hint: Use API key auth for agents. Store token in SDD_API_KEY env var.", err=True)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def register(
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p"),
    nickname: str = typer.Option(..., "--nickname", "-n"),
):
    try:
        client = get_client()
        data = client.post("/auth/register", json={"email": email, "password": password, "nickname": nickname})
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def whoami():
    try:
        client = get_client()
        data = client.get("/users/me")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def logout():
    cfg = Config.load()
    cfg.api_key = ""
    cfg.save()
    typer.echo("Logged out. API key removed from config.")
```

- [ ] **Step 4: 写测试 — me.py**

创建 `cli/tests/test_me.py`:

```python
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
import pytest

from sdd_cli.main import app


@pytest.fixture
def runner():
    return CliRunner()


class TestMeInfo:
    def test_me_success(self, runner, mock_client):
        mock_client.get.return_value = {
            "id": 1,
            "email": "test@test.com",
            "nickname": "Tester",
            "permissions": ["project:create", "member:invite"],
        }
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me"])
        assert result.exit_code == 0
        assert "test@test.com" in result.output


class TestMeTasks:
    def test_list_my_tasks(self, runner, mock_client):
        mock_client.get.return_value = {
            "items": [
                {"id": 1, "title": "Task A", "status": "coding", "requirement_title": "Req 1"},
                {"id": 2, "title": "Task B", "status": "pending", "requirement_title": "Req 2"},
            ],
            "total": 2,
            "offset": 0,
            "limit": 50,
            "has_more": False,
        }
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "tasks"])
        assert result.exit_code == 0
        assert "Task A" in result.output

    def test_list_my_tasks_with_status(self, runner, mock_client):
        mock_client.get.return_value = {
            "items": [{"id": 1, "title": "Task A", "status": "coding", "requirement_title": "Req 1"}],
            "total": 1,
            "offset": 0,
            "limit": 50,
            "has_more": False,
        }
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "tasks", "--status", "coding"])
        assert result.exit_code == 0
        mock_client.get.assert_called_once_with("/users/me/tasks", params={"status": "coding", "offset": 0, "limit": 50})


class TestMePending:
    def test_pending_items(self, runner, mock_client):
        mock_client.get.return_value = {
            "teams": [{"id": 1, "name": "Team A"}],
            "projects": [{"id": 1, "name": "Project A"}],
            "assigned_tasks": [{"id": 1, "title": "Task 1"}],
            "pending_reviews": [],
        }
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending"])
        assert result.exit_code == 0
        assert "Team A" in result.output


class TestMePendingReviews:
    def test_pending_reviews(self, runner, mock_client):
        mock_client.get.return_value = [
            {"requirement_id": 1, "requirement_title": "Req A", "review_type": "requirement", "status": "pending"},
        ]
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending-reviews"])
        assert result.exit_code == 0
        assert "Req A" in result.output

    def test_no_pending_reviews(self, runner, mock_client):
        mock_client.get.return_value = []
        with patch("sdd_cli.me.get_client", return_value=mock_client):
            result = runner.invoke(app, ["me", "pending-reviews"])
        assert result.exit_code == 0
```

- [ ] **Step 5: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest cli/tests/test_me.py -v
```

- [ ] **Step 6: 实现 me.py**

创建 `cli/sdd_cli/me.py`:

```python
import typer
from sdd_cli.client import get_client, APIError
from sdd_cli.output import print_response

app = typer.Typer(help="Current user commands", invoke_without_command=True)


@app.callback()
def me_main(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return
    try:
        client = get_client()
        data = client.get("/users/me")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command()
def tasks(
    status: str = typer.Option(None, "--status", "-s"),
    offset: int = typer.Option(0, "--offset"),
    limit: int = typer.Option(50, "--limit", "-l"),
):
    try:
        client = get_client()
        params = {"offset": offset, "limit": limit}
        if status:
            params["status"] = status
        data = client.get("/users/me/tasks", params=params)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="pending")
def pending():
    try:
        client = get_client()
        data = client.get("/users/me/pending")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command(name="pending-reviews")
def pending_reviews():
    try:
        client = get_client()
        data = client.get("/users/me/pending-reviews")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 7: 注册到 main.py**

修改 `cli/sdd_cli/main.py`:

```python
import typer
from sdd_cli import auth, me

app = typer.Typer(name="sdd", help="SDD CLI - Agent-driven development tool", no_args_is_help=True)
app.add_typer(auth.app, name="auth")
app.add_typer(me.app, name="me")


@app.callback()
def main():
    pass


if __name__ == "__main__":
    app()
```

- [ ] **Step 8: 跑全部 CLI 测试 → 通过**

```bash
conda run -n sdd python -m pytest cli/tests/ -v
```

- [ ] **Step 9: 提交**

```bash
git add cli/sdd_cli/auth.py cli/sdd_cli/me.py cli/sdd_cli/main.py cli/tests/test_auth.py cli/tests/test_me.py
git commit -m "feat: add auth and me command groups"
```

---

### Task 4: Teams Commands

> **NOTE:** Due to length, the full code for Tasks 4-8b and 9-13 is documented in the conversation history (Part 3 through Part 7). The implementing agent should reference those parts for complete code. The test and implementation patterns are identical to Task 3: mock `get_client` → invoke CLI → assert exit code and API call.

**Files:**
- Create: `cli/sdd_cli/teams.py`
- Create: `cli/tests/test_teams.py`
- Modify: `cli/sdd_cli/main.py`

**Commands:** get, create, update, delete, transfer, members, invite, remove-member, assign-roles, roles, create-role, update-role, delete-role, spec-template, agent-guide, update-spec-template (16 commands)

---

### Task 5: Projects + Iterations Commands

**Files:**
- Create: `cli/sdd_cli/projects.py`
- Create: `cli/sdd_cli/iterations.py`
- Create: `cli/tests/test_projects.py`
- Create: `cli/tests/test_iterations.py`
- Modify: `cli/sdd_cli/main.py`

**Projects commands:** list, get, create, update, archive, delete, test-stats (7 commands)
**Iterations commands:** list, get, create, update, start, complete, kanban, statistics, test-stats (9 commands)

---

### Task 6: Requirements Commands

**Files:**
- Create: `cli/sdd_cli/requirements.py`
- Create: `cli/tests/test_requirements.py`
- Modify: `cli/sdd_cli/main.py`

**Commands:** list, get, create, update, delete, patch, approve, full-context, submit-review, review, test-stats, spec, save-spec, save-spec-direct, spec-versions, spec-version, submit-spec-review, approve-spec, submit-tests-review, test-cases, create-test-case, tasks, create-task (24 commands)

---

### Task 7: Tasks Commands

**Files:**
- Create: `cli/sdd_cli/tasks.py`
- Create: `cli/tests/test_tasks.py`
- Modify: `cli/sdd_cli/main.py`

**Commands:** get, create, update, delete, patch, start-coding, start-testing, complete, git-info, test-executions, create-test-record, create-test-round (12 commands)

---

### Task 8a: Test Cases + Test Executions Commands

**Files:**
- Create: `cli/sdd_cli/test_cases.py`
- Create: `cli/sdd_cli/test_executions.py`
- Create: `cli/tests/test_test_cases.py`
- Create: `cli/tests/test_test_executions.py`
- Modify: `cli/sdd_cli/main.py`

**Test Cases commands:** create, update, delete (3 commands)
**Test Executions commands:** records, batch, update-record (3 commands)

---

### Task 8b: Admin Commands

**Files:**
- Create: `cli/sdd_cli/admin.py`
- Create: `cli/tests/test_admin.py`
- Modify: `cli/sdd_cli/main.py`

**Commands:** users, create-user, toggle-user, create-api-key, list-api-keys, revoke-api-key (6 commands)

---

## Phase 3: Skills

### Task 9: Skill — sdd-discover-work

**Files:**
- Create: `.superpowers/skills/sdd-discover-work/SKILL.md`

**Purpose:** Guide agents to find available work — check pending items, assigned tasks, pending reviews.

**Key commands:** `sdd me pending`, `sdd me tasks`, `sdd me pending-reviews`

---

### Task 10: Skill — sdd-project-setup

**Files:**
- Create: `.superpowers/skills/sdd-project-setup/SKILL.md`

**Purpose:** Guide agents to create team → project → iteration → requirements.

**Key commands:** `sdd teams create`, `sdd projects create`, `sdd iterations create`, `sdd requirements create`

---

### Task 11: Skill — sdd-spec-writing

**Files:**
- Create: `.superpowers/skills/sdd-spec-writing/SKILL.md`

**Purpose:** Guide agents to write specifications — get context, get template guide, write content, submit for review.

**Key commands:** `sdd requirements full-context`, `sdd teams agent-guide`, `sdd requirements save-spec`, `sdd requirements submit-spec-review`

---

### Task 12: Skill — sdd-task-execution

**Files:**
- Create: `.superpowers/skills/sdd-task-execution/SKILL.md`

**Purpose:** Guide agents to execute tasks — start coding, git tracking, run tests, submit results, complete.

**Key commands:** `sdd tasks start-coding`, `sdd tasks git-info`, `sdd tasks start-testing`, `sdd test-executions batch`, `sdd tasks complete`

---

### Task 13: Skill — sdd-review

**Files:**
- Create: `.superpowers/skills/sdd-review/SKILL.md`

**Purpose:** Guide agents to review submissions — read content, evaluate quality, approve or reject.

**Key commands:** `sdd me pending-reviews`, `sdd requirements full-context`, `sdd requirements review`, `sdd requirements approve`

---

## Summary

| Phase | Tasks | Content |
|-------|-------|---------|
| **Phase 1: Foundation** | Task 1-2 | CLI scaffold, config, output, SDDClient |
| **Phase 2: Commands** | Task 3-8b | auth, me, teams, projects, iterations, requirements, tasks, test-cases, test-executions, admin |
| **Phase 3: Skills** | Task 9-13 | discover-work, project-setup, spec-writing, task-execution, review |

**Total:** ~80 CLI commands across 14 modules, 5 Agent Skills, ~14 test files
