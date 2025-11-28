import os

from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'users.db')}"

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
    estado_suscripcion = Column(String, nullable=False, default="activo")


class SubscriptionDB(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, nullable=False, index=True)
    plan = Column(String, nullable=False)
    estado = Column(String, nullable=False, default="activo")
    fecha_inicio = Column(Date, nullable=False)
    fecha_vencimiento = Column(Date, nullable=True)
    monto_pagado = Column(Float, nullable=True)
    id_transaccion = Column(Integer, nullable=True)
    fecha_cancelacion = Column(Date, nullable=True)


class TransactionDB(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, nullable=False, index=True)
    id_suscripcion = Column(Integer, nullable=True)
    valor_transaccion = Column(Float, nullable=False)
    metodo_pago = Column(String, nullable=False)
    fecha_transaccion = Column(Date, nullable=False)
    fecha_inicio_suscripcion = Column(Date, nullable=False)
    fecha_fin_suscripcion = Column(Date, nullable=True)
    estado_pago = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)
