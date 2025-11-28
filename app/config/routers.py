from app.api import user_api
from app.api import ad_usuarios_api

ROUTERS = [user_api.router, ad_usuarios_api.router]
