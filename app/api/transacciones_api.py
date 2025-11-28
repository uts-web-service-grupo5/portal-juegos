from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.transaction_database import SessionLocal as TxSessionLocal
from app.user_database import SessionLocal as UserSessionLocal
from app.domain.transaction_model import PaymentRequest, PaymentResponse
from app.service.transaction_service import TransactionService
from app.service.user_service import UserService

router = APIRouter(prefix="/api/v1/transacciones", tags=["Transacciones"])


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


@router.post(
    "/pago",
    response_model=PaymentResponse,
    status_code=status.HTTP_200_OK,
    summary="Procesar pago de suscripción",
)
def procesar_pago(
    payload: PaymentRequest,
    authorization: str | None = Header(default=None, convert_underscores=False),
    tx_db: Session = Depends(get_tx_db),
    user_db: Session = Depends(get_user_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token requerido")
    token = authorization.removeprefix("Bearer ").strip()

    user_service = UserService(user_db)
    tx_service = TransactionService(tx_db, user_db)
    try:
        token_user_id = user_service.decode_token(token)
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
