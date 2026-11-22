import json
import uuid

import httpx
import pytest


async def test_request_id_is_generated(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    uuid.UUID(response.headers["x-request-id"])  # raises if not a UUID


async def test_security_headers_are_present(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


async def test_valid_incoming_request_id_is_echoed(client: httpx.AsyncClient) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": "abc-123_x.y"})
    assert response.headers["x-request-id"] == "abc-123_x.y"


@pytest.mark.parametrize("bad", ["has space", "x" * 65, 'quote"inject', "new\\nline"])
async def test_invalid_incoming_request_id_is_replaced(client: httpx.AsyncClient, bad: str) -> None:
    response = await client.get("/healthz", headers={"X-Request-ID": bad})
    assert response.headers["x-request-id"] != bad
    uuid.UUID(response.headers["x-request-id"])


async def test_unmatched_route_still_gets_request_id(client: httpx.AsyncClient) -> None:
    response = await client.get("/nope")
    assert response.status_code == 404
    assert "x-request-id" in response.headers


async def test_access_log_is_json_with_request_id(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    await client.get("/nope", headers={"X-Request-ID": "req-42"})
    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines() if line]
    access = [line for line in lines if line["event"] == "http_request"]
    assert len(access) == 1
    assert access[0]["request_id"] == "req-42"
    assert access[0]["status"] == 404
    assert access[0]["path"] == "/nope"
    assert access[0]["level"] == "info"
    assert "timestamp" in access[0]


async def test_health_endpoints_do_not_spam_access_log(
    client: httpx.AsyncClient, capsys: pytest.CaptureFixture[str]
) -> None:
    await client.get("/healthz")
    assert "http_request" not in capsys.readouterr().out


async def test_metrics_exposes_http_series_by_route_template(client: httpx.AsyncClient) -> None:
    await client.get("/healthz")
    await client.get("/some/unknown/path/123")
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert 'ansit_http_requests_total{method="GET",route="/healthz",status="200"}' in body
    assert 'route="unmatched",status="404"' in body
    assert "/some/unknown/path/123" not in body
    assert "ansit_http_request_duration_seconds_bucket" in body
    assert "ansit_ready" in body
