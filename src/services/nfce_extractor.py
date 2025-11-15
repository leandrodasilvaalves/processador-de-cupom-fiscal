import pdfplumber
import re
import os
from typing import Dict, Any
from config.log_config import logger

def _extract_field_with_regex(field_name: str, regex: str, text: str, existing_data: Dict[str, Any], transform=lambda x: x) -> None:
    """
    Extrai um campo usando regex e atualiza o dicionário existente apenas se o campo estiver vazio.
    """
    if field_name not in existing_data or existing_data[field_name] is None:
        match = re.search(regex, text)
        existing_data[field_name] = transform(match.group(1)) if match else None


def extract_totals(text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrai os totais de um texto e atualiza os dados existentes.
    """
    totals = existing_data or {}

    _extract_field_with_regex("total_compra", r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("desconto", r"Valor Descontos \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("valor_pago", r"Valor Pago \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("forma_pagamento", r"Forma Pagamento\s*(\w+)", text, totals)

    return totals


def __extract_company_info(text: str) -> Dict[str, Any]:
    cnpj_match = re.search(r"CNPJ:\s*([\d./-]+)\s*\|\s*IE:\s*([\d.-]+)", text)
    return {
        "razao_social": re.search(r"RAZÃO SOCIAL:\s*(.+)", text).group(1).strip() if re.search(r"RAZÃO SOCIAL:\s*(.+)", text) else None,
        "nome_fantasia": re.search(r"NOME FANTASIA:\s*(.+)", text).group(1).strip() if re.search(r"NOME FANTASIA:\s*(.+)", text) else None,
        "cnpj": cnpj_match.group(1) if cnpj_match else None,
        "ie": cnpj_match.group(2) if cnpj_match else None,
        "endereco": re.search(r"ENDEREÇO:\s*(.+)\n", text).group(1).strip() if re.search(r"ENDEREÇO:\s*(.+)\n", text) else None,         
    } 


def extract_company_info(text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrai as informações da empresa e atualiza os dados existentes.
    """
    company_info = existing_data or {}

    _extract_field_with_regex("razao_social", r"RAZÃO SOCIAL:\s*(.+)", text, company_info, str.strip)
    _extract_field_with_regex("nome_fantasia", r"NOME FANTASIA:\s*(.+)", text, company_info, str.strip)
    _extract_field_with_regex("cnpj", r"CNPJ:\s*([\d./-]+)", text, company_info)
    _extract_field_with_regex("ie", r"IE:\s*([\d.-]+)", text, company_info)
    _extract_field_with_regex("endereco", r"ENDEREÇO:\s*(.+)\n", text, company_info, str.strip)

    return company_info


def __extract_totals(text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrai os totais de um texto e atualiza os dados existentes de forma granular.
    """
    totals = existing_data or {}

    # Utiliza a função genérica para extrair e atualizar os campos
    _extract_field_with_regex("total_compra", r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("desconto", r"Valor Descontos \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("valor_pago", r"Valor Pago \(R\$\)\s*([\d,.]+)", text, totals, lambda x: float(x.replace(',', '.')))
    _extract_field_with_regex("forma_pagamento", r"Forma Pagamento\s*(\w+)", text, totals)

    return totals


def __extract_danfe_data(text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrai os dados do DANFE e atualiza os dados existentes de forma granular.
    """
    danfe_data = existing_data or {}

    _extract_field_with_regex("numero", r"NÚMERO:\s*(\d+)", text, danfe_data, str.strip)
    _extract_field_with_regex("serie", r"SÉRIE:\s*(\d+)", text, danfe_data, str.strip)

    return danfe_data


def __extract_footer_data(text: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extrai os dados do rodapé e atualiza os dados existentes de forma granular.
    """
    footer_data = existing_data or {}

    _extract_field_with_regex("chave_acesso_nfce", r"CHAVE DE ACESSO NFC-e\s*([\d\s]+)", text, footer_data, lambda x: x.replace(" ", ""))
    _extract_field_with_regex("data_emissao", r"Data de Emissão:\s*([\d/\s:]+)", text, footer_data, str.strip)
    _extract_field_with_regex("data_autorizacao", r"Data de Autorização:\s*([\d/\s:]+)", text, footer_data, str.strip)
    _extract_field_with_regex("protocolo", r"Protocolo:\s*(\d+)", text, footer_data, str.strip)
    _extract_field_with_regex("situacao", r"Situação:\s*(\w+)", text, footer_data, str.strip)

    return footer_data


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
                
                nfce_data["totais"] = __extract_totals(full_text, nfce_data.get("totais"))
                nfce_data["rodape"] = __extract_footer_data(full_text)
                
            nfce_data["itens"] = processed_items
                         
        return nfce_data

    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
        return None
