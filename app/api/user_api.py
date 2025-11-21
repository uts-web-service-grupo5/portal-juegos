from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.user_model import RegistroResponse, UserCreate, UserRecord
from app.service.user_service import UserService

router = APIRouter(prefix="/api/v1/cliente", tags=["Clientes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/registro",
    response_model=RegistroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar cliente",
)
def registrar_cliente(user: UserCreate, db: Session = Depends(get_db)):
    """Registra un nuevo cliente."""
    service = UserService(db)
    try:
        return service.create_user(user)
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        error_code = exc.status_code if exc.status_code != status.HTTP_503_SERVICE_UNAVAILABLE else 503
        message = (
            "Error en la validación de datos"
            if exc.status_code == status.HTTP_400_BAD_REQUEST
            else "No fue posible completar el registro"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": message,
                "data": {},
                "success": False,
                "error_code": error_code,
                "details": {"descripcion": descripcion},
            },
        )


@router.get("/{user_id}", response_model=UserRecord, summary="Obtener cliente")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Obtiene un cliente por ID."""
    service = UserService(db)
    return service.get_user(user_id)
