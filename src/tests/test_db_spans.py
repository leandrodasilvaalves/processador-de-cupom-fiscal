"""
Tests for database span instrumentation.
Covers: P8 (DB spans with attributes and closure) + exception edge cases.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
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


def _get_span_by_name(spans, name):
    return next((s for s in spans if s.name == name), None)


def _make_mock_db(return_value=None):
    mock_db = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = return_value
    mock_cursor.fetchall.return_value = []
    mock_cursor.lastrowid = 99
    mock_cursor.description = []
    mock_db.cursor.return_value = mock_cursor
    return mock_db, mock_cursor


# ---------------------------------------------------------------------------
# P8: Database spans are always closed with correct semantic attributes
# Feature: observability-logs-traces, Property 8: Database spans are always closed with correct semantic attributes
# ---------------------------------------------------------------------------

@given(operation=st.sampled_from(["get_by_hash_file", "get_by_nfce", "insert"]))
@settings(max_examples=30)
def test_p8_db_span_has_semantic_attributes(operation):
    # Feature: observability-logs-traces, Property 8: Database spans are always closed with correct semantic attributes
    provider, exporter = _make_provider()
    mock_db, mock_cursor = _make_mock_db()
    db_name = "testdb"

    with patch.dict(os.environ, {"MYSQL_DATABASE": db_name}):
        if operation == "get_by_hash_file":
            with patch("database.db_purchase.tracer", provider.get_tracer("db")):
                from database import db_purchase
                db_purchase.get_by_hash_file(mock_db, "somehash")
            expected_span = "db.get_by_hash_file"
            expected_op = "SELECT"

        elif operation == "get_by_nfce":
            with patch("database.db_purchase.tracer", provider.get_tracer("db")):
                from database import db_purchase
                db_purchase.get_by_nfce(mock_db, "somekey")
            expected_span = "db.get_by_nfce"
            expected_op = "SELECT"

        elif operation == "insert":
            mock_purchase = MagicMock()
            mock_purchase.company_id = 1
            mock_purchase.nfce_access_key = "key"
            mock_purchase.purchase_total = 10.0
            mock_purchase.discount = 0.0
            mock_purchase.paid_amount = 10.0
            mock_purchase.payment_method = "cash"
            mock_purchase.issue_date = None
            mock_purchase.authorization_date = None
            mock_purchase.situation = "ok"
            mock_purchase.danfe_number = "1"
            mock_purchase.danfe_series = "1"
            mock_purchase.protocol = "123"
            mock_purchase.file_hash = "abc"
            mock_purchase.line_of_business = None
            with patch("database.db_purchase.tracer", provider.get_tracer("db")), \
                 patch("database.db_purchase.dth.parse_datetime", return_value=None):
                from database import db_purchase
                db_purchase.insert(mock_db, mock_purchase)
            expected_span = "db.insert"
            expected_op = "INSERT"

    spans = exporter.get_finished_spans()
    span = _get_span_by_name(spans, expected_span)
    assert span is not None, f"Span '{expected_span}' not found"
    assert span.attributes.get("db.system") == "mysql"
    assert span.attributes.get("db.name") == db_name
    assert span.attributes.get("db.operation") == expected_op
    # Span must be finished (end_time is set)
    assert span.end_time is not None


def test_p8_db_span_closed_on_success():
    """Span is always closed even on success."""
    provider, exporter = _make_provider()
    mock_db, _ = _make_mock_db()

    with patch("database.db_purchase.tracer", provider.get_tracer("db")), \
         patch.dict(os.environ, {"MYSQL_DATABASE": "mydb"}):
        from database import db_purchase
        db_purchase.get_by_hash_file(mock_db, "hash")

    spans = exporter.get_finished_spans()
    span = _get_span_by_name(spans, "db.get_by_hash_file")
    assert span is not None
    assert span.end_time is not None


def test_p8_db_span_error_status_and_reraise_on_exception():
    """On DB exception: span has ERROR status, error.message set, exception re-raised."""
    provider, exporter = _make_provider()
    mock_db = MagicMock()
    mock_db.cursor.side_effect = Exception("DB connection lost")

    with patch("database.db_purchase.tracer", provider.get_tracer("db")), \
         patch.dict(os.environ, {"MYSQL_DATABASE": "mydb"}):
        from database import db_purchase
        with pytest.raises(Exception, match="DB connection lost"):
            db_purchase.get_by_hash_file(mock_db, "hash")

    spans = exporter.get_finished_spans()
    span = _get_span_by_name(spans, "db.get_by_hash_file")
    assert span is not None
    assert span.status.status_code == StatusCode.ERROR
    assert "DB connection lost" in span.attributes.get("error.message", "")
    assert span.end_time is not None


def test_p8_db_company_span_has_semantic_attributes():
    """db_company spans also have correct semantic attributes."""
    provider, exporter = _make_provider()
    mock_db, _ = _make_mock_db()

    with patch("database.db_company.tracer", provider.get_tracer("db")), \
         patch.dict(os.environ, {"MYSQL_DATABASE": "mydb"}):
        from database import db_company
        db_company.get_by_cnpj(mock_db, "12345678000100")

    spans = exporter.get_finished_spans()
    span = _get_span_by_name(spans, "db.get_by_cnpj")
    assert span is not None
    assert span.attributes.get("db.system") == "mysql"
    assert span.attributes.get("db.operation") == "SELECT"
    assert span.end_time is not None
