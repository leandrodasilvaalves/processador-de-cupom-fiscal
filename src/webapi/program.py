from fastapi import FastAPI
from .routers import company_router, line_of_business_router, purchase_router

app = FastAPI(
    title="Processador de Cupom Fiscal",
    description="API para processar cupons fiscais e gerenciar empresas.",
    version="1.0.0.beta",
)

@app.get("/hc")
def home():
    return {"status": "Healthy"}

app.include_router(company_router.router)
app.include_router(line_of_business_router.router)
app.include_router(purchase_router.router)
