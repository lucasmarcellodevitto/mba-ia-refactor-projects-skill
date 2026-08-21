import logging

from flask import jsonify, request

from auth import require_admin_auth
from errors import ValidationError
from services import pedidos_service

logger = logging.getLogger(__name__)


def criar_pedido():
    try:
        dados = request.get_json()

        if not dados:
            return jsonify({"erro": "Dados inválidos"}), 400

        usuario_id = dados.get("usuario_id")
        itens = dados.get("itens", [])

        if not usuario_id:
            return jsonify({"erro": "Usuario ID é obrigatório"}), 400
        if not itens or len(itens) == 0:
            return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

        resultado = pedidos_service.criar_pedido(usuario_id, itens)

        if "erro" in resultado:
            return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso"
        }), 201

    except Exception:
        logger.exception("Erro crítico ao criar pedido")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def listar_pedidos_usuario(usuario_id):
    try:
        pedidos = pedidos_service.get_pedidos_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos do usuário")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def listar_todos_pedidos():
    try:
        pedidos = pedidos_service.get_todos_pedidos()
        return jsonify({"dados": pedidos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar pedidos")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def atualizar_status_pedido(pedido_id):
    try:
        dados = request.get_json()
        novo_status = dados.get("status", "")

        pedidos_service.atualizar_status_pedido(pedido_id, novo_status)

        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200

    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao atualizar status do pedido")
        return jsonify({"erro": "Erro interno"}), 500
