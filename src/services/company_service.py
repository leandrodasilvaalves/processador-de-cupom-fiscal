from database import db_company
from entities.company import Company
from helpers.string_helper import extract_numbers
from typing import Optional, Tuple


def process(db: db_company, new_company: Company) -> Tuple[int, Optional[int]]:
    cnpj = extract_numbers(new_company.cnpj)
    company = db_company.get_by_cnpj(db, cnpj)
    
    if company is None:
        return (db_company.insert(db, new_company), None)

    return (company[0], company[8])
