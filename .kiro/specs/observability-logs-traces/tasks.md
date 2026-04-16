# Tasks — Observability: Logs & Traces

## Task List

- [x] 1. Criar `src/config/otel_config.py` com `OTel_Configurator` e `OtelTraceProcessor`
  - [x] 1.1 Implementar `configure_otel(service_name)` que lê env vars, cria Resource, configura TracerProvider e LoggerProvider com exportadores OTLP HTTP
  - [x] 1.2 Implementar `OtelTraceProcessor` que injeta `trace_id` e `span_id` do span ativo em cada evento structlog (zeros quando não há span ativo)
  - [x] 1.3 Atualizar `src/config/log_config.py` para aceitar processors adicionais e injetar `OtelTraceProcessor` no pipeline do structlog

- [x] 2. Instrumentar `src/worker_app/program.py` e `src/worker_app/worker.py`
  - [x] 2.1 Invocar `configure_otel()` em `program.py` antes do loop de polling
  - [x] 2.2 Adicionar span `worker.processing_cycle` com atributo `pending_files_count` em `worker.py`
  - [x] 2.3 Adicionar span `worker.process_file` com atributos `file.name` e `file.hash` para cada arquivo processado
  - [x] 2.4 Adicionar atributo `file.skipped_reason` ao span `worker.process_file` quando arquivo for duplicado
  - [x] 2.5 Emitir logs estruturados nos pontos-chave: início de processamento, conclusão com sucesso, skip por duplicidade, erro, e resumo do ciclo

- [x] 3. Instrumentar `src/services/nfce_extractor.py`
  - [x] 3.1 Adicionar span `nfce.extract` com atributo `file.path`
  - [x] 3.2 Adicionar atributos `nfce.access_key` e `company.cnpj` ao span em caso de sucesso
  - [x] 3.3 Registrar span com status `ERROR` e atributo `error.message` em caso de falha

- [x] 4. Instrumentar repositórios de banco de dados (`src/database/db_*.py`)
  - [x] 4.1 Adicionar span `db.<operação>` com atributos `db.system`, `db.name` e `db.operation` em `db_purchase.py`
  - [x] 4.2 Adicionar span `db.<operação>` com atributos semânticos em `db_company.py`
  - [x] 4.3 Adicionar span `db.<operação>` com atributos semânticos em `db_product.py` e `db_line_of_business.py`
  - [x] 4.4 Garantir que todos os spans de DB são encerrados em `finally` e registram `ERROR` em caso de exceção

- [x] 5. Instrumentar `src/webapi/program.py` e routers
  - [x] 5.1 Invocar `configure_otel()` e registrar `FastAPIInstrumentor` em `program.py` antes dos routers
  - [x] 5.2 Adicionar middleware de logging de requisição/resposta nos routers (entrada, saída com `status_code` e `duration_ms`, erro 5xx)

- [x] 6. Atualizar `docker-compose.yaml`
  - [x] 6.1 Adicionar variáveis `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME` e `OTEL_DEPLOYMENT_ENVIRONMENT` ao serviço `worker_app`
  - [x] 6.2 Adicionar as mesmas variáveis ao serviço `webapi`

- [x] 7. Escrever testes unitários e de propriedade
  - [x] 7.1 `test_otel_config.py`: P1 (Resource attributes), P2 (Tracer name), P13 (OTLP endpoint) + smoke tests de inicialização e edge cases (endpoint ausente, service_name ausente)
  - [x] 7.2 `test_log_correlation.py`: P3 (trace/span IDs no log), P4 (JSON válido) + edge case span inativo
  - [x] 7.3 `test_worker_spans.py`: P5 (processing_cycle span), P6 (process_file span), P7 (nfce.extract span) + edge cases de erro
  - [x] 7.4 `test_db_spans.py`: P8 (DB spans com atributos e encerramento) + edge cases de exceção
  - [x] 7.5 `test_webapi_spans.py`: P9 (HTTP spans), P10 (trace context propagation) + edge case 5xx
  - [x] 7.6 `test_worker_logs.py`: P11 (campos obrigatórios nos logs do worker) + edge case log de erro
  - [x] 7.7 `test_webapi_logs.py`: P12 (campos obrigatórios nos logs da WebAPI) + edge case log 5xx
