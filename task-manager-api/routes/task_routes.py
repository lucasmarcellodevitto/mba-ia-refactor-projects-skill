import logging

from flask import Blueprint, request, jsonify, g

from services.task_service import TaskService
from services.errors import ValidationError, NotFoundError, ForbiddenError, PersistenceError
from utils.auth import require_auth

task_bp = Blueprint('tasks', __name__)
task_service = TaskService()
logger = logging.getLogger(__name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    try:
        return jsonify(task_service.list_tasks()), 200
    except Exception:
        logger.exception('Erro ao listar tasks')
        return jsonify({'error': 'Erro interno'}), 500


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        return jsonify(task_service.get_task(task_id)), 200
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@task_bp.route('/tasks', methods=['POST'])
@require_auth
def create_task():
    data = request.get_json()
    try:
        task = task_service.create_task(data, g.current_user)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(task), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@require_auth
def update_task(task_id):
    data = request.get_json()
    try:
        task = task_service.update_task(task_id, data, g.current_user)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(task), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@require_auth
def delete_task(task_id):
    try:
        task_service.delete_task(task_id, g.current_user)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except ForbiddenError as e:
        return jsonify({'error': str(e)}), 403
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')
    return jsonify(task_service.search_tasks(query, status, priority, user_id)), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    return jsonify(task_service.get_stats()), 200
