from fastapi import APIRouter, status
from database import db as _db, db_line_of_business
from ..schemas.line_of_business_schema import LineOfBusiness

router = APIRouter(
    prefix="/ramos-de-atividade",
    tags=["ramos-de-atividade"],
)


@router.get("/")
async def listar_ramos_de_atividade():
    db = _db.connect()
    ramos = db_line_of_business.get_all_lines_of_business(db)
    db.close()
    return {"dados": ramos}


@router.get("/{ramo_id}")
async def obter_ramo_de_atividade(ramo_id: int):
    db = _db.connect()
    ramo = db_line_of_business.get_line_of_business_by_id(db, ramo_id)
    db.close()
    if ramo:
        return {"dados": ramo}
    return {"erro": "Ramo de atividade não encontrado."}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def criar_ramo_de_atividade(ramo: LineOfBusiness):
    db = _db.connect()
    description = ramo.descricao
    novo_id = db_line_of_business.insert_line_of_business(db, description)
    db.close()
    return {"sucesso": True, "dados": {"id": novo_id, "descricao": description}}


@router.put("/{ramo_id}")
async def atualizar_ramo_de_atividade(ramo_id: int, ramo: LineOfBusiness):
    db = _db.connect()
    description = ramo.descricao
    atualizado = db_line_of_business.update_line_of_business(db, ramo_id, description)
    db.close()
    if atualizado:
        return {"sucesso": True, "dados": {"id": ramo_id, "descricao": description}}
    return {"erro": "Ramo de atividade não encontrado."}


@router.delete("/{ramo_id}")
async def deletar_ramo_de_atividade(ramo_id: int):
    db = _db.connect()
    deletado = db_line_of_business.delete_line_of_business(db, ramo_id)
    db.close()
    if deletado:
        return {"sucesso": True}
    return {"erro": "Ramo de atividade não encontrado."}
