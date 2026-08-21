import os
import secrets

SECRET_KEY = os.environ.get("SECRET_KEY", "minha-chave-super-secreta-123")
DEBUG = True
DB_PATH = os.environ.get("DB_PATH", "loja.db")

ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    ADMIN_API_KEY = secrets.token_hex(32)
    print(
        "AVISO: variável de ambiente ADMIN_API_KEY não definida. "
        f"Chave temporária gerada para esta execução: {ADMIN_API_KEY}"
    )
    print("Defina ADMIN_API_KEY em produção com um valor fixo e seguro.")
