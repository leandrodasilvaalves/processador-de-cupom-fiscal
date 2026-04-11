import os

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from entities.company import Company
from helpers.string_helper import extract_numbers

tracer = trace.get_tracer(__name__)


def get_all_companies(db):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_all_companies") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT 
                    e.Id, e.nome_fantasia, e.razao_social, e.cnpj, 
                    e.ramos_atividade_id, 
                    ra.descricao as ramos_atividade,
                    e.endereco
                FROM empresas e LEFT JOIN ramos_atividade ra 
                ON ra.id = e.ramos_atividade_id;
            """
            )
            companies = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in companies]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_all_companies_without_line_of_business(db):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_all_companies_without_line_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
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
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_by_cnpj(db, cnpj: str):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_by_cnpj") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM empresas WHERE cnpj = %s", (cnpj,))
            return cursor.fetchone()
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def insert(db, company: Company):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.insert") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "INSERT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """INSERT INTO empresas (razao_social, nome_fantasia, cnpj, ie, endereco) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (
                    company.corporate_name,
                    company.trade_name,
                    extract_numbers(company.cnpj),
                    extract_numbers(company.ie),
                    company.address,
                ),
            )
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def update_company_activity_branch(db, company_id: int, ramo_atividade_id: int):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.update_company_activity_branch") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "UPDATE")
        try:
            cursor = db.cursor()
            cursor.execute(
                """UPDATE empresas 
                   SET ramos_atividade_id = %s 
                   WHERE id = %s""",
                (ramo_atividade_id, company_id),
            )
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise
