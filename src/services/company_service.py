from database import db_company
from helpers.string_helper import extract_numbers

def process(db, data):
    cnpj = extract_numbers(data['cnpj'])
    company = db_company.get_by_cnpj(db, cnpj)
    if company is None:
        return (db_company.insert(db, data), None)

    return (company[0], company[8])