from sqlalchemy.orm import Session

from app.database import UserDB
from app.domain.user_model import UserCreate


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate, hashed_password: str) -> UserDB:
        user = UserDB(
            nombre=user_data.nombre,
            nickname=user_data.nickname,
            correo=user_data.correo,
            contrasenia=hashed_password,
            fecha_nac=user_data.fecha_nac,
            suscripcion=user_data.suscripcion,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> UserDB | None:
        return self.db.query(UserDB).filter(UserDB.id == user_id).first()

    def get_user_by_email(self, email: str) -> UserDB | None:
        return self.db.query(UserDB).filter(UserDB.correo == email).first()

    def get_user_by_nickname(self, nickname: str) -> UserDB | None:
        return self.db.query(UserDB).filter(UserDB.nickname == nickname).first()

    def get_all_users(self) -> list[UserDB]:
        return self.db.query(UserDB).all()

    def update_user(self, user_id: int, updates: dict) -> UserDB:
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        for key, value in updates.items():
            setattr(user, key, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True
