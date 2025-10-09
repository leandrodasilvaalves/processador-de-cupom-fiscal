import mysql.connector as connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

db = connector.connect(
    host="localhost",
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

cursor = db.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Empresas (
        id INT AUTO_INCREMENT PRIMARY KEY,
        RazaoSocial VARCHAR(150) NOT NULL,
        NomeFantasia VARCHAR(150),
        CNPJ CHAR(14) NOT NULL UNIQUE,
        Endereco VARCHAR(255)
    )
""")