import hash_calculator
import os
from log_config import logger


def run():
    logger.info("Starting processing...")

    pending_dir = "./pdf-files/pending"
    pending_files = os.listdir(pending_dir)
    logger.info("Found pending files", count=len(pending_files))

    for file in pending_files:
        logger.info("Processing file", file_name=file)
        file_path = os.path.join(pending_dir, file)
        file_hash = hash_calculator.calculate(file_path)
        logger.info("Calculated hash", file_name=file, hash=file_hash)
