import os
from config.log_config import logger
from datetime import datetime
import shutil

pending_dir = "./pdf-files/pending"
processed_dir = "./pdf-files/processed"

def read_pending():
    pending_files = os.listdir(pending_dir)
    logger.info("Found pending files", count=len(pending_files))
    return pending_files


def move_to_processed(file):
    file_path = os.path.join(pending_dir, file)
    now = datetime.now().strftime("%Y%d%m%H%M%S")
    filename, ext = os.path.splitext(file)
    new_filename = f"{filename}_processed_at_{now}{ext}"
    dest_path = os.path.join(processed_dir, new_filename)
    shutil.move(file_path, dest_path)
    logger.info("Moved file to processed", original=file, new=new_filename)

def get_file_path(file):
    return os.path.join(pending_dir, file)