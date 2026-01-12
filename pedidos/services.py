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

#Nova classe para isolar a complexidade da rede, do sistema
class ClienteIntegration:
    async def pontuar_fidelidade(self, cliente_id: int, valor_total: float):
        if valor_total <= 100:
            return
        
        async with httpx.AsyncClient() as client:
            try:
                print(f"[INTEGRAÇÃO] Tentando conexão: {CLIENTES_URL}...")
                response = await client.patch(
                    f"{CLIENTES_URL}/clientes/{cliente_id}/fidelidade",
                    json={"incremento": 10},
                    timeout=2.5
                )
                response.raise_for_status()
                print("[INTEGRAÇÃO] Fidelidade atualizada com sucesso")

            except httpx.ConnectError:
                print("[ERRO DE CONEXÃO HTTP] Não foi possível conectar a Clientes")

            except httpx.TimeoutException:
                print("[ERRO DE TEMPO LIMITE EXCEDIDO] Serviço de Clientes muito lento")

            except httpx.HTTPStatusError as e:
                print("[ERRO DE NEGÓCIO] Serviço recusou: {e.response.status_code}")

#Mudança no PedidoService
class PedidoService:

    def __init__(self):
        #Buscando desacoplamento chamando o ClienteIntegration ao invés do httpx diretamente
        self.cliente_integration = ClienteIntegration()

    async def criar_pedido(self, pedido: PedidoRequest, db: Session):
        async with httpx.AsyncClient() as client:
            #catalogo
            resp_produto = await client.get(f"{CATALOGO_URL}/produtos/{pedido.produto_id}")
            if resp_produto.status_code != 200:
                raise HTTPException(status_code=404, detail="Produto não encontrado")
            
            produto = resp_produto.json()
            valor_total = produto["preco"] * pedido.quantidade

            #Estoque
            await client.post(
                f"{ESTOQUE_URL}/estoque/baixar",
                json={"produto_id": pedido.produto_id, "quantidade": pedido.quantidade}
            )
            
            #Persistencia - Salvando o Pedido antes para tentar Integrar
            status = "aprovado"
            pedido_db = Pedido(cliente_id=pedido.cliente_id, produto_id=pedido.produto_id, quantidade=pedido.quantidade, valor_total=valor_total, status=status)
            db.add(pedido_db)
            db.commit()
            db.refresh(pedido_db)

            #A Integração criada no método novo resolve tudo que antes era resolvido aqui
            await self.cliente_integration.pontuar_fidelidade(pedido.cliente_id, valor_total)

            return pedido_db