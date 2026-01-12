from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from clientes.database import SessionLocal, engine, Base
from clientes.models import Cliente
from pydantic import BaseModel

msg_cliente_nao_encontrado = "Cliente não encontrado"

Base.metadata.create_all(bind=engine)
app = FastAPI()

class ClienteCreate(BaseModel):
    nome: str
    email: str

class ClienteResponse(BaseModel):
    id: int
    nome: str
    email: str
    nivel_fidelidade: int
    class Config:
        orm_mode = True

class FidelidadeUpdate(BaseModel):
    incremento: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/clientes", response_model=ClienteResponse)
def criar_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    db_cliente = Cliente(nome=cliente.nome, email=cliente.email)
    db.add(db_cliente)
    db.commit()
    db.refresh(db_cliente)
    return db_cliente

@app.get("/clientes/{id}", response_model=ClienteResponse)
def get_cliente(id: int, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail=msg_cliente_nao_encontrado)
    return cliente

@app.patch("/clientes/{id}/fidelidade", response_model=ClienteResponse)
def atualizar_fidelidade(id: int, fidelidade: FidelidadeUpdate, db: Session = Depends(get_db)):
    cliente = db.query(Cliente).filter(Cliente.id == id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail=msg_cliente_nao_encontrado)
    cliente.nivel_fidelidade += fidelidade.incremento # type: ignore
    db.commit()
    db.refresh(cliente)
    return cliente

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
