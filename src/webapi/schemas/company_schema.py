from pydantic import BaseModel

class CompanyUpdateLineOfBusiness(BaseModel):
    """Modelo Pydantic para atualizar uma Empresa."""
    ramo_atividade_id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "ramo_atividade_id": 1,
            }
        }