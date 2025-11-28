from app.api import user_api, ad_usuarios_api, suscripciones_api, transacciones_api

ROUTERS = [user_api.router, ad_usuarios_api.router, suscripciones_api.router, transacciones_api.router]
