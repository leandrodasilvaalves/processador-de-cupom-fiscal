from fastapi import FastAPI

app = FastAPI()

items = [
    {"nome": "maçã", "preco": 1.50},
    {"nome": "banana", "preco": 0.75},
    {"nome": "laranja", "preco": 1.20},
]

@app.get("/")
def home():
    """Endpoint de boas-vindas."""
    return {"mensagem": "Olá, Mundo! Sua primeira API com FastAPI está funcionando."}

# @app.get("/empresas")
# def listar_empresas():
#     empresas = db_company.get_all_companies(db)
#     return {"empresas": empresas}

@app.get("/items/{item_id}")
def buscar_item(item_id: int):
    """Busca um item específico pelo seu ID (índice na lista)."""
    try:
        return items[item_id]
    except IndexError:
        return {"erro": "Item não encontrado."}