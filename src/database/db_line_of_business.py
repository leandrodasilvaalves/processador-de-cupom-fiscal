

def insert_line_of_business(db, description):
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO ramos_atividade (descricao) 
        VALUES (%s)
        """,
        (description,),
    )   
    db.commit()
    return cursor.lastrowid


def get_all_lines_of_business(db):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM ramos_atividade")
    lines = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in lines]


def get_line_of_business_by_id(db, ramo_id):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM ramos_atividade WHERE id = %s", (ramo_id,))
    row = cursor.fetchone()
    if row:
        columns = [desc[0] for desc in cursor.description]
        return dict(zip(columns, row))
    return None


def update_line_of_business(db, ramo_id, description):
    cursor = db.cursor()
    cursor.execute(
        "UPDATE ramos_atividade SET descricao = %s WHERE id = %s",
        (description, ramo_id),
    )
    db.commit()
    return cursor.rowcount > 0


def delete_line_of_business(db, ramo_id):
    cursor = db.cursor()
    cursor.execute("DELETE FROM ramos_atividade WHERE id = %s", (ramo_id,))
    db.commit()
    return cursor.rowcount > 0