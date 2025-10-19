from helpers import datetime_helper as dth

def get_by_hash_file(db, hash_file):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM compras WHERE hash_arquivo = %s", (hash_file,))
    return cursor.fetchone()


def get_by_company(db, company_id):
    cursor = db.cursor()
    cursor.execute(""" 
        SELECT 
            c.id, c.total_compra, c.desconto, 
            c.valor_pago, c.forma_pagamento,
            e.nome_fantasia, e.razao_social
        FROM compras c 
        LEFT JOIN empresas e ON e.id = c.empresa_id
        WHERE empresa_id = %s
    """, (company_id,))
    purchases =  cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in purchases]


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
        """INSERT INTO compras_items 
            (compra_id, produto_id, quantidade, preco, total, unidade) 
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (
            item['compra_id'],
            item['produto_id'],
            item['quantidade'],
            item['preco'],
            item['total'],
            item['unidade']
        )
    )
    db.commit()
    return