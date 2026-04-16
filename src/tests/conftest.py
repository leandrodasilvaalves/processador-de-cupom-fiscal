"""
Shared fixtures for observability tests.

Compatibility shim: opentelemetry-sdk 1.38.0 exposes logs API under
opentelemetry.sdk._logs (private). Alias it to the public name so that
src/config/otel_config.py (which uses the public name) can be imported.
"""
import sys
import os

# --- OTel SDK compatibility shim (must run before any src imports) ---
import opentelemetry.sdk._logs as _sdk_logs
import opentelemetry.sdk._logs.export as _sdk_logs_export

sys.modules.setdefault("opentelemetry.sdk.logs", _sdk_logs)
sys.modules.setdefault("opentelemetry.sdk.logs.export", _sdk_logs_export)
# --- end shim ---

import pytest  # noqa: E402

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from opentelemetry.sdk.trace import TracerProvider  # noqa: E402
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter  # noqa: E402
from opentelemetry.sdk.trace.export import SimpleSpanProcessor  # noqa: E402
from opentelemetry import trace  # noqa: E402


@pytest.fixture
def in_memory_exporter():
    """Returns a fresh InMemorySpanExporter."""
    return InMemorySpanExporter()


@pytest.fixture
def tracer_provider(in_memory_exporter):
    """Creates a TracerProvider backed by an InMemorySpanExporter."""
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(in_memory_exporter))
    return provider


@pytest.fixture
def tracer(tracer_provider):
    """Returns a tracer from the in-memory provider."""
    return tracer_provider.get_tracer("test-tracer")


@pytest.fixture(autouse=False)
def reset_otel():
    """Resets the global OTel tracer provider after each test."""
    yield
    from opentelemetry.sdk.trace import TracerProvider as _TP
    trace.set_tracer_provider(_TP())
