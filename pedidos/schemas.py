from pydantic import BaseModel

class PedidoRequest(BaseModel):
    cliente_id: int
    produto_id: int
    quantidade: int

class PedidoResponse(BaseModel):
    id: int
    cliente_id: int
    produto_id: int
    quantidade: int
    valor_total: float
    status: str
    class Config:
        orm_mode = True