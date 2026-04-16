"""
Tests for WebAPI span instrumentation.
Covers: P9 (HTTP spans), P10 (trace context propagation) + 5xx edge case.
"""
from hypothesis import given, settings
import hypothesis.strategies as st

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.trace import StatusCode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def _make_instrumented_app(provider):
    """Creates a fresh FastAPI app instrumented with the given provider."""
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/hc")
    def health():
        return {"status": "ok"}

    @app.get("/items/")
    def get_items():
        return []

    @app.post("/items/")
    def post_items():
        return {"id": 1}

    @app.put("/items/")
    def put_items():
        return {"updated": True}

    @app.delete("/items/")
    def delete_items():
        return {"deleted": True}

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    return app


# ---------------------------------------------------------------------------
# P9: HTTP request spans contain required semantic attributes
# Feature: observability-logs-traces, Property 9: HTTP request spans contain required semantic attributes
# ---------------------------------------------------------------------------

@given(method=st.sampled_from(["GET", "POST", "PUT", "DELETE"]))
@settings(max_examples=10, deadline=None)
def test_p9_http_span_has_required_attributes(method):
    # Feature: observability-logs-traces, Property 9: HTTP request spans contain required semantic attributes
    from fastapi.testclient import TestClient

    provider, exporter = _make_provider()
    app = _make_instrumented_app(provider)
    client = TestClient(app, raise_server_exceptions=False)

    method_fn = getattr(client, method.lower())
    method_fn("/items/")

    spans = exporter.get_finished_spans()
    assert len(spans) > 0, "No spans recorded"

    http_span = next(
        (s for s in spans if s.attributes.get("http.method") == method
         or s.attributes.get("http.request.method") == method),
        None
    )
    assert http_span is not None, f"No span found for method {method}"

    # Check http.method or http.request.method (OTel semconv v1 vs v2)
    method_attr = http_span.attributes.get("http.method") or http_span.attributes.get("http.request.method")
    assert method_attr == method

    # Check status code (http.status_code or http.response.status_code)
    status_attr = (http_span.attributes.get("http.status_code") or
                   http_span.attributes.get("http.response.status_code"))
    assert status_attr is not None, "No HTTP status code attribute found"

    # Check URL (http.url or url.full)
    url_attr = http_span.attributes.get("http.url") or http_span.attributes.get("url.full")
    assert url_attr is not None, "No HTTP URL attribute found"


# ---------------------------------------------------------------------------
# P10: Incoming trace context is propagated correctly
# Feature: observability-logs-traces, Property 10: Incoming trace context is propagated correctly
# ---------------------------------------------------------------------------

@given(trace_id=st.integers(min_value=1, max_value=2**128 - 1))
@settings(max_examples=10, deadline=None)
def test_p10_trace_context_propagated_from_header(trace_id):
    # Feature: observability-logs-traces, Property 10: Incoming trace context is propagated correctly
    from fastapi.testclient import TestClient

    provider, exporter = _make_provider()
    app = _make_instrumented_app(provider)
    client = TestClient(app, raise_server_exceptions=False)

    trace_id_hex = format(trace_id, "032x")
    span_id_hex = format(1, "016x")
    traceparent = f"00-{trace_id_hex}-{span_id_hex}-01"

    client.get("/hc", headers={"traceparent": traceparent})

    spans = exporter.get_finished_spans()
    assert len(spans) > 0, "No spans recorded"

    matched = any(
        format(s.context.trace_id, "032x") == trace_id_hex
        for s in spans
    )
    assert matched, f"No span found with trace_id {trace_id_hex}"


# ---------------------------------------------------------------------------
# Edge case: 5xx response → span has ERROR status
# ---------------------------------------------------------------------------

def test_edge_5xx_response_span_has_error_status():
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    provider, exporter = _make_provider()
    app = FastAPI()

    @app.get("/boom")
    def boom():
        raise Exception("Unexpected error")

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
    client = TestClient(app, raise_server_exceptions=False)
    client.get("/boom")

    spans = exporter.get_finished_spans()
    assert len(spans) > 0
    error_span = next(
        (s for s in spans if s.status.status_code == StatusCode.ERROR),
        None
    )
    assert error_span is not None, "Expected a span with ERROR status for 5xx"
