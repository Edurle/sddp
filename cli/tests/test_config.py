import json
import os
from unittest.mock import patch

import pytest

from sdd_cli.config import Config, DEFAULT_API_URL


class TestConfigLoad:
    def test_load_from_env(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with (
            patch("sdd_cli.config.CONFIG_FILE", cfg_file),
            patch.dict(os.environ, {"SDD_API_KEY": "env-key-123", "SDD_API_URL": "http://env:9999"}, clear=False),
        ):
            cfg = Config.load()
        assert cfg.api_key == "env-key-123"
        assert cfg.api_url == "http://env:9999"

    def test_load_from_file(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_url": "http://file:8000", "api_key": "file-key"}))
        env = {k: v for k, v in os.environ.items() if k not in ("SDD_API_KEY", "SDD_API_URL")}
        with (
            patch("sdd_cli.config.CONFIG_FILE", cfg_file),
            patch.dict(os.environ, env, clear=True),
        ):
            cfg = Config.load()
        assert cfg.api_url == "http://file:8000"
        assert cfg.api_key == "file-key"

    def test_defaults_when_no_env_no_file(self, tmp_path):
        cfg_file = tmp_path / "nonexistent.json"
        env = {k: v for k, v in os.environ.items() if k not in ("SDD_API_KEY", "SDD_API_URL")}
        with (
            patch("sdd_cli.config.CONFIG_FILE", cfg_file),
            patch.dict(os.environ, env, clear=True),
        ):
            cfg = Config.load()
        assert cfg.api_url == DEFAULT_API_URL
        assert cfg.api_key == ""

    def test_env_overrides_file(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_url": "http://file:8000", "api_key": "file-key"}))
        with (
            patch("sdd_cli.config.CONFIG_FILE", cfg_file),
            patch.dict(os.environ, {"SDD_API_KEY": "env-key", "SDD_API_URL": "http://env:9999"}, clear=False),
        ):
            cfg = Config.load()
        assert cfg.api_key == "env-key"
        assert cfg.api_url == "http://env:9999"


class TestConfigSave:
    def test_save_creates_file(self, tmp_path):
        cfg_file = tmp_path / "sdd" / "config.json"
        cfg = Config(api_url="http://test:8000", api_key="my-key")
        with patch("sdd_cli.config.CONFIG_FILE", cfg_file):
            with patch("sdd_cli.config.CONFIG_DIR", cfg_file.parent):
                cfg.save()
        assert cfg_file.exists()
        data = json.loads(cfg_file.read_text())
        assert data["api_url"] == "http://test:8000"
        assert data["api_key"] == "my-key"

    def test_save_overwrites(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_url": "old", "api_key": "old-key"}))
        cfg = Config(api_url="http://new:8000", api_key="new-key")
        with patch("sdd_cli.config.CONFIG_FILE", cfg_file):
            with patch("sdd_cli.config.CONFIG_DIR", cfg_file.parent):
                cfg.save()
        data = json.loads(cfg_file.read_text())
        assert data["api_url"] == "http://new:8000"
        assert data["api_key"] == "new-key"
