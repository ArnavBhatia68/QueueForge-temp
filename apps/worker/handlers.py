import asyncio
import csv
import io
import json
import re
import urllib.request
from collections import Counter
from statistics import mean
from urllib.error import HTTPError, URLError


def _body_preview(raw: str, limit: int = 1500) -> str:
    return raw[:limit]


async def webhook_request(payload: dict) -> dict:
    url = payload.get("url")
    if not url:
        raise ValueError("payload.url is required")

    method = str(payload.get("method", "POST")).upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
        raise ValueError("method must be GET, POST, PUT, PATCH, or DELETE")

    timeout = float(payload.get("timeout_seconds", 10))
    headers = payload.get("headers") or {}
    if not isinstance(headers, dict):
        raise ValueError("headers must be a JSON object")

    body = payload.get("body")

    def _request() -> dict:
        encoded_body = None
        request_headers = {"User-Agent": "QueueForge-Worker/1.0", **headers}
        if body is not None:
            encoded_body = json.dumps(body).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        req = urllib.request.Request(url=url, data=encoded_body, method=method, headers=request_headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310
                raw = response.read().decode("utf-8", errors="replace")
                return {
                    "ok": 200 <= response.getcode() < 300,
                    "status_code": response.getcode(),
                    "response_headers": dict(response.headers.items()),
                    "response_body_preview": _body_preview(raw),
                }
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else str(exc)
            return {
                "ok": False,
                "status_code": exc.code,
                "response_headers": dict(exc.headers.items()) if exc.headers else {},
                "response_body_preview": _body_preview(raw),
                "error": f"HTTP {exc.code}",
            }
        except URLError as exc:
            raise RuntimeError(f"Network request failed: {exc.reason}")

    return await asyncio.to_thread(_request)


async def csv_processing(payload: dict) -> dict:
    csv_text = payload.get("csv_text")
    if not isinstance(csv_text, str) or not csv_text.strip():
        raise ValueError("payload.csv_text is required")

    operation = payload.get("operation")
    allowed = {"csv_to_json", "dedupe_rows", "validate_required_columns", "summary_stats"}
    if operation not in allowed:
        raise ValueError(f"Unsupported CSV operation: {operation}")

    reader = csv.DictReader(io.StringIO(csv_text))
    if not reader.fieldnames:
        raise ValueError("CSV header row is required")

    rows = list(reader)
    fieldnames = reader.fieldnames

    if operation == "csv_to_json":
        return {
            "operation": operation,
            "rows": rows,
            "row_count": len(rows),
            "columns": fieldnames,
        }

    if operation == "dedupe_rows":
        seen = set()
        deduped = []
        for row in rows:
            key = tuple((k, row.get(k, "")) for k in fieldnames)
            if key not in seen:
                seen.add(key)
                deduped.append(row)
        return {
            "operation": operation,
            "original_count": len(rows),
            "deduplicated_count": len(deduped),
            "removed_duplicates": len(rows) - len(deduped),
            "rows": deduped,
        }

    if operation == "validate_required_columns":
        required_columns = payload.get("required_columns")
        if not isinstance(required_columns, list) or not all(isinstance(col, str) and col.strip() for col in required_columns):
            raise ValueError("payload.required_columns must be a non-empty list of column names")

        missing_columns = [col for col in required_columns if col not in fieldnames]
        return {
            "operation": operation,
            "valid": len(missing_columns) == 0,
            "columns": fieldnames,
            "required_columns": required_columns,
            "missing_columns": missing_columns,
        }

    # summary_stats
    completeness = Counter()
    numeric_values: dict[str, list[float]] = {col: [] for col in fieldnames}

    for row in rows:
        for col in fieldnames:
            value = str(row.get(col, "")).strip()
            if value:
                completeness[col] += 1
                try:
                    numeric_values[col].append(float(value))
                except ValueError:
                    pass

    numeric_summary = {
        col: {
            "count": len(values),
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "avg": round(mean(values), 6) if values else None,
        }
        for col, values in numeric_values.items()
    }

    return {
        "operation": operation,
        "row_count": len(rows),
        "columns": fieldnames,
        "completeness": {
            col: {
                "non_empty": completeness[col],
                "empty": len(rows) - completeness[col],
            }
            for col in fieldnames
        },
        "numeric_summary": numeric_summary,
    }


async def text_transform(payload: dict) -> dict:
    data_input = payload.get("input")
    if data_input is None:
        raise ValueError("payload.input is required")

    mode = payload.get("mode")
    allowed_modes = {
        "pretty_json",
        "extract_emails",
        "dedupe_lines",
        "normalize_whitespace",
        "counts",
    }
    if mode not in allowed_modes:
        raise ValueError(f"Unsupported transform mode: {mode}")

    input_text = data_input if isinstance(data_input, str) else json.dumps(data_input)

    if mode == "pretty_json":
        parsed = json.loads(input_text)
        pretty = json.dumps(parsed, indent=2, sort_keys=True)
        return {"mode": mode, "output": pretty}

    if mode == "extract_emails":
        emails = sorted(set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", input_text)))
        return {"mode": mode, "count": len(emails), "emails": emails}

    if mode == "dedupe_lines":
        seen = set()
        lines = []
        for line in input_text.splitlines():
            if line not in seen:
                seen.add(line)
                lines.append(line)
        return {"mode": mode, "output": "\n".join(lines), "line_count": len(lines)}

    if mode == "normalize_whitespace":
        normalized = re.sub(r"\s+", " ", input_text).strip()
        return {"mode": mode, "output": normalized}

    return {
        "mode": mode,
        "words": len(re.findall(r"\b\w+\b", input_text)),
        "lines": len(input_text.splitlines()),
        "characters": len(input_text),
    }


HANDLERS = {
    "webhook_request": webhook_request,
    "csv_processing": csv_processing,
    "text_transform": text_transform,
}
