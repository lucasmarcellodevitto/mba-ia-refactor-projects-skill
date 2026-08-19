from constants import FAIXAS_DESCONTO
from repositories import pedidos_repository


def relatorio_vendas():
    total_pedidos = pedidos_repository.count_all()
    faturamento = pedidos_repository.sum_total()
    if faturamento is None:
        faturamento = 0

    pendentes = pedidos_repository.count_by_status("pendente")
    aprovados = pedidos_repository.count_by_status("aprovado")
    cancelados = pedidos_repository.count_by_status("cancelado")

    desconto = 0
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            desconto = faturamento * percentual
            break

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
