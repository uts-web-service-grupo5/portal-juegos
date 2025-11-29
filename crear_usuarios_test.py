from app.database import SessionLocal, UserDB
from passlib.hash import bcrypt_sha256
from datetime import date

db = SessionLocal()

# Limpiar usuarios anteriores para empezar limpio
db.query(UserDB).delete()
db.commit()

usuarios = [
    {
        "nombre": "Claudia Gonzales",
        "nickname": "claugonza",
        "correo": "claudia@mail.com",
        "fecha_nac": date(1990, 5, 15),
        "suscripcion": 1,
        "contrasenia": "pass123",
        "caso": "Caso 1: Actualización exitosa"
    },
    {
        "nombre": "Juan Perez",
        "nickname": "juanperez",
        "correo": "juan@mail.com",
        "fecha_nac": date(1988, 3, 20),
        "suscripcion": 1,
        "contrasenia": "pass123",
        "caso": "Caso 2: Eliminación exitosa (sin suscripción activa)"
    },
    {
        "nombre": "Maria Lopez",
        "nickname": "marialopez",
        "correo": "maria@mail.com",
        "fecha_nac": date(1995, 7, 10),
        "suscripcion": 1,
        "contrasenia": "pass123",
        "caso": "Caso 3: Intento actualizar usuario inexistente (será borrado)"
    },
    {
        "nombre": "Nickname Base",
        "nickname": "base",
        "correo": "base@mail.com",
        "fecha_nac": date(1992, 11, 8),
        "suscripcion": 1,
        "contrasenia": "pass123",
        "caso": "Caso 4: Validación - nickname duplicado (intenta cambiar a 'duplicado')"
    },
    {
        "nombre": "Correo Duplicado Base",
        "nickname": "correobase",
        "correo": "correo@mail.com",
        "fecha_nac": date(1993, 2, 14),
        "suscripcion": 1,
        "contrasenia": "pass123",
        "caso": "Caso 5: Validación - correo duplicado (intenta cambiar a 'correo2@mail.com')"
    },
    {
        "nombre": "Con Suscripcion Activa",
        "nickname": "consuscripcion",
        "correo": "activa@mail.com",
        "fecha_nac": date(1991, 6, 25),
        "suscripcion": 2,
        "contrasenia": "pass123",
        "caso": "Caso 6: Intento eliminar con suscripción activa"
    }
]

for i, datos in enumerate(usuarios, 1):
    user = UserDB(
        nombre=datos["nombre"],
        nickname=datos["nickname"],
        correo=datos["correo"],
        contrasenia=bcrypt_sha256.hash(datos["contrasenia"]),
        fecha_nac=datos["fecha_nac"],
        suscripcion=datos["suscripcion"]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Usuario {i}: {user.nombre}")
    print(f"   ID: {user.id} | Nickname: {user.nickname} | Correo: {user.correo}")
    print(f"   {datos['caso']}\n")

db.close()
print("=" * 60)
print("✅ 6 usuarios creados para pruebas")
print("=" * 60)
