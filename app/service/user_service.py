from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.repository.user_repository import UserRepository
from app.domain.user_model import UserCreate, UserResponse


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)

    def create_user(self, user_data: UserCreate) -> UserResponse:
        existing_user = self.repository.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email ya registrado")

        if user_data.age < 18:
            raise HTTPException(status_code=400, detail="Debe ser mayor de edad")

        user = self.repository.create_user(
            name=user_data.name,
            email=user_data.email,
            age=user_data.age,
        )
        return UserResponse.from_orm(user)

    def get_user(self, user_id: int) -> UserResponse:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return UserResponse.from_orm(user)
