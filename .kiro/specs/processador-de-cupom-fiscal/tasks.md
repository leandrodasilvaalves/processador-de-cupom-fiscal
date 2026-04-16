# Implementation Plan

- [x] 1. Escrever teste de exploração da condição de bug
  - **Property 1: Bug Condition** - Separador de Milhar e Layout Multi-linha
  - **CRÍTICO**: Este teste DEVE FALHAR no código não corrigido — a falha confirma que o bug existe
  - **NÃO tente corrigir o teste ou o código quando ele falhar**
  - **NOTA**: O teste codifica o comportamento esperado — ele validará o fix quando passar após a implementação
  - **OBJETIVO**: Expor contraexemplos que demonstram os bugs
  - **Abordagem PBT Focada**: Para Bug B, gerar strings no formato `"X.XXX,XX"` (com separador de milhar); para Bug A, usar o texto literal com `\n` entre rótulo e valor
  - Bug B — testar que `_to_float("1.234,56")` retorna `1234.56` sem lançar `ValueError` (de `Entity._to_float`)
  - Bug A — testar que `Purchase._extract(texto, padrão)` retorna o valor quando rótulo e valor estão em linhas separadas (ex: `"Valor Total dos Produtos (R$)\n89,90"`)
  - Executar no código **não corrigido**
  - **RESULTADO ESPERADO**: Teste FALHA (isso é correto — prova que o bug existe)
  - Documentar os contraexemplos encontrados para entender a causa raiz
  - Marcar tarefa como concluída quando o teste estiver escrito, executado e a falha documentada
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Escrever testes de preservação (ANTES de implementar o fix)
  - **Property 2: Preservation** - Comportamento para Entradas Não-Bugadas
  - **IMPORTANTE**: Seguir metodologia observation-first
  - Observar no código não corrigido: `_to_float("89,90")` retorna `89.9`
  - Observar no código não corrigido: `_to_float(None)` retorna `0.0`
  - Observar no código não corrigido: `_to_float("0,50")` retorna `0.5`
  - Observar no código não corrigido: texto com rótulo e valor na mesma linha extrai corretamente
  - Escrever teste property-based: para toda string sem separador de milhar no formato `"X,XX"`, `_to_float(s)` retorna o float correto (de Preservation Requirements no design)
  - Escrever teste: `_to_float(None) == 0.0`
  - Escrever teste: texto com layout padrão (rótulo e valor na mesma linha) continua sendo extraído corretamente por `Purchase`
  - Executar no código **não corrigido**
  - **RESULTADO ESPERADO**: Testes PASSAM (confirma comportamento baseline a preservar)
  - Marcar tarefa como concluída quando os testes estiverem escritos, executados e passando no código não corrigido
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix para extração incorreta de valores monetários em PDFs da G Mira Ltda

  - [x] 3.1 Corrigir `_to_float()` em `src/entities/entitity.py`
    - Remover separador de milhar (ponto) antes de converter vírgula decimal para ponto
    - Implementar: `s.replace(".", "").replace(",", ".")` em vez de `s.replace(",", ".")`
    - Preservar: `_to_float(None)` continua retornando `0.0`
    - _Bug_Condition: bugB(input) — s = "1.234,56" → float("1.234.56") lança ValueError_
    - _Expected_Behavior: _to_float("1.234,56") == 1234.56, sem exceção_
    - _Preservation: _to_float("89,90") == 89.9, _to_float(None) == 0.0_
    - _Requirements: 1.2, 1.3, 2.2, 2.3, 3.2_

  - [x] 3.2 Corrigir regexes multi-linha nos setters de `Purchase` em `src/entities/purchase.py`
    - Atualizar setter `purchase_total`: padrão `r"Valor Total dos Produtos \(R\$\)\s*\n?\s*([\d,.]+)"`
    - Atualizar setter `discount`: padrão `r"Valor Descontos \(R\$\)\s*\n?\s*([\d,.]+)"`
    - Atualizar setter `paid_amount`: padrão `r"Valor Pago \(R\$\)\s*\n?\s*([\d,.]+)"`
    - _Bug_Condition: bugA(input) — texto com "\n" entre rótulo e valor → _extract() retorna None_
    - _Expected_Behavior: _extract() retorna o valor numérico mesmo com quebra de linha_
    - _Preservation: textos com rótulo e valor na mesma linha continuam sendo extraídos corretamente_
    - _Requirements: 1.1, 2.1, 3.1_

  - [x] 3.3 Verificar que o teste de exploração da condição de bug agora passa
    - **Property 1: Expected Behavior** - Separador de Milhar e Layout Multi-linha
    - **IMPORTANTE**: Re-executar o MESMO teste da tarefa 1 — NÃO escrever um novo teste
    - O teste da tarefa 1 codifica o comportamento esperado
    - Quando este teste passar, confirma que o comportamento esperado foi satisfeito
    - **RESULTADO ESPERADO**: Teste PASSA (confirma que o bug foi corrigido)
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 3.4 Verificar que os testes de preservação ainda passam
    - **Property 2: Preservation** - Comportamento para Entradas Não-Bugadas
    - **IMPORTANTE**: Re-executar os MESMOS testes da tarefa 2 — NÃO escrever novos testes
    - **RESULTADO ESPERADO**: Testes PASSAM (confirma ausência de regressões)
    - Confirmar que todos os testes passam após o fix (sem regressões)

- [x] 4. Checkpoint — Garantir que todos os testes passam
  - Executar toda a suíte de testes
  - Garantir que todos os testes passam; perguntar ao usuário se surgirem dúvidas
