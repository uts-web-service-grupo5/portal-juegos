from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.payment_method_model import PaymentMethodRequest, PaymentMethodResponse
from app.repository.payment_method_repository import PaymentMethodRepository
from app.repository.user_repository import UserRepository


class PaymentMethodService:
    def __init__(self, tx_db: Session, user_db: Session):
        self.repo = PaymentMethodRepository(tx_db)
        self.user_repo = UserRepository(user_db)

    def _mask_card(self, num_tarjeta: str) -> str:
        last4 = num_tarjeta[-4:]
        return f"**** **** **** {last4}"

    def save_method(self, payload: PaymentMethodRequest) -> PaymentMethodResponse:
        cliente = self.user_repo.get_user_by_id(payload.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        card = payload.datos_tarjeta
        if not card.num_tarjeta.isdigit() or not card.cvv.isdigit():
            raise HTTPException(
                status_code=400,
                detail="Los datos de la tarjeta son inválidos o están incompletos",
            )

        try:
            record = self.repo.upsert_method(
                id_cliente=payload.id_cliente,
                num_tarjeta_mask=self._mask_card(card.num_tarjeta),
                nombre_titular=card.nombre_titular,
                fecha_exp=card.fecha_exp,
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible registrar el método de pago por imposibilidad del servicio",
            )

        return PaymentMethodResponse(
            message="Método de pago guardado/modificado exitosamente",
            data={"id_cliente": record.id_cliente, "metodo_pago": record.num_tarjeta_mask},
            success=True,
            error_code=None,
            details=None,
        )
