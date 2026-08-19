from database import get_db


def create_pedido_header(usuario_id, status, total):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
        (usuario_id, status, total)
    )
    return cursor.lastrowid


def create_item(pedido_id, produto_id, quantidade, preco_unitario):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
        (pedido_id, produto_id, quantidade, preco_unitario)
    )


def commit():
    get_db().commit()


def find_by_usuario(usuario_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
    return cursor.fetchall()


def find_all():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM pedidos")
    return cursor.fetchall()


def find_itens_by_pedidos(pedido_ids):
    pedido_ids = list(pedido_ids)
    if not pedido_ids:
        return {}
    db = get_db()
    cursor = db.cursor()
    placeholders = ",".join("?" for _ in pedido_ids)
    cursor.execute(
        f"SELECT * FROM itens_pedido WHERE pedido_id IN ({placeholders})",
        pedido_ids
    )
    itens_por_pedido = {}
    for item in cursor.fetchall():
        itens_por_pedido.setdefault(item["pedido_id"], []).append(item)
    return itens_por_pedido


def update_status(pedido_id, novo_status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id)
    )
    db.commit()


def count_all():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos")
    return cursor.fetchone()[0]


def sum_total():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT SUM(total) FROM pedidos")
    return cursor.fetchone()[0]


def count_by_status(status):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) FROM pedidos WHERE status = ?", (status,))
    return cursor.fetchone()[0]
