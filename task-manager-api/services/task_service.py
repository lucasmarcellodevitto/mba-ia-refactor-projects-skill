import logging
from datetime import datetime

from models.task import Task
from repositories.task_repository import TaskRepository
from repositories.user_repository import UserRepository
from repositories.category_repository import CategoryRepository
from services.errors import ValidationError, NotFoundError, PersistenceError
from utils.helpers import (
    MIN_TITLE_LENGTH,
    MAX_TITLE_LENGTH,
    DEFAULT_PRIORITY,
    calculate_percentage,
    utcnow,
)

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, task_repo=None, user_repo=None, category_repo=None):
        self.task_repo = task_repo or TaskRepository()
        self.user_repo = user_repo or UserRepository()
        self.category_repo = category_repo or CategoryRepository()

    def list_tasks(self):
        tasks = self.task_repo.get_all()

        user_ids = {t.user_id for t in tasks if t.user_id}
        category_ids = {t.category_id for t in tasks if t.category_id}
        users_by_id = {u.id: u for u in self.user_repo.get_by_ids(user_ids)}
        categories_by_id = {c.id: c for c in self.category_repo.get_by_ids(category_ids)}

        result = []
        for t in tasks:
            data = t.to_dict()
            data['overdue'] = t.is_overdue()
            user = users_by_id.get(t.user_id) if t.user_id else None
            data['user_name'] = user.name if user else None
            category = categories_by_id.get(t.category_id) if t.category_id else None
            data['category_name'] = category.name if category else None
            result.append(data)

        return result

    def get_task(self, task_id):
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return data

    def create_task(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        title = data.get('title')
        self._validate_title(title)

        description = data.get('description', '')
        status = data.get('status', 'pending')
        priority = data.get('priority', DEFAULT_PRIORITY)
        user_id = data.get('user_id')
        category_id = data.get('category_id')
        due_date = data.get('due_date')
        tags = data.get('tags')

        if not Task.validate_status(status):
            raise ValidationError('Status inválido')
        if not Task.validate_priority(priority):
            raise ValidationError('Prioridade deve ser entre 1 e 5')

        if user_id and not self.user_repo.get_by_id(user_id):
            raise NotFoundError('Usuário não encontrado')
        if category_id and not self.category_repo.get_by_id(category_id):
            raise NotFoundError('Categoria não encontrada')

        task = Task()
        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date:
            task.due_date = self._parse_due_date(
                due_date, 'Formato de data inválido. Use YYYY-MM-DD'
            )

        if tags:
            task.tags = ','.join(tags) if isinstance(tags, list) else tags

        try:
            self.task_repo.add(task)
            self.task_repo.commit()
        except Exception:
            self.task_repo.rollback()
            logger.exception('Erro ao criar task')
            raise PersistenceError('Erro ao criar task')

        logger.info('Task criada: %s - %s', task.id, task.title)
        return task.to_dict()

    def update_task(self, task_id, data):
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        if not data:
            raise ValidationError('Dados inválidos')

        if 'title' in data:
            if len(data['title']) < MIN_TITLE_LENGTH:
                raise ValidationError('Título muito curto')
            if len(data['title']) > MAX_TITLE_LENGTH:
                raise ValidationError('Título muito longo')
            task.title = data['title']

        if 'description' in data:
            task.description = data['description']

        if 'status' in data:
            if not Task.validate_status(data['status']):
                raise ValidationError('Status inválido')
            task.status = data['status']

        if 'priority' in data:
            if not Task.validate_priority(data['priority']):
                raise ValidationError('Prioridade deve ser entre 1 e 5')
            task.priority = data['priority']

        if 'user_id' in data:
            if data['user_id'] and not self.user_repo.get_by_id(data['user_id']):
                raise NotFoundError('Usuário não encontrado')
            task.user_id = data['user_id']

        if 'category_id' in data:
            if data['category_id'] and not self.category_repo.get_by_id(data['category_id']):
                raise NotFoundError('Categoria não encontrada')
            task.category_id = data['category_id']

        if 'due_date' in data:
            if data['due_date']:
                task.due_date = self._parse_due_date(
                    data['due_date'], 'Formato de data inválido'
                )
            else:
                task.due_date = None

        if 'tags' in data:
            task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

        task.updated_at = utcnow()

        try:
            self.task_repo.commit()
        except Exception:
            self.task_repo.rollback()
            logger.exception('Erro ao atualizar task')
            raise PersistenceError('Erro ao atualizar')

        logger.info('Task atualizada: %s', task.id)
        return task.to_dict()

    def delete_task(self, task_id):
        task = self.task_repo.get_by_id(task_id)
        if not task:
            raise NotFoundError('Task não encontrada')

        try:
            self.task_repo.delete(task)
            self.task_repo.commit()
        except Exception:
            self.task_repo.rollback()
            logger.exception('Erro ao deletar task')
            raise PersistenceError('Erro ao deletar')

        logger.info('Task deletada: %s', task_id)

    def search_tasks(self, query, status, priority, user_id):
        tasks = self.task_repo.search(
            query=query or None,
            status=status or None,
            priority=int(priority) if priority else None,
            user_id=int(user_id) if user_id else None,
        )
        return [t.to_dict() for t in tasks]

    def get_stats(self):
        total = self.task_repo.count_all()
        done = self.task_repo.count_by_status('done')
        overdue_count = sum(1 for t in self.task_repo.get_all() if t.is_overdue())

        return {
            'total': total,
            'pending': self.task_repo.count_by_status('pending'),
            'in_progress': self.task_repo.count_by_status('in_progress'),
            'done': done,
            'cancelled': self.task_repo.count_by_status('cancelled'),
            'overdue': overdue_count,
            'completion_rate': calculate_percentage(done, total),
        }

    @staticmethod
    def _validate_title(title):
        if not title:
            raise ValidationError('Título é obrigatório')
        if len(title) < MIN_TITLE_LENGTH:
            raise ValidationError('Título muito curto')
        if len(title) > MAX_TITLE_LENGTH:
            raise ValidationError('Título muito longo')

    @staticmethod
    def _parse_due_date(due_date, error_message):
        try:
            return datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(error_message)
