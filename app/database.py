from sqlalchemy import Column, Date, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    nickname = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False, index=True)
    contrasenia = Column(String, nullable=False)
    fecha_nac = Column(Date, nullable=False)
    suscripcion = Column(Integer, nullable=False)


class VideojuegoDB(Base):
    __tablename__ = "videojuegos"

    id_videojuego = Column(Integer, primary_key=True, index=True)
    nombre_juego = Column(String, nullable=False)
    restriccion_edad = Column(String, nullable=False)
    acceso_plan = Column(String, nullable=False)


# Tabla de Suscripciones ( temporal, para pruebas en catalogo - Esteban)
class SuscripcionDB(Base):
    __tablename__ = "suscripciones"

    id_suscripcion = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, nullable=False, index=True)
    plan = Column(String, nullable=False)  # "Bronce", "Plata", "Oro"
    estado = Column(String, nullable=False)  # "activo", "inactivo", "vencido"
    fecha_inicio = Column(String, nullable=False)
    fecha_vencimiento = Column(String, nullable=True)  # NULL para plan Bronce
    id_transaccion = Column(Integer, nullable=True)  # NULL para plan Bronce
    monto_pagado = Column(Integer, nullable=True)


Base.metadata.create_all(bind=engine)
