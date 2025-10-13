import os
from config.log_config import logger
from database import db_purchase
from services import company_service, hash_calculator, nfce_extractor
from services import purchase_service

def run(db):
    logger.info("Starting processing...")

    pending_dir = "./pdf-files/pending"
    pending_files = os.listdir(pending_dir)
    logger.info("Found pending files", count=len(pending_files))

    for file in pending_files:
        logger.info("Processing file", file_name=file)
        file_path = os.path.join(pending_dir, file)
        
        file_hash = hash_calculator.calculate(file_path)
        logger.info("Calculated hash", file_name=file, hash=file_hash)

        if db_purchase.get_by_hash_file(db, file_hash):
            logger.info("File already processed, skipping", file_name=file, hash=file_hash)
            continue
        
        else:
            data = nfce_extractor.extract_nfce_data(file_path)

            company_id = company_service.process(db, data['emissor'])
            logger.info("Processed company", company_id=company_id)
            
            purchase_id = purchase_service.process(db, data, company_id, file_hash)
            logger.info("Created purchase record", purchase_id=purchase_id)

            purchase_service.process_items(db, data['itens'], purchase_id)
            logger.info("Processed purchase items", purchase_id=purchase_id, item_count=len(data['itens']))

           
           