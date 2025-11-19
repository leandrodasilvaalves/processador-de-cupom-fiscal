from database import db_product
from entities.Product import Product
from entities.purchase_item import PurchaseItem


def process(db, item:PurchaseItem) -> Product:
    product = db_product.get_by_name(db, item.description)
    if product:
        return product

    product = Product(item)
    
    id = db_product.insert(db, product)
    product.with_id(id)
    return product