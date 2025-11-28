from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.catalog_database import SessionLocal as CatSessionLocal
from app.user_database import SessionLocal as UserSessionLocal
from app.subscription_database import SessionLocal as SubSessionLocal
from app.domain.catalog_model import (
    CatalogAccessRequest,
    CatalogAccessResponse,
    GameInfoRequest,
    GameInfoResponse,
)
from app.service.catalog_service import CatalogService
from app.service.user_service import UserService

router = APIRouter(prefix="/api/v1/catalogo", tags=["Catalogo"])


def get_cat_db():
    db = CatSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_db():
    db = UserSessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sub_db():
    db = SubSessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/acceso-catalogo",
    response_model=CatalogAccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Acceso al catálogo",
)
def acceso_catalogo(
    payload: CatalogAccessRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    cat_db: Session = Depends(get_cat_db),
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db, sub_db)
    catalog_service = CatalogService(cat_db, user_db, sub_db)
    try:
        token_user_id = user_service.decode_token(token)
        if token_user_id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return catalog_service.acceso_catalogo(payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        if exc.status_code in (403, 404):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": exc.status_code,
                    "details": {"descripcion": descripcion},
                },
            )
        if exc.status_code == 502:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 502,
                    "details": {"descripcion": descripcion},
                },
            )
        if exc.status_code == 401:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 401,
                    "details": {"descripcion": descripcion},
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "Acceso denegado al catálogo",
                "data": {},
                "success": False,
                "error_code": exc.status_code,
                "details": {"descripcion": descripcion},
            },
        )


@router.post(
    "/informacion-juego",
    response_model=GameInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Información detallada de videojuego",
)
def informacion_juego(
    payload: GameInfoRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    cat_db: Session = Depends(get_cat_db),
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db, sub_db)
    catalog_service = CatalogService(cat_db, user_db, sub_db)
    try:
        # Solo validamos token, no se necesita id_cliente aquí, pero seguimos el mismo esquema.
        user_service.decode_token(token)
        return catalog_service.informacion_juego(payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        if exc.status_code == 404:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "No se encontró el videojuego solicitado",
                    "data": {},
                    "success": False,
                    "error_code": 404,
                    "details": {"descripcion": descripcion},
                },
            )
        if exc.status_code == 500:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "No se encontró el videojuego solicitado",
                    "data": {},
                    "success": False,
                    "error_code": 500,
                    "details": {"descripcion": descripcion},
                },
            )
        if exc.status_code == 401:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "Acceso denegado al catálogo",
                    "data": {},
                    "success": False,
                    "error_code": 401,
                    "details": {"descripcion": descripcion},
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "No se encontró el videojuego solicitado",
                "data": {},
                "success": False,
                "error_code": exc.status_code,
                "details": {"descripcion": descripcion},
            },
        )
