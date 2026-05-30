from __future__ import annotations

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
        self.config = config
        self._http = httpx.Client(
            base_url=self.config.api_url,
            timeout=30.0,
        )

    def _headers(self) -> dict[str, str]:
        if self.config.api_key:
            return {"X-API-Key": self.config.api_key}
        return {}

    def _unwrap(self, resp: httpx.Response):
        body = resp.json()
        if body.get("code", 0) != 0:
            raise APIError(
                code=body["code"],
                message=body.get("message", "Unknown error"),
                data=body.get("data"),
            )
        return body.get("data")

    def get(self, path: str, params: dict | None = None):
        resp = self._http.get(path, params=params, headers=self._headers())
        return self._unwrap(resp)

    def post(self, path: str, json: dict | None = None):
        resp = self._http.post(path, json=json, headers=self._headers())
        return self._unwrap(resp)

    def put(self, path: str, json: dict | None = None):
        resp = self._http.put(path, json=json, headers=self._headers())
        return self._unwrap(resp)

    def patch(self, path: str, json: dict | None = None):
        resp = self._http.patch(path, json=json, headers=self._headers())
        return self._unwrap(resp)

    def delete(self, path: str, headers: dict | None = None):
        merged = {**self._headers(), **(headers or {})}
        resp = self._http.delete(path, headers=merged)
        return self._unwrap(resp)


def get_client() -> SDDClient:
    return SDDClient()
