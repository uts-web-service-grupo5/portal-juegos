from sqlalchemy.orm import Session

from app.subscription_database import SubscriptionDB


class SubscriptionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_by_client(self, client_id: int) -> SubscriptionDB | None:
        return (
            self.db.query(SubscriptionDB)
            .filter(SubscriptionDB.id_cliente == client_id, SubscriptionDB.estado == "activo")
            .first()
        )

    def get_latest_by_client(self, client_id: int) -> SubscriptionDB | None:
        return (
            self.db.query(SubscriptionDB)
            .filter(SubscriptionDB.id_cliente == client_id)
            .order_by(SubscriptionDB.id.desc())
            .first()
        )

    def create_subscription(
        self,
        *,
        client_id: int,
        plan: str,
        estado: str,
        fecha_inicio,
        fecha_vencimiento,
        monto_pagado: float | None,
        id_transaccion: int | None,
        auto_renovacion: bool = True,
    ) -> SubscriptionDB:
        record = SubscriptionDB(
            id_cliente=client_id,
            plan=plan,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_vencimiento=fecha_vencimiento,
            monto_pagado=monto_pagado,
            id_transaccion=id_transaccion,
            auto_renovacion=auto_renovacion,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def update_subscription(self, sub_id: int, updates: dict) -> SubscriptionDB | None:
        subs = self.db.query(SubscriptionDB).filter(SubscriptionDB.id == sub_id).first()
        if not subs:
            return None
        for key, value in updates.items():
            setattr(subs, key, value)
        self.db.commit()
        self.db.refresh(subs)
        return subs
