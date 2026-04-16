# Design Técnico — github-actions-pipeline

## Visão Geral

Este documento descreve o design técnico da pipeline de CI/CD no GitHub Actions para o projeto **Processador de Cupom Fiscal**. A pipeline é definida em um único arquivo `.github/workflows/ci.yaml` e orquestra oito jobs interdependentes: pré-versionamento, build Python, testes, build das imagens Docker (webapi e worker_app), publicação das imagens Docker (webapi e worker_app), criação de tag semântica e geração de release notes.

A publicação no Docker Hub só ocorre quando o build de **ambas** as imagens foi bem-sucedido — garantindo que versões incompletas nunca sejam publicadas.

A pipeline reutiliza três workflows compartilhados hospedados em `laboratorio-net/actions`:
- `git-version.yaml@main` — cálculo de versão semântica via GitVersion
- `docker-build-publish.yaml@main` — build e push de imagem Docker para o Docker Hub
- `create-tag.yaml@main` — criação de tag Git

Para release notes, utiliza a action pública `softprops/action-gh-release`, pois não há workflow compartilhado disponível para essa finalidade.

---

## Arquitetura

### Arquivo a ser criado

```
.github/
└── workflows/
    └── ci.yaml
```

Nenhum outro arquivo de configuração é necessário. O workflow `git-version.yaml@main` executa o GitVersion internamente sem precisar de `GitVersion.yml` no repositório.

### Diagrama de Fluxo dos Jobs

```mermaid
flowchart TD
    A([push / pull_request\ndevelop · release/* · main]) --> B

    B[pre_versionamento\ngit-version.yaml@main\noutput: version]

    B --> C[build_python\nubuntu-latest · Python 3.11\ninstala deps + flake8]
    C --> D[testes\nubuntu-latest · Python 3.11\npytest src/tests/]

    D --> E[build_webapi\nubuntu-latest\ndocker build — sem push]
    D --> F[build_worker\nubuntu-latest\ndocker build — sem push]

    E --> G[publish_webapi\ndocker-build-publish.yaml@main\nsrc/webapi/Dockerfile]
    F --> G
    E --> H[publish_worker\ndocker-build-publish.yaml@main\nsrc/worker_app/Dockerfile]
    F --> H

    G --> I[create_tag\ncreate-tag.yaml@main]
    H --> I

    I --> J[release_notes\nsoftprops/action-gh-release]
```

### Cadeia de Dependências

| Job | Depende de | Execução condicional |
|---|---|---|
| `pre_versionamento` | — | sempre |
| `build_python` | `pre_versionamento` | sempre |
| `testes` | `build_python` | sempre |
| `build_webapi` | `testes` | sempre |
| `build_worker` | `testes` | sempre |
| `publish_webapi` | `build_webapi`, `build_worker` | sempre |
| `publish_worker` | `build_webapi`, `build_worker` | sempre |
| `create_tag` | `publish_webapi`, `publish_worker` | sempre |
| `release_notes` | `create_tag` | sempre |

> A separação entre build e publish é a chave da garantia: `publish_webapi` e `publish_worker` só executam quando **ambos** `build_webapi` e `build_worker` foram bem-sucedidos. Se qualquer build falhar, nenhuma imagem é publicada.

---

## Componentes e Interfaces

### Triggers (on)

```yaml
on:
  push:
    branches:
      - develop
      - 'release/**'
      - main
  pull_request:
    branches:
      - develop
      - 'release/**'
      - main
```

O padrão `release/**` cobre qualquer branch com prefixo `release/` (ex: `release/1.0`, `release/2.3.1`).

### Job: pre_versionamento

Chama o workflow compartilhado que executa o GitVersion internamente e expõe a versão semântica calculada.

**Inputs para o workflow chamado:** nenhum (o workflow é autossuficiente)

**Outputs expostos:**

| Output | Descrição |
|---|---|
| `version` | Versão semântica no formato `MAJOR.MINOR.PATCH` |

**Referência:** `laboratorio-net/actions/.github/workflows/git-version.yaml@main`

### Job: build_python

Job nativo (não usa workflow compartilhado). Valida o código Python antes de executar os testes.

**Runner:** `ubuntu-latest`  
**Python:** `3.11`

**Steps:**
1. `actions/checkout@v4`
2. `actions/setup-python@v5` com `python-version: '3.11'`
3. `pip install -r src/webapi/requirements.txt`
4. `pip install -r src/worker_app/requirements.txt`
5. `pip install pytest pytest-cov hypothesis opentelemetry-sdk`
6. `flake8 src/ --max-line-length=120`

### Job: testes

Job nativo. Executa a suíte de testes com pytest.

**Runner:** `ubuntu-latest`  
**Python:** `3.11`  
**Variável de ambiente:** `PYTHONPATH: src`

**Steps:**
1. `actions/checkout@v4`
2. `actions/setup-python@v5` com `python-version: '3.11'`
3. Instalação das dependências (mesma sequência do `build_python`)
4. `pytest src/tests/`

> O `PYTHONPATH=src` é necessário para que os imports relativos ao diretório `src/` funcionem corretamente, conforme convenção do projeto (ex: `from entities.purchase import Purchase`).

### Job: build_webapi

Job nativo. Faz apenas o build da imagem Docker da webapi, sem push, para validar que o Dockerfile compila corretamente.

**Runner:** `ubuntu-latest`

**Steps:**
1. `actions/checkout@v4`
2. `docker/setup-buildx-action@v3`
3. `docker build -f src/webapi/Dockerfile .` (sem push)

### Job: build_worker

Job nativo. Faz apenas o build da imagem Docker do worker_app, sem push.

**Runner:** `ubuntu-latest`

**Steps:**
1. `actions/checkout@v4`
2. `docker/setup-buildx-action@v3`
3. `docker build -f src/worker_app/Dockerfile .` (sem push)

### Job: publish_webapi

Chama o workflow compartilhado de build e publicação Docker para a webapi. Só executa quando **ambos** `build_webapi` e `build_worker` foram bem-sucedidos.

**Inputs:**

| Input | Valor |
|---|---|
| `context` | `.` |
| `dockerfile` | `src/webapi/Dockerfile` |
| `username` | `${{ secrets.DOCKERHUB_USERNAME }}` |
| `image-name` | `${{ secrets.DOCKERHUB_USERNAME }}/processador-cupom-webapi` |
| `version` | `${{ needs.pre_versionamento.outputs.version }}` |

**Secrets:**

| Secret | Valor |
|---|---|
| `usertoken` | `${{ secrets.DOCKERHUB_TOKEN }}` |

**Referência:** `laboratorio-net/actions/.github/workflows/docker-build-publish.yaml@main`

### Job: publish_worker

Chama o workflow compartilhado de build e publicação Docker para o worker_app. Só executa quando **ambos** `build_webapi` e `build_worker` foram bem-sucedidos.

**Inputs:**

| Input | Valor |
|---|---|
| `context` | `.` |
| `dockerfile` | `src/worker_app/Dockerfile` |
| `username` | `${{ secrets.DOCKERHUB_USERNAME }}` |
| `image-name` | `${{ secrets.DOCKERHUB_USERNAME }}/processador-cupom-worker` |
| `version` | `${{ needs.pre_versionamento.outputs.version }}` |

**Secrets:**

| Secret | Valor |
|---|---|
| `usertoken` | `${{ secrets.DOCKERHUB_TOKEN }}` |

**Referência:** `laboratorio-net/actions/.github/workflows/docker-build-publish.yaml@main`

### Job: create_tag

Chama o workflow compartilhado de criação de tag Git.

**Inputs:**

| Input | Valor |
|---|---|
| `version` | `${{ needs.pre_versionamento.outputs.version }}` |

**Referência:** `laboratorio-net/actions/.github/workflows/create-tag.yaml@main`

> A tag será criada no formato `v{MAJOR}.{MINOR}.{PATCH}` (ex: `v1.3.0`), conforme convenção do workflow compartilhado.

### Job: release_notes

Job nativo usando `softprops/action-gh-release`.

**Permissões necessárias:** `contents: write`

**Lógica condicional de pré-lançamento:**

```yaml
prerelease: ${{ github.ref != 'refs/heads/main' }}
```

Isso garante que:
- Pushes na `main` → GitHub Release com status `latest`
- Pushes em `develop` ou `release/*` → GitHub Release com status `prerelease`

**Configuração da action:**

| Parâmetro | Valor |
|---|---|
| `tag_name` | `v${{ needs.pre_versionamento.outputs.version }}` |
| `generate_release_notes` | `true` |
| `prerelease` | `${{ github.ref != 'refs/heads/main' }}` |

---

## Modelos de Dados

### Nomes das Imagens Docker

A estratégia de nomenclatura segue o padrão `{DOCKERHUB_USERNAME}/{app-slug}:{version}`, onde o slug identifica a aplicação dentro do projeto.

| Aplicação | Image name (sem tag) |
|---|---|
| webapi | `{DOCKERHUB_USERNAME}/processador-cupom-webapi` |
| worker_app | `{DOCKERHUB_USERNAME}/processador-cupom-worker` |

A tag da imagem é a versão semântica calculada pelo GitVersion (ex: `1.3.0`). O workflow compartilhado `docker-build-publish.yaml@main` é responsável por aplicar a tag e fazer o push.

### Propagação da Versão Semântica

O output `version` do job `pre_versionamento` é referenciado pelos jobs subsequentes via:

```yaml
needs.pre_versionamento.outputs.version
```

Para que isso funcione, o job `pre_versionamento` deve declarar explicitamente seus outputs mapeando para os outputs do workflow chamado:

```yaml
jobs:
  pre_versionamento:
    uses: laboratorio-net/actions/.github/workflows/git-version.yaml@main
    outputs:
      version: ${{ jobs.pre_versionamento.outputs.version }}
```

> O nome exato do output exposto pelo `git-version.yaml@main` deve ser confirmado na documentação do workflow compartilhado. O design assume que o output se chama `version`.

---

## Propriedades de Corretude

Esta feature é uma pipeline de CI/CD declarativa em YAML. Todos os critérios de aceitação são verificações de configuração estática (triggers, dependências entre jobs, inputs/secrets mapeados, comandos corretos). Não há lógica de código própria com comportamento variável por input.

**PBT não se aplica a esta feature.** Testes baseados em propriedades são inadequados para:
- Configuração declarativa (YAML de CI/CD)
- Verificação de infraestrutura e wiring de serviços externos
- Comportamentos que não variam com inputs gerados aleatoriamente

Todos os critérios de aceitação foram classificados como **SMOKE** na análise de prework — verificações pontuais de configuração que não se beneficiam de 100+ iterações.

---

## Tratamento de Erros

### Falha no pre_versionamento
O GitHub Actions cancela automaticamente todos os jobs que declaram `needs: [pre_versionamento]` quando o job pai falha. Nenhuma configuração adicional é necessária.

### Falha no build_python (flake8)
O flake8 retorna exit code `1` quando encontra violações, o que faz o step falhar e o job ser marcado como falho. O job `testes` não será executado.

### Falha nos testes
O pytest retorna exit code `1` quando há falhas. Os jobs `docker_webapi` e `docker_worker` não serão executados.

### Falha no build das imagens Docker
Os jobs `build_webapi` e `build_worker` executam em paralelo. Se qualquer um falhar, os jobs `publish_webapi` e `publish_worker` não serão executados — pois ambos dependem de `build_webapi` E `build_worker`. Nenhuma imagem é publicada no Docker Hub.

### Falha na autenticação Docker Hub
O workflow compartilhado `docker-build-publish.yaml@main` é responsável por tratar a falha de autenticação nos jobs `publish_webapi` e `publish_worker`. O job falha e os jobs `create_tag` e `release_notes` não são executados.
O workflow compartilhado `create-tag.yaml@main` é responsável por tratar conflitos de tag. O job falha e o job `release_notes` não é executado.

### Secret ausente
O GitHub Actions falha o job com erro de contexto quando um secret referenciado não está configurado no repositório. Não é necessário tratamento explícito no YAML.

---

## Estratégia de Testes

PBT não se aplica a esta feature (ver seção Propriedades de Corretude).

### Testes de Smoke (verificação estática do YAML)

A validação do arquivo `ci.yaml` deve ser feita por inspeção estática e execução real na plataforma GitHub Actions. As verificações recomendadas são:

**Estrutura de triggers:**
- O campo `on.push.branches` contém exatamente `[develop, 'release/**', main]`
- O campo `on.pull_request.branches` contém exatamente `[develop, 'release/**', main]`

**Dependências entre jobs:**
- `build_python` tem `needs: [pre_versionamento]`
- `testes` tem `needs: [build_python]`
- `build_webapi` tem `needs: [testes]`
- `build_worker` tem `needs: [testes]`
- `publish_webapi` tem `needs: [build_webapi, build_worker]`
- `publish_worker` tem `needs: [build_webapi, build_worker]`
- `create_tag` tem `needs: [publish_webapi, publish_worker]`
- `release_notes` tem `needs: [create_tag]`

**Configuração dos jobs nativos:**
- `build_python` e `testes` usam `runs-on: ubuntu-latest` e `python-version: '3.11'`
- `testes` tem `env: PYTHONPATH: src`
- Step de lint usa `flake8 src/ --max-line-length=120`
- Step de testes usa `pytest src/tests/`

**Segurança:**
- Nenhum valor de secret aparece hardcoded no YAML
- Todos os secrets são referenciados via `${{ secrets.NOME }}`

### Validação via `actionlint`

Recomenda-se usar a ferramenta [`actionlint`](https://github.com/rhysd/actionlint) para validação estática do YAML antes de fazer push:

```bash
actionlint .github/workflows/ci.yaml
```

### Validação em ambiente real

A validação definitiva é feita executando a pipeline no GitHub Actions em um branch de teste, verificando que cada job executa na ordem correta e com os inputs/outputs esperados.
