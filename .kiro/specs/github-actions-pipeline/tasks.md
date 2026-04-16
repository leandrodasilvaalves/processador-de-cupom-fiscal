# Plano de Implementação: github-actions-pipeline

## Visão Geral

Criação do arquivo `.github/workflows/ci.yaml` com 9 jobs encadeados que cobrem o ciclo completo de CI/CD: versionamento semântico, lint, testes, build e publicação de imagens Docker, criação de tag e geração de release notes.

## Tasks

- [x] 1. Criar estrutura de diretórios e o arquivo base do workflow
  - Criar o diretório `.github/workflows/` caso não exista
  - Criar o arquivo `.github/workflows/ci.yaml` com o nome do workflow e a seção `on:` configurada
  - Incluir triggers para `push` e `pull_request` nas branches `develop`, `release/**` e `main`
  - _Requisitos: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implementar o job `pre_versionamento`
  - Adicionar o job `pre_versionamento` usando `uses: laboratorio-net/actions/.github/workflows/git-version.yaml@main`
  - Declarar o bloco `outputs:` do job mapeando o output `version` do workflow chamado
  - Garantir que o job não possui `needs:` (executa primeiro)
  - _Requisitos: 2.1, 2.2, 2.3, 2.4_

- [x] 3. Implementar o job `build_python`
  - Adicionar o job com `runs-on: ubuntu-latest` e `needs: [pre_versionamento]`
  - Configurar o step `actions/setup-python@v5` com `python-version: '3.11'`
  - Adicionar steps de `pip install` para `src/webapi/requirements.txt`, `src/worker_app/requirements.txt` e as dependências de teste (`pytest`, `pytest-cov`, `hypothesis`, `opentelemetry-sdk`)
  - Adicionar step com `flake8 src/ --max-line-length=120`
  - _Requisitos: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 4. Implementar o job `testes`
  - Adicionar o job com `runs-on: ubuntu-latest` e `needs: [build_python]`
  - Configurar `env: PYTHONPATH: src` no nível do job
  - Repetir os steps de checkout, setup-python e instalação de dependências
  - Adicionar step com `pytest src/tests/`
  - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 5. Implementar os jobs `build_webapi` e `build_worker`
  - Adicionar `build_webapi` com `runs-on: ubuntu-latest` e `needs: [testes]`
  - Adicionar steps: `actions/checkout@v4`, `docker/setup-buildx-action@v3` e `docker build -f src/webapi/Dockerfile .`
  - Adicionar `build_worker` com `runs-on: ubuntu-latest` e `needs: [testes]`
  - Adicionar steps: `actions/checkout@v4`, `docker/setup-buildx-action@v3` e `docker build -f src/worker_app/Dockerfile .`
  - Confirmar que os dois jobs não possuem dependência entre si (executam em paralelo)
  - _Requisitos: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [x] 6. Checkpoint — verificar estrutura e dependências até aqui
  - Garantir que todos os jobs anteriores estão com `needs:` corretos conforme a cadeia de dependências do design
  - Verificar que nenhum secret está hardcoded no YAML
  - Garantir que os jobs de build não fazem push de imagem

- [x] 7. Implementar os jobs `publish_webapi` e `publish_worker`
  - Adicionar `publish_webapi` usando `uses: laboratorio-net/actions/.github/workflows/docker-build-publish.yaml@main`
  - Configurar `needs: [build_webapi, build_worker]`
  - Passar os inputs: `context: .`, `dockerfile: src/webapi/Dockerfile`, `username: ${{ secrets.DOCKERHUB_USERNAME }}`, `image-name: ${{ secrets.DOCKERHUB_USERNAME }}/processador-cupom-webapi`, `version: ${{ needs.pre_versionamento.outputs.version }}`
  - Passar o secret `usertoken: ${{ secrets.DOCKERHUB_TOKEN }}`
  - Repetir a mesma estrutura para `publish_worker` com `dockerfile: src/worker_app/Dockerfile` e `image-name: ${{ secrets.DOCKERHUB_USERNAME }}/processador-cupom-worker`
  - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 9.1, 9.2, 9.4_

- [x] 8. Implementar o job `create_tag`
  - Adicionar o job usando `uses: laboratorio-net/actions/.github/workflows/create-tag.yaml@main`
  - Configurar `needs: [publish_webapi, publish_worker]`
  - Passar o input `version: ${{ needs.pre_versionamento.outputs.version }}`
  - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5, 9.3_

- [x] 9. Implementar o job `release_notes`
  - Adicionar o job nativo com `runs-on: ubuntu-latest` e `needs: [create_tag]`
  - Adicionar `permissions: contents: write`
  - Adicionar step `actions/checkout@v4`
  - Adicionar step com `uses: softprops/action-gh-release` configurando:
    - `tag_name: v${{ needs.pre_versionamento.outputs.version }}`
    - `generate_release_notes: true`
    - `prerelease: ${{ github.ref != 'refs/heads/main' }}`
  - Passar `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` via `env:` ou `with: token:`
  - _Requisitos: 8.1, 8.3, 8.4, 8.5, 9.3, 9.4_

- [x] 10. Checkpoint final — validação estática do YAML completo
  - Revisar o arquivo `ci.yaml` completo garantindo que todos os 9 jobs estão presentes
  - Confirmar a cadeia de dependências: `pre_versionamento → build_python → testes → build_webapi/build_worker → publish_webapi/publish_worker → create_tag → release_notes`
  - Verificar que nenhum valor de secret aparece hardcoded
  - Executar `actionlint .github/workflows/ci.yaml` se a ferramenta estiver disponível

## Notas

- PBT não se aplica a esta feature — pipeline declarativa YAML sem lógica de código própria
- A separação entre `build_*` e `publish_*` é a garantia central: nenhuma imagem é publicada se qualquer build falhar
- O output `version` do `pre_versionamento` deve ser propagado via `needs.pre_versionamento.outputs.version` em todos os jobs que precisam da versão
- A validação definitiva é feita executando a pipeline no GitHub Actions em um branch de teste
