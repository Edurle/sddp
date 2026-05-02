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
