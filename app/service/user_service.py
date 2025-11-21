import os
from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.domain.user_model import (
    LoginRequest,
    LoginResponse,
    RegistroResponse,
    DeleteRequest,
    DeleteResponse,
    UpdateRequest,
    UpdateResponse,
    UserCreate,
    UserRecord,
)
from app.repository.user_repository import UserRepository
from passlib.hash import bcrypt_sha256
from jose import JWTError, jwt


class UserService:
    def __init__(self, db: Session):
        self.repository = UserRepository(db)
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")
        self.algorithm = "HS256"
        self.access_token_exp_minutes = 60

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

    def login(self, credentials: LoginRequest) -> LoginResponse:
        user = self.repository.get_user_by_email(credentials.correo)
        if not user:
            raise HTTPException(
                status_code=400,
                detail="Alguno de los parámetros de inicio de sesión es incorrecto o el usuario no se ha registrado",
            )

        if not bcrypt_sha256.verify(credentials.contrasenia, user.contrasenia):
            raise HTTPException(
                status_code=400,
                detail="Alguno de los parámetros de inicio de sesión es incorrecto o el usuario no se ha registrado",
            )

        return self.issue_token_response(user.id, user.correo)

    def _create_access_token(self, user_id: int) -> str:
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_exp_minutes)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def update_user(self, user_id: int, payload: UpdateRequest) -> UpdateResponse:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        updates = {}
        if payload.nombre is not None:
            updates["nombre"] = payload.nombre
        if payload.nickname is not None:
            updates["nickname"] = payload.nickname

        if not updates:
            raise HTTPException(status_code=400, detail="No se especificaron campos para actualizar")

        try:
            updated = self.repository.update_user(user_id, updates)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible completar la actualización, por indisponibilidad del backend",
            )

        return UpdateResponse(
            message="Solicitud de actualización de datos del cliente",
            data={key: getattr(updated, key) for key in updates.keys()},
            success=True,
            error_code=None,
            details=None,
        )

    def decode_token(self, token: str) -> int:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Token inválido")
            return int(user_id)
        except JWTError:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")

    def issue_token_response(self, user_id: int, correo: str) -> LoginResponse:
        token = self._create_access_token(user_id)
        return LoginResponse(
            message="Datos recibidos",
            data={"token": token, "correo": correo},
            success=True,
            error_code=None,
            details=None,
        )

    def _has_active_subscription(self, user_id: int) -> bool:
        # Placeholder para integración futura con API de Suscripciones.
        # Aquí se llamaría a GET /api/v1/suscripciones/verificacion/{id_cliente}
        # Por ahora devolvemos False (sin plan activo) para permitir pruebas internas.
        return False

    def delete_user(self, user_id: int, payload: DeleteRequest) -> DeleteResponse:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Verificar que quien solicita coincide con el id del token y del payload.
        if user.id != payload.id_cliente:
            raise HTTPException(status_code=403, detail="Operación no permitida para este usuario")

        if not bcrypt_sha256.verify(payload.contrasenia, user.contrasenia):
            raise HTTPException(status_code=401, detail="La contraseña no es válida.")

        if self._has_active_subscription(user.id):
            raise HTTPException(
                status_code=403,
                detail="El usuario mantiene un plan activo y no puede eliminar su cuenta.",
            )

        try:
            deleted = self.repository.delete_user(user.id)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible completar la eliminación por indisponibilidad del backend.",
            )

        if not deleted:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        return DeleteResponse(
            message="Solicitud de eliminación procesada",
            data={"id_cliente": user.id},
            success=True,
            error_code=None,
            details=None,
        )
