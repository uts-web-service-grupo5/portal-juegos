from pydantic import BaseModel, Field


class PaymentMethodData(BaseModel):
    num_tarjeta: str = Field(..., min_length=12, max_length=19)
    nombre_titular: str = Field(..., min_length=3)
    fecha_exp: str = Field(..., min_length=4, max_length=7)  # mm/yy o mm/yyyy
    cvv: str = Field(..., min_length=3, max_length=4)


class PaymentMethodRequest(BaseModel):
    id_cliente: int = Field(..., gt=0)
    datos_tarjeta: PaymentMethodData


class PaymentMethodResponse(BaseModel):
    message: str
    data: dict
    success: bool
    error_code: int | None = None
    details: dict | None = None
