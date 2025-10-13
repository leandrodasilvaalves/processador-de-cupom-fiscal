from helpers import datetime_helper as dth

def get_by_hash_file(db, hash_file):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM compras WHERE hash_arquivo = %s", (hash_file,))
    return cursor.fetchone()

def insert(db, purchase):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO compras (empresa_id, chave_acesso_nfce, total_compra, 
            desconto, valor_pago, forma_pagamento, data_emissao, 
            data_autorizacao, situacao, danfe_numero, danfe_serie, protocolo, hash_arquivo) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            purchase['empresa_id'],
            purchase['chave_acesso_nfce'],
            purchase['total_compra'],
            purchase['desconto'],
            purchase['valor_pago'],
            purchase['forma_pagamento'],
            dth.parse_datetime(purchase['data_emissao']),
            dth.parse_datetime(purchase['data_autorizacao']),
            purchase['situacao'],
            purchase['danfe_numero'],
            purchase['danfe_serie'],
            purchase['protocolo'],
            purchase['hash_arquivo']
        )
    )
    db.commit()
    return cursor.lastrowid


def insert_item(db, item):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO compras_items (compra_id, produto_id, quantidade, preco) 
           VALUES (%s, %s, %s, %s)""",
        (
            item['compra_id'],
            item['produto_id'],
            item['quantidade'],
            item['preco']
        )
    )
    db.commit()
    return