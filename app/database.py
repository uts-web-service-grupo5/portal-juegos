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


Base.metadata.create_all(bind=engine)
