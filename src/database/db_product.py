def get_by_name(db, name):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Produtos WHERE Nome = %s", (name,))
    return cursor.fetchone()

def insert(db, product):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO Produtos (Nome, Preco) 
           VALUES (%s, %s)""",
        (product['Nome'], product['Preco'])
    )
    db.commit()
    return cursor.lastrowid