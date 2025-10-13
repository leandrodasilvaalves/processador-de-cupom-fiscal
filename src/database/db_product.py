def get_by_name(db, name):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE nome = %s", (name,))
    return cursor.fetchone()

def insert(db, product):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO produtos (nome, preco, unidade) 
           VALUES (%s, %s, %s)""",
        (product['nome'], float(product['preco']), product['unidade'])
    )
    db.commit()
    return cursor.lastrowid