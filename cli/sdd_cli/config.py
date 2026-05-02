from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_API_URL = "http://localhost:8000/api/v1"
CONFIG_DIR = Path.home() / ".sdd"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    api_url: str = DEFAULT_API_URL
    api_key: str = ""

    @classmethod
    def load(cls) -> Config:
        cfg = cls()
        if CONFIG_FILE.exists():
            try:
                raw = json.loads(CONFIG_FILE.read_text())
                cfg.api_url = raw.get("api_url", cfg.api_url)
                cfg.api_key = raw.get("api_key", cfg.api_key)
            except (json.JSONDecodeError, OSError):
                pass
        env_url = os.environ.get("SDD_API_URL")
        if env_url:
            cfg.api_url = env_url
        env_key = os.environ.get("SDD_API_KEY")
        if env_key:
            cfg.api_key = env_key
        return cfg

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(
            json.dumps({"api_url": self.api_url, "api_key": self.api_key}, indent=2)
        )
