from flask import Blueprint, request, jsonify, g

from services.user_service import UserService
from services.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    PersistenceError,
)
from utils.auth import require_auth

user_bp = Blueprint('users', __name__)
user_service = UserService()


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        return jsonify(user_service.get_user(user_id)), 200
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    try:
        user = user_service.create_user(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(user), 201


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    data = request.get_json()
    try:
        user = user_service.update_user(user_id, data, g.current_user)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except ConflictError as e:
        return jsonify({'error': str(e)}), 409
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(user), 200


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_auth
def delete_user(user_id):
    try:
        user_service.delete_user(user_id, g.current_user)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Usuário deletado com sucesso'}), 200


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    try:
        return jsonify(user_service.get_user_tasks(user_id)), 200
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    try:
        result = user_service.login(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except UnauthorizedError as e:
        return jsonify({'error': str(e)}), 401
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    return jsonify(result), 200
