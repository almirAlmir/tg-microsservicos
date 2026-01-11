import httpx
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pedidos.database import SessionLocal, engine, Base
from pedidos.models import Pedido
from pydantic import BaseModel

msg_produto_nao_encontrado_estoque = "Produto não encontrado no estoque"

Base.metadata.create_all(bind=engine)
app = FastAPI()

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/pedidos", response_model=PedidoResponse)
async def criar_pedido(pedido: PedidoRequest, db: Session = Depends(get_db)):
    async with httpx.AsyncClient() as client:
        # Consultar preço do produto
        resp_produto = await client.get(f"http://localhost:8002/produtos/{pedido.produto_id}")
        if resp_produto.status_code != 200:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        produto = resp_produto.json()
        valor_total = produto["preco"] * pedido.quantidade

        # Baixar estoque
        resp_estoque = await client.post(
            "http://localhost:8003/estoque/baixar",
            json={"produto_id": pedido.produto_id, "quantidade": pedido.quantidade}
        )
        if resp_estoque.status_code == 400:
            status = "rejeitado"
            pedido_db = Pedido(
                cliente_id=pedido.cliente_id,
                produto_id=pedido.produto_id,
                quantidade=pedido.quantidade,
                valor_total=valor_total,
                status=status
            )
            db.add(pedido_db)
            db.commit()
            db.refresh(pedido_db)
            raise HTTPException(status_code=400, detail="Saldo insuficiente")
        elif resp_estoque.status_code != 200:
            raise HTTPException(status_code=404, detail=msg_produto_nao_encontrado_estoque)

        # Persistir pedido como aprovado
        status = "aprovado"
        pedido_db = Pedido(
            cliente_id=pedido.cliente_id,
            produto_id=pedido.produto_id,
            quantidade=pedido.quantidade,
            valor_total=valor_total,
            status=status
        )
        db.add(pedido_db)
        db.commit()
        db.refresh(pedido_db)

        # Regra de fidelidade
        if valor_total > 100:
            await client.patch(
                f"http://localhost:8001/clientes/{pedido.cliente_id}/fidelidade",
                json={"incremento": 10}
            )

        return pedido_db

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
