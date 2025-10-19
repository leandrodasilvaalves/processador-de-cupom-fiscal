import mysql.connector as connector
from mysql.connector.pooling import PooledMySQLConnection
import os
from dotenv import load_dotenv
from config.log_config import logger

__db : PooledMySQLConnection = None

def connect():
    global __db 
    
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
    logger.info("Connecting to the database...")
    
    __db = connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        port=int(os.getenv("MYSQL_PORT"))
    )
    return __db 

def close():
    if __db is not None and __db.is_connected():
        __db.close()
        logger.info("Database connection closed.")