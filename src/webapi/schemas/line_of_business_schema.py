
from pydantic import BaseModel

class LineOfBusiness(BaseModel):
    """Modelo Pydantic para a criação/atualizar um Ramo de Atividade."""
    descricao: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "descricao": "Supermercado"
            }
        }