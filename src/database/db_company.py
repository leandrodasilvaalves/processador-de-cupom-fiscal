from helpers.string_helper import extract_numbers


def get_all_companies(db):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            e.Id, e.nome_fantasia, e.razao_social, e.cnpj, e.ramos_atividade_id, 
            ra.descricao as ramos_atividade 
        FROM empresas e LEFT JOIN ramos_atividade ra 
        ON ra.id = e.ramos_atividade_id;
    """
    )
    companies = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in companies]

def get_all_companies_without_line_of_business(db):
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT 
            e.Id, e.nome_fantasia, e.razao_social, e.cnpj 
        FROM empresas e 
        WHERE e.ramos_atividade_id IS NULL;
    """
    )
    companies = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in companies]


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
            company["razao_social"],
            company["nome_fantasia"],
            extract_numbers(company["cnpj"]),
            extract_numbers(company["ie"]),
            company["endereco"],
        ),
    )
    db.commit()
    return cursor.lastrowid

def update_company_activity_branch(db, company_id, ramo_atividade_id):
    cursor = db.cursor()
    cursor.execute(
        """UPDATE empresas 
           SET ramos_atividade_id = %s 
           WHERE id = %s""",
        (ramo_atividade_id, company_id),
    )
    db.commit()
    return cursor.rowcount > 0
