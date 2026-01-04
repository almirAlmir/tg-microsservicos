
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from catalogo.database import SessionLocal, engine, Base
from catalogo.models import Produto
from pydantic import BaseModel
import httpx

Base.metadata.create_all(bind=engine)
app = FastAPI()

class ProdutoCreate(BaseModel):
    nome: str
    descricao: str
    preco: float

class ProdutoResponse(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float
    class Config:
        orm_mode = True

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/produtos", response_model=ProdutoResponse)
def criar_produto(produto: ProdutoCreate, db: Session = Depends(get_db)):
    db_produto = Produto(**produto.dict())
    db.add(db_produto)
    db.commit()
    db.refresh(db_produto)
    print(f"Produto criado com ID: {db_produto.id}")
    aviso = None
    if db_produto.id is not None:
        try:
            response = httpx.post(
                "http://localhost:8003/estoque/inicializar",
                json={"produto_id": db_produto.id, "quantidade": 0}
            )
            if response.status_code != 200:
                aviso = "Produto cadastrado, mas não foi possível inicializar o estoque."
        except Exception as e:
            aviso = f"Produto cadastrado, mas falha ao comunicar com o serviço de estoque: {str(e)}"
    if aviso:
        raise HTTPException(status_code=201, detail=aviso)
    return db_produto

@app.get("/produtos/{id}", response_model=ProdutoResponse)
def get_produto(id: int, db: Session = Depends(get_db)):
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return produto

@app.get("/produtos", response_model=list[ProdutoResponse])
def listar_produtos(db: Session = Depends(get_db)):
    produtos = db.query(Produto).all()
    return produtos

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
