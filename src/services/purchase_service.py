from database import db_purchase, db_product


def process(db, data, company_id, file_hash):
    data['emissor']['empresa_id'] = company_id
    data['emissor']['hash_arquivo'] = file_hash
    data['emissor']['total_compra'] = float(data['totais']['total_compra'])
    data['emissor']['desconto'] = float(data['totais']['desconto'])
    data['emissor']['valor_pago'] = float(data['totais']['valor_pago'])
    data['emissor']['forma_pagamento'] = data['totais']['forma_pagamento']

    purchase_id = db_purchase.insert(db, data['emissor'])
    return purchase_id

def process_items(db, items, purchase_id):
    for item in items:
        product = db_product.get_by_name(db, item['compra_id'])
        item['compra_id'] = purchase_id
        item['quantidade'] = float(item['quantidade'])
        item['unidade'] = item['unidade']
        item['preco'] = float(item['preco'])
        if 'desconto' in item:
            item['desconto'] = float(item['desconto'])
       
        db_purchase.insert_item(db, item)
