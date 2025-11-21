from datetime import date

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=1)
    nickname: str = Field(..., min_length=1)
    correo: EmailStr
    fecha_nac: date
    suscripcion: int = Field(..., ge=1)


class UserCreate(UserBase):
    contrasenia: str = Field(..., min_length=6)


class UserRecord(UserBase):
    id: int

    class Config:
        from_attributes = True


class RegistroResponse(BaseModel):
    message: str
    data: dict | UserRecord
    success: bool
    error_code: int | None = None
    details: dict | None = None


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasenia: str = Field(..., min_length=6)


class LoginResponse(BaseModel):
    message: str
    data: dict  # Contiene token y/o correo
    success: bool
    error_code: int | None = None
    details: dict | None = None


class UpdateRequest(BaseModel):
    nombre: str | None = None
    nickname: str | None = None


class UpdateResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None
