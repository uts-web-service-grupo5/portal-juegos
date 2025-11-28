from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.subscription_model import (
    SubscriptionAssignRequest,
    SubscriptionRecord,
    SubscriptionResponse,
    CancelSubscriptionResponse,
)
from app.domain.transaction_model import PaymentRequest
from app.repository.subscription_repository import SubscriptionRepository
from app.repository.user_repository import UserRepository
from app.service.transaction_service import TransactionService


class SubscriptionService:
    PLAN_COSTOS = {"Plata": 14.99, "Oro": 29.99, "Bronce": 0.0}

    def __init__(self, sub_db: Session, user_db: Session, tx_service: TransactionService | None = None):
        self.sub_repo = SubscriptionRepository(sub_db)
        self.user_repo = UserRepository(user_db)
        self.tx_service = tx_service

    def _plan_valido(self, plan: str) -> bool:
        return plan in {"Bronce", "Plata", "Oro"}

    def _fecha_vencimiento(self, plan: str) -> date | None:
        if plan == "Bronce":
            return None
        return date.today() + timedelta(days=30)

    def _procesar_pago(self, client_id: int, plan: str) -> tuple[int, float]:
        """Integra con el servicio de transacciones para procesar pago real."""
        if not self.tx_service:
            raise HTTPException(status_code=503, detail="Servicio de transacciones no disponible")
        resp = self.tx_service.procesar_pago(
            PaymentRequest(id_cliente=client_id, plan=plan, id_suscripcion=None)
        )
        data = resp.data
        return data["id_transaccion"], data["valor_transaccion"]

    def asignar(self, req: SubscriptionAssignRequest) -> SubscriptionResponse:
        if not self._plan_valido(req.plan):
            raise HTTPException(status_code=400, detail="Plan de suscripción no válido")

        # Validar cliente existe
        cliente = self.user_repo.get_user_by_id(req.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        # Validar que no tenga suscripción activa
        if self.sub_repo.get_active_by_client(req.id_cliente):
            raise HTTPException(
                status_code=400,
                detail="El cliente ya posee una suscripción activa",
            )

        # Validar pago para planes pagos
        id_transaccion = None
        monto_pagado = None
        if req.plan in {"Plata", "Oro"}:
            if not req.metodo_pago:
                raise HTTPException(
                    status_code=400,
                    detail="Método de pago requerido para planes de pago",
                )
            try:
                id_transaccion, monto_pagado = self._procesar_pago(req.id_cliente, req.plan)
            except Exception:
                raise HTTPException(
                    status_code=402,
                    detail="La transacción fue rechazada. Verifique los datos de pago o intente con otro método.",
                )

        fecha_inicio = date.today()
        fecha_vencimiento = self._fecha_vencimiento(req.plan)

        try:
            record = self.sub_repo.create_subscription(
                client_id=req.id_cliente,
                plan=req.plan,
                estado="activo",
                fecha_inicio=fecha_inicio,
                fecha_vencimiento=fecha_vencimiento,
                monto_pagado=monto_pagado,
                id_transaccion=id_transaccion,
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        data = SubscriptionRecord.from_orm(record)
        return SubscriptionResponse(
            message="Suscripción asignada correctamente",
            data=data.model_dump(),
            success=True,
            error_code=None,
            details=None,
        )

    def verificar(self, client_id: int) -> SubscriptionResponse:
        cliente = self.user_repo.get_user_by_id(client_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        try:
            subs = self.sub_repo.get_latest_by_client(client_id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        if not subs:
            raise HTTPException(status_code=404, detail="El cliente no tiene suscripción registrada")

        estado = subs.estado
        if subs.plan == "Bronce":
            estado = "activo"
            fecha_venc = None
        else:
            fecha_venc = subs.fecha_vencimiento
            if estado == "activo" and fecha_venc and fecha_venc < date.today():
                estado = "vencido"

        data = {
            "id_suscripcion": subs.id,
            "plan": subs.plan,
            "estado": estado,
            "fecha_inicio": subs.fecha_inicio.isoformat(),
            "fecha_vencimiento": fecha_venc.isoformat() if fecha_venc else None,
        }

        return SubscriptionResponse(
            message="Consulta de suscripción exitosa",
            data=data,
            success=True,
            error_code=None,
            details=None,
        )

    def cancelar(self, client_id: int) -> CancelSubscriptionResponse:
        # Obtener la suscripción activa o la última
        try:
            subs = self.sub_repo.get_active_by_client(client_id) or self.sub_repo.get_latest_by_client(client_id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        if not subs:
            raise HTTPException(status_code=404, detail="El cliente no tiene suscripción registrada")

        if subs.plan == "Bronce":
            raise HTTPException(
                status_code=403,
                detail="El plan Bronce es gratuito y no requiere cancelación.",
            )

        if subs.plan not in {"Plata", "Oro"}:
            raise HTTPException(status_code=400, detail="Plan de suscripción no válido para cancelación")

        try:
            updated = self.sub_repo.update_subscription(
                subs.id,
                {"estado": "cancelado", "fecha_cancelacion": date.today()},
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible procesar la cancelación por indisponibilidad del servicio.",
            )

        if not updated:
            raise HTTPException(status_code=404, detail="El cliente no tiene suscripción registrada")

        return CancelSubscriptionResponse(
            message="Cancelación de suscripción procesada",
            data={"id_cliente": client_id, "estado_suscripcion": "cancelado"},
            success=True,
            error_code=None,
            details=None,
        )
