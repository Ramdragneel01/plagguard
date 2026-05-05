from __future__ import annotations

from backend.api import routes


def test_reports_list_endpoint_returns_items(client, monkeypatch):
    monkeypatch.setattr(
        routes,
        "list_reports",
        lambda limit=20: [{"id": "r1", "report_type": "detect", "created_at": "2026-05-05T00:00:00"}],
    )

    res = client.get("/api/v1/reports")

    assert res.status_code == 200
    body = res.json()
    assert isinstance(body, list)
    assert body[0]["id"] == "r1"


def test_get_report_endpoint_returns_404_when_missing(client, monkeypatch):
    monkeypatch.setattr(routes, "get_report", lambda report_id: None)

    res = client.get("/api/v1/reports/missing-report")

    assert res.status_code == 404
    assert res.json()["detail"] == "Report not found"


def test_get_report_endpoint_returns_payload(client, monkeypatch):
    monkeypatch.setattr(
        routes,
        "get_report",
        lambda report_id: {
            "id": report_id,
            "input_text": "Sample text",
            "result": {"overall_similarity": 0.2},
            "report_type": "detect",
            "created_at": "2026-05-05T00:00:00",
        },
    )

    res = client.get("/api/v1/reports/rpt-1")

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == "rpt-1"
    assert body["report_type"] == "detect"


def test_get_report_html_renders_generated_markup(client, monkeypatch):
    monkeypatch.setattr(
        routes,
        "get_report",
        lambda report_id: {
            "id": report_id,
            "input_text": "Sample text",
            "result": {"overall_similarity": 0.2},
            "report_type": "detect",
            "created_at": "2026-05-05T00:00:00",
        },
    )
    monkeypatch.setattr(routes, "generate_html_report", lambda result, text: "<html><body>ok</body></html>")

    res = client.get("/api/v1/reports/rpt-1/html")

    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "ok" in res.text
