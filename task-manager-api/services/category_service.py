import logging

from models.category import Category
from repositories.category_repository import CategoryRepository
from repositories.task_repository import TaskRepository
from services.errors import ValidationError, NotFoundError, PersistenceError
from utils.helpers import DEFAULT_COLOR

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, category_repo=None, task_repo=None):
        self.category_repo = category_repo or CategoryRepository()
        self.task_repo = task_repo or TaskRepository()

    def list_categories(self):
        categories = self.category_repo.get_all()
        task_counts = self.task_repo.count_by_category()

        result = []
        for c in categories:
            data = c.to_dict()
            data['task_count'] = task_counts.get(c.id, 0)
            result.append(data)
        return result

    def create_category(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        if not name:
            raise ValidationError('Nome é obrigatório')

        category = Category()
        category.name = name
        category.description = data.get('description', '')
        category.color = data.get('color', DEFAULT_COLOR)

        try:
            self.category_repo.add(category)
            self.category_repo.commit()
        except Exception:
            self.category_repo.rollback()
            logger.exception('Erro ao criar categoria')
            raise PersistenceError('Erro ao criar categoria')

        return category.to_dict()

    def update_category(self, cat_id, data):
        cat = self.category_repo.get_by_id(cat_id)
        if not cat:
            raise NotFoundError('Categoria não encontrada')

        if 'name' in data:
            cat.name = data['name']
        if 'description' in data:
            cat.description = data['description']
        if 'color' in data:
            cat.color = data['color']

        try:
            self.category_repo.commit()
        except Exception:
            self.category_repo.rollback()
            logger.exception('Erro ao atualizar categoria')
            raise PersistenceError('Erro ao atualizar')

        return cat.to_dict()

    def delete_category(self, cat_id):
        cat = self.category_repo.get_by_id(cat_id)
        if not cat:
            raise NotFoundError('Categoria não encontrada')

        try:
            self.category_repo.delete(cat)
            self.category_repo.commit()
        except Exception:
            self.category_repo.rollback()
            logger.exception('Erro ao deletar categoria')
            raise PersistenceError('Erro ao deletar')
