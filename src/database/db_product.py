def get_by_name(db, name):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE nome = %s", (name,))
    return cursor.fetchone()

def insert(db, product):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO produtos (nome, preco) 
           VALUES (%s, %s)""",
        (product['nome'], product['preco'])
    )
    db.commit()
    return cursor.lastrowid