from helpers.string_helper import extract_numbers

def get_by_cnpj(db, cnpj):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM empresas WHERE cnpj = %s", (cnpj,))
    return cursor.fetchone()


def insert(db, company):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO empresas (razao_social, nome_fantasia, cnpj, ie, endereco) 
           VALUES (%s, %s, %s, %s, %s)""",
        (
            company['razao_social'],
            company['nome_fantasia'],
            extract_numbers(company['cnpj']),
            extract_numbers(company['ie']),
            company['endereco']
        )
    )
    db.commit()
    return cursor.lastrowid