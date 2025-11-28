from sqlalchemy.orm import Session

from app.transaction_database import PaymentMethodDB


class PaymentMethodRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert_method(
        self, *, id_cliente: int, num_tarjeta_mask: str, nombre_titular: str, fecha_exp: str, tipo: str = "tarjeta"
    ) -> PaymentMethodDB:
        record = (
            self.db.query(PaymentMethodDB)
            .filter(PaymentMethodDB.id_cliente == id_cliente)
            .first()
        )
        if record:
            record.num_tarjeta_mask = num_tarjeta_mask
            record.nombre_titular = nombre_titular
            record.fecha_exp = fecha_exp
            record.tipo = tipo
        else:
            record = PaymentMethodDB(
                id_cliente=id_cliente,
                num_tarjeta_mask=num_tarjeta_mask,
                nombre_titular=nombre_titular,
                fecha_exp=fecha_exp,
                tipo=tipo,
            )
            self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_client(self, id_cliente: int) -> PaymentMethodDB | None:
        return (
            self.db.query(PaymentMethodDB)
            .filter(PaymentMethodDB.id_cliente == id_cliente)
            .first()
        )
