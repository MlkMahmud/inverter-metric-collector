from typing import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_time() -> Generator[MagicMock]:
    with patch("utils.retry.time") as mod:
        mod.sleep = MagicMock()
        yield mod
