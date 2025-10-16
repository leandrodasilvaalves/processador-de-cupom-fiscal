from config.log_config import logger
from database import db_migrations as migrations

def _create_line_of_business_table(cursor):
    sql = """
        CREATE TABLE IF NOT EXISTS ramos_atividade (
            id INT AUTO_INCREMENT PRIMARY KEY,
            descricao VARCHAR(100) NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """
    migrations.execute_with_migration(sql, "create_ramos_atividade_table", cursor)


def _create_company_table(cursor):
    sql = """
        CREATE TABLE IF NOT EXISTS empresas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            razao_social VARCHAR(150) NOT NULL,
            nome_fantasia VARCHAR(150),
            cnpj CHAR(14) NOT NULL UNIQUE,
            ie CHAR(20),
            endereco VARCHAR(255),
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            ramos_atividade_id INT NULL, 
            FOREIGN KEY (ramos_atividade_id) REFERENCES ramos_atividade(id) ON DELETE SET NULL,
            INDEX idx_empresas_cnpj (cnpj)
        )
    """
    migrations.execute_with_migration(sql, "create_empresas_table", cursor)


def _create_product_table(cursor):
    sql = """
        CREATE TABLE IF NOT EXISTS produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL,
            preco DECIMAL(10, 2) NOT NULL,
            unidade VARCHAR(10) NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_produtos_nome (nome)
        )
    """
    migrations.execute_with_migration(sql, "create_produtos_table", cursor)


def _create_purchase_table(cursor):
    sql = """
        CREATE TABLE IF NOT EXISTS compras (
            id INT AUTO_INCREMENT PRIMARY KEY,
            empresa_id INT,
            chave_acesso_nfce CHAR(44) NOT NULL UNIQUE,
            total_compra DECIMAL(10, 2) NOT NULL,
            desconto DECIMAL(10, 2) DEFAULT 0,
            valor_pago DECIMAL(10, 2) NOT NULL,
            forma_pagamento VARCHAR(50) NOT NULL,
            data_emissao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_autorizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            situacao CHAR(20) NOT NULL,
            danfe_numero CHAR(20),
            danfe_serie CHAR(10),
            protocolo CHAR(20), 
            hash_arquivo VARCHAR(64),    
            ramos_atividade_id INT NULL, 
            FOREIGN KEY (ramos_atividade_id) REFERENCES ramos_atividade(id) ON DELETE SET NULL,           
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            INDEX idx_compras_hash_arquivo (hash_arquivo)
        )
    """
    migrations.execute_with_migration(sql, "create_compras_table", cursor)


def _create_purchase_items_table(cursor):
    sql = """
        CREATE TABLE IF NOT EXISTS compras_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            compra_id INT,
            produto_id INT,
            quantidade DECIMAL(10, 5) NOT NULL, 
            unidade VARCHAR(10) NOT NULL,           
            preco DECIMAL(10, 2) NOT NULL,
            desconto DECIMAL(10, 2) DEFAULT 0,
            total DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE SET NULL 
        )
    """
    migrations.execute_with_migration(sql, "create_compras_items_table", cursor)


def setup_database(db):
    logger.info("Setting up the database...")
    cursor = db.cursor()

    migrations.create_table(cursor)
    _create_line_of_business_table(cursor)
    _create_company_table(cursor)
    _create_product_table(cursor)
    _create_purchase_table(cursor)
    _create_purchase_items_table(cursor)

    db.commit()
    logger.info("Database setup complete.")
