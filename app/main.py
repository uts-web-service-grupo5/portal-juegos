from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config.routers import ROUTERS

app = FastAPI(
    title="Portal de juegos",
    description="API con arquitectura en capas",
    version="1.0.0",
)

for router in ROUTERS:
    app.include_router(router)


@app.get("/")
async def root():
    return {"message": "API funcionando correctamente"}


@app.get("/health")
async def health_check():
    return JSONResponse(status_code=200, content={"status": "healthy"})
