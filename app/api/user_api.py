from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.user_database import SessionLocal as UserSessionLocal
from app.subscription_database import SessionLocal as SubSessionLocal
from app.domain.user_model import (
    DeleteRequest,
    DeleteResponse,
    LoginRequest,
    LoginResponse,
    RegistroResponse,
    UpdateRequest,
    UpdateResponse,
    UserCreate,
    UserRecord,
)
from app.service.user_service import UserService

router = APIRouter(prefix="/api/v1/cliente", tags=["Clientes"])


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
    "/registro",
    response_model=RegistroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente",
)
def registrar_cliente(user: UserCreate, user_db: Session = Depends(get_user_db), sub_db: Session = Depends(get_sub_db)):
    """Registra un nuevo cliente."""
    service = UserService(user_db, sub_db)
    try:
        return service.create_user(user)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        error_code = exc.status_code if exc.status_code != status.HTTP_503_SERVICE_UNAVAILABLE else 503
        message = (
            "Error en la validación de datos"
            if exc.status_code == status.HTTP_400_BAD_REQUEST
            else "No fue posible completar el registro"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": message,
                "data": {},
                "success": False,
                "error_code": error_code,
                "details": {"descripcion": descripcion},
            },
        )


@router.get("/{user_id}", response_model=UserRecord, summary="Obtener cliente")
def get_user(user_id: int, user_db: Session = Depends(get_user_db), sub_db: Session = Depends(get_sub_db)):
    """Obtiene un cliente por ID."""
    service = UserService(user_db, sub_db)
    return service.get_user(user_id)


@router.post(
    "/sesion",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Inicio de sesión de cliente",
)
def iniciar_sesion(
    credentials: LoginRequest,
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    """Inicia sesión de cliente."""
    service = UserService(user_db, sub_db)
    try:
        return service.login(credentials)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "Error al procesar inicio de sesión",
                "data": {},
                "success": False,
                "error_code": 403,
                "details": {"description": descripcion},
            },
        )


@router.patch(
    "/actualizar",
    response_model=UpdateResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar datos de cliente",
)
def actualizar_cliente(
    payload: UpdateRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    """Actualiza datos de cliente."""
    service = UserService(user_db, sub_db)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user_id = service.decode_token(token)
        return service.update_user(user_id, payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = (
            "No se pudo actualizar el/los campo(s)"
            if exc.status_code in {status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN}
            else "No se pudo procesar la solicitud"
        )
        error_code = (
            403
            if exc.status_code == status.HTTP_403_FORBIDDEN
            else exc.status_code if exc.status_code != status.HTTP_503_SERVICE_UNAVAILABLE else 503
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": message,
                "data": {},
                "success": False,
                "error_code": error_code,
                "details": {"description": descripcion},
            },
        )


@router.delete(
    "/eliminar",
    response_model=DeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Eliminar cuenta de cliente",
)
def eliminar_cliente(
    payload: DeleteRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    """Elimina la cuenta si no tiene plan activo."""
    service = UserService(user_db, sub_db)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        user_id = service.decode_token(token)
        return service.delete_user(user_id, payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = (
            "No se puede eliminar la cuenta"
            if exc.status_code == status.HTTP_403_FORBIDDEN
            else "No se pudo procesar la solicitud"
        )
        error_code = (
            403
            if exc.status_code == status.HTTP_403_FORBIDDEN
            else exc.status_code if exc.status_code != status.HTTP_503_SERVICE_UNAVAILABLE else 503
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": message,
                "data": {},
                "success": False,
                "error_code": error_code,
                "details": {"description": descripcion},
            },
        )
