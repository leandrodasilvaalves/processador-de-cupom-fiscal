from database import db_purchase

def process(db, data, company_id, file_hash):
    data['Emissor']['EmpresaID'] = company_id
    data['Emissor']['HashArquivo'] = file_hash
    data['Emissor']['TotalCompra'] = float(data['Totais']['TotalCompra'])
    data['Emissor']['Desconto'] = float(data['Totais']['Desconto'])
    data['Emissor']['ValorPago'] = float(data['Totais']['ValorPago'])
    data['Emissor']['FormaPagamento'] = data['Totais']['FormaPagamento']

    purchase_id = db_purchase.insert(db, data['Emissor'])
    return purchase_id

