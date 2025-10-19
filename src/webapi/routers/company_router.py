from fastapi import APIRouter
from database import db as _db, db_company, db_purchase
from ..schemas.company_schema import CompanyUpdateLineOfBusiness

router = APIRouter(
    prefix="/empresas",
    tags=["empresas"],
)

@router.get("/")
async def listar_empresas():
    db = _db.connect()
    empresas = db_company.get_all_companies(db)
    db.close()
    return {"dados": empresas}


@router.get("/sem-ramo-atividade")
async def listar_empresas_sem_ramo_atividade():
    db = _db.connect()
    empresas = db_company.get_all_companies_without_line_of_business(db)
    db.close()
    return {"dados": empresas}


@router.get("/{id}/compras/")
async def listar_compras_por_empresa(id: int):
    db = _db.connect()
    compras = db_purchase.get_by_company(db, id)
    db.close()
    return {"dados": compras}


@router.put("/{company_id}")
async def atualizar_ramo_atividade(company_id: int, company: CompanyUpdateLineOfBusiness):
    db = _db.connect()
    sucesso = db_company.update_company_activity_branch(db, company_id, company.ramo_atividade_id)
    db.close()
    return {"sucesso": sucesso}

