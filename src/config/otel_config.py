import logging
import os

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry._logs import set_logger_provider

_logger = logging.getLogger(__name__)

DEFAULT_OTLP_ENDPOINT = "http://grafana:4318"


class OtelTraceProcessor:
    """structlog processor that injects trace_id and span_id from the active OTel span."""

    def __call__(self, logger, method, event_dict):
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            event_dict["trace_id"] = format(ctx.trace_id, "032x")
            event_dict["span_id"] = format(ctx.span_id, "016x")
        else:
            event_dict["trace_id"] = "00000000000000000000000000000000"
            event_dict["span_id"] = "0000000000000000"
        return event_dict


def configure_otel(service_name: str | None = None) -> trace.Tracer:
    """
    Inicializa TracerProvider e LoggerProvider com exportadores OTLP HTTP.
    Adiciona o OtelTraceProcessor ao pipeline do structlog.
    Retorna o Tracer global para o serviço.
    """
    # Resolve service name
    resolved_service_name = service_name or os.environ.get("OTEL_SERVICE_NAME")
    if not resolved_service_name:
        raise ValueError(
            "service_name must be provided or OTEL_SERVICE_NAME env var must be set"
        )

    # Resolve endpoint
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        endpoint = DEFAULT_OTLP_ENDPOINT
        _logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT not set, using default: %s", endpoint
        )

    # Resolve deployment environment
    deployment_env = os.environ.get("OTEL_DEPLOYMENT_ENVIRONMENT", "development")

    # Build Resource
    resource = Resource.create(
        {
            "service.name": resolved_service_name,
            "service.version": "1.0.0",
            "deployment.environment": deployment_env,
        }
    )

    # Configure TracerProvider
    tracer_provider = TracerProvider(resource=resource)
    span_exporter = OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Configure LoggerProvider
    logger_provider = LoggerProvider(resource=resource)
    log_exporter = OTLPLogExporter(endpoint=f"{endpoint}/v1/logs")
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(log_exporter))
    set_logger_provider(logger_provider)

    # Inject OtelTraceProcessor into structlog pipeline
    from config.log_config import configure_logging
    configure_logging(extra_processors=[OtelTraceProcessor()])

    return trace.get_tracer(resolved_service_name)
