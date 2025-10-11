from log_config import logger
import create_tables
import worker

logger.info("Starting the application...")
create_tables.setup_database()

worker.run()