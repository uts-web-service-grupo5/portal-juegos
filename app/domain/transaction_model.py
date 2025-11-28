from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


PlanType = Literal["Bronce", "Plata", "Oro"]


class PaymentRequest(BaseModel):
    id_cliente: int = Field(..., gt=0)
    id_suscripcion: int | None = None
    plan: PlanType | None = None


class PaymentResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None


class PaymentRecord(BaseModel):
    id_transaccion: int = Field(alias="id")
    id_cliente: int
    id_suscripcion: int | None = None
    valor_transaccion: float
    metodo_pago: str
    fecha_transaccion: date
    fecha_inicio_suscripcion: date
    fecha_fin_suscripcion: date | None
    estado_pago: str

    class Config:
        from_attributes = True
        populate_by_name = True
