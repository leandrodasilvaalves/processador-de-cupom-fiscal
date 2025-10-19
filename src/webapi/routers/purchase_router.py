from fastapi import FastAPI, APIRouter
from database import db as _db, db_purchase

router = APIRouter(
    prefix="/compras",
    tags=["compras"],
)

@router.get("/")
async def listar_compras():
    db = _db.connect()
    compras = db_purchase.get_all_purchases(db)
    db.close()
    return {"dados": compras}

@router.get("/{id}/items")
async def listar_itens_compra(id: int):
    db = _db.connect()
    itens = db_purchase.get_items(db, id)
    db.close()
    return {"dados": itens}


@router.put("/ramos-atividade")
async def atualizar_todas_compras():
    db = _db.connect()
    count = db_purchase.update_all_line_of_business(db)
    db.close()
    return {"sucesso": True, "atualizadas": count}
