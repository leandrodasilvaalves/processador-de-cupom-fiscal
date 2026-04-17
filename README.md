# Processador de Cupom Fiscal

Sistema que processa automaticamente cupons fiscais brasileiros (NFC-e) a partir de arquivos PDF. Extrai dados estruturados — empresa emissora, itens comprados, totais, forma de pagamento, chave de acesso — e persiste tudo em um banco MySQL, expondo uma API REST para consulta.

---

## Como funciona

O sistema é composto por dois serviços principais:

**worker_app** — loop de polling que roda a cada 5 segundos:
1. Lê os PDFs em `pdf-files/pending/`
2. Calcula o hash SHA-256 de cada arquivo para detectar duplicatas
3. Extrai o texto do PDF com `pdfplumber` e aplica regex para capturar os campos da NFC-e
4. Verifica duplicata por hash e por chave de acesso NFC-e antes de persistir
5. Salva empresa (se nova), compra e itens no MySQL
6. Move o arquivo para `pdf-files/processed/` com timestamp no nome

**webapi** — API REST com FastAPI na porta 8000 (8081 no host):
- Consulta de compras, empresas e itens
- Gerenciamento de ramos de atividade (categorias de empresa)
- Associação de empresas a ramos de atividade

### Deduplicação

Cada PDF é verificado duas vezes antes de ser processado:
- Por **hash do arquivo** (SHA-256) — evita reprocessar o mesmo arquivo
- Por **chave de acesso NFC-e** — evita duplicar a mesma nota fiscal mesmo que o arquivo seja diferente

### Schema do banco de dados

```
ramos_atividade   → categorias de empresa (ex: Supermercado, Farmácia)
empresas          → empresas emissoras das notas (CNPJ, razão social, endereço)
produtos          → catálogo de produtos extraídos das notas
compras           → cada nota fiscal processada
compras_items     → itens de cada compra (produto, quantidade, preço, total)
_migrations       → controle de migrações aplicadas
```

O schema é criado automaticamente pelo worker na inicialização via `db_tables.setup_database()`.

---

## Pré-requisitos

- Docker e Docker Compose
- Python 3.11 (para desenvolvimento local)

---

## Executando com Docker

```bash
# Subir todos os serviços
docker compose up -d

# Subir e forçar rebuild das imagens
docker compose up -d --build

# Parar tudo
docker compose down

# Ver logs em tempo real
docker compose logs -f worker_app
docker compose logs -f webapi
```

### Serviços e portas

| Serviço    | URL                                    | Descrição                        |
|------------|----------------------------------------|----------------------------------|
| webapi     | http://localhost:8081                  | API REST                         |
| webapi     | http://localhost:8081/docs             | Swagger UI (documentação da API) |
| phpMyAdmin | http://localhost:8082                  | Interface web para o MySQL       |
| Grafana    | http://localhost:3110                  | Dashboards e observabilidade     |
| MySQL      | localhost:3307                         | Banco de dados                   |
| OTLP gRPC  | localhost:4327                         | Endpoint OpenTelemetry gRPC      |
| OTLP HTTP  | localhost:4328                         | Endpoint OpenTelemetry HTTP      |

---

## Processando PDFs

Coloque arquivos PDF de NFC-e na pasta `pdf-files/pending/`. O worker os detecta automaticamente no próximo ciclo (até 5 segundos).

Para carregar os arquivos de exemplo:

```bash
bash scripts/load-pending-files.sh
```

Isso limpa `pending/` e `processed/` e copia todos os PDFs de `pdf-files/0-samples/` para `pending/`.

---

## Desenvolvimento local

### Configurando o ambiente

```bash
# Criar o venv na raiz do projeto
python -m venv venv

# Ativar o venv
source venv/bin/activate          # Linux/macOS
venv\Scripts\activate             # Windows

# Instalar todas as dependências (webapi + worker_app)
pip install -r requirements.txt
```

### Desativar o venv

```bash
deactivate
```

### Instalando novos pacotes

Sempre instale com o venv ativo e atualize o `requirements.txt` do app correspondente:

```bash
# Ativar o venv primeiro
source venv/bin/activate

# Instalar o pacote
pip install nome-do-pacote

# Atualizar o requirements.txt do app que vai usar o pacote
pip freeze | grep nome-do-pacote >> src/webapi/requirements.txt
# ou
pip freeze | grep nome-do-pacote >> src/worker_app/requirements.txt
```

> O `requirements.txt` na raiz é para desenvolvimento local (union dos dois apps).
> Cada Dockerfile usa o `requirements.txt` do seu próprio app para manter as imagens enxutas.

### Rodando localmente (sem Docker)

Você precisa de um MySQL acessível. Configure o `.env` com `MYSQL_HOST=localhost`.

```bash
# Worker
python src/worker_app/program.py

# WebAPI
uvicorn src.webapi.program:app --reload
```

Ou use as configurações de debug do VS Code (`.vscode/launch.json`):
- **Worker** — roda o worker com `load pending files` como pré-tarefa
- **Webapi** — sobe o uvicorn com hot reload desativado por padrão

---

## Variáveis de ambiente

Definidas no arquivo `.env` na raiz do projeto:

| Variável              | Descrição                                      |
|-----------------------|------------------------------------------------|
| `MYSQL_HOST`          | Host do MySQL                                  |
| `MYSQL_PORT`          | Porta do MySQL (padrão: 3306)                  |
| `MYSQL_DATABASE`      | Nome do banco de dados                         |
| `MYSQL_USER`          | Usuário do banco                               |
| `MYSQL_PASSWORD`      | Senha do usuário                               |
| `MYSQL_ROOT_PASSWORD` | Senha do root (usado pelo container MySQL)     |
| `CONTAINER_PREFIX`    | Prefixo dos nomes dos containers Docker        |
| `UID` / `GID`         | UID e GID do usuário host (permissões de arquivo) |

---

## API REST

A documentação interativa completa está disponível em `http://localhost:8081/docs`.

### Endpoints principais

**Empresas**
```
GET  /empresas/                        Lista todas as empresas
GET  /empresas/sem-ramo-atividade      Empresas sem ramo de atividade associado
GET  /empresas/{id}/compras/           Compras de uma empresa
PUT  /empresas/{id}                    Associa ramo de atividade a uma empresa
```

**Compras**
```
GET  /compras/                         Lista todas as compras
GET  /compras/{id}/items               Itens de uma compra
PUT  /compras/ramos-atividade          Propaga ramo de atividade para todas as compras
```

**Ramos de Atividade**
```
GET    /ramos-de-atividade/            Lista todos os ramos
GET    /ramos-de-atividade/{id}        Busca ramo por ID
POST   /ramos-de-atividade/            Cria novo ramo
PUT    /ramos-de-atividade/{id}        Atualiza ramo
DELETE /ramos-de-atividade/{id}        Remove ramo
```

**Health check**
```
GET  /hc                               Retorna {"status": "Healthy"}
```

---

## Observabilidade

O sistema usa OpenTelemetry com exportação via OTLP HTTP para o Grafana LGTM stack:

- **Traces** — cada ciclo do worker, cada arquivo processado e cada operação de banco geram spans rastreáveis
- **Logs** — logs estruturados em JSON via `structlog`, com `trace_id` e `span_id` injetados automaticamente para correlação
- **Grafana** — acesse `http://localhost:3110` para visualizar traces e logs (login anônimo habilitado)

---

## Estrutura do projeto

```
.
├── docker-compose.yaml
├── .env
├── requirements.txt              # Dependências unificadas para dev local
├── pdf-files/
│   ├── 0-samples/                # PDFs de exemplo para testes
│   ├── pending/                  # Drop PDFs aqui para processar
│   └── processed/                # Worker move os arquivos processados aqui
├── scripts/
│   ├── load-pending-files.sh     # Carrega amostras em pending/
│   └── rename-files*.sh          # Utilitários de renomeação
└── src/
    ├── config/                   # Logging (structlog) e OpenTelemetry
    ├── database/                 # Conexão MySQL + repositórios por entidade
    ├── entities/                 # Modelos de domínio com extração via regex
    ├── helpers/                  # Utilitários de data e string
    ├── services/                 # Lógica de negócio (extração, hash, persistência)
    ├── tests/                    # Testes de observabilidade (spans e logs)
    ├── webapi/                   # FastAPI app (routers, schemas, Dockerfile)
    └── worker_app/               # Worker de polling (program.py, worker.py, Dockerfile)
```
