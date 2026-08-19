import logging

from models.user import User
from repositories.user_repository import UserRepository
from repositories.task_repository import TaskRepository
from services.errors import (
    ValidationError,
    NotFoundError,
    ConflictError,
    UnauthorizedError,
    ForbiddenError,
    PersistenceError,
)
from utils.helpers import validate_email, MIN_PASSWORD_LENGTH, VALID_ROLES

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, user_repo=None, task_repo=None):
        self.user_repo = user_repo or UserRepository()
        self.task_repo = task_repo or TaskRepository()

    def list_users(self):
        users = self.user_repo.get_all()
        task_counts = self.task_repo.count_by_user()

        result = []
        for u in users:
            data = {
                'id': u.id,
                'name': u.name,
                'email': u.email,
                'role': u.role,
                'active': u.active,
                'created_at': str(u.created_at),
                'task_count': task_counts.get(u.id, 0),
            }
            result.append(data)
        return result

    def get_user(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        data = user.to_dict()
        tasks = self.task_repo.get_by_user_id(user_id)
        data['tasks'] = [t.to_dict() for t in tasks]
        return data

    def create_user(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')

        if not name:
            raise ValidationError('Nome é obrigatório')
        if not email:
            raise ValidationError('Email é obrigatório')
        if not password:
            raise ValidationError('Senha é obrigatória')
        if not validate_email(email):
            raise ValidationError('Email inválido')
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha deve ter no mínimo 4 caracteres')
        if self.user_repo.get_by_email(email):
            raise ConflictError('Email já cadastrado')
        if role not in VALID_ROLES:
            raise ValidationError('Role inválido')

        user = User()
        user.name = name
        user.email = email
        user.set_password(password)
        user.role = role

        try:
            self.user_repo.add(user)
            self.user_repo.commit()
        except Exception:
            self.user_repo.rollback()
            logger.exception('Erro ao criar usuário')
            raise PersistenceError('Erro ao criar usuário')

        logger.info('Usuário criado: %s - %s', user.id, user.name)
        return user.to_dict()

    def update_user(self, user_id, data):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        if not data:
            raise ValidationError('Dados inválidos')

        if 'name' in data:
            user.name = data['name']

        if 'email' in data:
            if not validate_email(data['email']):
                raise ValidationError('Email inválido')
            existing = self.user_repo.get_by_email(data['email'])
            if existing and existing.id != user_id:
                raise ConflictError('Email já cadastrado')
            user.email = data['email']

        if 'password' in data:
            if len(data['password']) < MIN_PASSWORD_LENGTH:
                raise ValidationError('Senha muito curta')
            user.set_password(data['password'])

        if 'role' in data:
            if data['role'] not in VALID_ROLES:
                raise ValidationError('Role inválido')
            user.role = data['role']

        if 'active' in data:
            user.active = data['active']

        try:
            self.user_repo.commit()
        except Exception:
            self.user_repo.rollback()
            logger.exception('Erro ao atualizar usuário')
            raise PersistenceError('Erro ao atualizar')

        return user.to_dict()

    def delete_user(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self.task_repo.get_by_user_id(user_id)
        for t in tasks:
            self.task_repo.delete(t)

        try:
            self.user_repo.delete(user)
            self.user_repo.commit()
        except Exception:
            self.user_repo.rollback()
            logger.exception('Erro ao deletar usuário')
            raise PersistenceError('Erro ao deletar')

        logger.info('Usuário deletado: %s', user_id)

    def get_user_tasks(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError('Usuário não encontrado')

        tasks = self.task_repo.get_by_user_id(user_id)
        result = []
        for t in tasks:
            data = {
                'id': t.id,
                'title': t.title,
                'description': t.description,
                'status': t.status,
                'priority': t.priority,
                'created_at': str(t.created_at),
                'due_date': str(t.due_date) if t.due_date else None,
                'overdue': t.is_overdue(),
            }
            result.append(data)
        return result

    def login(self, data):
        if not data:
            raise ValidationError('Dados inválidos')

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            raise ValidationError('Email e senha são obrigatórios')

        user = self.user_repo.get_by_email(email)
        if not user:
            raise UnauthorizedError('Credenciais inválidas')
        if not user.check_password(password):
            raise UnauthorizedError('Credenciais inválidas')
        if not user.active:
            raise ForbiddenError('Usuário inativo')

        return {
            'message': 'Login realizado com sucesso',
            'user': user.to_dict(),
            'token': 'fake-jwt-token-' + str(user.id),
        }
