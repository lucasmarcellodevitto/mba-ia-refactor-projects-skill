CATEGORIAS_VALIDAS = ["informatica", "moveis", "vestuario", "geral", "eletronicos", "livros"]

STATUS_VALIDOS = ["pendente", "aprovado", "enviado", "entregue", "cancelado"]

# (limite_faturamento, percentual_desconto) — ordenado do maior para o menor limite
FAIXAS_DESCONTO = [
    (10000, 0.10),
    (5000, 0.05),
    (1000, 0.02),
]
