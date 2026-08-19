class ServiceError(Exception):
    """Base para erros de serviço traduzidos em respostas HTTP pelo controller."""


class ValidationError(ServiceError):
    """Entrada inválida (mapeado para HTTP 400)."""


class NotFoundError(ServiceError):
    """Recurso não encontrado (mapeado para HTTP 404)."""


class ConflictError(ServiceError):
    """Conflito com estado existente (mapeado para HTTP 409)."""


class UnauthorizedError(ServiceError):
    """Credenciais inválidas (mapeado para HTTP 401)."""


class ForbiddenError(ServiceError):
    """Acesso negado (mapeado para HTTP 403)."""


class PersistenceError(ServiceError):
    """Falha ao persistir alterações (mapeado para HTTP 500)."""
