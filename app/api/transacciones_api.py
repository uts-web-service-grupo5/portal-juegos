from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.transaction_database import SessionLocal as TxSessionLocal
from app.user_database import SessionLocal as UserSessionLocal
from app.subscription_database import SessionLocal as SubSessionLocal
from app.domain.transaction_model import (
    PaymentRequest,
    PaymentResponse,
    HistorialRequest,
)
from app.domain.payment_method_model import PaymentMethodRequest, PaymentMethodResponse
from app.service.transaction_service import TransactionService
from app.service.user_service import UserService
from app.service.payment_method_service import PaymentMethodService

router = APIRouter(prefix="/api/v1/transacciones", tags=["Transacciones"])
auth_scheme = HTTPBearer(scheme_name="BearerAuth")


def get_tx_db():
    db = TxSessionLocal()
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
    "/pago",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar pago de suscripción",
)
def procesar_pago(
    payload: PaymentRequest,
    credentials: HTTPAuthorizationCredentials = Security(auth_scheme),
    tx_db: Session = Depends(get_tx_db),
    user_db: Session = Depends(get_user_db),
):
    user_service = UserService(user_db)
    tx_service = TransactionService(tx_db, user_db)
    try:
        token_user_id = user_service.decode_token(credentials.credentials)
        if token_user_id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return tx_service.procesar_pago(payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = "Método de pago no encontrado" if exc.status_code == 404 else "Error al procesar el pago"
        error_code = (
            404
            if exc.status_code == 404
            else 402
            if exc.status_code == status.HTTP_402_PAYMENT_REQUIRED
            else exc.status_code
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": message,
                "data": None if exc.status_code == 404 else {},
                "success": False,
                "error_code": error_code,
                "details": {"descripcion": descripcion},
            },
        )

@router.get(
    "/renovacion/{id_cliente}",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar próxima renovación",
)
def obtener_renovacion(
    id_cliente: int,
    credentials: HTTPAuthorizationCredentials = Security(auth_scheme),
    tx_db: Session = Depends(get_tx_db),
    user_db: Session = Depends(get_user_db),
    sub_db: Session = Depends(get_sub_db),
):
    user_service = UserService(user_db)
    tx_service = TransactionService(tx_db, user_db, sub_db)
    try:
        token_user_id = user_service.decode_token(credentials.credentials)
        if token_user_id != id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return tx_service.obtener_renovacion(id_cliente)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = "Información de renovación obtenida exitosamente"
        error_code = exc.status_code
        if exc.status_code == 404:
            message = "Suscripción no encontrada"
            error_code = 404
        elif exc.status_code == 400:
            message = "Error al obtener renovación"
            error_code = 400
        elif exc.status_code == 401:
            message = "Token requerido"
            error_code = 401
        elif exc.status_code == 503:
            message = "Error al consultar la suscripción"
            error_code = 503
        elif exc.status_code == 403:
            message = "Operación no permitida"
            error_code = 403

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


@router.post(
    "/metodo-pago",
    response_model=PaymentMethodResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar/Actualizar método de pago",
)
def guardar_metodo_pago(
    payload: PaymentMethodRequest,
    credentials: HTTPAuthorizationCredentials = Security(auth_scheme),
    tx_db: Session = Depends(get_tx_db),
    user_db: Session = Depends(get_user_db),
):
    user_service = UserService(user_db)
    pm_service = PaymentMethodService(tx_db, user_db)
    try:
        token_user_id = user_service.decode_token(credentials.credentials)
        if token_user_id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return pm_service.save_method(payload)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        message = "Método de pago guardado/modificado exitosamente"
        error_code = exc.status_code
        if exc.status_code == 400:
            message = "Error con el método de pago"
            error_code = 400
        elif exc.status_code == 404:
            message = "Cliente no encontrado"
            error_code = 404
        elif exc.status_code == 503:
            message = "Error con el método de pago"
            error_code = 503
        elif exc.status_code == 403:
            message = "Operación no permitida"
            error_code = 403
        elif exc.status_code == 401:
            message = "Token requerido"
            error_code = 401

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


@router.post(
    "/historial-transacciones",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Historial de transacciones",
)
def historial_transacciones(
    payload: HistorialRequest,
    credentials: HTTPAuthorizationCredentials = Security(auth_scheme),
    tx_db: Session = Depends(get_tx_db),
    user_db: Session = Depends(get_user_db),
):
    user_service = UserService(user_db)
    tx_service = TransactionService(tx_db, user_db)
    try:
        token_user_id = user_service.decode_token(credentials.credentials)
        if token_user_id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")
        return tx_service.historial(payload.id_cliente)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        if exc.status_code == 404:
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "message": "No se encontraron transacciones para el cliente",
                    "data": {"transacciones": [], "total": 0},
                    "success": False,
                    "error_code": 404,
                    "details": {"descripcion": descripcion},
                },
            )
        message = "Error al obtener historial"
        error_code = exc.status_code if exc.status_code != 503 else 503
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
