from database import db_company


def process(data):
    company = db_company.get_by_cnpj(data['CNPJ'])
    if company is None:
        db_company.insert(data)