from datetime import date

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.user_model import RegistroResponse, UserCreate, UserRecord
from app.repository.user_repository import UserRepository
from passlib.hash import bcrypt_sha256


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def _hash_password(self, raw_password: str) -> str:
        
        return bcrypt_sha256.hash(raw_password)

    def _is_adult(self, birthday: date) -> bool:
        today = date.today()
        age = today.year - birthday.year - (
            (today.month, today.day) < (birthday.month, birthday.day)
        )
        return age >= 18

    def create_user(self, user_data: UserCreate) -> RegistroResponse:
        if self.repository.get_user_by_email(user_data.correo):
            raise HTTPException(status_code=400, detail="Correo ya registrado")

        if not self._is_adult(user_data.fecha_nac):
            raise HTTPException(status_code=400, detail="Debe ser mayor de edad")

        hashed_password = self._hash_password(user_data.contrasenia)

        try:
            user = self.repository.create_user(user_data=user_data, hashed_password=hashed_password)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible completar el registro, por indisponibilidad del backend",
            )

        return RegistroResponse(
            message="Datos recibidos",
            data=UserRecord.from_orm(user),
            success=True,
            error_code=None,
            details=None,
        )

    def get_user(self, user_id: int) -> UserRecord:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return UserRecord.from_orm(user)
