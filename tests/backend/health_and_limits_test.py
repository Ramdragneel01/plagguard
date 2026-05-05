from __future__ import annotations

from backend.api import middleware as api_middleware


def test_health_endpoint_shape(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200

    body = res.json()
    assert body["status"] == "healthy"
    assert body["version"] == "1.0.0"
    assert isinstance(body["models_loaded"], bool)


def test_rate_limit_blocks_after_threshold(client):
    for _ in range(api_middleware._RATE_LIMIT):
        ok_res = client.get("/api/v1/health")
        assert ok_res.status_code == 200

    blocked_res = client.get("/api/v1/health")
    assert blocked_res.status_code == 429
    assert "Rate limit exceeded" in blocked_res.json()["detail"]


def test_request_size_limit_returns_413(client):
    too_large = api_middleware.RequestSizeLimitMiddleware.MAX_SIZE + 1
    res = client.post(
        "/api/v1/detect",
        content="{}",
        headers={
            "content-type": "application/json",
            "content-length": str(too_large),
        },
    )

    assert res.status_code == 413
    assert "Request body too large" in res.json()["detail"]
