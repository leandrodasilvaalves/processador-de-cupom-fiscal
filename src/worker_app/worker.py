from config.log_config import logger
from database import db_purchase
from services import company_service, hash_calculator, nfce_extractor
from services import purchase_service
from services import file_service
from database import db as _db

def process():
    logger.info("Starting processing...")
    db = _db.connect()

    pending_files = file_service.read_pending()

    for file in pending_files:
        logger.info("Processing file", file_name=file)
        
        file_path = file_service.get_file_path(file)
        file_hash = hash_calculator.calculate(file_path)
        logger.info("Calculated hash", file_name=file, hash=file_hash)

        if db_purchase.get_by_hash_file(db, file_hash):
            logger.info("File already processed, skipping", file_name=file, hash=file_hash)
            file_service.move_to_processed(file)
            continue
        
        else:
            receipt = nfce_extractor.extract_nfce_data(file_path)
            receipt.with_file_hash(file_hash)

            company = company_service.process(db, receipt.company)
            receipt.with_company(company[0])
            receipt.with_line_of_business(company[1])
            logger.info("Processed company", company_id=company[0])
            
            purchase_id = purchase_service.process(db, receipt.purchase)
            logger.info("Created purchase record", purchase_id=purchase_id, item_count=len(receipt.purchase.items))

            file_service.move_to_processed(file)

    logger.info("Processing completed. Pending files count: %d", len(pending_files))

    _db.close()