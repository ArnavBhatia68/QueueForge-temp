import asyncio
import urllib.request

import pytest

from handlers import csv_processing, text_transform, webhook_request


def test_csv_summary_statistics():
    payload = {"operation": "summary_statistics", "csv_text": "name,email\nada,ada@example.com\nlin,"}
    result = asyncio.run(csv_processing(payload))
    assert result["row_count"] == 2
    assert "email" in result["columns"]


def test_csv_validate_required_columns_reports_issues():
    payload = {
        "operation": "validate_required_columns",
        "required_columns": ["name", "email"],
        "csv_text": "name,email\nada,ada@example.com\nlin,",
    }
    result = asyncio.run(csv_processing(payload))
    assert result["invalid_row_count"] == 1


def test_text_transform_extract_emails():
    result = asyncio.run(text_transform({"mode": "extract_emails", "input": "a@x.com b@x.com a@x.com"}))
    assert result["count"] == 2


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
