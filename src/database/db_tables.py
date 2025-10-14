from config.log_config import logger

def setup_database(db):
    logger.info("Setting up the database...")
    cursor = db.cursor()

    logger.info("Creating tables if they do not exist...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            razao_social VARCHAR(150) NOT NULL,
            nome_fantasia VARCHAR(150),
            cnpj CHAR(14) NOT NULL UNIQUE,
            ie CHAR(20),
            endereco VARCHAR(255)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nome VARCHAR(150) NOT NULL,
            preco DECIMAL(10, 2) NOT NULL,
            unidade VARCHAR(10) NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_produtos_nome (nome)
        )
    """)

    cursor.execute("""
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
            FOREIGN KEY (empresa_id) REFERENCES empresas(id),
            INDEX idx_compras_hash_arquivo (hash_arquivo)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compras_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            compra_id INT,
            produto_id INT,
            quantidade DECIMAL(10, 5) NOT NULL, 
            unidade VARCHAR(10) NOT NULL,           
            preco DECIMAL(10, 2) NOT NULL,
            desconto DECIMAL(10, 2) DEFAULT 0,
            total DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (compra_id) REFERENCES compras(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id)
        )
    """)