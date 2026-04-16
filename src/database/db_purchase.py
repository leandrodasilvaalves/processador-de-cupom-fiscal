import os

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from entities.purchase import Purchase
from entities.purchase_item import PurchaseItem
from helpers import datetime_helper as dth

tracer = trace.get_tracer(__name__)


def get_by_hash_file(db, hash_file):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_by_hash_file") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM compras WHERE hash_arquivo = %s", (hash_file,))
            return cursor.fetchone()
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_by_nfce(db, access_key: str):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_by_nfce") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM compras WHERE chave_acesso_nfce = %s", (access_key,))
            return cursor.fetchone()
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_all_purchases(db):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_all_purchases") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT
                    c.id, c.total_compra, c.desconto,
                    c.valor_pago, c.forma_pagamento,
                    e.nome_fantasia, e.razao_social,
                    e.endereco,
                    ra.id as ra_id,
                    ra.descricao as ramo_atividade
                FROM compras c
                LEFT JOIN empresas e ON e.id = c.empresa_id
                LEFT JOIN ramos_atividade ra ON ra.id = c.ramos_atividade_id
            """
            )
            purchases = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in purchases]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_by_company(db, company_id):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_by_company") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT
                    c.id, c.total_compra, c.desconto,
                    c.valor_pago, c.forma_pagamento,
                    e.nome_fantasia, e.razao_social
                FROM compras c
                LEFT JOIN empresas e ON e.id = c.empresa_id
                WHERE empresa_id = %s
            """,
                (company_id,),
            )
            purchases = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in purchases]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def get_items(db, purchase_id):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.get_items") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "SELECT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """
                SELECT
                    ci.id, p.nome as produto, p.id as pid,
                    ci.quantidade, ci.preco, ci.total, ci.unidade
                FROM compras_items ci
                LEFT JOIN produtos p ON p.id = ci.produto_id
                WHERE ci.compra_id = %s
            """,
                (purchase_id,),
            )
            items = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in items]
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def insert(db, purchase: Purchase):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.insert") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "INSERT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """INSERT INTO compras (empresa_id, chave_acesso_nfce, total_compra,
                    desconto, valor_pago, forma_pagamento, data_emissao,
                    data_autorizacao, situacao, danfe_numero, danfe_serie, protocolo,
                    hash_arquivo, ramos_atividade_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    purchase.company_id,
                    purchase.nfce_access_key,
                    purchase.purchase_total,
                    purchase.discount,
                    purchase.paid_amount,
                    purchase.payment_method,
                    dth.parse_datetime(purchase.issue_date),
                    dth.parse_datetime(purchase.authorization_date),
                    purchase.situation,
                    purchase.danfe_number,
                    purchase.danfe_series,
                    purchase.protocol,
                    purchase.file_hash,
                    purchase.line_of_business,
                ),
            )
            db.commit()
            return cursor.lastrowid
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def insert_item(db, item: PurchaseItem):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.insert_item") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "INSERT")
        try:
            cursor = db.cursor()
            cursor.execute(
                """INSERT INTO compras_items
                    (compra_id, produto_id, quantidade, preco, total, unidade)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (
                    item.purchase_id,
                    item.product_id,
                    item.quantity,
                    item.price,
                    item.total,
                    item.unity,
                ),
            )
            db.commit()
            return
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise


def update_all_line_of_business(db):
    db_name = os.environ.get("MYSQL_DATABASE", "unknown")
    with tracer.start_as_current_span("db.update_all_line_of_business") as span:
        span.set_attribute("db.system", "mysql")
        span.set_attribute("db.name", db_name)
        span.set_attribute("db.operation", "UPDATE")
        try:
            cursor = db.cursor()
            cursor.execute(
                """
                    UPDATE compras c
                    SET ramos_atividade_id = (
                        SELECT e.ramos_atividade_id
                        FROM empresas e
                        WHERE e.id = c.empresa_id
                    )
                    WHERE c.ramos_atividade_id IS NULL;
                """
            )
            db.commit()
            return cursor.rowcount
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.set_attribute("error.message", str(e))
            raise
