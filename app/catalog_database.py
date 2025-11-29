from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config.settings import settings

engine = create_engine(settings.catalog_db_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class GameDB(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    nombre_juego = Column(String, nullable=False)
    restriccion_edad = Column(Integer, nullable=False, default=0)
    acceso_plan = Column(String, nullable=False)  # valores separados por coma: Bronce,Plata,Oro
    descripcion = Column(String, nullable=True)
    genero = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)
