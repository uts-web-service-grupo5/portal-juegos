from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.service.catalogo_service import CatalogoService
from app.domain.catalogo_model import (
    AccesoCatalogoRequest,
    APIResponse
)

router = APIRouter(prefix="/api/v1/catalogo", tags=["Catálogo"])


def get_db():
    """Dependencia para obtener sesión de base de datos"""
    db = SessionLocal()

    # PRUEBA: ver si se conecta
    print("Conexión a DB:", db)

    try:
        yield db
    finally:
        db.close()


@router.post(
    "/acceso-catalogo",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener catálogo de videojuegos",
    description="""
    Obtiene el catálogo de videojuegos disponibles según:
    - Plan de suscripción del cliente (Bronce, Plata, Oro)
    - Edad del cliente (restricciones 7+, 12+, 16+, 18+)
    - Estado de la suscripción (debe estar activa)
    """
)
def acceso_catalogo(
    request: AccesoCatalogoRequest,
    db: Session = Depends(get_db)
) -> APIResponse:
    """
    Endpoint para consultar el catálogo de videojuegos

    **Casos de éxito:**
    - Cliente con suscripción activa recibe su catálogo filtrado

    **Casos de error:**
    - 404: Cliente no encontrado
    - 403: Suscripción inactiva o inexistente
    - 502: Error al obtener datos del catálogo
    """
    service = CatalogoService(db)
    return service.obtener_catalogo(request)
