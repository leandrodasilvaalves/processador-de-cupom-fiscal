"""
Tests for src/config/otel_config.py
Covers: P1 (Resource attributes), P2 (Tracer name), P13 (OTLP endpoint)
        + smoke tests and edge cases.
"""
import os
import pytest
from unittest.mock import patch, MagicMock, call
from hypothesis import given, settings
import hypothesis.strategies as st


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_configure_otel(service_name: str, extra_env: dict = None):
    """
    Calls configure_otel with mocked exporters/processors.
    Returns (tracer, captured_tracer_provider, mock_span_exporter, mock_log_exporter).
    """
    env_vars = {
        "OTEL_SERVICE_NAME": service_name,
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    }
    if extra_env:
        env_vars.update(extra_env)

    captured = {}

    def fake_set_tracer_provider(provider):
        captured["tracer_provider"] = provider

    with patch.dict(os.environ, env_vars, clear=False):
        with patch("config.otel_config.OTLPSpanExporter") as mock_span_exp, \
             patch("config.otel_config.OTLPLogExporter") as mock_log_exp, \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.trace.set_tracer_provider", side_effect=fake_set_tracer_provider), \
             patch("config.otel_config.set_logger_provider"):
            mock_span_exp.return_value = MagicMock()
            mock_log_exp.return_value = MagicMock()

            # Also patch get_tracer so we can inspect the tracer name
            from opentelemetry.sdk.trace import TracerProvider
            real_provider = TracerProvider()
            captured["tracer_provider"] = real_provider

            def fake_set_tp(provider):
                captured["tracer_provider"] = provider

            with patch("config.otel_config.trace.set_tracer_provider", side_effect=fake_set_tp), \
                 patch("config.otel_config.trace.get_tracer", wraps=lambda name: _make_mock_tracer(name)) as mock_get_tracer:
                from config.otel_config import configure_otel
                tracer = configure_otel(service_name)
                captured["mock_span_exp"] = mock_span_exp
                captured["mock_log_exp"] = mock_log_exp
                captured["mock_get_tracer"] = mock_get_tracer

    return tracer, captured


def _make_mock_tracer(name: str):
    """Creates a mock tracer with instrumenting_scope.name set."""
    from opentelemetry.sdk.trace import TracerProvider
    provider = TracerProvider()
    return provider.get_tracer(name)


# ---------------------------------------------------------------------------
# P1: Resource attributes reflect environment configuration
# Feature: observability-logs-traces, Property 1: Resource attributes reflect environment configuration
# ---------------------------------------------------------------------------

@given(
    service_name=st.text(
        min_size=1, max_size=30,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )
    ),
    deployment_env=st.text(
        min_size=1, max_size=30,
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="_-"
        )
    ),
)
@settings(max_examples=30, deadline=None)
def test_p1_resource_attributes_reflect_env_config(service_name, deployment_env):
    # Feature: observability-logs-traces, Property 1: Resource attributes reflect environment configuration
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource

    captured_provider = {}

    def fake_set_tp(provider):
        captured_provider["p"] = provider

    env_vars = {
        "OTEL_SERVICE_NAME": service_name,
        "OTEL_DEPLOYMENT_ENVIRONMENT": deployment_env,
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("config.otel_config.OTLPSpanExporter"), \
             patch("config.otel_config.OTLPLogExporter"), \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider", side_effect=fake_set_tp), \
             patch("config.otel_config.trace.get_tracer", return_value=MagicMock()):
            from config.otel_config import configure_otel
            configure_otel(service_name)

    assert "p" in captured_provider, "TracerProvider was not set"
    resource_attrs = captured_provider["p"].resource.attributes
    assert resource_attrs.get("service.name") == service_name
    assert resource_attrs.get("deployment.environment") == deployment_env


# ---------------------------------------------------------------------------
# P2: Tracer name matches service name
# Feature: observability-logs-traces, Property 2: Tracer name matches service name
# ---------------------------------------------------------------------------

@given(service_name=st.text(
    min_size=1, max_size=30,
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-")
))
@settings(max_examples=30, deadline=None)
def test_p2_tracer_name_matches_service_name(service_name):
    # Feature: observability-logs-traces, Property 2: Tracer name matches service name
    captured_tracer_name = {}

    def fake_get_tracer(name):
        captured_tracer_name["name"] = name
        from opentelemetry.sdk.trace import TracerProvider
        return TracerProvider().get_tracer(name)

    env_vars = {
        "OTEL_SERVICE_NAME": service_name,
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("config.otel_config.OTLPSpanExporter"), \
             patch("config.otel_config.OTLPLogExporter"), \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider"), \
             patch("config.otel_config.trace.get_tracer", side_effect=fake_get_tracer):
            from config.otel_config import configure_otel
            tracer = configure_otel(service_name)

    assert captured_tracer_name.get("name") == service_name


# ---------------------------------------------------------------------------
# P13: OTLP exporter uses endpoint from environment variable
# Feature: observability-logs-traces, Property 13: OTLP exporter uses endpoint from environment variable
# ---------------------------------------------------------------------------

@given(endpoint=st.from_regex(r'https?://[a-zA-Z0-9.-]+:\d+', fullmatch=True))
@settings(max_examples=30, deadline=None)
def test_p13_otlp_exporter_uses_env_endpoint(endpoint):
    # Feature: observability-logs-traces, Property 13: OTLP exporter uses endpoint from environment variable
    env_vars = {
        "OTEL_SERVICE_NAME": "test-service",
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("config.otel_config.OTLPSpanExporter") as mock_span_exp, \
             patch("config.otel_config.OTLPLogExporter") as mock_log_exp, \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider"), \
             patch("config.otel_config.trace.get_tracer", return_value=MagicMock()):
            from config.otel_config import configure_otel
            configure_otel("test-service")

    assert mock_span_exp.called, "OTLPSpanExporter was not instantiated"
    assert mock_log_exp.called, "OTLPLogExporter was not instantiated"

    span_endpoint = mock_span_exp.call_args[1].get("endpoint") or (
        mock_span_exp.call_args[0][0] if mock_span_exp.call_args[0] else ""
    )
    log_endpoint = mock_log_exp.call_args[1].get("endpoint") or (
        mock_log_exp.call_args[0][0] if mock_log_exp.call_args[0] else ""
    )
    assert endpoint in span_endpoint, (
        f"Expected {endpoint} in span exporter endpoint {span_endpoint}"
    )
    assert endpoint in log_endpoint, (
        f"Expected {endpoint} in log exporter endpoint {log_endpoint}"
    )


# ---------------------------------------------------------------------------
# Smoke test: configure_otel initializes without error
# ---------------------------------------------------------------------------

def test_smoke_configure_otel_initializes():
    env_vars = {
        "OTEL_SERVICE_NAME": "smoke-test-service",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
    }
    with patch.dict(os.environ, env_vars, clear=False):
        with patch("config.otel_config.OTLPSpanExporter"), \
             patch("config.otel_config.OTLPLogExporter"), \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider"), \
             patch("config.otel_config.trace.get_tracer", return_value=MagicMock()) as mock_get_tracer:
            from config.otel_config import configure_otel
            tracer = configure_otel("smoke-test-service")
            assert tracer is not None


# ---------------------------------------------------------------------------
# Edge case: missing OTEL_EXPORTER_OTLP_ENDPOINT → uses default + warning
# ---------------------------------------------------------------------------

def test_edge_missing_endpoint_uses_default():
    env_without_endpoint = {k: v for k, v in os.environ.items()
                            if k != "OTEL_EXPORTER_OTLP_ENDPOINT"}
    env_without_endpoint["OTEL_SERVICE_NAME"] = "svc"

    with patch.dict(os.environ, env_without_endpoint, clear=True):
        with patch("config.otel_config.OTLPSpanExporter") as mock_span_exp, \
             patch("config.otel_config.OTLPLogExporter"), \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider"), \
             patch("config.otel_config.trace.get_tracer", return_value=MagicMock()), \
             patch("config.otel_config._logger") as mock_logger:
            from config.otel_config import configure_otel, DEFAULT_OTLP_ENDPOINT
            configure_otel("svc")
            mock_logger.warning.assert_called_once()
            span_endpoint = mock_span_exp.call_args[1].get("endpoint") or mock_span_exp.call_args[0][0]
            assert DEFAULT_OTLP_ENDPOINT in span_endpoint


# ---------------------------------------------------------------------------
# Edge case: missing service_name → raises ValueError
# ---------------------------------------------------------------------------

def test_edge_missing_service_name_raises():
    env_without_service = {k: v for k, v in os.environ.items()
                           if k != "OTEL_SERVICE_NAME"}
    with patch.dict(os.environ, env_without_service, clear=True):
        with patch("config.otel_config.OTLPSpanExporter"), \
             patch("config.otel_config.OTLPLogExporter"), \
             patch("config.otel_config.BatchSpanProcessor", return_value=MagicMock()), \
             patch("config.otel_config.BatchLogRecordProcessor", return_value=MagicMock()), \
             patch("config.log_config.configure_logging"), \
             patch("config.otel_config.set_logger_provider"), \
             patch("config.otel_config.trace.set_tracer_provider"), \
             patch("config.otel_config.trace.get_tracer", return_value=MagicMock()):
            from config.otel_config import configure_otel
            with pytest.raises(ValueError, match="service_name"):
                configure_otel(None)
