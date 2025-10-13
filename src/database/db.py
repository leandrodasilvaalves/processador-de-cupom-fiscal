import mysql.connector as connector
import os
from dotenv import load_dotenv
from config.log_config import logger

__db = None

def connect():
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    logger.info("Connecting to the database...")
    
    __db = connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE")
    )
    return __db

def close():
    if __db.is_connected():
        __db.close()
        logger.info("Database connection closed.")