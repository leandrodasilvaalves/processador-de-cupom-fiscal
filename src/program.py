from config.log_config import logger
from database import db_tables
from database.db import connect, close as db_close
import worker

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)
db_close()

worker.process()
logger.info("Application finished.")