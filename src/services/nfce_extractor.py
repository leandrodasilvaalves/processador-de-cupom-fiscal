import pdfplumber
import os
from config.log_config import logger
from entities.company import Company
from entities.purchase import Purchase
from entities.receipt import Receipt

def extract_nfce_data(file_path: str) -> Receipt:
    if not os.path.exists(file_path):
        logger.error(f"File not found '{file_path}'.")
        return None
    try:
        with pdfplumber.open(file_path) as pdf:
            if len(pdf.pages) == 0:
                logger.error(f"No pages found in PDF '{file_path}'.")
                return None

            company = Company()
            purchase = Purchase()
            for page in pdf.pages:
                full_text = page.extract_text()
                company.load(full_text)
                purchase.load(full_text)

            receipt = Receipt(company, purchase)
            return receipt

    except Exception as e:
        logger.exception(f"An unexpected error has occurred: {e}")
    return None