from sqlalchemy.orm import Session
from app.repository.catalogo_repository import CatalogoRepository
from app.domain.catalogo_model import (
    AccesoCatalogoRequest,
    APIResponse,
    CatalogoData,
    VideojuegoInfo,
    DetallesError
)
from fastapi import HTTPException
from datetime import datetime
from typing import List


class CatalogoService:

    def __init__(self, db: Session):
        self.repository = CatalogoRepository(db)

    def obtener_catalogo(self, request: AccesoCatalogoRequest) -> APIResponse:

        #  Cliente existe
        cliente = self.repository.get_cliente_by_id(request.id_cliente)

        if not cliente:
            raise HTTPException(
                status_code=404,
                detail={
                    "message": "Cliente no encontrado",
                    "data": {},
                    "success": False,
                    "error_code": 404,
                    "details": {
                        "descripcion": f"No existe un cliente con ID {request.id_cliente}",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )

        # Suscripción existe
        suscripcion = self.repository.get_suscripcion_by_cliente(
            request.id_cliente)

        if not suscripcion:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 403,
                    "details": {
                        "descripcion": "El cliente no tiene una suscripción válida para acceder al catálogo",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )

        #  Suscripción está activa
        if suscripcion.estado != "activo":
            raise HTTPException(
                status_code=403,
                detail={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 403,
                    "details": {
                        "descripcion": "El cliente no tiene una suscripción activa o válida para acceder al catálogo",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )

        #  Obtener videojuegos según plan
        videojuegos_plan = self.repository.get_videojuegos_by_plan(
            suscripcion.plan)

        if not videojuegos_plan:
            raise HTTPException(
                status_code=502,
                detail={
                    "message": "Error al obtener catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 502,
                    "details": {
                        "descripcion": "No fue posible obtener los datos necesarios",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
            )

        # filtrar por edad
        edad_cliente = self.repository.calcular_edad(cliente.fecha_nac)
        videojuegos_filtrados = self._filtrar_por_edad(
            videojuegos_plan, edad_cliente)

       # respuesta exitosa

        videojuegos_info = [
            VideojuegoInfo(
                id_videojuego=juego.id_videojuego,
                nombre_juego=juego.nombre_juego,
                restriccion_edad=juego.restriccion_edad,
                acceso_plan=juego.acceso_plan
            )
            for juego in videojuegos_filtrados
        ]

        catalogo_data = CatalogoData(
            id_cliente=request.id_cliente,
            plan=suscripcion.plan,
            estado_suscripcion=suscripcion.estado,
            edad_cliente=edad_cliente,
            videojuegos_disponibles=videojuegos_info
        )

        return APIResponse(
            message="Catálogo obtenido exitosamente",
            data=catalogo_data,
            success=True,
            error_code=None,
            details=None
        )

    def _filtrar_por_edad(self, videojuegos: List, edad_cliente: int) -> List:

        videojuegos_permitidos = []

        for juego in videojuegos:
            restriccion = juego.restriccion_edad

            edad_minima = int(restriccion.replace("+", ""))

            if edad_cliente >= edad_minima:
                videojuegos_permitidos.append(juego)

        return videojuegos_permitidos
