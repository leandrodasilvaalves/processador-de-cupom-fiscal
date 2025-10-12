import pdfplumber
import re
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def extract_nfce_data(file_path: str) -> Dict[str, Any] | None:
    if not os.path.exists(file_path):
        logger.error(f"File not found '{file_path}'.")
        return None

    nfce_data = {}

    try:
        with pdfplumber.open(file_path) as pdf:
            page = pdf.pages[0]
            full_text = page.extract_text()
            
            cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)\s*\|\s*IE:\s*([\d.-]+)", full_text)
            series_number_match = re.search(r"NÚMERO:\s*(\d+)\s*SÉRIE:\s*(\d+)", full_text)            
            issue_date_match = re.search(r"Data de Emissão:\s*([\d/\s:]+)", full_text)
            authorization_date_match = re.search(r"Data de Autorização:\s*([\d/\s:]+)", full_text)
            protocol_match = re.search(r"Protocolo:\s*(\d+)", full_text)
            status_match = re.search(r"Situação:\s*(\w+)", full_text)
            access_key_match = re.search(r"CHAVE DE ACESSO NFC-e\s*([\d\s]+)", full_text)

            nfce_data["Emissor"] = {
                "RazaoSocial": re.search(r"RAZÃO SOCIAL:\s*(.+)", full_text).group(1).strip() if re.search(r"RAZÃO SOCIAL:\s*(.+)", full_text) else None,
                "NomeFantasia": re.search(r"NOME FANTASIA:\s*(.+)", full_text).group(1).strip() if re.search(r"NOME FANTASIA:\s*(.+)", full_text) else None,
                "CNPJ": cnpj_match.group(1) if cnpj_match else None,
                "IE": cnpj_match.group(2) if cnpj_match else None,
                "Endereco": re.search(r"ENDEREÇO:\s*(.+)\n", full_text).group(1).strip() if re.search(r"ENDEREÇO:\s*(.+)\n", full_text) else None,
                "DanfeNumero": series_number_match.group(1).strip() if series_number_match else None,
                "DanfeSerie": series_number_match.group(2).strip() if series_number_match else None,                
                "ChaveAcessoNFCe": access_key_match.group(1).replace(" ", "") if access_key_match else None,                
                "DataEmissao": issue_date_match.group(1).strip() if issue_date_match else None,
                "DataAutorizacao": authorization_date_match.group(1).strip() if authorization_date_match else None,
                "Protocolo": protocol_match.group(1).strip() if protocol_match else None,
                "Situacao": status_match.group(1).strip() if status_match else None,
            }
            
            ITEM_PATTERN = re.compile(r"\s*(\d{3})\s+(.+?)\s+([\d.,]+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)")

            processed_items = []
            
            for match in ITEM_PATTERN.finditer(full_text):
                item, description, quantity, unity, price, discount, total = match.groups()
                
                def to_float(s):
                    return float(s.replace(',', '.'))
                
                processed_items.append({
                    "Item": item.strip(),
                    "CompraID": description.strip(),
                    "quantity": to_float(quantity),
                    "Quantidade": unity.strip(),
                    "Preco": to_float(price),
                    "Desconto": to_float(discount),
                    "Total": to_float(total),
                })
            
            nfce_data["Itens"] = processed_items

            totals = {}
            totals["TotalCompra"] = float(re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["Desconto"] = float(re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["ValorPago"] = float(re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["MetodoPagamento"] = re.search(r"Forma Pagamento\s*(\w+)", full_text).group(1).strip() if re.search(r"Forma Pagamento\s*(\w+)", full_text) else None

            nfce_data["Totais"] = totals
                         
        return nfce_data

    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
        return None
