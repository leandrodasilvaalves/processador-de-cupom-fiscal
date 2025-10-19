def get_by_name(db, name):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE nome = %s", (name,))
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))

def insert(db, product):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO produtos (nome, preco, unidade) 
           VALUES (%s, %s, %s)""",
        (product['nome'], float(product['preco']), product['unidade'])
    )
    db.commit()
    return cursor.lastrowid