from sqlalchemy import Column, Integer
from .database import Base

class Estoque(Base):
    __tablename__ = "estoque"
    produto_id = Column(Integer, primary_key=True, index=True, autoincrement=False)
    quantidade = Column(Integer, nullable=False)
