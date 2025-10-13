from database import db_company
from helpers.string_helper import extract_numbers

def process(db, data):
    cnpj = extract_numbers(data['CNPJ'])
    company = db_company.get_by_cnpj(db, cnpj)
    if company is None:
        return db_company.insert(db, data)

    return company[0]