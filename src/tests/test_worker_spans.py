"""
Tests for worker spans.
Covers: P5 (processing_cycle span), P6 (process_file span), P7 (nfce.extract span)
        + error edge cases.
"""
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


def _run_worker(provider, pending_files, mock_receipt=None, hash_return="abc123",
                hash_file_result=None, nfce_result=None):
    """Helper to run worker.process() with all external deps mocked."""
    mock_db = MagicMock()
    if mock_receipt is None:
        mock_receipt = MagicMock()
        mock_receipt.purchase.nfce_access_key = "key123"
        mock_receipt.purchase.items = []
        mock_receipt.company = MagicMock()

    with patch("worker_app.worker.tracer", provider.get_tracer("worker")), \
         patch("worker_app.worker.file_service.read_pending", return_value=pending_files), \
         patch("worker_app.worker.file_service.get_file_path", side_effect=lambda f: f"/tmp/{f}"), \
         patch("worker_app.worker.hash_calculator.calculate", return_value=hash_return), \
         patch("worker_app.worker.db_purchase.get_by_hash_file", return_value=hash_file_result), \
         patch("worker_app.worker.db_purchase.get_by_nfce", return_value=nfce_result), \
         patch("worker_app.worker.nfce_extractor.extract_nfce_data", return_value=mock_receipt), \
         patch("worker_app.worker.company_service.process", return_value=(1, 2)), \
         patch("worker_app.worker.purchase_service.process", return_value=42), \
         patch("worker_app.worker.file_service.move_to_processed"), \
         patch("worker_app.worker._db.connect", return_value=mock_db), \
         patch("worker_app.worker._db.close"):
        from worker_app import worker as worker_module
        worker_module.process()

# ---------------------------------------------------------------------------
# P6: Process file span contains file identity attributes
# Feature: observability-logs-traces, Property 6: Process file span contains file identity attributes
# ---------------------------------------------------------------------------


@given(
    file_name=st.text(
        min_size=1, max_size=30,
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-.")
    ),
    file_hash_bytes=st.binary(min_size=1, max_size=32),
)
@settings(max_examples=20, deadline=None)
def test_p6_process_file_span_has_file_attributes(file_name, file_hash_bytes):
    # Feature: observability-logs-traces, Property 6: Process file span contains file identity attributes
    file_hash = file_hash_bytes.hex()
    provider, exporter = _make_provider()
    _run_worker(provider, [file_name], hash_return=file_hash)

    spans = exporter.get_finished_spans()
    file_span = _get_span_by_name(spans, "worker.process_file")
    assert file_span is not None, "worker.process_file span not found"
    assert file_span.attributes.get("file.name") == file_name
    assert file_span.attributes.get("file.hash") == file_hash


def test_p6_process_file_span_has_skipped_reason_on_duplicate():
    # Feature: observability-logs-traces, Property 6: Process file span contains file identity attributes (duplicate)
    provider, exporter = _make_provider()
    _run_worker(provider, ["dup_file.pdf"], hash_file_result={"id": 1})

    spans = exporter.get_finished_spans()
    file_span = _get_span_by_name(spans, "worker.process_file")
    assert file_span is not None
    assert file_span.attributes.get("file.skipped_reason") == "duplicate_hash"


# ---------------------------------------------------------------------------
# P7: NFC-e extract span contains extraction result attributes
# Feature: observability-logs-traces, Property 7: NFC-e extract span contains extraction result attributes
# ---------------------------------------------------------------------------

@given(
    access_key=st.text(min_size=1, max_size=44, alphabet=st.characters(whitelist_categories=("Nd",))),
    cnpj=st.text(
        min_size=1, max_size=18,
        alphabet=st.characters(whitelist_categories=("Nd",), whitelist_characters="./- ")
    ),
)
@settings(max_examples=20, deadline=None)
def test_p7_nfce_extract_span_success_attributes(access_key, cnpj):
    # Feature: observability-logs-traces, Property 7: NFC-e extract span contains extraction result attributes
    provider, exporter = _make_provider()

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = lambda s: s
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [MagicMock()]
    mock_pdf.pages[0].extract_text.return_value = "some text"

    mock_company = MagicMock()
    mock_company.cnpj = cnpj
    mock_purchase = MagicMock()
    mock_purchase.nfce_access_key = access_key

    mock_receipt = MagicMock()
    mock_receipt.company = mock_company
    mock_receipt.purchase = mock_purchase

    with patch("services.nfce_extractor.tracer", provider.get_tracer("nfce")), \
         patch("services.nfce_extractor.pdfplumber.open", return_value=mock_pdf), \
         patch("services.nfce_extractor.Company", return_value=mock_company), \
         patch("services.nfce_extractor.Purchase", return_value=mock_purchase), \
         patch("services.nfce_extractor.Receipt", return_value=mock_receipt), \
         patch("os.path.exists", return_value=True):
        from services import nfce_extractor
        nfce_extractor.extract_nfce_data("/tmp/test.pdf")

    spans = exporter.get_finished_spans()
    extract_span = _get_span_by_name(spans, "nfce.extract")
    assert extract_span is not None, "nfce.extract span not found"
    assert extract_span.attributes.get("file.path") == "/tmp/test.pdf"
    assert extract_span.attributes.get("nfce.access_key") == access_key
    assert extract_span.attributes.get("company.cnpj") == cnpj


def test_p7_nfce_extract_span_error_status_on_failure():
    # Feature: observability-logs-traces, Property 7: NFC-e extract span has ERROR status on failure
    provider, exporter = _make_provider()

    with patch("services.nfce_extractor.tracer", provider.get_tracer("nfce")), \
         patch("os.path.exists", return_value=True), \
         patch("services.nfce_extractor.pdfplumber.open", side_effect=Exception("PDF parse error")):
        from services import nfce_extractor
        result = nfce_extractor.extract_nfce_data("/tmp/bad.pdf")

    assert result is None
    spans = exporter.get_finished_spans()
    extract_span = _get_span_by_name(spans, "nfce.extract")
    assert extract_span is not None
    assert extract_span.status.status_code == StatusCode.ERROR
    assert "PDF parse error" in extract_span.attributes.get("error.message", "")
