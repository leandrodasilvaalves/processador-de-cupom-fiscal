import pdfplumber
import os
from opentelemetry import trace
from opentelemetry.trace import StatusCode
from config.log_config import logger
from entities.company import Company
from entities.purchase import Purchase
from entities.receipt import Receipt

tracer = trace.get_tracer(__name__)


def extract_nfce_data(file_path: str) -> Receipt:
    if not os.path.exists(file_path):
        logger.error(f"File not found '{file_path}'.")
        return None

    with tracer.start_as_current_span("nfce.extract") as span:
        span.set_attribute("file.path", file_path)
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    logger.error(f"No pages found in PDF '{file_path}'.")
                    return None

                company = Company()
                purchase = Purchase()
                full_text = "\n".join(
                    page.extract_text() or "" for page in pdf.pages
                )
                company.load(full_text)
                purchase.load(full_text)

                receipt = Receipt(company, purchase)
                span.set_attribute("nfce.access_key", receipt.purchase.nfce_access_key or "")
                span.set_attribute("company.cnpj", receipt.company.cnpj or "")
                return receipt

        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            logger.exception(f"An unexpected error has occurred: {e}")
            return None
