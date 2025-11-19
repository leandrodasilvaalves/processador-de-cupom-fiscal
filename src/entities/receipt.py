from entities.company import Company
from entities.entitity import Entity
from entities.purchase import Purchase


class Receipt(Entity):
    def __init__(self, company: Company, purchase: Purchase):
        self.company = company
        self.purchase = purchase

    def with_file_hash(self, hash: str):
        self.purchase.file_hash = hash

    def with_line_of_business(self, id: int | None):
        if id is not None:
            self.company.line_of_business = id
            self.purchase.line_of_business = id

    def with_company(self, id: int):
        self.company.id = id
        self.purchase.company_id = id
