# Tech Stack

## Language & Runtime
- Python 3.11 (both apps run on `python:3.11-slim` Docker image)

## Applications

### worker_app
- Polling loop (5s interval) that processes PDF files from `pdf-files/pending/`
- PDF parsing: `pdfplumber`, `pdfminer.six`, `pypdfium2`
- No web framework — plain Python script

### webapi
- REST API built with **FastAPI** + **Uvicorn**
- Pydantic v2 for request/response schemas
- Runs on port 8000 (mapped to 8081 on host)

## Database
- MySQL 8.0 via `mysql-connector-python`
- No ORM — raw SQL with parameterized queries
- Connection managed manually (connect/close per request or worker cycle)
- Schema setup via `db_tables.setup_database()` on worker startup

## Observability
- Structured JSON logging via `structlog`
- OpenTelemetry instrumentation (OTLP exporter via gRPC/HTTP)
- Grafana LGTM stack (`grafana/otel-lgtm`) on ports 3100, 4317, 4318

## Infrastructure
- Docker Compose orchestrates all services
- Services: `iniciador`, `webapi`, `worker_app`, `mysql`, `phpmyadmin`, `grafana`
- Config via `.env` file (MySQL credentials, container prefix, UID/GID)

## Common Commands

```bash
# Start all services
docker compose up -d

# Rebuild and start
docker compose up -d --build

# View logs
docker compose logs -f worker_app
docker compose logs -f webapi

# Stop all services
docker compose down

# Load pending PDF files (copies from 0-samples to pending)
bash scripts/load-pending-files.sh

# Install dependencies locally (per app)
pip install -r src/webapi/requirements.txt
pip install -r src/worker_app/requirements.txt
```

## Ports (host)
| Service     | Port  |
|-------------|-------|
| webapi      | 8081  |
| MySQL       | 3307  |
| phpMyAdmin  | 8082  |
| Grafana     | 3100  |
| OTLP gRPC   | 4317  |
| OTLP HTTP   | 4318  |
