# Bugfix Requirements Document

## Introduction

Durante o processamento de PDFs de NFC-e da empresa **G Mira Ltda**, o worker falha em extrair corretamente os valores monetários (total da compra, valor pago, desconto) e os preços dos itens. Como resultado, esses campos são salvos como `0.0` ou `null` no banco de dados — ou o processamento do arquivo falha silenciosamente — dependendo do formato do valor no PDF.

A causa raiz está em dois problemas combinados na camada de extração:

1. **Layout de texto diferente**: em alguns PDFs da G Mira Ltda, o `pdfplumber` extrai o rótulo e o valor monetário em linhas separadas (ex: `"Valor Total dos Produtos (R$)\n89,90"`), enquanto os regexes esperam rótulo e valor na mesma linha (ex: `"Valor Total dos Produtos (R$) 89,90"`). O regex não casa, `_extract()` retorna `None`, e `_to_float(None)` retorna `0.0`.

2. **Conversão de float com separador de milhar**: o método `_to_float()` faz apenas `s.replace(",", ".")`, o que transforma `"1.234,56"` em `"1.234.56"` — um float inválido que lança `ValueError`. Esse erro é capturado pelo `try/except` genérico em `nfce_extractor.py`, que retorna `None` para o receipt inteiro, impedindo qualquer dado de ser salvo.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN o PDF da NFC-e contém o rótulo de valor monetário e o valor numérico em linhas separadas (ex: `"Valor Total dos Produtos (R$)\n89,90"`) THEN o sistema retorna `None` para o campo extraído e salva `0.0` no banco de dados

1.2 WHEN o PDF da NFC-e contém um valor monetário com separador de milhar no formato brasileiro (ex: `"1.234,56"`) THEN o sistema lança `ValueError` em `_to_float()`, o `nfce_extractor` captura a exceção e retorna `None` para o receipt inteiro, e nenhum dado é salvo no banco de dados

1.3 WHEN o PDF da NFC-e contém itens cujos preços ou totais usam separador de milhar (ex: `"1.234,56"`) THEN o sistema lança `ValueError` ao instanciar `PurchaseItem`, e o processamento do arquivo falha silenciosamente

### Expected Behavior (Correct)

2.1 WHEN o PDF da NFC-e contém o rótulo de valor monetário e o valor numérico em linhas separadas THEN o sistema SHALL extrair corretamente o valor numérico e salvá-lo no banco de dados

2.2 WHEN o PDF da NFC-e contém um valor monetário com separador de milhar no formato brasileiro (ex: `"1.234,56"`) THEN o sistema SHALL converter corretamente para float `1234.56` sem lançar exceção

2.3 WHEN o PDF da NFC-e contém itens cujos preços ou totais usam separador de milhar THEN o sistema SHALL converter corretamente os valores e salvar os itens no banco de dados

### Unchanged Behavior (Regression Prevention)

3.1 WHEN o PDF da NFC-e contém rótulo e valor monetário na mesma linha (formato padrão) THEN o sistema SHALL CONTINUE TO extrair e salvar os valores corretamente

3.2 WHEN o PDF da NFC-e contém valores monetários sem separador de milhar (ex: `"89,90"`) THEN o sistema SHALL CONTINUE TO converter corretamente para float `89.9`

3.3 WHEN o PDF da NFC-e já foi processado anteriormente (mesmo hash ou mesma chave de acesso) THEN o sistema SHALL CONTINUE TO ignorar o arquivo e movê-lo para `processed/`

3.4 WHEN o PDF da NFC-e é de outra empresa (não G Mira Ltda) com layout padrão THEN o sistema SHALL CONTINUE TO processar e salvar todos os dados corretamente
