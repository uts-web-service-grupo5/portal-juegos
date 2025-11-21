1
from sqlalchemy import create_engine, Column, Integer, String
# Importa herramientas de SQLAlchemy para crear la base de datos
2
from sqlalchemy.ext.declarative import declarative_base
# Para crear una clase base que usarán todos los modelos

from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./usuarios.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
# Clase base para todos los modelos de la base de datos

class UserDB(Base):
    # Define la estructura de la tabla "users" en la base de datos

    __tablename__ = "usuarios"

    #id = Column(Integer, primary_key=True, index=True)
    # Columna 'id': número entero, clave primaria, se autoincrementa

    #name = Column(String, nullable=False)

    #email = Column(String, unique=True, nullable=False)

    #age = Column(Integer)

    Base.metadata.create_all(bind=engine)