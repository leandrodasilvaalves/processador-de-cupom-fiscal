from log_config import logger
import db_tables
import worker
from db import connect

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)

worker.run(db)