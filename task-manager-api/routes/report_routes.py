from flask import Blueprint, request, jsonify

from services.report_service import ReportService
from services.category_service import CategoryService
from services.errors import ValidationError, NotFoundError, PersistenceError

report_bp = Blueprint('reports', __name__)
report_service = ReportService()
category_service = CategoryService()


@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():
    return jsonify(report_service.summary_report()), 200


@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    try:
        return jsonify(report_service.user_report(user_id)), 200
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404


@report_bp.route('/categories', methods=['GET'])
def get_categories():
    return jsonify(category_service.list_categories()), 200


@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    try:
        category = category_service.create_category(data)
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(category), 201


@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    data = request.get_json()
    try:
        category = category_service.update_category(cat_id, data)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify(category), 200


@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    try:
        category_service.delete_category(cat_id)
    except NotFoundError as e:
        return jsonify({'error': str(e)}), 404
    except PersistenceError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': 'Categoria deletada'}), 200
