from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from estoque.database import SessionLocal, engine, Base
from estoque.models import Estoque
from pydantic import BaseModel

msg_produto_nao_encontrado_estoque = "Produto não encontrado no estoque"

Base.metadata.create_all(bind=engine)
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class EstoqueResponse(BaseModel):
    produto_id: int
    quantidade: int
    class Config:
        orm_mode = True

class BaixarEstoqueRequest(BaseModel):
    produto_id: int
    quantidade: int

class InicializarEstoqueRequest(BaseModel):
    produto_id: int
    quantidade: int

@app.post("/estoque/inicializar", response_model=EstoqueResponse)
def inicializar_estoque(request: InicializarEstoqueRequest, db: Session = Depends(get_db)):
    if db.query(Estoque).filter(Estoque.produto_id == request.produto_id).first():
        raise HTTPException(status_code=400, detail="Estoque já inicializado para este produto")
    novo_estoque = Estoque(produto_id=request.produto_id, quantidade=request.quantidade)
    db.add(novo_estoque)
    db.commit()
    db.refresh(novo_estoque)
    print(f"Estoque inicializado para produto_id: {novo_estoque.produto_id}")
    return novo_estoque

@app.post("/estoque/reabastecer", response_model=EstoqueResponse)
def reabastecer_estoque(request: BaixarEstoqueRequest, db: Session = Depends(get_db)):
    estoque = db.query(Estoque).filter(Estoque.produto_id == request.produto_id).first()
    if not estoque:
        raise HTTPException(status_code=404, detail=msg_produto_nao_encontrado_estoque)
    estoque.quantidade += request.quantidade
    db.commit()
    db.refresh(estoque)
    return estoque

class EstoqueResponse(BaseModel):
    produto_id: int
    quantidade: int
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/estoque/{produto_id}", response_model=EstoqueResponse)
def get_estoque(produto_id: int, db: Session = Depends(get_db)):
    estoque = db.query(Estoque).filter(Estoque.produto_id == produto_id).first()
    if not estoque:
        raise HTTPException(status_code=404, detail=msg_produto_nao_encontrado_estoque)
    return estoque

@app.post("/estoque/baixar", response_model=EstoqueResponse)
def baixar_estoque(request: BaixarEstoqueRequest, db: Session = Depends(get_db)):
    estoque = db.query(Estoque).filter(Estoque.produto_id == request.produto_id).first()
    if not estoque:
        raise HTTPException(status_code=404, detail=msg_produto_nao_encontrado_estoque)
    if estoque.quantidade < request.quantidade:
        raise HTTPException(status_code=400, detail="Saldo insuficiente")
    estoque.quantidade -= request.quantidade
    db.commit()
    db.refresh(estoque)
    return estoque

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
