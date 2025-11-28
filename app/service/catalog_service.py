from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.catalog_model import (
    CatalogAccessRequest,
    CatalogAccessResponse,
    GameInfoRequest,
    GameInfoResponse,
)
from app.repository.catalog_repository import CatalogRepository
from app.repository.subscription_repository import SubscriptionRepository
from app.repository.user_repository import UserRepository


class CatalogService:
    def __init__(self, cat_db: Session, user_db: Session, sub_db: Session):
        self.catalog_repo = CatalogRepository(cat_db)
        self.user_repo = UserRepository(user_db)
        self.sub_repo = SubscriptionRepository(sub_db)

    def acceso_catalogo(self, req: CatalogAccessRequest) -> CatalogAccessResponse:
        # Cliente
        cliente = self.user_repo.get_user_by_id(req.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        # Calcular edad a partir de fecha_nac
        today = date.today()
        edad = today.year - cliente.fecha_nac.year - (
            (today.month, today.day) < (cliente.fecha_nac.month, cliente.fecha_nac.day)
        )

        # Suscripción
        try:
            subs = self.sub_repo.get_active_by_client(req.id_cliente)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=502,
                detail="No fue posible obtener los datos necesarios",
            )

        if not subs or subs.estado != "activo":
            raise HTTPException(
                status_code=403,
                detail="El cliente no tiene una suscripción activa o válida para acceder al catálogo",
            )

        # Juegos filtrados
        try:
            juegos = self.catalog_repo.get_games_for(subs.plan, edad)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=502,
                detail="No fue posible obtener los datos necesarios",
            )

        juegos_data = [
            {
                "id_videojuego": g.id,
                "nombre_juego": g.nombre_juego,
                "restriccion_edad": g.restriccion_edad,
                "acceso_plan": g.acceso_plan,
            }
            for g in juegos
        ]

        return CatalogAccessResponse(
            message="Catálogo obtenido exitosamente",
            data={
                "cliente": {
                    "id_cliente": req.id_cliente,
                    "edad": edad,
                    "plan": subs.plan,
                },
                "juegos_disponibles": juegos_data,
            },
            success=True,
            error_code=None,
            details=None,
        )

    def informacion_juego(self, req: GameInfoRequest) -> GameInfoResponse:
        try:
            game = self.catalog_repo.get_by_id(req.id_videojuego)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=500,
                detail="Se produjo un error al obtener la información del videojuego",
            )

        if not game:
            raise HTTPException(
                status_code=404,
                detail="El ID de videojuego proporcionado no existe en el catálogo",
            )

        return GameInfoResponse(
            message="Solicitud de datos de juego fue un éxito",
            data={
                "id_videojuego": game.id,
                "nombre_juego": game.nombre_juego,
                "descripcion": game.descripcion,
                "genero": game.genero,
                "restriccion_edad": f"{game.restriccion_edad}+",
            },
            success=True,
            error_code=None,
            details=None,
        )
