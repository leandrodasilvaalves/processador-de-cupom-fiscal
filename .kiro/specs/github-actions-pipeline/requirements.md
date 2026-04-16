# Documento de Requisitos

## Introdução

Este documento descreve os requisitos para a pipeline de CI/CD no GitHub Actions do projeto **Processador de Cupom Fiscal**. A pipeline automatiza o ciclo de integração e entrega contínua, cobrindo versionamento semântico, build do código Python, execução de testes, build e publicação de imagens Docker e geração de release notes — sempre que houver commits ou pull requests nas branches de integração.

## Glossário

- **Pipeline**: Conjunto de jobs do GitHub Actions definidos em um arquivo YAML dentro de `.github/workflows/`.
- **Job**: Unidade de execução dentro da pipeline, podendo depender de outros jobs.
- **Workflow Compartilhado**: Workflow reutilizável hospedado em `laboratorio-net/actions/.github/workflows/` e consumido via `uses:`.
- **GitVersion**: Ferramenta de versionamento semântico baseada no histórico Git, executada internamente pelo workflow compartilhado `git-version.yaml`.
- **Versão Semântica**: Versão no formato `MAJOR.MINOR.PATCH` calculada automaticamente pelo GitVersion.
- **Docker Hub**: Registro público de imagens Docker onde as imagens do projeto são publicadas.
- **webapi**: Aplicação FastAPI do projeto, com Dockerfile em `src/webapi/Dockerfile`.
- **worker_app**: Aplicação worker de polling do projeto, com Dockerfile em `src/worker_app/Dockerfile`.
- **pytest**: Framework de testes utilizado pelo projeto, com testes em `src/tests/`.
- **flake8**: Ferramenta de lint estático para Python.
- **Branch de Integração**: Qualquer branch que aciona a pipeline: `develop`, `release/*` e `main`.
- **Secret**: Variável de ambiente criptografada configurada no repositório GitHub para autenticação segura.

---

## Requisitos

### Requisito 1: Acionamento da Pipeline

**User Story:** Como desenvolvedor, quero que a pipeline seja acionada automaticamente em eventos de push e pull request nas branches de integração, para que todo código integrado passe pelo processo de CI/CD.

#### Critérios de Aceitação

1. WHEN um push é realizado na branch `develop`, THE Pipeline SHALL iniciar a execução de todos os jobs configurados.
2. WHEN um push é realizado em qualquer branch com prefixo `release/`, THE Pipeline SHALL iniciar a execução de todos os jobs configurados.
3. WHEN um push é realizado na branch `main`, THE Pipeline SHALL iniciar a execução de todos os jobs configurados.
4. WHEN um pull request é aberto ou atualizado com destino às branches `develop`, `release/*` ou `main`, THE Pipeline SHALL iniciar a execução de todos os jobs configurados.
5. THE Pipeline SHALL ignorar eventos de push em branches que não sejam `develop`, `release/*` ou `main`.

---

### Requisito 2: Job de Pré-Versionamento

**User Story:** Como desenvolvedor, quero que a pipeline calcule a versão semântica antes dos demais jobs, para que a versão calculada seja propagada como entrada para os jobs subsequentes.

#### Critérios de Aceitação

1. THE Job_Pre_Versionamento SHALL ser o primeiro job a executar na pipeline, sem dependências de outros jobs.
2. THE Job_Pre_Versionamento SHALL utilizar o workflow compartilhado `laboratorio-net/actions/.github/workflows/git-version.yaml@main`, que internamente instala o GitVersion, executa o cálculo e expõe a versão semântica como output — sem necessidade de configuração adicional no repositório.
3. WHEN o Job_Pre_Versionamento é concluído com sucesso, THE Pipeline SHALL disponibilizar a versão semântica calculada como output `version` para os jobs dependentes.
4. IF o Job_Pre_Versionamento falhar, THEN THE Pipeline SHALL interromper a execução de todos os jobs dependentes.

---

### Requisito 3: Job de Build do Código Python

**User Story:** Como desenvolvedor, quero que a pipeline valide o código Python instalando dependências e executando lint estático, para que erros de sintaxe e violações de estilo sejam detectados antes da execução dos testes.

#### Critérios de Aceitação

1. THE Job_Build_Python SHALL executar em um runner `ubuntu-latest` com Python 3.11.
2. THE Job_Build_Python SHALL instalar as dependências de `src/webapi/requirements.txt` e `src/worker_app/requirements.txt`.
3. THE Job_Build_Python SHALL instalar as dependências de teste: `pytest`, `pytest-cov`, `hypothesis` e `opentelemetry-sdk`.
4. THE Job_Build_Python SHALL executar o `flake8` sobre o diretório `src/` com tolerância máxima de linha de 120 caracteres.
5. IF o `flake8` reportar erros de lint, THEN THE Job_Build_Python SHALL falhar e exibir os erros encontrados.
6. THE Job_Build_Python SHALL executar após a conclusão bem-sucedida do Job_Pre_Versionamento.

---

### Requisito 4: Job de Execução dos Testes de Unidade

**User Story:** Como desenvolvedor, quero que a pipeline execute automaticamente todos os testes de unidade com pytest, para que regressões sejam detectadas antes do build da imagem Docker.

#### Critérios de Aceitação

1. THE Job_Testes SHALL executar em um runner `ubuntu-latest` com Python 3.11.
2. THE Job_Testes SHALL instalar todas as dependências necessárias para execução dos testes, incluindo `pytest`, `hypothesis` e `opentelemetry-sdk`.
3. WHEN o comando `pytest src/tests/` é executado, THE Job_Testes SHALL coletar e executar todos os arquivos de teste encontrados no diretório `src/tests/`.
4. IF pelo menos um teste falhar, THEN THE Job_Testes SHALL falhar com código de saída diferente de zero e exibir o relatório de falhas.
5. WHEN todos os testes passam, THE Job_Testes SHALL concluir com sucesso e prosseguir para os jobs dependentes.
6. THE Job_Testes SHALL executar após a conclusão bem-sucedida do Job_Build_Python.
7. THE Job_Testes SHALL configurar a variável de ambiente `PYTHONPATH=src` para que os imports relativos ao diretório `src/` funcionem corretamente.

---

### Requisito 5: Jobs de Build das Imagens Docker

**User Story:** Como desenvolvedor, quero que a pipeline construa as imagens Docker da webapi e do worker_app em paralelo, para que erros de build sejam detectados antes de qualquer publicação no Docker Hub.

#### Critérios de Aceitação

1. THE Job_Build_Webapi SHALL executar em um runner `ubuntu-latest` após a conclusão bem-sucedida do Job_Testes.
2. THE Job_Build_Worker SHALL executar em um runner `ubuntu-latest` após a conclusão bem-sucedida do Job_Testes.
3. THE Job_Build_Webapi e THE Job_Build_Worker SHALL executar em paralelo, sem dependência entre si.
4. THE Job_Build_Webapi SHALL construir a imagem Docker usando `src/webapi/Dockerfile` com contexto na raiz do repositório, sem fazer push.
5. THE Job_Build_Worker SHALL construir a imagem Docker usando `src/worker_app/Dockerfile` com contexto na raiz do repositório, sem fazer push.
6. IF o build de qualquer uma das imagens falhar, THEN THE Pipeline SHALL não publicar nenhuma imagem no Docker Hub.

---

### Requisito 6: Jobs de Publicação das Imagens Docker

**User Story:** Como desenvolvedor, quero que a publicação das imagens no Docker Hub só ocorra quando o build de ambas as imagens foi bem-sucedido, para garantir que versões incompletas nunca sejam publicadas.

#### Critérios de Aceitação

1. THE Job_Publish_Webapi SHALL utilizar o workflow compartilhado `laboratorio-net/actions/.github/workflows/docker-build-publish.yaml@main`.
2. THE Job_Publish_Worker SHALL utilizar o workflow compartilhado `laboratorio-net/actions/.github/workflows/docker-build-publish.yaml@main`.
3. THE Job_Publish_Webapi e THE Job_Publish_Worker SHALL executar somente após a conclusão bem-sucedida de Job_Build_Webapi E Job_Build_Worker.
4. THE Job_Publish_Webapi SHALL passar `context: .`, `dockerfile: src/webapi/Dockerfile`, `image-name` da webapi e `version` calculada pelo Job_Pre_Versionamento.
5. THE Job_Publish_Worker SHALL passar `context: .`, `dockerfile: src/worker_app/Dockerfile`, `image-name` do worker_app e `version` calculada pelo Job_Pre_Versionamento.
6. Ambos os jobs SHALL autenticar no Docker Hub utilizando o secret `DOCKERHUB_USERNAME` como `username` e o secret `DOCKERHUB_TOKEN` como `usertoken`.
7. IF a autenticação no Docker Hub falhar, THEN o job SHALL falhar com mensagem de erro descritiva.

---

### Requisito 7: Job de Criação de Tag Semântica

**User Story:** Como desenvolvedor, quero que a pipeline crie automaticamente uma tag Git com a versão semântica ao final do processo, para que cada build bem-sucedido seja rastreável no histórico do repositório.

#### Critérios de Aceitação

1. THE Job_Create_Tag SHALL utilizar o workflow compartilhado `laboratorio-net/actions/.github/workflows/create-tag.yaml@main`.
2. THE Job_Create_Tag SHALL receber a versão semântica calculada pelo Job_Pre_Versionamento como input.
3. THE Job_Create_Tag SHALL executar somente após a conclusão bem-sucedida de Job_Publish_Webapi e Job_Publish_Worker.
4. WHEN a tag é criada com sucesso, THE Job_Create_Tag SHALL registrar a tag no formato `v{MAJOR}.{MINOR}.{PATCH}` no repositório.
5. IF a criação da tag falhar por conflito com tag existente, THEN THE Job_Create_Tag SHALL falhar com mensagem de erro descritiva.

---

### Requisito 8: Job de Release Notes

**User Story:** Como desenvolvedor, quero que a pipeline gere automaticamente release notes baseadas nos commits, para que seja possível visualizar claramente o que cada release entrega.

#### Critérios de Aceitação

1. THE Job_Release_Notes SHALL executar somente após a conclusão bem-sucedida do Job_Create_Tag.
2. WHERE o workflow compartilhado `laboratorio-net/actions/.github/workflows/` disponibilizar um workflow de release notes compatível, THE Job_Release_Notes SHALL utilizá-lo.
3. WHERE nenhum workflow compartilhado de release notes compatível estiver disponível, THE Job_Release_Notes SHALL utilizar a action `softprops/action-gh-release` para criar uma GitHub Release com as mensagens dos commits desde a tag anterior.
4. THE Job_Release_Notes SHALL associar as release notes à tag criada pelo Job_Create_Tag.
5. WHEN as release notes são geradas com sucesso, THE Job_Release_Notes SHALL publicar a GitHub Release com status `latest` na branch `main` e status de pré-lançamento nas demais branches.

---

### Requisito 9: Segurança e Secrets

**User Story:** Como desenvolvedor, quero que credenciais e tokens sejam gerenciados exclusivamente via secrets do GitHub, para que informações sensíveis nunca sejam expostas nos logs ou no código da pipeline.

#### Critérios de Aceitação

1. THE Pipeline SHALL utilizar o secret `DOCKERHUB_USERNAME` para o nome de usuário do Docker Hub.
2. THE Pipeline SHALL utilizar o secret `DOCKERHUB_TOKEN` para o token de acesso ao Docker Hub.
3. THE Pipeline SHALL utilizar o secret `GITHUB_TOKEN` provido automaticamente pelo GitHub Actions para operações de criação de tag e release.
4. THE Pipeline SHALL garantir que nenhum valor de secret seja impresso diretamente nos logs de execução.
5. IF um secret obrigatório não estiver configurado no repositório, THEN THE Job dependente SHALL falhar com mensagem indicando o secret ausente.
