from config.log_config import logger
from database import db_tables
import worker
from database.db import connect, close as db_close

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)

worker.run(db)
db_close()