from database import db_purchase, db_product
from services import product_service


def process(db, data, company, file_hash):
    purchase = {}
    purchase['empresa_id'] = company[0]
    purchase['chave_acesso_nfce'] = data['rodape']['chave_acesso_nfce']
    purchase['total_compra'] = float(data['totais']['total_compra'])
    purchase['desconto'] = float(data['totais']['desconto'])
    purchase['valor_pago'] = float(data['totais']['valor_pago'])
    purchase['forma_pagamento'] = data['totais']['forma_pagamento']
    purchase['data_emissao'] = data['rodape']['data_emissao']
    purchase['data_autorizacao'] = data['rodape']['data_autorizacao']
    purchase['situacao'] = data['rodape']['situacao']
    purchase['danfe_numero'] = data['danfe']['numero']
    purchase['danfe_serie'] = data['danfe']['serie']
    purchase['protocolo'] = data['rodape']['protocolo']
    purchase['hash_arquivo'] = file_hash
    purchase['ramos_atividade_id'] = company[1]

    purchase_id = db_purchase.insert(db, purchase)
    return purchase_id


def process_items(db, items, purchase_id):
    for item in items:
        product = product_service.process(db, item)

        item['produto_id'] = product['id']
        item['compra_id'] = purchase_id
        item['quantidade'] = float(item['quantidade'])
        item['preco'] = float(item['preco'])
        item['total'] = float(item['total'])
        if 'desconto' in item:
            item['desconto'] = float(item['desconto'])
       
        db_purchase.insert_item(db, item)
