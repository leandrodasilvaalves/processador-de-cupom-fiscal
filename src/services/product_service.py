from database import db_product


def process(db, purchase_item):
    product = db_product.get_by_name(db, purchase_item["descricao"])
    if product:
        return product

    product = {
        "nome": purchase_item["descricao"],
        "preco": float(purchase_item["preco"]),
        "unidade": purchase_item["unidade"],
    }
    
    product_id = db_product.insert(db, product)
    product["id"] = product_id
    return product