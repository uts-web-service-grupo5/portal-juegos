from app.api import user_api, suscripciones_api, transacciones_api, catalogo_api

ROUTERS = [
    user_api.router,
    suscripciones_api.router,
    transacciones_api.router,
    catalogo_api.router,
]
