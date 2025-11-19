from entities.Product import Product


def get_by_name(db, name) -> Product:
    cursor = db.cursor()
    cursor.execute("SELECT * FROM produtos WHERE nome = %s", (name,))
    row = cursor.fetchone()
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    product = dict(zip(columns, row))
    return Product.from_dict(product)


def insert(db, product: Product):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO produtos (nome, preco, unidade) 
           VALUES (%s, %s, %s)""",
        (product.name, product.price, product.unity),
    )
    db.commit()
    return cursor.lastrowid
