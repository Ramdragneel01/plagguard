from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.api import middleware as api_middleware
from backend.main import app


@pytest.fixture(autouse=True)
def reset_rate_limiter() -> None:
    api_middleware._requests.clear()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)
