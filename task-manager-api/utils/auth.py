import time
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from repositories.user_repository import UserRepository

TOKEN_EXPIRATION_SECONDS = 24 * 60 * 60


def generate_token(user):
    now = int(time.time())
    payload = {
        'sub': user.id,
        'role': user.role,
        'iat': now,
        'exp': now + TOKEN_EXPIRATION_SECONDS,
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def _decode_token(token):
    return jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])


def require_auth(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token de autenticação ausente'}), 401

        token = auth_header[len('Bearer '):].strip()
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token inválido'}), 401

        user = UserRepository().get_by_id(payload.get('sub'))
        if not user or not user.active:
            return jsonify({'error': 'Usuário inválido ou inativo'}), 401

        g.current_user = user
        return view_func(*args, **kwargs)

    return wrapper


def require_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if not user or not user.is_admin():
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        return view_func(*args, **kwargs)

    return wrapper
