from pydantic import BaseModel, Field

from app.domain.subscription_model import PlanType


class CatalogAccessRequest(BaseModel):
    id_cliente: int = Field(..., gt=0)


class GameItem(BaseModel):
    id_videojuego: int
    nombre_juego: str
    restriccion_edad: int
    acceso_plan: str


class CatalogAccessResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None


class GameInfoRequest(BaseModel):
    id_videojuego: int = Field(..., gt=0)


class GameInfoResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None
