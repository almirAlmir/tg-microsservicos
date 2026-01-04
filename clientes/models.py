from sqlalchemy import Column, Integer, String
from .database import Base

class Cliente(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    nivel_fidelidade = Column(Integer, default=0)
