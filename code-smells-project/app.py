import logging

from flask import Flask
from flask_cors import CORS

import config
import database
from controllers import (
    pedidos_controller,
    produtos_controller,
    relatorios_controller,
    sistema_controller,
    usuarios_controller,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["DEBUG"] = config.DEBUG
CORS(app)

database.init_app(app)
database.init_db()

app.add_url_rule("/produtos", "listar_produtos", produtos_controller.listar_produtos, methods=["GET"])
app.add_url_rule("/produtos/busca", "buscar_produtos", produtos_controller.buscar_produtos, methods=["GET"])
app.add_url_rule("/produtos/<int:id>", "buscar_produto", produtos_controller.buscar_produto, methods=["GET"])
app.add_url_rule("/produtos", "criar_produto", produtos_controller.criar_produto, methods=["POST"])
app.add_url_rule("/produtos/<int:id>", "atualizar_produto", produtos_controller.atualizar_produto, methods=["PUT"])
app.add_url_rule("/produtos/<int:id>", "deletar_produto", produtos_controller.deletar_produto, methods=["DELETE"])

app.add_url_rule("/usuarios", "listar_usuarios", usuarios_controller.listar_usuarios, methods=["GET"])
app.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuarios_controller.buscar_usuario, methods=["GET"])
app.add_url_rule("/usuarios", "criar_usuario", usuarios_controller.criar_usuario, methods=["POST"])
app.add_url_rule("/login", "login", usuarios_controller.login, methods=["POST"])

app.add_url_rule("/pedidos", "criar_pedido", pedidos_controller.criar_pedido, methods=["POST"])
app.add_url_rule("/pedidos", "listar_todos_pedidos", pedidos_controller.listar_todos_pedidos, methods=["GET"])
app.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_pedidos_usuario",
    pedidos_controller.listar_pedidos_usuario,
    methods=["GET"],
)
app.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status_pedido",
    pedidos_controller.atualizar_status_pedido,
    methods=["PUT"],
)

app.add_url_rule("/relatorios/vendas", "relatorio_vendas", relatorios_controller.relatorio_vendas, methods=["GET"])

app.add_url_rule("/health", "health_check", sistema_controller.health_check, methods=["GET"])
app.add_url_rule("/", "index", sistema_controller.index, methods=["GET"])
app.add_url_rule("/admin/reset-db", "reset_database", sistema_controller.reset_database, methods=["POST"])
app.add_url_rule("/admin/query", "executar_query", sistema_controller.executar_query, methods=["POST"])

if __name__ == "__main__":
    print("=" * 50)
    print("SERVIDOR INICIADO")
    print("Rodando em http://localhost:5000")
    print("=" * 50)

    app.run(host="0.0.0.0", port=5000, debug=True)
