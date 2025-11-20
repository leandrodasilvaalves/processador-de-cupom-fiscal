from entities.entitity import Entity


class Company(Entity):

    def __init__(self):

        self._id = None
        self._cnpj = None
        self._ie = None
        self._corporate_name = None
        self._trade_name = None
        self._address = None
        self._line_of_business = None

    @property
    def id(self) -> int:
        return self._id

    @id.setter
    def id(self, value: int):
        self._id = value

    @property
    def cnpj(self) -> str:
        return self._cnpj

    @cnpj.setter
    def cnpj(self, value: str):
        if self._cnpj is None:
            self._cnpj = self._extract(
                value, r"CNPJ:\s*([\d./-]+)\s*\|\s*IE:\s*([\d.-]+)", 1
            )

    @property
    def ie(self) -> str:
        return self._ie

    @ie.setter
    def ie(self, value: str):
        if self._ie is None:
            self._ie = self._extract(
                value, r"CNPJ:\s*([\d./-]+)\s*\|\s*IE:\s*([\d.-]+)", 2
            )

    @property
    def corporate_name(self) -> str:
        return self._corporate_name

    @corporate_name.setter
    def corporate_name(self, value: str):
        if self._corporate_name is None:
            self._corporate_name = self._extract(value, r"RAZÃO SOCIAL:\s*(.+)")

    @property
    def trade_name(self) -> str:
        return self._trade_name

    @trade_name.setter
    def trade_name(self, value: str):
        if self._trade_name is None:
            self._trade_name = self._extract(value, r"NOME FANTASIA:\s*(.+)")

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str):
        if self._address is None:
            self._address = self._extract(value, r"ENDEREÇO:\s*(.+)\n")

    @property
    def line_of_business(self) -> int | None:
        return self._id

    @line_of_business.setter
    def line_of_business(self, value: int):
        self._line_of_business = value

    def load(self, text: str):
        self.cnpj = text
        self.ie = text
        self.corporate_name = text
        self.trade_name = text
        self.address = text
        