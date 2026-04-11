import os

from opentelemetry import trace
from opentelemetry.trace import StatusCode

tracer = trace.get_tracer(__name__)


def insert_line_of_business(db, description):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.insert_line_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "INSERT")
        try:
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
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_all_lines_of_business(db):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_all_lines_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM ramos_atividade")
            lines = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in lines]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_line_of_business_by_id(db, ramo_id):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_line_of_business_by_id") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM ramos_atividade WHERE id = %s", (ramo_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def update_line_of_business(db, ramo_id, description):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.update_line_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "UPDATE")
        try:
            cursor = db.cursor()
            cursor.execute(
                "UPDATE ramos_atividade SET descricao = %s WHERE id = %s",
                (description, ramo_id),
            )
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def delete_line_of_business(db, ramo_id):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.delete_line_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "DELETE")
        try:
            cursor = db.cursor()
            cursor.execute("DELETE FROM ramos_atividade WHERE id = %s", (ramo_id,))
            db.commit()
            return cursor.rowcount > 0
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise
