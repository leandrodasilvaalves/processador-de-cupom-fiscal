from helpers.string_helper import extract_numbers

def get_by_cnpj(db, cnpj):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM Empresas WHERE CNPJ = %s", (cnpj,))
    return cursor.fetchone()


def insert(db, company):
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO Empresas (RazaoSocial, NomeFantasia, CNPJ, IE, Endereco) 
           VALUES (%s, %s, %s, %s, %s)""",
        (
            company['RazaoSocial'],
            company['NomeFantasia'],
            extract_numbers(company['CNPJ']),
            extract_numbers(company['IE']),
            company['Endereco']
        )
    )
    db.commit()
    return cursor.lastrowid