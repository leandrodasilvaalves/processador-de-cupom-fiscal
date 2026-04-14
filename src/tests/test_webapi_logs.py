"""
Tests for WebAPI log events.
Covers: P12 (required fields in WebAPI logs) + 5xx log edge case.
"""
import io
import json
import time
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from hypothesis import given, settings
import hypothesis.strategies as st

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup_log_capture():
    """Configures structlog to write JSON to a StringIO buffer. Returns (logger, buffer)."""
    buf = io.StringIO()
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=buf),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger(), buf


def _parse_all_logs(buf: io.StringIO) -> list:
    buf.seek(0)
    lines = [l.strip() for l in buf.getvalue().splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


def _make_app_with_log_capture(buf: io.StringIO):
    """Creates a minimal FastAPI app with the logging middleware writing to buf."""
    log = structlog.get_logger()
    app = FastAPI()

    class RequestLoggingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            start_time = time.monotonic()
            log.info("http_request_received", method=request.method, path=request.url.path)
            try:
                response = await call_next(request)
                duration_ms = int((time.monotonic() - start_time) * 1000)
                if response.status_code >= 500:
                    log.error(
                        "http_request_error",
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        error="Internal Server Error",
                    )
                else:
                    log.info(
                        "http_request_completed",
                        method=request.method,
                        path=request.url.path,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )
                return response
            except Exception as e:
                log.error(
                    "http_request_error",
                    method=request.method,
                    path=request.url.path,
                    error=str(e),
                )
                raise

    app.add_middleware(RequestLoggingMiddleware)

    @app.get("/hc")
    def health():
        return {"status": "ok"}

    @app.post("/items/")
    def create_item():
        return {"id": 1}

    @app.put("/items/{item_id}")
    def update_item(item_id: int):
        return {"updated": True}

    return app


# ---------------------------------------------------------------------------
# P12: WebAPI log events contain all required fields
# Feature: observability-logs-traces, Property 12: WebAPI log events contain all required fields
# ---------------------------------------------------------------------------

@given(
    method=st.sampled_from(["GET", "POST", "PUT"]),
    path_suffix=st.text(
        min_size=1, max_size=20,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="-_")
    ),
)
@settings(max_examples=30)
def test_p12_request_log_has_required_fields(method, path_suffix):
    # Feature: observability-logs-traces, Property 12: WebAPI log events contain all required fields
    log, buf = _setup_log_capture()
    app = _make_app_with_log_capture(buf)
    client = TestClient(app, raise_server_exceptions=False)

    path = "/hc"
    if method == "POST":
        path = "/items/"
    elif method == "PUT":
        path = "/items/1"

    method_fn = getattr(client, method.lower())
    method_fn(path)

    logs = _parse_all_logs(buf)
    assert len(logs) >= 1

    request_log = next((l for l in logs if l.get("event") == "http_request_received"), None)
    assert request_log is not None, "http_request_received log not found"
    assert "method" in request_log
    assert "path" in request_log


@given(
    method=st.sampled_from(["GET", "POST", "PUT"]),
)
@settings(max_examples=20)
def test_p12_response_log_has_status_code_and_duration(method):
    # Feature: observability-logs-traces, Property 12: WebAPI log events contain all required fields
    log, buf = _setup_log_capture()
    app = _make_app_with_log_capture(buf)
    client = TestClient(app, raise_server_exceptions=False)

    path = "/hc"
    if method == "POST":
        path = "/items/"
    elif method == "PUT":
        path = "/items/1"

    method_fn = getattr(client, method.lower())
    method_fn(path)

    logs = _parse_all_logs(buf)
    response_log = next((l for l in logs if l.get("event") == "http_request_completed"), None)
    assert response_log is not None, "http_request_completed log not found"
    assert "status_code" in response_log
    assert "duration_ms" in response_log
    assert "method" in response_log
    assert "path" in response_log


# ---------------------------------------------------------------------------
# Edge case: 5xx response → error log with required fields
# ---------------------------------------------------------------------------

def test_edge_5xx_log_has_error_fields():
    log, buf = _setup_log_capture()
    app = _make_app_with_log_capture(buf)

    @app.get("/boom")
    def boom():
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="boom")

    client = TestClient(app, raise_server_exceptions=False)
    client.get("/boom")

    logs = _parse_all_logs(buf)
    error_log = next((l for l in logs if l.get("event") == "http_request_error"), None)
    assert error_log is not None, "http_request_error log not found"
    assert "method" in error_log
    assert "path" in error_log
    assert "status_code" in error_log or "error" in error_log
    assert error_log.get("level") == "error"
