import asyncio
import urllib.request

import pytest

from handlers import csv_processing, text_transform, webhook_request


def test_csv_summary_stats():
    payload = {"operation": "summary_stats", "csv_text": "name,amount\nA,10\nB,20"}
    result = asyncio.run(csv_processing(payload))
    assert result["row_count"] == 2
    assert "amount" in result["columns"]
    assert result["numeric_summary"]["amount"]["avg"] == 15.0


def test_csv_dedupe_rows():
    payload = {"operation": "dedupe_rows", "csv_text": "name,amount\nA,10\nA,10\nB,20"}
    result = asyncio.run(csv_processing(payload))
    assert result["deduplicated_count"] == 2


def test_csv_validate_required_columns_reports_missing_columns():
    payload = {
        "operation": "validate_required_columns",
        "required_columns": ["name", "amount", "email"],
        "csv_text": "name,amount\nA,10\nB,20",
    }
    result = asyncio.run(csv_processing(payload))
    assert result["valid"] is False
    assert result["missing_columns"] == ["email"]


def test_text_transform_dedupe_lines():
    result = asyncio.run(text_transform({"mode": "dedupe_lines", "input": "a\nb\na"}))
    assert result["output"] == "a\nb"


def test_text_transform_counts():
    result = asyncio.run(text_transform({"mode": "counts", "input": "one two\nthree"}))
    assert result["words"] == 3
    assert result["lines"] == 2


def test_unsupported_transform_mode_fails_cleanly():
    with pytest.raises(ValueError, match="Unsupported transform mode"):
        asyncio.run(text_transform({"mode": "deduplicate_lines", "input": "a"}))


def test_unsupported_csv_operation_fails_cleanly():
    with pytest.raises(ValueError, match="Unsupported CSV operation"):
        asyncio.run(csv_processing({"operation": "summary_statistics", "csv_text": "a,b\n1,2"}))


def test_webhook_validates_url():
    with pytest.raises(ValueError, match="payload.url is required"):
        asyncio.run(webhook_request({"body": {"ok": True}}))


def test_webhook_makes_http_call(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            return False

        def read(self):
            return b'{"received":true}'

        def getcode(self):
            return 200

        @property
        def headers(self):
            class H:
                def items(self):
                    return {"content-type": "application/json"}.items()

            return H()

    def fake_urlopen(req, timeout=5):  # noqa: ARG001
        assert isinstance(req, urllib.request.Request)
        return FakeResponse()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    result = asyncio.run(webhook_request({"url": "https://example.com/hook", "body": {"x": 1}}))
    assert result["status_code"] == 200
    assert result["ok"] is True
