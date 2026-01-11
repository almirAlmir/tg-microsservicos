import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pedidos.models import Pedido
from pedidos.schemas import PedidoRequest

msg_produto_nao_encontrado_estoque = "Produto não encontrado no estoque"

# Configuração das urls dos outros microsserviços
CATALOGO_URL = "http://localhost:8002"
ESTOQUE_URL = "http://localhost:8003"
CLIENTES_URL = "http://localhost:8001"

class PedidoService:
    async def criar_pedido(self, pedido: PedidoRequest, db: Session):
        async with httpx.AsyncClient() as client:
            #catalogo
            resp_produto = await client.get(f"{CATALOGO_URL}/produtos/{pedido.produto_id}")
            if resp_produto.status_code != 200:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            produto = resp_produto.json()
            valor_total = produto["preco"] * pedido.quantidade

            #Estoque
            resp_estoque = await client.post(
                f"{ESTOQUE_URL}/estoque/baixar",
                json={"produto_id": pedido.produto_id, "quantidade": pedido.quantidade}
            )
            
            #Validação
            if resp_estoque.status_code == 400:
                status = "rejeitado"
                pedido_db = Pedido(cliente_id=pedido.cliente_id, produto_id=pedido.produto_id, quantidade=pedido.quantidade, valor_total=valor_total, status=status)
                db.add(pedido_db)
                db.commit()
                raise HTTPException(status_code=400, detail="Saldo insuficiente")
            
            elif resp_estoque.status_code != 200:
                raise HTTPException(status_code=404, detail=msg_produto_nao_encontrado_estoque)

            #Persistencia
            status = "aprovado"
            pedido_db = Pedido(cliente_id=pedido.cliente_id, produto_id=pedido.produto_id, quantidade=pedido.quantidade, valor_total=valor_total, status=status)
            db.add(pedido_db)
            db.commit()
            db.refresh(pedido_db)

            #Lógica de Fidelidade
            if valor_total > 100:
                await client.patch(f"{CLIENTES_URL}/clientes/{pedido.cliente_id}/fidelidade", json={"incremento": 10})

            return pedido_db