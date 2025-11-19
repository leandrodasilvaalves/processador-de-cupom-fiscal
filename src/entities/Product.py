from entities.entitity import Entity
from entities.purchase_item import PurchaseItem
from typing import Optional


class Product(Entity):
    def __init__(self, item: Optional['PurchaseItem'] = None):
        if item:
            self.name = item.description
            self.price = item.price
            self.unity = item.unity
        self.id = None

    def with_id(self, id: int):
        self.id = id

    @classmethod
    def from_dict(cls, data: dict):
        product = cls()
        product.name = data.get("nome")
        product.price = float(data.get("preco"))
        product.unity = data.get("unidade")
        product.id = data.get("id")
        return product