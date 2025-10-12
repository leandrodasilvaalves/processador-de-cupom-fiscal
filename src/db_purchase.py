def get_by_hash_file(db, hash_file):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Compras WHERE HashArquivo = %s", (hash_file,))
    return cursor.fetchone()

def insert(db, purchase):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO Compras (EmpresaID, ChaveAcessoNFCe, ValorTotal, 
            ValorDescontos, ValorPago, FormaPagamento, DataEmissao, 
            DataAutorizacao, Situacao, DanfeNumero, DanfeSerie, Protocolo, HashArquivo) 
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            purchase['EmpresaID'],
            purchase['ChaveAcessoNFCe'],
            purchase['ValorTotal'],
            purchase['ValorDescontos'],
            purchase['ValorPago'],
            purchase['FormaPagamento'],
            purchase['DataEmissao'],
            purchase['DataAutorizacao'],
            purchase['Situacao'],
            purchase.get('DanfeNumero'),
            purchase.get('DanfeSerie'),
            purchase.get('Protocolo'),
            purchase['HashArquivo']
        )
    )
    db.commit()
    return cursor.lastrowid


def insert_item(db, item):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO ItensCompra (CompraID, ProdutoID, Quantidade, Preco, PrecoTotal) 
           VALUES (%s, %s, %s, %s, %s)""",
        (
            item['CompraID'],
            item['ProdutoID'],
            item['Quantidade'],
            item['Preco'],
            item['PrecoTotal']
        )
    )
    db.commit()
    return cursor.lastrowid