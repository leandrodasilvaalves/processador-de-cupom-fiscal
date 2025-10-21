from config.log_config import logger
from database import db_tables
from database.db import connect, close as db_close
import worker
from time import sleep

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)
db_close()

while True:
    logger.info("Starting process.")
    worker.process()
    logger.info("Process finished.")
    sleep(5)
