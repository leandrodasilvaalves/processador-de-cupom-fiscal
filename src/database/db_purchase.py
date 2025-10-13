from helpers import datetime_helper as dth

def get_by_hash_file(db, hash_file):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Compras WHERE HashArquivo = %s", (hash_file,))
    return cursor.fetchone()

def insert(db, purchase):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO Compras (EmpresaID, ChaveAcessoNFCe, TotalCompra, 
            Desconto, ValorPago, FormaPagamento, DataEmissao, 
            DataAutorizacao, Situacao, DanfeNumero, DanfeSerie, Protocolo, HashArquivo) 
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
        (
            purchase['EmpresaID'],
            purchase['ChaveAcessoNFCe'],
            purchase['TotalCompra'],
            purchase['Desconto'],
            purchase['ValorPago'],
            purchase['FormaPagamento'],
            dth.parse_datetime(purchase['DataEmissao']),
            dth.parse_datetime(purchase['DataAutorizacao']),
            purchase['Situacao'],
            purchase['DanfeNumero'],
            purchase['DanfeSerie'],
            purchase['Protocolo'],
            purchase['HashArquivo']
        )
    )
    db.commit()
    return cursor.lastrowid


def insert_item(db, item):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO ItensCompra (CompraID, ProdutoID, Quantidade, Preco) 
           VALUES (%s, %s, %s, %s)""",
        (
            item['CompraID'],
            item['ProdutoID'],
            item['Quantidade'],
            item['Preco']
        )
    )
    db.commit()
    return cursor.lastrowid