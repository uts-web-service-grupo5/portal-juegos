from sqlalchemy.orm import Session

from app.database import TransactionDB


class TransactionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_transaction(
        self,
        *,
        id_cliente: int,
        id_suscripcion: int | None,
        valor_transaccion: float,
        metodo_pago: str,
        fecha_transaccion,
        fecha_inicio_suscripcion,
        fecha_fin_suscripcion,
        estado_pago: str,
    ) -> TransactionDB:
        record = TransactionDB(
            id_cliente=id_cliente,
            id_suscripcion=id_suscripcion,
            valor_transaccion=valor_transaccion,
            metodo_pago=metodo_pago,
            fecha_transaccion=fecha_transaccion,
            fecha_inicio_suscripcion=fecha_inicio_suscripcion,
            fecha_fin_suscripcion=fecha_fin_suscripcion,
            estado_pago=estado_pago,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
