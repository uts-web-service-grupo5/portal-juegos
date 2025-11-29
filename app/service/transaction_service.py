import random
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.transaction_model import PaymentRecord, PaymentRequest, PaymentResponse, PlanType
from app.repository.transaction_repository import TransactionRepository
from app.repository.user_repository import UserRepository
from app.repository.subscription_repository import SubscriptionRepository


class TransactionService:
    PLAN_COSTOS = {"Bronce": 0.0, "Plata": 14990.0, "Oro": 29990.0}

    def __init__(self, tx_db: Session, user_db: Session, sub_db: Session | None = None):
        self.tx_repo = TransactionRepository(tx_db)
        self.user_repo = UserRepository(user_db)
        self.sub_repo = SubscriptionRepository(sub_db) if sub_db else None

    def _metodo_pago_registrado(self, user_id: int) -> str | None:
        """
        Placeholder: en el futuro se consultará la tabla de métodos de pago.
        Aquí simulamos que el usuario siempre tiene un método registrado,
        y devolvemos una tarjeta enmascarada.
        """
        return "Tarjeta de crédito terminada en 1234"

    def _procesar_pago_banco(self, plan: PlanType) -> bool:
        """
        Placeholder de integración con el banco.
        Hoy siempre aprueba; si se quiere simular rechazo, cambiar aquí.
        """
        return True

    def procesar_pago(self, payload: PaymentRequest) -> PaymentResponse:
        # Validar cliente
        cliente = self.user_repo.get_user_by_id(payload.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        plan = payload.plan or "Bronce"
        if plan not in self.PLAN_COSTOS:
            raise HTTPException(status_code=400, detail="Plan de suscripción no válido")

        metodo_pago = self._metodo_pago_registrado(payload.id_cliente)
        if not metodo_pago:
            raise HTTPException(
                status_code=404,
                detail="El cliente no tiene un método de pago registrado. Por favor, registre una tarjeta antes de realizar el pago",
            )

        if plan != "Bronce":
            aprobado = self._procesar_pago_banco(plan)
            if not aprobado:
                raise HTTPException(
                    status_code=402,
                    detail="La transacción fue rechazada. Verifique los datos de pago o intente con otro método.",
                )

        valor = self.PLAN_COSTOS[plan]
        fecha_inicio = date.today()
        fecha_fin = fecha_inicio + timedelta(days=30) if plan != "Bronce" else None
        estado_pago = "APROBADO"
        fecha_tx = fecha_inicio

        try:
            tx = self.tx_repo.create_transaction(
                id_cliente=payload.id_cliente,
                id_suscripcion=payload.id_suscripcion,
                valor_transaccion=valor,
                metodo_pago=metodo_pago,
                fecha_transaccion=fecha_tx,
                fecha_inicio_suscripcion=fecha_inicio,
                fecha_fin_suscripcion=fecha_fin,
                estado_pago=estado_pago,
                descripcion="Suscripción",
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        record = PaymentRecord.from_orm(tx)
        return PaymentResponse(
            message="Pago procesado exitosamente",
            data={
                "id_transaccion": record.id_transaccion,
                "id_cliente": record.id_cliente,
                "id_suscripcion": record.id_suscripcion,
                "valor_transaccion": record.valor_transaccion,
                "metodo_pago": record.metodo_pago,
                "fecha_transaccion": record.fecha_transaccion.isoformat(),
                "fecha_inicio_suscripcion": record.fecha_inicio_suscripcion.isoformat(),
                "fecha_fin_suscripcion": record.fecha_fin_suscripcion.isoformat()
                if record.fecha_fin_suscripcion
                else None,
                "estado_pago": record.estado_pago,
            },
            success=True,
            error_code=None,
            details=None,
        )

    def _metodo_pago_registrado_flag(self, user_id: int) -> bool:
        # Placeholder: retornar True si hay método; aquí lo simulamos como True.
        return True

    def obtener_renovacion(self, client_id: int) -> PaymentResponse:
        # Validar cliente
        cliente = self.user_repo.get_user_by_id(client_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="El cliente no fue encontrado en el sistema")

        # Validar suscripción
        if not self.sub_repo:
            raise HTTPException(status_code=503, detail="Servicio de suscripciones no disponible")
        subs = self.sub_repo.get_active_by_client(client_id)
        if not subs:
            raise HTTPException(status_code=404, detail="El cliente no tiene una suscripción activa")

        # Última transacción aprobada
        last_tx = self.tx_repo.get_last_approved_by_client(client_id)
        if not last_tx:
            raise HTTPException(status_code=404, detail="No hay transacciones previas para este cliente")

        # Método de pago registrado
        if not self._metodo_pago_registrado_flag(client_id):
            raise HTTPException(
                status_code=400,
                detail="La renovación automática fallará, el cliente debe registrar un método de pago antes de la fecha de renovación",
            )

        fecha_base = subs.fecha_vencimiento or last_tx.fecha_fin_suscripcion or last_tx.fecha_transaccion
        fecha_proxima = fecha_base + timedelta(days=30)
        dias_restantes = (fecha_proxima - date.today()).days
        monto = self.PLAN_COSTOS.get(subs.plan, 0.0)

        data = {
            "id_cliente": client_id,
            "id_suscripcion": subs.id,
            "plan": subs.plan,
            "fecha_transaccion": last_tx.fecha_transaccion.isoformat(),
            "fecha_proxima_renovacion": fecha_proxima.isoformat(),
            "monto_renovacion": monto,
            "dias_restantes": dias_restantes,
            "estado": subs.estado,
            "auto_renovacion_activa": True,
            "metodo_pago_registrado": True,
        }

        return PaymentResponse(
            message="Información de renovación obtenida exitosamente",
            data=data,
            success=True,
            error_code=None,
            details=None,
        )

    def historial(self, client_id: int) -> PaymentResponse:
        cliente = self.user_repo.get_user_by_id(client_id)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        try:
            txs = self.tx_repo.list_by_client(client_id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="Imposibilidad del servicio",
            )

        if not txs:
            raise HTTPException(
                status_code=404,
                detail="El cliente no tiene registros de transacciones en el sistema",
            )

        tx_list = []
        for tx in txs:
            tx_list.append(
                {
                    "id_transaccion": tx.id,
                    "fecha_transaccion": tx.fecha_transaccion.isoformat(),
                    "valor_transaccion": tx.valor_transaccion,
                    "metodo_pago": tx.metodo_pago,
                    "descripcion": tx.descripcion or "",
                }
            )

        return PaymentResponse(
            message="Historial de transacciones obtenido con éxito",
            data={"transacciones": tx_list, "total": len(tx_list)},
            success=True,
            error_code=None,
            details=None,
        )
