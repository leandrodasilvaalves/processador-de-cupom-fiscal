from entities.entitity import Entity


class PurchaseItem(Entity):
    def __init__(self, groups: tuple[str]):
        item, description, quantity, unity, price, discount, total = groups
        self.item = item.strip()
        self.description = description.strip()
        self.quantity = self._to_float(quantity)
        self.unity = unity.strip()
        self.price = self._to_float(price)
        self.discount = self._to_float(discount)
        self.total = self._to_float(total)
        self.product_id = None
        self.purchase_id = None

    def with_product(self, id: int):
        self.product_id = id

    def with_purchase(self, id: int):
        self.purchase_id = id
