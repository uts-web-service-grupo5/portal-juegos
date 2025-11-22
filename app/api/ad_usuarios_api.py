import os
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain.user_model import UpdateRequest
from app.service.user_service import UserService


router = APIRouter(prefix="/api/v1/admin/usuarios", tags=["Admin Usuarios"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def admin_required(x_admin_token: str | None = Header(default=None, convert_underscores=False)):
    admin_token = os.getenv("ADMIN_TOKEN", "admin-secret")
    if not x_admin_token or x_admin_token != admin_token:
        raise HTTPException(status_code=403, detail="Permisos de administrador requeridos")
    return True


@router.put("/{user_id}", status_code=status.HTTP_200_OK)
def actualizar_usuario_admin(
    user_id: int,
    payload: UpdateRequest,
    _admin: bool = Depends(admin_required),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    try:
        resp = service.update_user(user_id, payload)
        return JSONResponse(
            status_code=200,
            content={
                "message": resp.message,
                "data": resp.data,
                "success": resp.success,
                "error_code": resp.error_code,
                "details": resp.details,
            },
        )
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        ts = datetime.utcnow().isoformat() + "Z"
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No existe el usuario a actualizar",
                    "data": {},
                    "success": False,
                    "error_code": 404,
                    "details": {
                        "description": "El usuario con ID especificado no consta con registro en la base de datos.",
                        "timestamp": ts,
                    },
                },
            )
        if exc.status_code == 400:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "Error en la validación de datos",
                    "data": {},
                    "success": False,
                    "error_code": 400,
                    "details": {"description": descripcion, "timestamp": ts},
                },
            )
        # 503 or other errors
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "Error al procesar la operación",
                "data": {},
                "success": False,
                "error_code": 503,
                "details": {"description": descripcion, "timestamp": ts},
            },
        )


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def eliminar_usuario_admin(
    user_id: int,
    _admin: bool = Depends(admin_required),
    db: Session = Depends(get_db),
):
    service = UserService(db)
    try:
        resp = service.delete_user_admin(user_id)
        return JSONResponse(
            status_code=200,
            content={
                "message": resp.message,
                "data": resp.data,
                "success": resp.success,
                "error_code": resp.error_code,
                "details": resp.details,
            },
        )
    except HTTPException as exc:
        descripcion = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        ts = datetime.utcnow().isoformat() + "Z"
        if exc.status_code == 404:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "No existe el usuario a actualizar",
                    "data": {},
                    "success": False,
                    "error_code": 404,
                    "details": {"description": descripcion, "timestamp": ts},
                },
            )
        if exc.status_code == 400:
            return JSONResponse(
                status_code=400,
                content={
                    "message": "No se puede eliminar el usuario",
                    "data": {},
                    "success": False,
                    "error_code": 400,
                    "details": {"description": descripcion, "timestamp": ts},
                },
            )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": "Error al procesar la operación",
                "data": {},
                "success": False,
                "error_code": 503,
                "details": {"description": descripcion, "timestamp": ts},
            },
        )
