from database import db_purchase
from entities.purchase import Purchase
from entities.purchase_item import PurchaseItem
from services import product_service


def process(db, purchase: Purchase):
    purchase_id = db_purchase.insert(db, purchase)
    
    for item in purchase.items:
        product = product_service.process(db, item)
        item.with_product(int(product.id))
        item.with_purchase(int(purchase_id))
        db_purchase.insert_item(db, item)