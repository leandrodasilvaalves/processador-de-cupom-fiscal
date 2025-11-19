import re
from entities.purchase_item import PurchaseItem
from entities.entitity import Entity
import pdfplumber


class Purchase(Entity):
    def __init__(self):
        self._company_id = None
        self._purchase_total = None
        self._discount = None
        self._paid_amount = None
        self._payment_method = None
        self._nfce_access_key = None
        self._issue_date = None
        self._authorization_date = None
        self._protocol = None
        self._situation = None
        self._danfe_number = None
        self._danfe_series = None
        self._file_hash = None
        self._line_of_business = None
        self._items = []

    @property
    def company_id(self) -> int | None:
        return self._company_id

    @company_id.setter
    def company_id(self, value: int):
        self._company_id = value

    @property
    def items(self) -> list[PurchaseItem]:
        return self._items

    @property
    def file_hash(self) -> str:
        return self._file_hash

    @file_hash.setter
    def file_hash(self, value: str):
        self._file_hash = value

    @property
    def line_of_business(self) -> str:
        return self._line_of_business

    @line_of_business.setter
    def line_of_business(self, value: str):
        self._line_of_business = value

    @property
    def purchase_total(self) -> float:
        return self._purchase_total

    @purchase_total.setter
    def purchase_total(self, value: float):
        if self._purchase_total is None:
            self._purchase_total = self._to_float(
                self._extract(value, r"Valor Total dos Produtos \(R\$\)\s*([\d,.]+)")
            )

    @property
    def discount(self) -> float:
        return self._discount

    @discount.setter
    def discount(self, value: float):
        if self._discount is None:
            self._discount = self._to_float(
                self._extract(value, r"Valor Descontos \(R\$\)\s*([\d,.]+)")
            )

    @property
    def paid_amount(self) -> float:
        return self._paid_amount

    @paid_amount.setter
    def paid_amount(self, value: float):
        if self._paid_amount is None:
            self._paid_amount = self._to_float(
                self._extract(value, r"Valor Pago \(R\$\)\s*([\d,.]+)")
            )

    @property
    def payment_method(self) -> str:
        return self._payment_method

    @payment_method.setter
    def payment_method(self, value: str):
        if self._payment_method is None:
            self._payment_method = self._extract(
                value, r"Forma Pagamento\s*([\w\s]+)\n"
            )

    @property
    def nfce_access_key(self) -> str:
        return self._nfce_access_key

    @nfce_access_key.setter
    def nfce_access_key(self, value: str):
        if self._nfce_access_key is None:
            self._nfce_access_key = self._extract(
                value, r"CHAVE DE ACESSO NFC-e\s*([\d\s]+)"
            )

    @property
    def issue_date(self) -> str:
        return self._issue_date

    @issue_date.setter
    def issue_date(self, value: str):
        if self._issue_date is None:
            self._issue_date = self._extract(value, r"Data de Emissão:\s*([\d/\s:]+)")

    @property
    def authorization_date(self) -> str:
        return self._authorization_date

    @authorization_date.setter
    def authorization_date(self, value: str):
        if self._authorization_date is None:
            self._authorization_date = self._extract(
                value, r"Data de Autorização:\s*([\d/\s:]+)"
            )

    @property
    def protocol(self) -> str:
        return self._protocol

    @protocol.setter
    def protocol(self, value: str):
        if self._protocol is None:
            self._protocol = self._extract(value, r"Protocolo:\s*(\d+)")

    @property
    def situation(self) -> str:
        return self._situation

    @situation.setter
    def situation(self, value: str):
        if self._situation is None:
            self._situation = self._extract(value, r"Situação:\s*(\w+)")

    @property
    def danfe_number(self) -> str:
        return self._danfe_number

    @danfe_number.setter
    def danfe_number(self, value: str):
        if self._danfe_number is None:
            self._danfe_number = self._extract(value, r"NÚMERO:\s*(\d+)")

    @property
    def danfe_series(self) -> str:
        return self._danfe_series

    @danfe_series.setter
    def danfe_series(self, value: str):
        if self._danfe_series is None:
            self._danfe_series = self._extract(value, r"SÉRIE:\s*(\d+)")

    def append_items(self, text: str):
        pattern = re.compile(
            r"\s*(\d{3})\s+(.+?)\s+([\d.,]+)\s+(\w+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)"
        )
        for match in pattern.finditer(text):
            self._items.append(PurchaseItem(match.groups()))

    def load(self, text: str):
        self.purchase_total = text
        self.discount = text
        self.paid_amount = text
        self.payment_method = text
        self.nfce_access_key = text
        self.issue_date = text
        self.authorization_date = text
        self.protocol = text
        self.situation = text
        self.danfe_number = text
        self.danfe_series = text
        self.append_items(text)


if __name__ == "__main__":
    purchase = Purchase()
    with pdfplumber.open(
        "/home/leandro/workspace/python/processador-de-cupom-fiscal/pdf-files/pending/NFC-e Consulta para dispositivos móveis copy.pdf"
    ) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            purchase.load(text)

    with pdfplumber.open(
        "/home/leandro/workspace/python/processador-de-cupom-fiscal/pdf-files/pending/NFC-e Consulta para dispositivos móveis-7.pdf"
    ) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            purchase.load(text)

    print(purchase.to_json())
    print("total itens:", len(purchase.items))
