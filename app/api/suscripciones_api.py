from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.subscription_database import SessionLocal as SubSessionLocal
from app.user_database import SessionLocal as UserSessionLocal
from app.transaction_database import SessionLocal as TxSessionLocal
from app.domain.subscription_model import (
    SubscriptionAssignRequest,
    SubscriptionResponse,
    SubscriptionVerificationResponse,
    CancelSubscriptionResponse,
)
from app.service.subscription_service import SubscriptionService
from app.service.transaction_service import TransactionService
from app.service.user_service import UserService

router = APIRouter(prefix="/api/v1/suscripciones", tags=["Suscripciones"])


def get_sub_db():
    db = SubSessionLocal()
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


def get_tx_db():
    db = TxSessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/asignar",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Asignar plan de suscripción",
)
def asignar_suscripcion(
    payload: SubscriptionAssignRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    sub_db: Session = Depends(get_sub_db),
    user_db: Session = Depends(get_user_db),
    tx_db: Session = Depends(get_tx_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db, sub_db)
    tx_service = TransactionService(tx_db, user_db)
    sub_service = SubscriptionService(sub_db, user_db, tx_service)
    try:
        token_user_id = user_service.decode_token(token)
        if token_user_id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return sub_service.asignar(payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = "Error al asignar la suscripción"
        error_code = exc.status_code

        if exc.status_code == status.HTTP_400_BAD_REQUEST and "suscripción activa" in descripcion:
            message = "El cliente ya posee una suscripción activa"
            error_code = 400
        elif exc.status_code == status.HTTP_402_PAYMENT_REQUIRED:
            message = "Error al procesar el pago"
            error_code = 402
        elif exc.status_code == status.HTTP_404_NOT_FOUND:
            message = "Cliente no encontrado"
            error_code = 404
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            message = "Token requerido"
            error_code = 401
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            message = "Error al asignar la suscripción"
            error_code = 503

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


@router.get(
    "/cancelar/{id_cliente}",
    response_model=CancelSubscriptionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancelar suscripción",
)
def cancelar_suscripcion(
    id_cliente: int,
    authorization: str | None = Header(default=None, convert_underscores=False),
    sub_db: Session = Depends(get_sub_db),
    user_db: Session = Depends(get_user_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db, sub_db)
    sub_service = SubscriptionService(sub_db, user_db)
    try:
        token_user_id = user_service.decode_token(token)
        if token_user_id != id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return sub_service.cancelar(id_cliente)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = (
            "No aplica cancelación para plan gratuito"
            if exc.status_code == status.HTTP_403_FORBIDDEN
            else "No se pudo procesar la cancelación"
        )
        error_code = (
            400
            if exc.status_code == status.HTTP_400_BAD_REQUEST
            else 403
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


@router.get(
    "/verificacion/{id_cliente}",
    response_model=SubscriptionVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verificar estado de suscripción",
)
def verificar_suscripcion(
    id_cliente: int,
    authorization: str | None = Header(default=None, convert_underscores=False),
    sub_db: Session = Depends(get_sub_db),
    user_db: Session = Depends(get_user_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db, sub_db)
    sub_service = SubscriptionService(sub_db, user_db)
    try:
        token_user_id = user_service.decode_token(token)
        if token_user_id != id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return sub_service.verificar(id_cliente)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = "Error al consultar la suscripción"
        error_code = exc.status_code
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            message = "Cliente no encontrado" if "Cliente no" in descripcion else "El cliente no tiene suscripción registrada"
            error_code = 404
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            message = "Token requerido"
            error_code = 401
        elif exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            message = "Error al consultar la suscripción"
            error_code = 503
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            message = "Operación no permitida"
            error_code = 403

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
