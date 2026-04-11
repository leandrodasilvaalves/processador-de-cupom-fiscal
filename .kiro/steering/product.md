# Product

**Processador de Cupom Fiscal** is a system that automatically processes Brazilian NFC-e (Nota Fiscal do Consumidor Eletrônica) receipts from PDF files.

## What it does

- Watches a folder for incoming NFC-e PDF files
- Extracts structured data (company info, purchase totals, line items, payment method, access key, etc.) using regex-based text parsing
- Deduplicates receipts by file hash and NFC-e access key
- Persists companies, purchases, and purchase items to a MySQL database
- Exposes a REST API to query the processed data

## Domain language

The codebase mixes Portuguese and English. Domain terms follow Brazilian fiscal/tax vocabulary:
- `compra` = purchase
- `empresa` = company
- `ramo de atividade` = line of business
- `cupom fiscal` / `NFC-e` = consumer receipt
- `DANFE` = fiscal document number/series
- `chave de acesso` = NFC-e access key
