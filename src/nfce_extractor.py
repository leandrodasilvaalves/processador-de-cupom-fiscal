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
            
            nfce_data["Issuer"] = {
                "BusinessName": re.search(r"RAZÃO SOCIAL:\s*(.+)", full_text).group(1).strip() if re.search(r"RAZÃO SOCIAL:\s*(.+)", full_text) else None,
            }
            
            ITEM_PATTERN = re.compile(r"\s*(\d{3})\s+(.+?)\s+([\d.,]+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)")

            processed_items = []
            
            for match in ITEM_PATTERN.finditer(full_text):
                item, description, quantity, unity, price, descount, total = match.groups()
                
                def to_float(s):
                    return float(s.replace(',', '.'))
                
                processed_items.append({
                    "item": item.strip(),
                    "description": description.strip(),
                    "quantity": to_float(quantity),
                    "unity": unity.strip(),
                    "price": to_float(price),
                    "descount": to_float(descount),
                    "total": to_float(total),
                })
            
            nfce_data["Itens"] = processed_items

            totals = {}
            totals["Total_Purchase"] = float(re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["Descount"] = float(re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Descontos \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["Amount_Paid"] = float(re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", full_text).group(1).replace(',', '.')) if re.search(r"Valor Pago \(R\$\)\s*([\d,.]+)", full_text) else 0.0
            totals["Payment_Method"] = re.search(r"Forma Pagamento\s*(\w+)", full_text).group(1).strip() if re.search(r"Forma Pagamento\s*(\w+)", full_text) else None

            nfce_data["Totais"] = totals
                         
        return nfce_data

    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
        return None
