import os

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from entities.Product import Product

tracer = trace.get_tracer(__name__)


def get_by_name(db, name) -> Product:
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_by_name") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM produtos WHERE nome = %s", (name,))
            row = cursor.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cursor.description]
            product = dict(zip(columns, row))
            return Product.from_dict(product)
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def insert(db, product: Product):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.insert") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "INSERT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """INSERT INTO produtos (nome, preco, unidade)
                   VALUES (%s, %s, %s)""",
                (product.name, product.price, product.unity),
            )
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise
