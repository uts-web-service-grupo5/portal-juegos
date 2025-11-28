from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.subscription_model import (
    SubscriptionAssignRequest,
    SubscriptionRecord,
    SubscriptionResponse,
    CancelSubscriptionResponse,
    CancelSubscriptionRequest,
    ChangePlanRequest,
    ChangePlanResponse,
)
from app.domain.transaction_model import PaymentRequest
from app.repository.subscription_repository import SubscriptionRepository
from app.repository.user_repository import UserRepository
from app.service.transaction_service import TransactionService
from passlib.hash import bcrypt_sha256


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
            # Validaciones básicas del método de pago
            if not req.metodo_pago.num_tarjeta.isdigit() or not req.metodo_pago.cvv.isdigit():
                raise HTTPException(status_code=400, detail="Los datos de la tarjeta son inválidos o están incompletos")
            try:
                id_transaccion, monto_pagado = self._procesar_pago(req.id_cliente, req.plan)
            except HTTPException:
                # Propagar errores específicos (ej. 402)
                raise
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
                auto_renovacion=True,
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

    def cambio_plan(self, req: ChangePlanRequest) -> ChangePlanResponse:
        # Validaciones básicas
        if not self._plan_valido(req.plan_nuevo):
            raise HTTPException(status_code=400, detail="Plan de suscripción no válido")

        # Cliente y suscripción
        cliente = self.user_repo.get_user_by_id(req.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        try:
            subs = self.sub_repo.get_active_by_client(req.id_cliente)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        if not subs:
            raise HTTPException(status_code=404, detail="El cliente no tiene una suscripción activa")

        plan_actual = subs.plan
        if plan_actual == req.plan_nuevo:
            raise HTTPException(
                status_code=400,
                detail=f"El plan seleccionado es el mismo que el actual ({plan_actual})",
            )

        # Orden de planes
        orden = {"Bronce": 0, "Plata": 1, "Oro": 2}
        es_upgrade = orden[req.plan_nuevo] > orden[plan_actual]
        hoy = date.today()

        # Upgrade desde Bronce a pago: inmediato con cobro
        if plan_actual == "Bronce" and req.plan_nuevo in {"Plata", "Oro"}:
            if not req.metodo_pago:
                raise HTTPException(
                    status_code=400,
                    detail="Para cambiar de Bronce a un plan pago, debe proporcionar un método de pago válido.",
                )
            if not req.metodo_pago.num_tarjeta.isdigit() or not req.metodo_pago.cvv.isdigit():
                raise HTTPException(status_code=400, detail="Los datos de la tarjeta son inválidos o están incompletos")
            try:
                id_tx, monto = self._procesar_pago(req.id_cliente, req.plan_nuevo)
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(
                    status_code=402,
                    detail="La transacción fue rechazada. Verifique los datos de pago o intente con otro método.",
                )

            fecha_venc = hoy + timedelta(days=30)
            try:
                updated = self.sub_repo.update_subscription(
                    subs.id,
                    {
                        "plan": req.plan_nuevo,
                        "estado": "activo",
                        "fecha_inicio": hoy,
                        "fecha_vencimiento": fecha_venc,
                        "monto_pagado": monto,
                        "id_transaccion": id_tx,
                        "auto_renovacion": True,
                        "plan_programado": None,
                        "fecha_cambio": None,
                    },
                )
            except SQLAlchemyError:
                raise HTTPException(
                    status_code=503,
                    detail="No fue posible conectarse al servidor de base de datos",
                )

            return ChangePlanResponse(
                message="Cambio de plan exitoso",
                data={
                    "id_cliente": req.id_cliente,
                    "id_suscripcion": updated.id,
                    "plan_anterior": plan_actual,
                    "plan_nuevo": req.plan_nuevo,
                    "fecha_efectiva": hoy.isoformat(),
                    "tipo_cambio": "upgrade",
                    "monto_cobrado": monto,
                    "id_transaccion": id_tx,
                    "renovacion_automatica": True,
                },
                success=True,
                error_code=None,
                details=None,
            )

        # Cambios entre planes pagos o downgrades
        fecha_base = subs.fecha_vencimiento or hoy
        fecha_efectiva = fecha_base

        updates = {
            "plan_programado": req.plan_nuevo,
            "fecha_cambio": fecha_efectiva,
        }

        tipo_cambio = "upgrade" if es_upgrade else "downgrade"

        if not es_upgrade:
            # Downgrade: cancela auto-renovación si va a Bronce
            if req.plan_nuevo == "Bronce":
                updates["auto_renovacion"] = False
            updates["estado"] = subs.estado  # mantiene acceso hasta fecha cambio
        else:
            # Upgrade entre pagos: programado al siguiente ciclo
            updates["estado"] = subs.estado

        try:
            updated = self.sub_repo.update_subscription(subs.id, updates)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        data_resp = {
            "id_cliente": req.id_cliente,
            "id_suscripcion": subs.id,
            "plan_anterior": plan_actual,
            "plan_nuevo": req.plan_nuevo,
            "fecha_efectiva": fecha_efectiva.isoformat(),
            "tipo_cambio": tipo_cambio,
        }

        if not es_upgrade:
            data_resp["acceso_actual_hasta"] = fecha_efectiva.isoformat()
            if req.plan_nuevo == "Bronce":
                data_resp["renovacion_automatica"] = False
        else:
            data_resp["monto_diferencia"] = max(self.PLAN_COSTOS.get(req.plan_nuevo, 0) - self.PLAN_COSTOS.get(plan_actual, 0), 0)

        return ChangePlanResponse(
            message="Cambio de plan exitoso",
            data=data_resp,
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
                {
                    "estado": "cancelado",
                    "fecha_cancelacion": date.today(),
                    "auto_renovacion": False,
                    "plan_programado": None,
                    "fecha_cambio": None,
                },
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

    def cancelar_pago(self, payload: CancelSubscriptionRequest) -> CancelSubscriptionResponse:
        cliente = self.user_repo.get_user_by_id(payload.id_cliente)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")

        try:
            subs = self.sub_repo.get_active_by_client(payload.id_cliente) or self.sub_repo.get_latest_by_client(payload.id_cliente)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        if not subs:
            raise HTTPException(status_code=400, detail="El cliente no tiene ninguna suscripción registrada")

        if subs.estado == "cancelado":
            raise HTTPException(
                status_code=400,
                detail=f"Esta suscripción ya fue cancelada el {subs.fecha_cancelacion.isoformat() if subs.fecha_cancelacion else 'anteriormente'}. El acceso finalizará el {subs.fecha_vencimiento.isoformat() if subs.fecha_vencimiento else 'fin de periodo'}.",
            )

        if subs.plan == "Bronce":
            raise HTTPException(
                status_code=400,
                detail="El plan Bronce es gratuito y no requiere cancelación. Si desea eliminar su cuenta, utilice la opción de dar de baja cuenta.",
            )

        if subs.estado != "activo":
            raise HTTPException(
                status_code=400,
                detail=f"No existe una suscripción activa para cancelar. Estado actual: {subs.estado}",
            )

        if not bcrypt_sha256.verify(payload.contrasena, cliente.contrasenia):
            raise HTTPException(
                status_code=401,
                detail="La contraseña proporcionada no es correcta. Por favor, verifique e intente nuevamente.",
            )

        # Detener cobros automáticos: placeholder (no implementamos integración real aquí)
        fecha_cancel = date.today()
        acceso_hasta = subs.fecha_vencimiento or fecha_cancel
        dias_restantes = (acceso_hasta - fecha_cancel).days if acceso_hasta else 0

        try:
            updated = self.sub_repo.update_subscription(
                subs.id,
                {
                    "estado": "cancelada",
                    "fecha_cancelacion": fecha_cancel,
                    "auto_renovacion": False,
                    "plan_programado": None,
                    "fecha_cambio": None,
                },
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible conectarse al servidor de base de datos",
            )

        return CancelSubscriptionResponse(
            message="Suscripción cancelada correctamente",
            data={
                "id_cliente": payload.id_cliente,
                "id_suscripcion": updated.id,
                "plan": updated.plan,
                "estado": updated.estado,
                "fecha_cancelacion": fecha_cancel.isoformat(),
                "acceso_hasta": acceso_hasta.isoformat() if acceso_hasta else None,
                "renovacion_automatica": False,
                "dias_restantes": dias_restantes,
                "mensaje_informativo": f"Mantendrás acceso a tu plan {updated.plan} hasta el {acceso_hasta.isoformat() if acceso_hasta else 'fin de periodo'}",
            },
            success=True,
            error_code=None,
            details=None,
        )
