from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pedidos.database import SessionLocal, engine, Base
from pedidos.schemas import PedidoRequest, PedidoResponse # type: ignore
from pedidos.services import PedidoService

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/pedidos", response_model=PedidoResponse)
async def criar_pedido(pedido: PedidoRequest, db: Session = Depends(get_db)):
   service = PedidoService()
   return await service.criar_pedido(pedido, db) 

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)