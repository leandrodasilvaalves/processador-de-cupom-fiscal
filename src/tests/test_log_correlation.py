"""
Tests for log correlation with OTel trace/span IDs.
Covers: P3 (trace/span IDs in log), P4 (valid JSON output) + edge case inactive span.
"""
import io
import json
import sys
import pytest
from unittest.mock import patch
from hypothesis import given, settings
import hypothesis.strategies as st

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import context as otel_context, trace

import structlog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tracer_with_ids(trace_id: int, span_id: int):
    """Creates a tracer provider and a span with specific trace/span IDs via mock."""
    from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
    from opentelemetry.trace import SpanContext, TraceFlags, NonRecordingSpan

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


def _capture_log_output(log_fn, *args, **kwargs) -> str:
    """Captures structlog JSON output from stdout."""
    buf = io.StringIO()
    with patch("sys.stdout", buf):
        log_fn(*args, **kwargs)
    return buf.getvalue().strip()


def _setup_structlog_with_otel_processor():
    """Configures structlog with OtelTraceProcessor and JSON output to a buffer."""
    from config.otel_config import OtelTraceProcessor
    buf = io.StringIO()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            OtelTraceProcessor(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=buf),
        cache_logger_on_first_use=False,
    )
    return structlog.get_logger(), buf


# ---------------------------------------------------------------------------
# P3: Log events within an active span contain correct trace and span IDs
# Feature: observability-logs-traces, Property 3: Log events within an active span contain correct trace and span IDs
# ---------------------------------------------------------------------------

@given(
    trace_id=st.integers(min_value=1, max_value=2**128 - 1),
    span_id=st.integers(min_value=1, max_value=2**64 - 1),
)
@settings(max_examples=50)
def test_p3_log_contains_correct_trace_and_span_ids(trace_id, span_id):
    # Feature: observability-logs-traces, Property 3: Log events within an active span contain correct trace and span IDs
    from opentelemetry.trace import SpanContext, TraceFlags, NonRecordingSpan

    log, buf = _setup_structlog_with_otel_processor()

    span_ctx = SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
    )
    span = NonRecordingSpan(span_ctx)
    token = trace.use_span(span, end_on_exit=False)

    ctx = trace.use_span(span, end_on_exit=False)
    with ctx:
        log.info("test_event", key="value")

    output = buf.getvalue().strip()
    assert output, "No log output captured"
    data = json.loads(output)

    expected_trace_id = format(trace_id, "032x")
    expected_span_id = format(span_id, "016x")
    assert data.get("trace_id") == expected_trace_id
    assert data.get("span_id") == expected_span_id


# ---------------------------------------------------------------------------
# P4: Log output is always valid JSON
# Feature: observability-logs-traces, Property 4: Log output is always valid JSON
# ---------------------------------------------------------------------------

@given(
    event=st.text(min_size=1, max_size=50),
    str_field=st.text(max_size=100),
    num_field=st.floats(allow_nan=False, allow_infinity=False),
    list_field=st.lists(st.text(max_size=20), max_size=5),
)
@settings(max_examples=50)
def test_p4_log_output_is_valid_json(event, str_field, num_field, list_field):
    # Feature: observability-logs-traces, Property 4: Log output is always valid JSON
    log, buf = _setup_structlog_with_otel_processor()

    log.info(event, str_field=str_field, num_field=num_field, list_field=list_field)

    output = buf.getvalue().strip()
    assert output, "No log output captured"
    # Must be parseable JSON — raises json.JSONDecodeError if not
    data = json.loads(output)
    assert isinstance(data, dict)


# ---------------------------------------------------------------------------
# Edge case: no active span → trace_id and span_id are zeros
# ---------------------------------------------------------------------------

def test_edge_no_active_span_injects_zeros():
    from opentelemetry.trace import NonRecordingSpan, INVALID_SPAN_CONTEXT

    log, buf = _setup_structlog_with_otel_processor()

    # Ensure no active span
    with trace.use_span(NonRecordingSpan(INVALID_SPAN_CONTEXT), end_on_exit=False):
        log.info("no_span_event")

    output = buf.getvalue().strip()
    assert output
    data = json.loads(output)
    assert data.get("trace_id") == "00000000000000000000000000000000"
    assert data.get("span_id") == "0000000000000000"
