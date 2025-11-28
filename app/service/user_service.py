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
from app.repository.subscription_repository import SubscriptionRepository
from passlib.hash import bcrypt_sha256
from jose import JWTError, jwt


class UserService:
    def __init__(self, db: Session, sub_db: Session | None = None):
        self.repository = UserRepository(db)
        self.subscription_repo = SubscriptionRepository(sub_db or db)
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
            # validar nickname único
            existing = self.repository.get_user_by_nickname(payload.nickname)
            if existing and existing.id != user.id:
                raise HTTPException(status_code=400, detail="Nickname en uso por otro usuario")
            updates["nickname"] = payload.nickname
        if payload.correo is not None:
            # validar correo único
            existing_email = self.repository.get_user_by_email(payload.correo)
            if existing_email and existing_email.id != user.id:
                raise HTTPException(status_code=400, detail="Correo en uso por otro usuario")
            updates["correo"] = payload.correo

        if not updates:
            raise HTTPException(status_code=400, detail="No se especificaron campos para actualizar")

        try:
            updated = self.repository.update_user(user_id, updates)
        except SQLAlchemyError:
            raise HTTPException(
                status_code=503,
                detail="No fue posible completar la actualización, por indisponibilidad del backend",
            )

        # Construir respuesta con formato esperado por la HU
        response_data = {
            "id_cliente": updated.id,
            "nombre": updated.nombre,
            "nickname": updated.nickname,
            "correo": updated.correo,
        }

        return UpdateResponse(
            message="Actualización ejecutada de forma exitosa",
            data=response_data,
            success=True,
            error_code=None,
            details=None,
        )

    def delete_user_admin(self, user_id: int) -> DeleteResponse:
        user = self.repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        try:
            has_plan = self._has_active_subscription(user.id)
        except HTTPException:
            # Propagar errores de conexión a la API de suscripciones
            raise

        if has_plan:
            raise HTTPException(
                status_code=400,
                detail="El usuario tiene una suscripción activa. Debe cancelar la suscripción antes de eliminar la cuenta.",
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
            message="Usuario eliminado exitosamente",
            data={},
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
        """
        Verifica si el usuario tiene una suscripción activa consultando la tabla de suscripciones.
        """
        active = self.subscription_repo.get_active_by_client(user_id)
        return active is not None

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
