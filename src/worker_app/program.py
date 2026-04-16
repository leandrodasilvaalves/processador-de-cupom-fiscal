from config.otel_config import configure_otel
configure_otel("worker_app")

from config.log_config import logger  # noqa: E402
from database import db_tables  # noqa: E402
from database.db import connect, close as db_close  # noqa: E402
import worker  # noqa: E402
from time import sleep  # noqa: E402

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)
db_close()

while True:
    logger.info("Starting process.")
    worker.process()
    logger.info("Process finished.")
    sleep(5)
