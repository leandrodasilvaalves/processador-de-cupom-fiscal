# Design Document — Processador de Cupom Fiscal (Bugfix)

## Overview

Dois bugs combinados impedem a extração correta de valores monetários em PDFs da G Mira Ltda:

1. **Bug A — Layout multi-linha**: os regexes em `Purchase` esperam rótulo e valor na mesma linha, mas o `pdfplumber` extrai o texto da G Mira Ltda com quebra de linha entre rótulo e valor.
2. **Bug B — Separador de milhar**: `_to_float()` em `Entity` faz apenas `s.replace(",", ".")`, convertendo `"1.234,56"` em `"1.234.56"` (float inválido), lançando `ValueError`.

## Bug Condition

### isBugCondition(input)

```
isBugCondition(input) ≡
  bugA(input) OR bugB(input)

bugA(input) ≡
  input é texto extraído de PDF onde rótulo monetário e valor estão em linhas separadas
  ex: "Valor Total dos Produtos (R$)\n89,90"
  → _extract() retorna None → _to_float(None) retorna 0.0

bugB(input) ≡
  input é string com separador de milhar no formato brasileiro
  ex: s = "1.234,56"
  → s.replace(",", ".") == "1.234.56" → float("1.234.56") lança ValueError
```

### Arquivos afetados

| Arquivo | Método | Bug |
|---|---|---|
| `src/entities/entitity.py` | `_to_float(s)` | Bug B |
| `src/entities/purchase.py` | setters `purchase_total`, `discount`, `paid_amount` | Bug A |

## Expected Behavior

### expectedBehavior(result)

```
Para Bug A:
  dado texto = "Valor Total dos Produtos (R$)\n89,90"
  _extract(texto, r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)") retorna "89,90"
  → o regex deve usar re.DOTALL ou o padrão deve aceitar \n entre rótulo e valor

Para Bug B:
  dado s = "1.234,56"
  _to_float("1.234,56") retorna 1234.56  (sem lançar exceção)

  dado s = "89,90"
  _to_float("89,90") retorna 89.9  (comportamento preservado)

  dado s = None
  _to_float(None) retorna 0.0  (comportamento preservado)
```

## Preservation Requirements

### Comportamentos que NÃO devem mudar

```
preservação(input) ≡ NOT isBugCondition(input)

P1: Para qualquer texto com rótulo e valor na mesma linha (formato padrão):
    _extract(texto, padrão) continua retornando o valor correto

P2: Para qualquer string sem separador de milhar (ex: "89,90"):
    _to_float("89,90") == 89.9

P3: Para s = None:
    _to_float(None) == 0.0

P4: PDFs de outras empresas com layout padrão continuam sendo processados corretamente

P5: Deduplicação por hash e chave de acesso continua funcionando
```

## Implementation Plan

### Fix A — Regex multi-linha em `Purchase`

Nos setters `purchase_total`, `discount` e `paid_amount`, atualizar os padrões regex para aceitar `\s*\n?\s*` entre o rótulo e o valor:

```python
# Antes
r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)"

# Depois
r"Valor Total dos Produtos \(R\$\)\s*\n?\s*([\d,.]+)"
```

Aplicar o mesmo padrão para `discount` e `paid_amount`.

### Fix B — `_to_float()` em `Entity`

```python
# Antes
@staticmethod
def _to_float(s) -> float:
    return 0.0 if s is None else float(s.replace(",", "."))

# Depois
@staticmethod
def _to_float(s) -> float:
    if s is None:
        return 0.0
    # Remove separador de milhar (ponto) e converte vírgula decimal para ponto
    normalized = s.replace(".", "").replace(",", ".")
    return float(normalized)
```

## Correctness Properties

### Property 1: Bug Condition — Conversão com separador de milhar

Para qualquer string no formato `"X.XXX,XX"` (com separador de milhar):
- `_to_float(s)` NÃO lança exceção
- `_to_float(s)` retorna o float correto

### Property 2: Preservation — Comportamento para entradas não-bugadas

Para qualquer string sem separador de milhar (ex: `"89,90"`, `"0,50"`):
- `_to_float(s)` continua retornando o float correto
- `_to_float(None)` continua retornando `0.0`
