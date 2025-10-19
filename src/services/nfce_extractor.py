import pdfplumber
import re
import os
from typing import Dict, Any
from config.log_config import logger

def __extract_company_info(text: str) -> Dict[str, Any]:
    cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)\s*\|\s*IE:\s*([\d.-]+)", text)
    return {
        "razao_social": re.search(r"RAZÃO SOCIAL:\s*(.+)", text).group(1).strip() if re.search(r"RAZÃO SOCIAL:\s*(.+)", text) else None,
        "nome_fantasia": re.search(r"NOME FANTASIA:\s*(.+)", text).group(1).strip() if re.search(r"NOME FANTASIA:\s*(.+)", text) else None,
        "cnpj": cnpj_match.group(1) if cnpj_match else None,
        "ie": cnpj_match.group(2) if cnpj_match else None,
        "endereco": re.search(r"ENDEREÇO:\s*(.+)\n", text).group(1).strip() if re.search(r"ENDEREÇO:\s*(.+)\n", text) else None,         
    } 


def __extract_totals(text: str) -> Dict[str, Any]:
    return {
        "total_compra": float(re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", text).group(1).replace(',', '.')) if re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", text) else 0.0,
        "desconto": float(re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", text).group(1).replace(',', '.')) if re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", text) else 0.0,
        "valor_pago": float(re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", text).group(1).replace(',', '.')) if re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", text) else 0.0,
        "forma_pagamento": re.search(r"Forma Pagamento\s*(\w+)", text).group(1).strip() if re.search(r"Forma Pagamento\s*(\w+)", text) else None,
    }


def __extract_danfe_data(text: str) -> Dict[str, Any]:
    series_number_match = re.search(r"NÚMERO:\s*(\d+)\s*SÉRIE:\s*(\d+)", text)
    return {
        "numero": series_number_match.group(1).strip() if series_number_match else None,
        "serie": series_number_match.group(2).strip() if series_number_match else None, 
    }


def __extract_footer_data(text: str) -> Dict[str, Any]:
    access_key_match = re.search(r"CHAVE DE ACESSO NFC-e\s*([\d\s]+)", text)
    status_match = re.search(r"Situação:\s*(\w+)", text)
    protocol_match = re.search(r"Protocolo:\s*(\d+)", text)
    authorization_date_match = re.search(r"Data de Autorização:\s*([\d/\s:]+)", text)
    issue_date_match = re.search(r"Data de Emissão:\s*([\d/\s:]+)", text)

    return {
        "chave_acesso_nfce": access_key_match.group(1).replace(" ", "") if access_key_match else None,                
        "data_emissao": issue_date_match.group(1).strip() if issue_date_match else None,
        "data_autorizacao": authorization_date_match.group(1).strip() if authorization_date_match else None,
        "protocolo": protocol_match.group(1).strip() if protocol_match else None,
        "situacao": status_match.group(1).strip() if status_match else None,
    }

def __extract_items(text: str) -> list[Dict[str, Any]]:
    ITEM_PATTERN = re.compile(r"\s*(\d{3})\s+(.+?)\s+([\d.,]+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)")
    items = []

    for match in ITEM_PATTERN.finditer(text):
        item, description, quantity, unity, price, discount, total = match.groups()
        
        def to_float(s):
            return float(s.replace(',', '.'))
        
        items.append({
            "item": item.strip(),
            "descricao": description.strip(),
            "quantidade": to_float(quantity),
            "unidade": unity.strip(),
            "preco": to_float(price),
            "desconto": to_float(discount),
            "total": to_float(total),
        })
    
    return items    


def extract_nfce_data(file_path: str) -> Dict[str, Any] | None:
    if not os.path.exists(file_path):
        logger.error(f"File not found '{file_path}'.")
        return None    

    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                logger.error(f"No pages found in PDF '{file_path}'.")
                return None
            
            first_page_text = pdf.pages[0].extract_text() or ""
            nfce_data ={}
            nfce_data["empresa"] = __extract_company_info(first_page_text)
            nfce_data["danfe"] = __extract_danfe_data(first_page_text)

            processed_items = []
            
            for page in pdf.pages:
                full_text = page.extract_text()                        
                processed_items.extend(__extract_items(full_text)) 
                
                nfce_data["totais"] = __extract_totals(full_text)
                nfce_data["rodape"] = __extract_footer_data(full_text)
                
            nfce_data["itens"] = processed_items
                         
        return nfce_data

    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
        return None
