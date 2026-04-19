from time import sleep

from config.otel_config import configure_otel
from config.log_config import logger
from database import db_tables
from database.db import connect, close as db_close
import worker

configure_otel("worker_app")

logger.info("Starting the application...")

db = connect()
db_tables.setup_database(db)
db_close()

while True:
    worker.process()
    sleep(5)
