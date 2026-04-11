import structlog
import logging
import sys
from typing import List, Any

def configure_logging(extra_processors: List[Any] | None = None):
    base_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Inject extra processors (e.g. OtelTraceProcessor) before the JSON renderer
    if extra_processors:
        base_processors.extend(extra_processors)

    base_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=base_processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)

    return structlog.get_logger("processador-cupom-fiscal")


logger = configure_logging()


if __name__ == "__main__":

    logger.info(
        "transacao_teste_iniciada",
        usuario_id="user_123",
        produto="subscription",
        valor=49.90,
    )

    contextual_logger = logger.bind(usuario_id="user_456", origem="api_v2")

    contextual_logger.warning("dados_invalidos", campo="email")
    contextual_logger.info("transacao_finalizada", status="falha")
