import functools
import hmac

from flask import jsonify, request

import config


def require_admin_auth(view_func):
    """Guard reutilizável para rotas administrativas sensíveis.

    Exige o header `X-Admin-Api-Key` com o valor configurado em
    `config.ADMIN_API_KEY`. Segue o padrão de middleware/guard do
    refactoring-playbook (seção 4) para centralizar a verificação em vez de
    duplicá-la em cada handler.
    """

    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-Admin-Api-Key", "")
        if not api_key or not hmac.compare_digest(api_key, config.ADMIN_API_KEY):
            return jsonify({"erro": "Autenticação necessária", "sucesso": False}), 401
        return view_func(*args, **kwargs)

    return wrapper
