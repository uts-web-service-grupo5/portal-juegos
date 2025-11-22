from sqlalchemy.orm import Session
from app.database import UserDB, SuscripcionDB, VideojuegoDB
from typing import List, Optional
from datetime import date


class CatalogoRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_cliente_by_id(self, id_cliente: int) -> Optional[UserDB]:

        return self.db.query(UserDB).filter(UserDB.id == id_cliente).first()

    def get_suscripcion_by_cliente(self, id_cliente: int) -> Optional[SuscripcionDB]:

        return self.db.query(SuscripcionDB).filter(
            SuscripcionDB.id_cliente == id_cliente
        ).first()

    def get_videojuegos_by_plan(self, plan: str) -> List[VideojuegoDB]:

        if plan == "Oro":
            # Oro tiene acceso a todo
            return self.db.query(VideojuegoDB).all()
        elif plan == "Plata":
            # Plata tiene acceso a Bronce + Plata
            return self.db.query(VideojuegoDB).filter(
                VideojuegoDB.acceso_plan.in_(["Bronce", "Plata"])
            ).all()
        elif plan == "Bronce":
            # Bronce solo tiene acceso a Bronce
            return self.db.query(VideojuegoDB).filter(
                VideojuegoDB.acceso_plan == "Bronce"
            ).all()
        else:
            # Plan no válido
            return []

    def calcular_edad(self, fecha_nac: date) -> int:

        hoy = date.today()
        edad = hoy.year - fecha_nac.year

        if (hoy.month, hoy.day) < (fecha_nac.month, fecha_nac.day):
            edad -= 1

        return edad
