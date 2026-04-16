# Requirements Document

## Introduction

Este documento descreve os requisitos para adicionar instrumentação estratégica de logs e traces ao sistema **Processador de Cupom Fiscal**, utilizando OpenTelemetry como protocolo de exportação e a stack Grafana LGTM (Loki + Tempo + Prometheus + Grafana) como backend de visualização.

O sistema possui dois aplicativos: `worker_app` (loop de polling que processa PDFs de NFC-e) e `webapi` (API REST FastAPI). Ambos já possuem as dependências do OpenTelemetry instaladas e o `structlog` configurado para logging estruturado em JSON, mas ainda não possuem traces distribuídos nem logs correlacionados com trace IDs.

O objetivo é instrumentar os pontos-chave do sistema — processamento de PDF, extração de dados, operações de banco de dados e requisições HTTP — de forma que os dados sejam visíveis e correlacionáveis no Grafana.

---

## Glossary

- **OTel_Configurator**: Módulo Python responsável por inicializar o TracerProvider e o LoggerProvider do OpenTelemetry com exportadores OTLP.
- **Tracer**: Instância do OpenTelemetry usada para criar spans em um serviço.
- **Span**: Unidade de trabalho rastreada pelo OpenTelemetry, com nome, atributos, duração e status.
- **Trace**: Conjunto de spans correlacionados que representam uma operação de ponta a ponta.
- **Trace_ID**: Identificador único de um trace, usado para correlacionar logs e spans.
- **OTLP_Exporter**: Exportador OpenTelemetry Protocol que envia dados para o coletor (grafana/otel-lgtm).
- **Worker_App**: Aplicativo de polling que lê PDFs da pasta `pdf-files/pending/` e os processa.
- **WebAPI**: Aplicativo FastAPI que expõe endpoints REST para consulta dos dados processados.
- **NFC-e**: Nota Fiscal do Consumidor Eletrônica — documento fiscal brasileiro em formato PDF processado pelo sistema.
- **PDF_Processor**: Componente do `Worker_App` responsável por orquestrar o processamento de um arquivo PDF de NFC-e.
- **NFC-e_Extractor**: Serviço (`nfce_extractor`) responsável por extrair dados estruturados de um PDF de NFC-e.
- **DB_Repository**: Módulo de acesso ao banco de dados (arquivos `db_*.py` em `src/database/`).
- **Loki**: Componente da stack LGTM responsável por armazenar e indexar logs.
- **Tempo**: Componente da stack LGTM responsável por armazenar e indexar traces.
- **Grafana**: Interface de visualização da stack LGTM.
- **CNPJ**: Cadastro Nacional da Pessoa Jurídica — identificador único de empresa no Brasil.
- **Chave_de_Acesso**: Identificador único de 44 dígitos de uma NFC-e.

---

## Requirements

### Requirement 1: Inicialização do OpenTelemetry

**User Story:** Como desenvolvedor, quero que o OpenTelemetry seja inicializado corretamente em ambos os aplicativos na inicialização, para que todos os traces e logs sejam exportados para o Grafana LGTM via OTLP.

#### Acceptance Criteria

1. THE `OTel_Configurator` SHALL inicializar um `TracerProvider` com exportador OTLP gRPC apontando para o endpoint configurado via variável de ambiente `OTEL_EXPORTER_OTLP_ENDPOINT`.
2. THE `OTel_Configurator` SHALL inicializar um `LoggerProvider` com exportador OTLP gRPC para envio de logs estruturados ao Loki via OpenTelemetry.
3. THE `OTel_Configurator` SHALL configurar o `Resource` do OpenTelemetry com os atributos `service.name`, `service.version` e `deployment.environment`.
4. WHEN o `Worker_App` inicializa, THE `OTel_Configurator` SHALL ser invocado antes do início do loop de polling.
5. WHEN o `WebAPI` inicializa, THE `OTel_Configurator` SHALL ser invocado antes do registro dos routers FastAPI.
6. THE `OTel_Configurator` SHALL registrar o `Tracer` global com o nome do serviço correspondente (`worker_app` ou `webapi`).
7. IF a variável de ambiente `OTEL_EXPORTER_OTLP_ENDPOINT` não estiver definida, THEN THE `OTel_Configurator` SHALL usar o valor padrão `http://grafana:4318` e registrar um log de aviso indicando o uso do valor padrão.

---

### Requirement 2: Correlação de Logs com Trace IDs

**User Story:** Como desenvolvedor, quero que todos os logs estruturados incluam o `trace_id` e `span_id` do contexto OpenTelemetry ativo, para que eu possa correlacionar logs e traces no Grafana.

#### Acceptance Criteria

1. THE `OTel_Configurator` SHALL adicionar um processor ao `structlog` que injeta os campos `trace_id` e `span_id` do span ativo em cada evento de log.
2. WHEN nenhum span estiver ativo no momento do log, THE `OTel_Configurator` SHALL injetar `trace_id` e `span_id` com valor `"00000000000000000000000000000000"` e `"0000000000000000"` respectivamente.
3. THE `OTel_Configurator` SHALL garantir que os logs continuem sendo emitidos no formato JSON para `stdout`, compatível com a coleta pelo Loki.

---

### Requirement 3: Traces no Worker App — Ciclo de Processamento

**User Story:** Como operador, quero visualizar no Grafana o trace completo de cada ciclo de processamento do worker, para que eu possa identificar gargalos e falhas no pipeline de NFC-e.

#### Acceptance Criteria

1. WHEN o `Worker_App` inicia um ciclo de processamento, THE `PDF_Processor` SHALL criar um span raiz com o nome `worker.processing_cycle` contendo o atributo `pending_files_count` com o número de arquivos pendentes encontrados.
2. WHEN o `PDF_Processor` processa um arquivo PDF individual, THE `PDF_Processor` SHALL criar um span filho com o nome `worker.process_file` contendo os atributos `file.name` e `file.hash`.
3. WHEN o `NFC-e_Extractor` extrai dados de um PDF, THE `NFC-e_Extractor` SHALL criar um span filho com o nome `nfce.extract` contendo o atributo `file.path`.
4. WHEN a extração de NFC-e é concluída com sucesso, THE `NFC-e_Extractor` SHALL adicionar ao span os atributos `nfce.access_key` (Chave_de_Acesso) e `company.cnpj`.
5. IF a extração de NFC-e falhar, THEN THE `NFC-e_Extractor` SHALL registrar o span com status `ERROR` e adicionar o atributo `error.message` com a descrição da falha.
6. WHEN um arquivo é identificado como já processado (por hash ou Chave_de_Acesso), THE `PDF_Processor` SHALL adicionar o atributo `file.skipped_reason` com o valor `"duplicate_hash"` ou `"duplicate_access_key"` ao span `worker.process_file` e encerrá-lo com status `OK`.

---

### Requirement 4: Traces nas Operações de Banco de Dados

**User Story:** Como desenvolvedor, quero que as operações de banco de dados sejam rastreadas como spans filhos do contexto ativo, para que eu possa medir a latência de cada query e identificar operações lentas no Grafana.

#### Acceptance Criteria

1. WHEN o `DB_Repository` executa uma operação de inserção ou consulta, THE `DB_Repository` SHALL criar um span filho com o nome no formato `db.<operação>` (ex: `db.insert_purchase`, `db.get_by_cnpj`).
2. THE `DB_Repository` SHALL adicionar ao span os atributos `db.system` com valor `"mysql"`, `db.name` com o nome do banco de dados e `db.operation` com o tipo da operação (`SELECT`, `INSERT`, `UPDATE`).
3. IF uma operação de banco de dados lançar uma exceção, THEN THE `DB_Repository` SHALL registrar o span com status `ERROR`, adicionar o atributo `error.message` e relançar a exceção original.
4. THE `DB_Repository` SHALL encerrar o span de banco de dados independentemente de sucesso ou falha, garantindo que nenhum span fique aberto indefinidamente.

---

### Requirement 5: Traces nas Requisições HTTP da WebAPI

**User Story:** Como operador, quero que cada requisição HTTP recebida pela WebAPI gere um trace no Grafana, para que eu possa monitorar latência, taxa de erros e throughput dos endpoints.

#### Acceptance Criteria

1. THE `WebAPI` SHALL instrumentar automaticamente todas as rotas FastAPI com spans OpenTelemetry usando `opentelemetry-instrumentation-fastapi`.
2. WHEN uma requisição HTTP é recebida, THE `WebAPI` SHALL criar um span com o nome no formato `HTTP <METHOD> <rota>` (ex: `HTTP GET /compras/`).
3. THE `WebAPI` SHALL adicionar ao span os atributos `http.method`, `http.route`, `http.status_code` e `http.url`.
4. IF uma requisição HTTP resultar em status code 5xx, THEN THE `WebAPI` SHALL registrar o span com status `ERROR`.
5. WHEN uma requisição HTTP é recebida, THE `WebAPI` SHALL propagar o contexto de trace via headers HTTP padrão W3C TraceContext (`traceparent`, `tracestate`).

---

### Requirement 6: Logs Estratégicos no Worker App

**User Story:** Como operador, quero que o worker emita logs estruturados nos pontos-chave do processamento, para que eu possa auditar o histórico de processamento de cada NFC-e no Loki.

#### Acceptance Criteria

1. WHEN o `PDF_Processor` inicia o processamento de um arquivo, THE `PDF_Processor` SHALL emitir um log de nível `INFO` com os campos `event`, `file_name` e `trace_id`.
2. WHEN o `PDF_Processor` conclui o processamento de um arquivo com sucesso, THE `PDF_Processor` SHALL emitir um log de nível `INFO` com os campos `event`, `file_name`, `company_id`, `purchase_id`, `item_count` e `trace_id`.
3. WHEN um arquivo é ignorado por duplicidade, THE `PDF_Processor` SHALL emitir um log de nível `INFO` com os campos `event`, `file_name`, `skipped_reason` e `trace_id`.
4. IF o `PDF_Processor` encontrar um erro ao processar um arquivo, THEN THE `PDF_Processor` SHALL emitir um log de nível `ERROR` com os campos `event`, `file_name`, `error` e `trace_id`, sem interromper o processamento dos demais arquivos.
5. WHEN o `Worker_App` conclui um ciclo de polling, THE `Worker_App` SHALL emitir um log de nível `INFO` com os campos `event`, `processed_count`, `skipped_count`, `error_count` e `duration_ms`.

---

### Requirement 7: Logs Estratégicos na WebAPI

**User Story:** Como operador, quero que a WebAPI emita logs estruturados para cada requisição recebida, para que eu possa auditar o uso da API e correlacionar com traces no Grafana.

#### Acceptance Criteria

1. WHEN a `WebAPI` recebe uma requisição HTTP, THE `WebAPI` SHALL emitir um log de nível `INFO` com os campos `event`, `method`, `path` e `trace_id`.
2. WHEN a `WebAPI` retorna uma resposta HTTP com sucesso, THE `WebAPI` SHALL emitir um log de nível `INFO` com os campos `event`, `method`, `path`, `status_code`, `duration_ms` e `trace_id`.
3. IF a `WebAPI` retornar uma resposta HTTP com status 5xx, THEN THE `WebAPI` SHALL emitir um log de nível `ERROR` com os campos `event`, `method`, `path`, `status_code`, `error` e `trace_id`.

---

### Requirement 8: Configuração via Variáveis de Ambiente

**User Story:** Como operador de infraestrutura, quero configurar todos os parâmetros de observabilidade via variáveis de ambiente, para que o comportamento possa ser ajustado por ambiente (dev, prod) sem alteração de código.

#### Acceptance Criteria

1. THE `OTel_Configurator` SHALL ler o endpoint OTLP da variável de ambiente `OTEL_EXPORTER_OTLP_ENDPOINT`.
2. THE `OTel_Configurator` SHALL ler o nome do serviço da variável de ambiente `OTEL_SERVICE_NAME`.
3. THE `OTel_Configurator` SHALL ler o ambiente de deployment da variável de ambiente `OTEL_DEPLOYMENT_ENVIRONMENT`, usando `"development"` como valor padrão caso não esteja definida.
4. THE `docker-compose.yaml` SHALL definir as variáveis `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME` e `OTEL_DEPLOYMENT_ENVIRONMENT` para os serviços `worker_app` e `webapi`, apontando para o serviço `grafana` na rede interna Docker.

---

### Requirement 9: Visualização no Grafana

**User Story:** Como desenvolvedor, quero acessar o Grafana e visualizar logs e traces do sistema sem configuração manual adicional, para que eu possa começar a monitorar imediatamente após o deploy.

#### Acceptance Criteria

1. THE `grafana/otel-lgtm` SHALL receber logs via OTLP e armazená-los no Loki, tornando-os consultáveis via LogQL no Grafana.
2. THE `grafana/otel-lgtm` SHALL receber traces via OTLP e armazená-los no Tempo, tornando-os consultáveis via TraceQL no Grafana.
3. WHEN um log contém um `trace_id` válido, THE Grafana SHALL permitir navegar do log para o trace correspondente no Tempo usando a funcionalidade de correlação Loki → Tempo.
4. THE `grafana/otel-lgtm` container SHALL estar acessível na porta `3110` do host para acesso ao dashboard do Grafana.
