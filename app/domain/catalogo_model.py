from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


# ENTRADA (REQUEST)


class AccesoCatalogoRequest(BaseModel):

    id_cliente: int

    class Config:
        json_schema_extra = {
            "example": {
                "id_cliente": 2
            }
        }


# SALIDA (RESPONSE)


class VideojuegoInfo(BaseModel):

    id_videojuego: int
    nombre_juego: str
    restriccion_edad: str
    acceso_plan: str

    class Config:
        from_attributes = True


class CatalogoData(BaseModel):

    id_cliente: int
    plan: str
    estado_suscripcion: str
    edad_cliente: int
    videojuegos_disponibles: List[VideojuegoInfo]


class DetallesError(BaseModel):

    descripcion: str
    timestamp: str


class APIResponse(BaseModel):

    message: str
    data: Optional[CatalogoData | dict] = {}
    success: bool
    error_code: Optional[int] = None
    details: Optional[DetallesError | dict] = None

    class Config:
        json_schema_extra = {
            "example_success": {
                "message": "Catálogo obtenido exitosamente",
                "data": {
                    "id_cliente": 2,
                    "plan": "Plata",
                    "estado_suscripcion": "activo",
                    "edad_cliente": 30,
                    "videojuegos_disponibles": [
                        {
                            "id_videojuego": 1,
                            "nombre_juego": "Minecraft",
                            "restriccion_edad": "7+",
                            "acceso_plan": "Bronce"
                        },
                        {
                            "id_videojuego": 2,
                            "nombre_juego": "FIFA 25",
                            "restriccion_edad": "12+",
                            "acceso_plan": "Plata"
                        }
                    ]
                },
                "success": True,
                "error_code": None,
                "details": None
            },
            "example_error": {
                "message": "Acceso denegado al catálogo",
                "data": {},
                "success": False,
                "error_code": 403,
                "details": {
                    "descripcion": "El cliente no tiene una suscripción activa o válida para acceder al catálogo",
                    "timestamp": "2025-11-21T23:30:00Z"
                }
            }
        }
