# Bugfix Requirements Document

## Introduction

O CI/linter executa o flake8 com `--extend-ignore=E302,E203,E402,E741,W291,W292,W293,W391,F401,F811,F841`, suprimindo 11 categorias de erros de estilo e qualidade de código em todo o diretório `src/`. Isso mascara problemas reais como imports não utilizados, variáveis ambíguas, espaços em branco desnecessários e imports fora de ordem. O objetivo é remover essa supressão e corrigir todos os erros apontados pelas regras no código-fonte, garantindo que o lint passe sem nenhum `--extend-ignore`.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN o flake8 é executado com `--extend-ignore=E302,E203,E402,E741,W291,W292,W293,W391,F401,F811,F841` THEN o sistema ignora erros de qualidade de código e o CI passa mesmo com o código violando as regras

1.2 WHEN há imports não utilizados (F401) em arquivos como `src/webapi/routers/purchase_router.py` (`FastAPI` importado mas não usado) e `src/tests/test_worker_logs.py` (`pytest`, `patch`, `MagicMock` importados mas não usados) THEN o sistema não reporta esses imports como erro

1.3 WHEN há redefinição de nome não utilizado (F811) em `src/tests/conftest.py` (re-importação de `trace` após já importado) THEN o sistema não reporta a redefinição

1.4 WHEN há variáveis locais atribuídas mas nunca usadas (F841) como `purchase_id` em `src/worker_app/worker.py` THEN o sistema não reporta a variável como erro

1.5 WHEN há imports no meio do arquivo (E402) como `from config.log_config import configure_logging` dentro de uma função em `src/config/otel_config.py` e os imports após código executável em `src/worker_app/program.py` THEN o sistema não reporta a violação de ordem de imports

1.6 WHEN há nomes de variáveis ambíguos (E741) como `l` em `src/tests/test_worker_logs.py` e `src/tests/test_webapi_logs.py` THEN o sistema não reporta o nome ambíguo

1.7 WHEN há espaços em branco desnecessários (W291, W293) em arquivos como `src/database/db.py`, `src/entities/entitity.py`, `src/services/file_service.py` THEN o sistema não reporta os espaços extras

1.8 WHEN há ausência de linha em branco no final do arquivo (W292) ou linha em branco extra no final (W391) em arquivos como `src/services/nfce_extractor.py`, `src/webapi/schemas/line_of_business_schema.py` THEN o sistema não reporta a violação

1.9 WHEN há separação insuficiente entre definições de funções/classes de nível superior (E302 — esperadas 2 linhas em branco) em arquivos como `src/config/log_config.py`, `src/services/nfce_extractor.py`, `src/services/file_service.py`, `src/webapi/routers/company_router.py` THEN o sistema não reporta a falta de linhas em branco

### Expected Behavior (Correct)

2.1 WHEN o flake8 é executado sem `--extend-ignore` THEN o sistema SHALL reportar zero erros em todo o diretório `src/`

2.2 WHEN há imports não utilizados em qualquer arquivo de `src/` THEN o sistema SHALL reportar erro F401 e o código SHALL ter esses imports removidos

2.3 WHEN há redefinição de nome não utilizado em qualquer arquivo de `src/` THEN o sistema SHALL reportar erro F811 e o código SHALL ter a redefinição eliminada

2.4 WHEN há variáveis locais atribuídas mas nunca usadas em qualquer arquivo de `src/` THEN o sistema SHALL reportar erro F841 e o código SHALL ter essas variáveis removidas ou utilizadas

2.5 WHEN há imports no meio do arquivo (após código executável) em qualquer arquivo de `src/` THEN o sistema SHALL reportar erro E402 e o código SHALL ter os imports reorganizados para o topo do arquivo ou a violação justificada com `# noqa: E402` apenas quando tecnicamente inevitável (ex: import condicional pós-configuração de runtime)

2.6 WHEN há nomes de variáveis ambíguos (E741) em qualquer arquivo de `src/` THEN o sistema SHALL reportar o erro e o código SHALL usar nomes descritivos no lugar de `l`, `O`, `I`

2.7 WHEN há espaços em branco desnecessários em linhas (W291, W293) em qualquer arquivo de `src/` THEN o sistema SHALL reportar o erro e o código SHALL ter esses espaços removidos

2.8 WHEN um arquivo não termina com exatamente uma linha em branco (W292/W391) em qualquer arquivo de `src/` THEN o sistema SHALL reportar o erro e o arquivo SHALL terminar com exatamente uma newline

2.9 WHEN há menos de 2 linhas em branco entre definições de funções/classes de nível superior (E302) em qualquer arquivo de `src/` THEN o sistema SHALL reportar o erro e o código SHALL ter as 2 linhas em branco exigidas pelo PEP 8

### Unchanged Behavior (Regression Prevention)

3.1 WHEN o CI executa os testes com `pytest src/tests/` THEN o sistema SHALL CONTINUE TO passar todos os testes sem falhas

3.2 WHEN o worker processa arquivos PDF pendentes THEN o sistema SHALL CONTINUE TO extrair, deduplicar e persistir os dados corretamente no banco de dados

3.3 WHEN a webapi recebe requisições HTTP THEN o sistema SHALL CONTINUE TO retornar as respostas corretas em todos os endpoints existentes

3.4 WHEN o flake8 é executado com `--max-line-length=120` THEN o sistema SHALL CONTINUE TO respeitar esse limite de comprimento de linha (sem alteração nessa regra)

3.5 WHEN imports são reorganizados para corrigir E402 THEN o sistema SHALL CONTINUE TO funcionar corretamente em runtime, sem erros de importação circular ou de ordem de inicialização
