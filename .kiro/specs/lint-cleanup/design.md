# lint-cleanup Bugfix Design

## Overview

O CI executa o flake8 com `--extend-ignore=E302,E203,E402,E741,W291,W292,W293,W391,F401,F811,F841`,
suprimindo 11 categorias de erros em todo `src/`. Isso mascara imports não utilizados, variáveis
ambíguas, espaços em branco desnecessários e imports fora de ordem.

A correção consiste em dois passos complementares:
1. Corrigir todos os erros apontados pelas 11 regras nos arquivos-fonte afetados.
2. Remover o `--extend-ignore` do CI, fazendo o lint passar sem supressão.

## Glossary

- **Bug_Condition (C)**: A presença de qualquer violação das regras F401, F811, F841, E402, E741,
  W291, W292, W293, W391, E302 em arquivos dentro de `src/`
- **Property (P)**: Após a correção, `flake8 src/ --max-line-length=120` retorna código 0 sem
  nenhum `--extend-ignore`
- **Preservation**: O comportamento de runtime do worker e da webapi, bem como todos os testes
  existentes, devem permanecer inalterados após as correções de lint
- **isBugCondition**: Função que identifica se um arquivo/linha contém uma das violações suprimidas
- **extend-ignore**: Flag do flake8 em `.github/workflows/ci.yaml` que suprime as 11 regras
- **noqa**: Comentário inline que suprime um erro específico do flake8 em uma linha — usado apenas
  quando a violação é tecnicamente inevitável (ex: import condicional pós-inicialização de runtime)

## Bug Details

### Bug Condition

O bug manifesta-se quando o flake8 é executado com `--extend-ignore`, ocultando violações reais
de qualidade de código. Cada arquivo afetado contém uma ou mais das seguintes violações:

| Arquivo | Violações |
|---|---|
| `src/webapi/routers/purchase_router.py` | F401 (`FastAPI` importado, não usado) |
| `src/tests/test_worker_logs.py` | F401 (`pytest`, `patch`, `MagicMock`), E741 (`l`) |
| `src/tests/test_webapi_logs.py` | E741 (`l`), F401 (`pytest`, `patch`, `MagicMock`) |
| `src/tests/conftest.py` | F811 (re-importação de `trace`) |
| `src/worker_app/worker.py` | F841 (`purchase_id` atribuído, nunca usado) |
| `src/config/otel_config.py` | E402 (`from config.log_config import configure_logging` dentro de função) |
| `src/worker_app/program.py` | E402 (imports após `configure_otel("worker_app")`) |
| `src/database/db.py` | W291/W293 (trailing whitespace) |
| `src/entities/entitity.py` | W291/W293 (trailing whitespace) |
| `src/services/file_service.py` | W291/W293, E302 (falta 2 linhas em branco entre funções) |
| `src/services/nfce_extractor.py` | W391/W292, E302 |
| `src/webapi/schemas/line_of_business_schema.py` | W391/W292 |
| `src/config/log_config.py` | E302 |
| `src/webapi/routers/company_router.py` | E302 |
| `.github/workflows/ci.yaml` | `--extend-ignore` a remover |

**Formal Specification:**
```
FUNCTION isBugCondition(file, line)
  INPUT: file — caminho de arquivo em src/; line — linha de código
  OUTPUT: boolean

  RETURN (
    hasUnusedImport(file, line)           -- F401
    OR hasRedefinedUnusedName(file, line) -- F811
    OR hasUnusedVariable(file, line)      -- F841
    OR hasModuleLevelImportNotAtTop(file, line) -- E402
    OR hasAmbiguousVariableName(file, line)     -- E741
    OR hasTrailingWhitespace(file, line)        -- W291 / W293
    OR hasMissingNewlineAtEOF(file)             -- W292
    OR hasBlankLineAtEOF(file)                  -- W391
    OR hasInsufficientBlankLinesBetweenDefs(file, line) -- E302
  )
END FUNCTION
```

### Examples

- `purchase_router.py` linha 1: `from fastapi import FastAPI, APIRouter` — `FastAPI` não é
  referenciado em nenhum lugar do arquivo → F401
- `test_worker_logs.py` linha 55: `lines = [l.strip() for l in ...]` — variável de loop `l` é
  nome ambíguo → E741
- `conftest.py`: `from opentelemetry import trace` aparece duas vezes (uma via shim implícito,
  outra explícita) → F811
- `worker.py`: `purchase_id = purchase_service.process(db, receipt.purchase)` — valor atribuído
  mas nunca lido → F841
- `program.py`: `from config.log_config import logger` aparece após `configure_otel("worker_app")`
  que é código executável → E402
- `otel_config.py`: `from config.log_config import configure_logging` dentro do corpo da função
  `configure_otel` → E402 (caso especial: necessário para evitar import circular; usar `# noqa: E402`)
- `db.py`: linhas com espaços após `global __db ` e `return __db ` → W291
- `nfce_extractor.py`: última linha é linha em branco extra → W391
- `file_service.py`: `def move_to_processed` e `def get_file_path` separadas por apenas 1 linha
  em branco → E302

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- `pytest src/tests/` deve continuar passando todos os testes sem falhas
- O worker deve continuar extraindo, deduplicando e persistindo dados de PDFs corretamente
- Todos os endpoints da webapi devem continuar retornando as respostas corretas
- O limite `--max-line-length=120` permanece inalterado no CI
- A inicialização do OTel (TracerProvider + LoggerProvider) antes do logger deve continuar
  funcionando corretamente em runtime

**Scope:**
Todas as alterações são puramente de estilo/qualidade (remoção de imports, renomeação de variáveis
de loop, remoção de espaços, adição de linhas em branco). Nenhuma lógica de negócio é alterada.
Inputs que não envolvem as linhas corrigidas não são afetados.

## Hypothesized Root Cause

O problema não é um bug de lógica, mas de configuração de qualidade de código acumulada ao longo
do tempo. As causas são:

1. **Supressão ampla no CI**: O `--extend-ignore` foi adicionado provavelmente para fazer o CI
   passar rapidamente sem corrigir os erros existentes, acumulando dívida técnica.

2. **Imports de conveniência não limpos**: `FastAPI` importado em `purchase_router.py` e
   `pytest`/`patch`/`MagicMock` em arquivos de teste foram deixados após refatorações.

3. **Variáveis de loop com nome curto**: `l` usado como variável de loop em list comprehensions
   nos arquivos de teste — padrão comum mas proibido pelo E741.

4. **Import circular em otel_config.py**: O import de `configure_logging` dentro da função
   `configure_otel` é intencional para evitar import circular entre `otel_config` e `log_config`.
   Este é o único caso onde `# noqa: E402` é justificado.

5. **Ordem de inicialização em program.py**: `configure_otel()` precisa ser chamado antes de
   outros imports para garantir que o TracerProvider esteja configurado antes que qualquer módulo
   use `trace.get_tracer()`. Isso viola E402 estruturalmente — usar `# noqa: E402` nas linhas
   de import subsequentes.

6. **Trailing whitespace e formatação**: Editores sem configuração de trim-on-save deixaram
   espaços em branco em `db.py`, `entitity.py` e `file_service.py`.

7. **E302 em múltiplos arquivos**: Funções de nível superior separadas por apenas 1 linha em
   branco em vez das 2 exigidas pelo PEP 8.

## Correctness Properties

Property 1: Bug Condition - Lint Passa Sem Supressão

_For any_ arquivo em `src/` após a aplicação das correções, a execução de
`flake8 src/ --max-line-length=120` (sem `--extend-ignore`) SHALL retornar código de saída 0,
sem reportar nenhum erro das categorias F401, F811, F841, E402, E741, W291, W292, W293, W391
ou E302.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9**

Property 2: Preservation - Comportamento de Runtime Inalterado

_For any_ entrada processada pelo worker ou pela webapi, o código corrigido SHALL produzir
exatamente o mesmo resultado que o código original, preservando toda a lógica de negócio,
extração de dados, persistência e respostas HTTP.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5**

## Fix Implementation

### Changes Required

**Arquivo: `src/webapi/routers/purchase_router.py`**
- Remover `FastAPI` do import: `from fastapi import APIRouter` (F401)

**Arquivo: `src/tests/test_worker_logs.py`**
- Remover imports não utilizados: `pytest`, `patch`, `MagicMock` (F401)
- Renomear variável de loop `l` para `line` em `_parse_all_logs` (E741)

**Arquivo: `src/tests/test_webapi_logs.py`**
- Remover imports não utilizados: `pytest`, `patch`, `MagicMock` (F401)
- Renomear variável de loop `l` para `line` em `_parse_all_logs` (E741)

**Arquivo: `src/tests/conftest.py`**
- Remover a importação duplicada de `trace` (F811): o `from opentelemetry import trace` no
  bloco de fixtures já está presente; verificar qual das duas ocorrências é redundante e remover

**Arquivo: `src/worker_app/worker.py`**
- Remover a atribuição `purchase_id = purchase_service.process(...)` ou usar o valor retornado
  no log `file_processing_completed` (F841) — o log já usa `purchase_id`, então a variável
  deve ser mantida e o erro F841 indica que o linter não a reconhece como usada; revisar se
  o uso no logger.info conta como referência ou se há outro problema

**Arquivo: `src/config/otel_config.py`**
- Adicionar `# noqa: E402` na linha `from config.log_config import configure_logging` dentro
  da função `configure_otel` — import intencional para evitar circular import (E402 justificado)

**Arquivo: `src/worker_app/program.py`**
- Adicionar `# noqa: E402` nos imports que seguem `configure_otel("worker_app")` — a ordem
  é intencional para garantir inicialização do OTel antes dos demais módulos (E402 justificado)

**Arquivo: `src/database/db.py`**
- Remover trailing whitespace nas linhas com `global __db ` e `return __db ` (W291/W293)

**Arquivo: `src/entities/entitity.py`**
- Remover trailing whitespace nas linhas afetadas (W291/W293)

**Arquivo: `src/services/file_service.py`**
- Remover trailing whitespace (W291/W293)
- Adicionar linha em branco extra entre `move_to_processed` e `get_file_path` (E302)

**Arquivo: `src/services/nfce_extractor.py`**
- Corrigir final de arquivo: remover linha em branco extra ou garantir exatamente uma newline (W391/W292)
- Adicionar linha em branco extra entre `extract_nfce_data` e qualquer outra definição de nível
  superior, se necessário (E302)

**Arquivo: `src/webapi/schemas/line_of_business_schema.py`**
- Corrigir final de arquivo: garantir exatamente uma newline (W391/W292)
- Remover linha em branco inicial desnecessária

**Arquivo: `src/config/log_config.py`**
- Adicionar linha em branco extra entre definições de nível superior onde E302 é reportado (E302)

**Arquivo: `src/webapi/routers/company_router.py`**
- Adicionar linha em branco extra entre as funções de rota onde E302 é reportado (E302)

**Arquivo: `.github/workflows/ci.yaml`**
- Remover `--extend-ignore=E302,E203,E402,E741,W291,W292,W293,W391,F401,F811,F841` da linha
  do flake8, mantendo apenas `--max-line-length=120`

## Testing Strategy

### Validation Approach

A estratégia segue duas fases: primeiro confirmar as violações no código não corrigido (exploratory),
depois verificar que o lint passa e o comportamento é preservado após as correções.

### Exploratory Bug Condition Checking

**Goal**: Confirmar as violações antes de aplicar as correções. Verificar que o flake8 sem
`--extend-ignore` realmente falha nos arquivos identificados.

**Test Plan**: Executar `flake8 src/ --max-line-length=120` sem `--extend-ignore` no código
atual e observar os erros reportados. Isso confirma ou refuta a lista de violações mapeada.

**Test Cases**:
1. **F401 em purchase_router.py**: Executar flake8 no arquivo — deve reportar `FastAPI` importado
   mas não usado (falha no código não corrigido)
2. **E741 em test_worker_logs.py**: Executar flake8 — deve reportar variável `l` ambígua
   (falha no código não corrigido)
3. **F811 em conftest.py**: Executar flake8 — deve reportar redefinição de `trace`
   (falha no código não corrigido)
4. **E402 em program.py**: Executar flake8 — deve reportar imports após código executável
   (falha no código não corrigido)

**Expected Counterexamples**:
- `purchase_router.py:1:1: F401 'fastapi.FastAPI' imported but unused`
- `test_worker_logs.py:55:20: E741 ambiguous variable name 'l'`
- `conftest.py:XX:1: F811 redefinition of unused 'trace'`
- `program.py:3:1: E402 module level import not at top of file`

### Fix Checking

**Goal**: Verificar que após as correções, o flake8 sem `--extend-ignore` retorna código 0.

**Pseudocode:**
```
FOR ALL file IN src/ DO
  violations := flake8(file, max_line_length=120, extend_ignore=[])
  ASSERT len(violations) == 0
END FOR
```

### Preservation Checking

**Goal**: Verificar que as correções de lint não alteram o comportamento de runtime.

**Pseudocode:**
```
FOR ALL test IN pytest_suite DO
  result_before := run_test(test, original_code)
  result_after  := run_test(test, fixed_code)
  ASSERT result_before == result_after
END FOR
```

**Testing Approach**: Os testes existentes em `src/tests/` cobrem o comportamento de runtime.
Executar `pytest src/tests/` após as correções é suficiente para verificar a preservação, pois
os testes cobrem logs do worker, logs da webapi e fixtures de OTel.

**Test Cases**:
1. **Preservação dos testes de worker logs**: `pytest src/tests/test_worker_logs.py` deve passar
2. **Preservação dos testes de webapi logs**: `pytest src/tests/test_webapi_logs.py` deve passar
3. **Preservação das fixtures**: `pytest src/tests/conftest.py` (via outros testes) deve funcionar
4. **Inicialização do OTel**: Após reorganização de imports em `program.py` e `otel_config.py`,
   a inicialização deve continuar funcionando sem erros de import circular

### Unit Tests

- Verificar que cada arquivo corrigido não contém as violações específicas mapeadas
- Verificar que `purchase_router.py` usa apenas `APIRouter` do fastapi
- Verificar que variáveis de loop em `_parse_all_logs` têm nomes descritivos

### Property-Based Tests

- Os testes de hipótese existentes em `test_worker_logs.py` e `test_webapi_logs.py` já cobrem
  propriedades de preservação — devem continuar passando após as correções
- Nenhum novo teste de propriedade é necessário para as correções de lint em si, pois são
  alterações puramente estruturais sem lógica nova

### Integration Tests

- Executar `flake8 src/ --max-line-length=120` sem `--extend-ignore` como teste de integração
  final — deve retornar código 0
- Executar `pytest src/tests/` completo para verificar que nenhum teste regrediu
- Verificar que o CI passa com o `--extend-ignore` removido do `ci.yaml`
