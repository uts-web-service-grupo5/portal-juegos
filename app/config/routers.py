from app.api import user_api
from app.api import ad_usuarios_api
from app.api import catalogo_api

ROUTERS = [user_api.router, ad_usuarios_api.router, catalogo_api.router]
