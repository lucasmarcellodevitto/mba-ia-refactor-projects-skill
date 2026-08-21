import logging

from flask import jsonify, request

from auth import require_admin_auth
from errors import NotFoundError, ValidationError
from services import produtos_service

logger = logging.getLogger(__name__)


def listar_produtos():
    try:
        produtos = produtos_service.listar_produtos()
        return jsonify({"dados": produtos, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar produtos")
        return jsonify({"erro": "Erro interno"}), 500


def buscar_produto(id):
    try:
        produto = produtos_service.buscar_produto(id)
        if produto:
            return jsonify({"dados": produto, "sucesso": True}), 200
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    except Exception:
        logger.exception("Erro ao buscar produto")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def criar_produto():
    try:
        dados = request.get_json()
        produto_id = produtos_service.criar_produto(dados)
        logger.info("Produto criado com ID: %s", produto_id)
        return jsonify({"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}), 201
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao criar produto")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def atualizar_produto(id):
    try:
        dados = request.get_json()
        produtos_service.atualizar_produto(id, dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200
    except NotFoundError:
        return jsonify({"erro": "Produto não encontrado"}), 404
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao atualizar produto")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def deletar_produto(id):
    try:
        produtos_service.deletar_produto(id)
        logger.info("Produto %s deletado", id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
    except NotFoundError:
        return jsonify({"erro": "Produto não encontrado"}), 404
    except Exception:
        logger.exception("Erro ao deletar produto")
        return jsonify({"erro": "Erro interno"}), 500


def buscar_produtos():
    try:
        termo = request.args.get("q", "")
        categoria = request.args.get("categoria", None)
        preco_min = request.args.get("preco_min", None)
        preco_max = request.args.get("preco_max", None)

        if preco_min:
            preco_min = float(preco_min)
        if preco_max:
            preco_max = float(preco_max)

        resultados = produtos_service.buscar_produtos(termo, categoria, preco_min, preco_max)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao buscar produtos")
        return jsonify({"erro": "Erro interno"}), 500
