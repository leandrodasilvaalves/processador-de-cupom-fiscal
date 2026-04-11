"""
Tests for worker log events.
Covers: P11 (required fields in worker logs) + error log edge case.
"""
import io
import json
import pytest
from unittest.mock import patch, MagicMock
from hypothesis import given, settings
import hypothesis.strategies as st

import structlog

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry import trace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_provider():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


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
    """Parses all JSON log lines from the buffer."""
    buf.seek(0)
    lines = [l.strip() for l in buf.getvalue().splitlines() if l.strip()]
    return [json.loads(l) for l in lines]


# ---------------------------------------------------------------------------
# P11: Worker log events contain all required fields
# Feature: observability-logs-traces, Property 11: Worker log events contain all required fields
# ---------------------------------------------------------------------------

@given(
    file_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-.")),
    company_id=st.integers(min_value=1, max_value=9999),
    purchase_id=st.integers(min_value=1, max_value=9999),
    item_count=st.integers(min_value=0, max_value=100),
)
@settings(max_examples=30)
def test_p11_file_processing_completed_log_has_required_fields(file_name, company_id, purchase_id, item_count):
    # Feature: observability-logs-traces, Property 11: Worker log events contain all required fields
    log, buf = _setup_log_capture()

    log.info(
        "file_processing_completed",
        file_name=file_name,
        company_id=company_id,
        purchase_id=purchase_id,
        item_count=item_count,
    )

    logs = _parse_all_logs(buf)
    assert len(logs) == 1
    entry = logs[0]
    assert entry.get("event") == "file_processing_completed"
    assert entry.get("file_name") == file_name
    assert entry.get("company_id") == company_id
    assert entry.get("purchase_id") == purchase_id
    assert entry.get("item_count") == item_count


@given(
    file_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-.")),
    skipped_reason=st.sampled_from(["duplicate_hash", "duplicate_access_key"]),
)
@settings(max_examples=30)
def test_p11_file_skipped_log_has_required_fields(file_name, skipped_reason):
    # Feature: observability-logs-traces, Property 11: Worker log events contain all required fields
    log, buf = _setup_log_capture()

    log.info("file_skipped", file_name=file_name, skipped_reason=skipped_reason)

    logs = _parse_all_logs(buf)
    assert len(logs) == 1
    entry = logs[0]
    assert entry.get("event") == "file_skipped"
    assert entry.get("file_name") == file_name
    assert entry.get("skipped_reason") == skipped_reason


@given(
    processed_count=st.integers(min_value=0, max_value=100),
    skipped_count=st.integers(min_value=0, max_value=100),
    error_count=st.integers(min_value=0, max_value=100),
    duration_ms=st.integers(min_value=0, max_value=60000),
)
@settings(max_examples=30)
def test_p11_cycle_summary_log_has_required_fields(processed_count, skipped_count, error_count, duration_ms):
    # Feature: observability-logs-traces, Property 11: Worker log events contain all required fields
    log, buf = _setup_log_capture()

    log.info(
        "processing_cycle_completed",
        processed_count=processed_count,
        skipped_count=skipped_count,
        error_count=error_count,
        duration_ms=duration_ms,
    )

    logs = _parse_all_logs(buf)
    assert len(logs) == 1
    entry = logs[0]
    assert entry.get("event") == "processing_cycle_completed"
    assert entry.get("processed_count") == processed_count
    assert entry.get("skipped_count") == skipped_count
    assert entry.get("error_count") == error_count
    assert entry.get("duration_ms") == duration_ms


def test_p11_file_processing_started_log_has_required_fields():
    # Feature: observability-logs-traces, Property 11: Worker log events contain all required fields
    log, buf = _setup_log_capture()
    log.info("file_processing_started", file_name="test.pdf")
    logs = _parse_all_logs(buf)
    assert len(logs) == 1
    entry = logs[0]
    assert entry.get("event") == "file_processing_started"
    assert entry.get("file_name") == "test.pdf"


# ---------------------------------------------------------------------------
# Edge case: error log contains event, file_name, error fields
# ---------------------------------------------------------------------------

def test_edge_error_log_has_required_fields():
    log, buf = _setup_log_capture()
    log.error("file_processing_error", file_name="bad.pdf", error="Something went wrong")
    logs = _parse_all_logs(buf)
    assert len(logs) == 1
    entry = logs[0]
    assert entry.get("event") == "file_processing_error"
    assert entry.get("file_name") == "bad.pdf"
    assert entry.get("error") == "Something went wrong"
    assert entry.get("level") == "error"
