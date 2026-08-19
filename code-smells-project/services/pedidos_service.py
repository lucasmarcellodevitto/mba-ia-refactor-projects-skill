from errors import ValidationError
from constants import STATUS_VALIDOS
from repositories import pedidos_repository, produtos_repository
from services import notificacoes_service


def criar_pedido(usuario_id, itens):
    produto_ids = [item["produto_id"] for item in itens]
    produtos_por_id = produtos_repository.find_by_ids(produto_ids)

    total = 0
    for item in itens:
        produto = produtos_por_id.get(item["produto_id"])
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total = total + (produto["preco"] * item["quantidade"])

    pedido_id = pedidos_repository.create_pedido_header(usuario_id, "pendente", total)

    for item in itens:
        produto = produtos_por_id[item["produto_id"]]
        pedidos_repository.create_item(pedido_id, item["produto_id"], item["quantidade"], produto["preco"])
        produtos_repository.decrement_estoque(item["produto_id"], item["quantidade"])

    pedidos_repository.commit()

    notificacoes_service.notificar_pedido_criado(pedido_id, usuario_id)

    return {"pedido_id": pedido_id, "total": total}


def get_pedidos_usuario(usuario_id):
    return _montar_pedidos(pedidos_repository.find_by_usuario(usuario_id))


def get_todos_pedidos():
    return _montar_pedidos(pedidos_repository.find_all())


def atualizar_status_pedido(pedido_id, novo_status):
    if novo_status not in STATUS_VALIDOS:
        raise ValidationError("Status inválido")

    pedidos_repository.update_status(pedido_id, novo_status)
    notificacoes_service.notificar_status_pedido(pedido_id, novo_status)


def _montar_pedidos(rows):
    pedido_ids = [row["id"] for row in rows]
    itens_por_pedido = pedidos_repository.find_itens_by_pedidos(pedido_ids)

    todos_produto_ids = {
        item["produto_id"]
        for itens in itens_por_pedido.values()
        for item in itens
    }
    produtos_por_id = produtos_repository.find_by_ids(todos_produto_ids)

    pedidos = []
    for row in rows:
        itens = itens_por_pedido.get(row["id"], [])
        pedidos.append({
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [
                {
                    "produto_id": item["produto_id"],
                    "produto_nome": produtos_por_id.get(item["produto_id"], {}).get("nome", "Desconhecido"),
                    "quantidade": item["quantidade"],
                    "preco_unitario": item["preco_unitario"],
                }
                for item in itens
            ],
        })
    return pedidos
