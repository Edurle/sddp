import json
from unittest.mock import MagicMock, patch

import httpx
import pytest

from sdd_cli.client import APIError, SDDClient
from sdd_cli.config import Config


def _make_response(body: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.json.return_value = body
    resp.status_code = status_code
    return resp


class TestSDDClientInit:
    def test_init_with_config(self):
        cfg = Config(api_url="http://test:8000", api_key="key")
        client = SDDClient(config=cfg)
        assert client.config is cfg

    def test_init_loads_config(self):
        cfg = Config(api_url="http://test:8000", api_key="loaded-key")
        with patch("sdd_cli.client.Config.load", return_value=cfg):
            client = SDDClient()
        assert client.config.api_key == "loaded-key"


class TestSDDClientHeaders:
    def test_headers_with_api_key(self):
        client = SDDClient(config=Config(api_key="my-key"))
        assert client._headers() == {"X-API-Key": "my-key"}

    def test_headers_without_api_key(self):
        client = SDDClient(config=Config(api_key=""))
        assert client._headers() == {}


class TestSDDClientMethods:
    def setup_method(self):
        self.cfg = Config(api_url="http://test:8000", api_key="key")
        self.client = SDDClient(config=self.cfg)
        self.success_body = {"code": 0, "message": "success", "data": {"id": 1}}

    def test_get_success(self):
        resp = _make_response(self.success_body)
        with patch.object(self.client._http, "get", return_value=resp):
            result = self.client.get("/test")
        assert result == {"id": 1}

    def test_get_with_params(self):
        resp = _make_response({"code": 0, "message": "success", "data": [{"id": 1}]})
        with patch.object(self.client._http, "get", return_value=resp) as mock_get:
            result = self.client.get("/test", params={"page": 1})
        mock_get.assert_called_once_with("/test", params={"page": 1}, headers={"X-API-Key": "key"})
        assert result == [{"id": 1}]

    def test_post_success(self):
        resp = _make_response({"code": 0, "message": "success", "data": {"created": True}})
        with patch.object(self.client._http, "post", return_value=resp):
            result = self.client.post("/test", json={"name": "foo"})
        assert result == {"created": True}

    def test_put_success(self):
        resp = _make_response({"code": 0, "message": "success", "data": {"updated": True}})
        with patch.object(self.client._http, "put", return_value=resp):
            result = self.client.put("/test", json={"name": "bar"})
        assert result == {"updated": True}

    def test_patch_success(self):
        resp = _make_response({"code": 0, "message": "success", "data": {"patched": True}})
        with patch.object(self.client._http, "patch", return_value=resp):
            result = self.client.patch("/test", json={"name": "baz"})
        assert result == {"patched": True}

    def test_delete_success(self):
        resp = _make_response({"code": 0, "message": "success", "data": None})
        with patch.object(self.client._http, "delete", return_value=resp):
            result = self.client.delete("/test/1")
        assert result is None


class TestAPIError:
    def test_raises_on_nonzero_code(self):
        resp = _make_response({"code": 40100, "message": "Unauthorized", "data": None})
        client = SDDClient(config=Config())
        with patch.object(client._http, "get", return_value=resp):
            with pytest.raises(APIError) as exc_info:
                client.get("/test")
        assert exc_info.value.code == 40100
        assert exc_info.value.message == "Unauthorized"

    def test_raises_on_validation_error(self):
        error_data = [{"field": "name", "message": "required"}]
        resp = _make_response({"code": 40001, "message": "Validation failed", "data": error_data})
        client = SDDClient(config=Config())
        with patch.object(client._http, "post", return_value=resp):
            with pytest.raises(APIError) as exc_info:
                client.post("/test", json={})
        assert exc_info.value.code == 40001
        assert exc_info.value.data == error_data

    def test_unwrap_returns_data_field(self):
        resp = _make_response({"code": 0, "message": "ok", "data": {"items": [1, 2]}})
        client = SDDClient(config=Config())
        with patch.object(client._http, "get", return_value=resp):
            result = client.get("/test")
        assert result == {"items": [1, 2]}

    def test_unwrap_empty_data(self):
        resp = _make_response({"code": 0, "message": "ok"})
        client = SDDClient(config=Config())
        with patch.object(client._http, "get", return_value=resp):
            result = client.get("/test")
        assert result is None
