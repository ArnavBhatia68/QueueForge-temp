import asyncio
import csv
import io
import json
import urllib.request
from statistics import mean


async def send_email(payload: dict) -> dict:
    """Simple deterministic email simulation with input validation."""
    to_email = payload.get("email")
    if not to_email:
        raise ValueError("Missing required field: email")

    subject = payload.get("subject", "QueueForge Notification")
    body = payload.get("body", "Hello from QueueForge")
    await asyncio.sleep(0)
    return {
        "message": "Email request accepted",
        "to": to_email,
        "subject": subject,
        "body_length": len(body),
    }


async def send_webhook(payload: dict) -> dict:
    """Send a JSON webhook to a target URL."""
    url = payload.get("url")
    if not url:
        raise ValueError("Missing required field: url")

    body = payload.get("body", {})
    method = payload.get("method", "POST").upper()
    timeout = float(payload.get("timeout", 5))

    if method not in {"POST", "PUT", "PATCH"}:
        raise ValueError("Webhook method must be one of POST, PUT, PATCH")

    def _request() -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:  # nosec B310
            raw = response.read().decode("utf-8", errors="replace")
            return {
                "status_code": response.getcode(),
                "response_preview": raw[:200],
            }

    result = await asyncio.to_thread(_request)
    return {
        "url": url,
        "method": method,
        **result,
    }


async def generate_csv_report(payload: dict) -> dict:
    """Generate a CSV report from input records and compute simple stats."""
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) == 0:
        raise ValueError("rows must be a non-empty list of objects")
    if not all(isinstance(r, dict) for r in rows):
        raise ValueError("Each row must be an object")

    headers = sorted({k for row in rows for k in row.keys()})
    if not headers:
        raise ValueError("rows contain no columns")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)

    numeric_values = []
    for row in rows:
        for value in row.values():
            if isinstance(value, (int, float)):
                numeric_values.append(float(value))

    return {
        "columns": headers,
        "row_count": len(rows),
        "csv_preview": output.getvalue().splitlines()[:6],
        "numeric_mean": round(mean(numeric_values), 4) if numeric_values else None,
    }


async def process_csv(payload: dict) -> dict:
    """Parse CSV content and return structural metrics."""
    csv_content = payload.get("csv_content")
    if not csv_content or not isinstance(csv_content, str):
        raise ValueError("Missing required field: csv_content")

    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise ValueError("CSV header row is required")

    row_count = 0
    invalid_rows = 0
    for row in reader:
        row_count += 1
        if any(v is None for v in row.values()):
            invalid_rows += 1

    return {
        "columns": reader.fieldnames,
        "rows_processed": row_count,
        "invalid_rows": invalid_rows,
    }


async def simulate_ml_task(payload: dict) -> dict:
    """Deterministic classifier-style output for demo workloads."""
    text = str(payload.get("text", payload))
    score = (sum(ord(c) for c in text) % 1000) / 1000
    label = "fraud" if score >= 0.7 else "legit"
    await asyncio.sleep(0)
    return {"confidence": round(score, 3), "label": label}


HANDLERS = {
    "send_email": send_email,
    "send_webhook": send_webhook,
    "generate_csv_report": generate_csv_report,
    "process_csv": process_csv,
    "simulate_ml_task": simulate_ml_task,
}
