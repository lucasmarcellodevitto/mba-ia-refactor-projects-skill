import logging

from flask import jsonify

from services import relatorios_service

logger = logging.getLogger(__name__)


def relatorio_vendas():
    try:
        relatorio = relatorios_service.relatorio_vendas()
        return jsonify({"dados": relatorio, "sucesso": True}), 200
    except Exception:
        logger.exception("Erro ao gerar relatório de vendas")
        return jsonify({"erro": "Erro interno"}), 500
