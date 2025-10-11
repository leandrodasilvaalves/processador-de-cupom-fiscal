import mysql.connector as connector
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

db = connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

cursor = db.cursor()

print("Creating tables if they do not exist...")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Empresas (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        RazaoSocial VARCHAR(150) NOT NULL,
        NomeFantasia VARCHAR(150),
        CNPJ CHAR(14) NOT NULL UNIQUE,
        Endereco VARCHAR(255)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Produtos (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        Nome VARCHAR(150) NOT NULL,
        Preco DECIMAL(10, 2) NOT NULL,
        DataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UltimaAtualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS Compras (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        EmpresaID INT,
        ChaveAcessoNFCe CHAR(44) NOT NULL UNIQUE,
        ValorTotal DECIMAL(10, 2) NOT NULL,
        ValorDescontos DECIMAL(10, 2) DEFAULT 0,
        ValorPago DECIMAL(10, 2) NOT NULL,
        FormaPagamento VARCHAR(50) NOT NULL,
        DataEmissao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        DataAutorizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        Situacao CHAR(20) NOT NULL,
        DanfeNumero CHAR(20),
        DanfeSerie CHAR(10),
        HashArquivo VARCHAR(64),               
        FOREIGN KEY (EmpresaID) REFERENCES Empresas(Id),
        INDEX idx_compras_hasharquivo (HashArquivo)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS CompraItens (
        Id INT AUTO_INCREMENT PRIMARY KEY,
        CompraID INT,
        ProdutoID INT,
        Quantidade INT NOT NULL,
        PrecoUnitario DECIMAL(10, 2) NOT NULL,
        Desconto DECIMAL(10, 2) DEFAULT 0,
        FOREIGN KEY (CompraID) REFERENCES Compras(Id),
        FOREIGN KEY (ProdutoID) REFERENCES Produtos(Id)
    )
""")