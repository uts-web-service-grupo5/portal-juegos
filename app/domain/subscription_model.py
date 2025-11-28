from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


PlanType = Literal["Bronce", "Plata", "Oro"]


class MetodoPago(BaseModel):
    num_tarjeta: str = Field(..., min_length=12, max_length=19)
    nombre_titular: str = Field(..., min_length=3)
    fecha_exp: str = Field(..., min_length=4, max_length=7)  # mm/yy o mm/yyyy
    cvv: str = Field(..., min_length=3, max_length=4)


class SubscriptionAssignRequest(BaseModel):
    id_cliente: int = Field(..., gt=0)
    plan: PlanType
    metodo_pago: MetodoPago | None = None


class SubscriptionRecord(BaseModel):
    id_suscripcion: int
    id_cliente: int
    plan: PlanType
    estado: str
    fecha_inicio: date
    fecha_vencimiento: date | None = None
    monto_pagado: float | None = None
    id_transaccion: int | None = None

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None


class SubscriptionVerificationResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None


class CancelSubscriptionResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None
