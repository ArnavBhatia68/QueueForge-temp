import asyncio
import urllib.request

import pytest

from handlers import generate_csv_report, process_csv, send_webhook


def test_generate_csv_report_returns_preview_and_stats():
    payload = {
        "rows": [
            {"id": 1, "name": "alice", "score": 12},
            {"id": 2, "name": "bob", "score": 18},
        ]
    }
    result = asyncio.run(generate_csv_report(payload))
    assert result["row_count"] == 2
    assert "id" in result["columns"]
    assert result["numeric_mean"] is not None


def test_process_csv_returns_structure_metrics():
    payload = {"csv_content": "name,score\nalice,10\nbob,20"}
    result = asyncio.run(process_csv(payload))
    assert result["rows_processed"] == 2
    assert result["invalid_rows"] == 0
    assert result["columns"] == ["name", "score"]


def test_process_csv_requires_header():
    with pytest.raises(ValueError, match="Missing required field: csv_content"):
        asyncio.run(process_csv({"csv_content": ""}))


def test_send_webhook_validates_url():
    with pytest.raises(ValueError, match="Missing required field: url"):
        asyncio.run(send_webhook({"body": {"ok": True}}))


def test_send_webhook_makes_http_call(monkeypatch):
    class FakeResponse:
        def __init__(self):
            self._code = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def read(self):
            return b'{"received":true}'

        def getcode(self):
            return self._code

    def fake_urlopen(req, timeout=5):  # noqa: ARG001
        assert isinstance(req, urllib.request.Request)
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = asyncio.run(send_webhook({"url": "https://example.com/hook", "body": {"x": 1}}))
    assert result["status_code"] == 200
    assert result["method"] == "POST"
