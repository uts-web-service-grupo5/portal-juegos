import os

from sqlalchemy import Column, Date, Float, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'transactions.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


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
    descripcion = Column(String, nullable=True)


class PaymentMethodDB(Base):
    __tablename__ = "payment_methods"

    id = Column(Integer, primary_key=True, index=True)
    id_cliente = Column(Integer, nullable=False, index=True, unique=True)
    num_tarjeta_mask = Column(String, nullable=False)
    nombre_titular = Column(String, nullable=False)
    fecha_exp = Column(String, nullable=False)
    tipo = Column(String, nullable=False, default="tarjeta")


Base.metadata.create_all(bind=engine)
