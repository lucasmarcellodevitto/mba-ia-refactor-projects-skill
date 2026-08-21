import logging

from flask import jsonify, request

from auth import require_admin_auth
from errors import ValidationError
from services import usuarios_service

logger = logging.getLogger(__name__)


@require_admin_auth
def listar_usuarios():
    try:
        usuarios = usuarios_service.listar_usuarios()
        return jsonify({"dados": usuarios, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao listar usuários")
        return jsonify({"erro": "Erro interno"}), 500


@require_admin_auth
def buscar_usuario(id):
    try:
        usuario = usuarios_service.buscar_usuario(id)
        if usuario:
            return jsonify({"dados": usuario, "sucesso": True}), 200
        return jsonify({"erro": "Usuário não encontrado"}), 404
    except Exception:
        logger.exception("Erro ao buscar usuário")
        return jsonify({"erro": "Erro interno"}), 500


def criar_usuario():
    try:
        dados = request.get_json()
        usuario_id = usuarios_service.criar_usuario(dados)
        logger.info("Usuário criado: %s", (dados or {}).get("email", ""))
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201
    except ValidationError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception:
        logger.exception("Erro ao criar usuário")
        return jsonify({"erro": "Erro interno"}), 500


def login():
    try:
        dados = request.get_json()
        email = dados.get("email", "")
        senha = dados.get("senha", "")

        if not email or not senha:
            return jsonify({"erro": "Email e senha são obrigatórios"}), 400

        usuario = usuarios_service.login(email, senha)
        if usuario:
            logger.info("Login bem-sucedido: %s", email)
            return jsonify({"dados": usuario, "sucesso": True, "mensagem": "Login OK"}), 200

        logger.info("Login falhou: %s", email)
        return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
    except Exception:
        logger.exception("Erro no login")
        return jsonify({"erro": "Erro interno"}), 500
