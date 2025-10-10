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

print('Creating table "Empresas"...')
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Empresas (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        RazaoSocial VARCHAR(150) NOT NULL,
        NomeFantasia VARCHAR(150),
        CNPJ CHAR(14) NOT NULL UNIQUE,
        Endereco VARCHAR(255)
    )
""")

print('Creating table "Produtos"...')
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        Nome VARCHAR(150) NOT NULL,
        Preco DECIMAL(10, 2) NOT NULL,
        DataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UltimaAtualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
""")

print('Creating table "Compras"...')
cursor.execute("""
    CREATE TABLE IF NOT EXISTS Compras (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        EmpresaID INT,
        ChaveAcessoNFCe CHAR(44) NOT NULL UNIQUE,
        ValorTotal DECIMAL(10, 2) NOT NULL,
        DataEmissao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        DataAutorizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Situacao CHAR(20) NOT NULL,
        FOREIGN KEY (EmpresaID) REFERENCES Empresas(Id)
    )
""")
print("All tables has been created. ")