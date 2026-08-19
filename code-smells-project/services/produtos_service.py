from constants import CATEGORIAS_VALIDAS
from errors import NotFoundError, ValidationError
from repositories import produtos_repository


def listar_produtos():
    return produtos_repository.find_all()


def buscar_produto(produto_id):
    return produtos_repository.find_by_id(produto_id)


def buscar_produtos(termo, categoria=None, preco_min=None, preco_max=None):
    return produtos_repository.search(termo, categoria, preco_min, preco_max)


def criar_produto(dados):
    nome, descricao, preco, estoque, categoria = _validar_campos_obrigatorios(dados)

    if len(nome) < 2:
        raise ValidationError("Nome muito curto")
    if len(nome) > 200:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {CATEGORIAS_VALIDAS}")

    return produtos_repository.create(nome, descricao, preco, estoque, categoria)


def atualizar_produto(produto_id, dados):
    if not produtos_repository.find_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")

    nome, descricao, preco, estoque, categoria = _validar_campos_obrigatorios(dados)
    produtos_repository.update(produto_id, nome, descricao, preco, estoque, categoria)


def deletar_produto(produto_id):
    if not produtos_repository.find_by_id(produto_id):
        raise NotFoundError("Produto não encontrado")
    produtos_repository.delete(produto_id)


def _validar_campos_obrigatorios(dados):
    """Validação comum a criar/atualizar. Mantém intencionalmente as mesmas
    regras (e a mesma ausência de checagem de tamanho/categoria) que o
    fluxo de atualização já tinha antes da refatoração, para não alterar
    o contrato de PUT /produtos/<id>."""
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    descricao = dados.get("descricao", "")
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")

    return nome, descricao, preco, estoque, categoria
