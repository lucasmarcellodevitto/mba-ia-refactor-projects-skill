from werkzeug.security import check_password_hash, generate_password_hash

from errors import ValidationError
from repositories import usuarios_repository


def listar_usuarios():
    return usuarios_repository.find_all()


def buscar_usuario(usuario_id):
    return usuarios_repository.find_by_id(usuario_id)


def criar_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    senha_hash = generate_password_hash(senha)
    return usuarios_repository.create(nome, email, senha_hash)


def login(email, senha):
    usuario = usuarios_repository.find_by_email(email)
    if usuario and check_password_hash(usuario["senha"], senha):
        return {
            "id": usuario["id"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "tipo": usuario["tipo"],
        }
    return None
