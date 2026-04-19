import time

from opentelemetry import trace

from config.log_config import logger
from database import db_purchase
from services import company_service, hash_calculator, nfce_extractor
from services import purchase_service
from services import file_service
from database import db as _db

tracer = trace.get_tracer(__name__)


def process():
    start_time = time.monotonic()

    db = _db.connect()
    pending_files = file_service.read_pending()

    processed_count = 0
    skipped_count = 0
    error_count = 0

    for file in pending_files:
        with tracer.start_as_current_span("worker.process_file") as file_span:
            file_path = file_service.get_file_path(file)
            file_hash = hash_calculator.calculate(file_path)

            file_span.set_attribute("file.name", file)
            file_span.set_attribute("file.hash", file_hash)

            logger.info("file_processing_started", file_name=file)

            try:
                if _is_duplicate(file, db_purchase.get_by_hash_file(db, file_hash)):
                    file_span.set_attribute("file.skipped_reason", "duplicate_hash")
                    logger.info("file_skipped", file_name=file, skipped_reason="duplicate_hash")
                    skipped_count += 1
                    continue

                receipt = nfce_extractor.extract_nfce_data(file_path)
                receipt.with_file_hash(file_hash)
                purchase = receipt.purchase

                if _is_duplicate(file, db_purchase.get_by_nfce(db, purchase.nfce_access_key)):
                    file_span.set_attribute("file.skipped_reason", "duplicate_access_key")
                    logger.info("file_skipped", file_name=file, skipped_reason="duplicate_access_key")
                    skipped_count += 1
                    continue

                company = company_service.process(db, receipt.company)
                receipt.with_company(company[0])
                receipt.with_line_of_business(company[1])

                purchase_id = purchase_service.process(db, receipt.purchase)

                file_service.move_to_processed(file)

                logger.info(
                    "file_processing_completed",
                    file_name=file,
                    company_id=company[0],
                    purchase_id=purchase_id,
                    item_count=len(receipt.purchase.items),
                )
                processed_count += 1

            except Exception as e:
                logger.error("file_processing_error", file_name=file, error=str(e))
                error_count += 1

    duration_ms = int((time.monotonic() - start_time) * 1000)
    logger.info(
        "processing_cycle_completed",
        processed_count=processed_count,
        skipped_count=skipped_count,
        error_count=error_count,
        duration_ms=duration_ms,
    )

    _db.close()


def _is_duplicate(file: str, checker: any) -> bool:
    return bool(checker)
