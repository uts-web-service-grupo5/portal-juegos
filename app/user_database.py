import os

from sqlalchemy import Column, Date, Integer, String, create_engine
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


Base.metadata.create_all(bind=engine)
