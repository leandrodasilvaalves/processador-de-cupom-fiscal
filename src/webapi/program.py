import time
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from config.otel_config import configure_otel
from config.log_config import logger

# 5.1 — Initialize OTel before creating the app (reads OTEL_SERVICE_NAME from env)
configure_otel()

app = FastAPI(
    title="Processador de Cupom Fiscal",
    description="API para processar cupons fiscais e gerenciar empresas.",
    version="1.0.0.beta",
)

# 5.1 — Register FastAPI automatic instrumentation
FastAPIInstrumentor.instrument_app(app)


# 5.2 — Request/response logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.monotonic()
        logger.info(
            "http_request_received",
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
            duration_ms = int((time.monotonic() - start_time) * 1000)
            if response.status_code >= 500:
                logger.error(
                    "http_request_error",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    error="Internal Server Error",
                )
            else:
                logger.info(
                    "http_request_completed",
                    method=request.method,
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )
            return response
        except Exception as e:
            duration_ms = int((time.monotonic() - start_time) * 1000)
            logger.error(
                "http_request_error",
                method=request.method,
                path=request.url.path,
                error=str(e),
            )
            raise


app.add_middleware(RequestLoggingMiddleware)


@app.get("/hc")
def home():
    return {"status": "Healthy"}


from .routers import company_router, line_of_business_router, purchase_router  # noqa: E402

app.include_router(company_router.router)
app.include_router(line_of_business_router.router)
app.include_router(purchase_router.router)
