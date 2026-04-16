# Project Structure

```
.
├── docker-compose.yaml
├── .env                        # Environment config (DB credentials, ports, UID/GID)
├── pdf-files/
│   ├── 0-samples/              # Sample NFC-e PDFs for testing
│   ├── pending/                # Drop PDFs here to be processed by worker
│   └── processed/              # Worker moves files here after processing
├── scripts/
│   ├── load-pending-files.sh   # Copies 0-samples into pending/
│   └── rename-files*.sh        # Utility scripts for file renaming
└── src/
    ├── config/                 # Shared: logging setup (structlog)
    ├── database/               # Shared: DB connection + raw SQL per entity
    ├── entities/               # Shared: domain model classes
    ├── helpers/                # Shared: datetime and string utilities
    ├── services/               # Shared: business logic (extraction, hashing, file ops)
    ├── webapi/                 # FastAPI app
    │   ├── routers/            # One router file per resource
    │   ├── schemas/            # Pydantic request/response models
    │   ├── program.py          # FastAPI app entry point
    │   ├── requirements.txt
    │   └── Dockerfile
    └── worker_app/             # Polling worker app
        ├── program.py          # Entry point: DB setup + polling loop
        ├── worker.py           # Core processing logic
        ├── requirements.txt
        └── Dockerfile
```

## Key Conventions

- `src/config`, `src/database`, `src/entities`, `src/helpers`, and `src/services` are **shared** between both apps. Both Dockerfiles copy these into the image.
- `PYTHONPATH=/app/src` is set in both containers, so imports are relative to `src/` (e.g. `from entities.purchase import Purchase`).
- Database access follows a **repository pattern** per entity: one file per table in `src/database/` (e.g. `db_purchase.py`, `db_company.py`). Functions receive a `db` connection as the first argument.
- Entities in `src/entities/` extend the abstract `Entity` base class, which provides `_extract()` (regex helper), `_to_float()`, and `to_json()`.
- Entity fields use Python properties with setters that apply regex extraction and only set the value once (idempotent setters guard with `if self._field is None`).
- API routers open and close a DB connection per request. No connection pooling.
- Naming: database columns and API responses use Portuguese (`empresa_id`, `total_compra`, `ramos_atividade_id`). Python class/method names use English.
- New routers must be registered in `src/webapi/program.py` via `app.include_router(...)`.
- New database tables must be added to `src/database/db_tables.py` and called from `setup_database()`.
