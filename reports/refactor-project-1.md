================================
REFACTORING REPORT
================================
Project: code-smells-project
Baseline: reports/audit-2026-08-18.md (20 findings)

Arquitetura resultante
- app.py            → registro de rotas (Flask), inalterado na superfície pública
- config.py          → configuração (SECRET_KEY/DB_PATH via variável de ambiente)
- constants.py       → constantes de domínio (categorias, status, faixas de desconto)
- errors.py          → exceções de domínio (ValidationError, NotFoundError)
- database.py        → ciclo de vida da conexão (flask.g, por request) + schema/seed
- repositories/       → acesso a dados, SQL 100% parametrizado, por domínio
- services/           → regras de negócio, validação, orquestração, por domínio
- controllers/        → parsing HTTP + delegação + serialização, por domínio

Findings corrigidos (relatório de auditoria → status)

[CRITICAL] SQL Injection via concatenação de strings → CORRIGIDO
  Todas as queries de repositories/*.py usam parametrização (`?`). Validado
  manualmente enviando payloads de injeção em nome/email/termo de busca/login
  (ex.: email "x' OR '1'='1") — tratados como valor literal, sem alterar
  estrutura da query nem autenticar indevidamente.

[CRITICAL] Endpoint /admin/query sem autenticação → NÃO ALTERADO (decisão do usuário)
  Usuário optou por "manter como está". Comportamento e contrato preservados
  integralmente. Risco permanece registrado no relatório de auditoria.

[CRITICAL] Endpoint /admin/reset-db sem autenticação → NÃO ALTERADO (decisão do usuário)
  Mesma decisão acima.

[CRITICAL] SECRET_KEY hardcoded → PARCIALMENTE CORRIGIDO
  config.py agora lê SECRET_KEY de os.environ, com fallback para o mesmo
  valor atual ("minha-chave-super-secreta-123") para não alterar o
  comportamento de boot sem configuração adicional. Para remediação completa,
  definir a variável de ambiente SECRET_KEY em produção.

[CRITICAL] Exposição de secret_key/debug em /health → NÃO ALTERADO (decisão do usuário)
  Resposta de GET /health preservada campo a campo, incluindo secret_key e
  debug. Risco permanece registrado no relatório de auditoria.

[CRITICAL] Senha em texto plano → CORRIGIDO (armazenamento), campo mantido (decisão do usuário)
  - Novas senhas são gravadas com werkzeug.security.generate_password_hash
    (services/usuarios_service.py).
  - Senhas pré-existentes no loja.db (texto plano) foram migradas para hash
    automaticamente na inicialização (database.py:_migrar_senhas_texto_plano),
    preservando as credenciais atuais — validado via POST /login com as
    credenciais originais (admin@loja.com/admin123) após a migração: 200 OK.
  - O campo "senha" continua presente em GET /usuarios e GET /usuarios/<id>
    (decisão explícita do usuário), porém agora contém o hash, não mais o
    valor original.

[HIGH] God Module (models.py) → CORRIGIDO
  Substituído por repositories/ (acesso a dados) e services/ (regras de
  negócio), um arquivo por domínio.

[HIGH] Responsabilidade excessiva nos controllers → CORRIGIDO
  Validação de negócio movida para services/*_service.py. Notificações
  (email/SMS/push simulados) extraídas para services/notificacoes_service.py.

[HIGH] Acoplamento forte à implementação concreta do banco → CORRIGIDO
  Controllers e services não acessam mais sqlite3 diretamente; toda leitura/
  escrita passa pelos repositories, que encapsulam get_db().

[HIGH] Estado global mutável compartilhado (conexão) → CORRIGIDO
  database.py agora usa flask.g com uma conexão por request, fechada em
  teardown_appcontext, eliminando a conexão global mutável compartilhada.

[HIGH] Ausência sistêmica de autenticação/autorização → NÃO IMPLEMENTADO (decisão do usuário)
  Fora de escopo desta refatoração por decisão explícita — mudaria o
  contrato de quase todos os endpoints de escrita.

[MEDIUM] Queries N+1 ao montar pedidos → CORRIGIDO
  services/pedidos_service.py:_montar_pedidos busca itens e produtos em lote
  (IN (...)) em vez de uma query por pedido/item. Validado via
  GET /pedidos/usuario/<id> e GET /pedidos — mesma estrutura de resposta.

[MEDIUM] Queries redundantes em criar_pedido → CORRIGIDO
  services/pedidos_service.py:criar_pedido busca os produtos uma única vez
  (find_by_ids) e reaproveita o resultado na validação de estoque e na
  inserção dos itens.

[MEDIUM] Tratamento de erro genérico expõe detalhes internos → CORRIGIDO (parcial)
  Nos controllers de produtos/usuarios/pedidos/relatórios, o `except
  Exception` genérico agora loga a exceção real via `logging` e responde
  com {"erro": "Erro interno"} em vez do texto cru da exceção. Mantém
  status code 500 e a mesma estrutura de campos — só o conteúdo da
  mensagem muda. Os endpoints administrativos (/health, /admin/query)
  foram deixados como estavam, por decisão do usuário sobre não alterar
  esse grupo de rotas.

[MEDIUM] Validação insuficiente de tipos (preco/estoque) → NÃO ALTERADO
  Corrigir isso mudaria o status code de 500 para 400 em entradas
  malformadas — um contrato protegido pelas regras invioláveis da skill.
  Mantido como estava; segue registrado como risco conhecido.

[MEDIUM] Duplicação significativa de lógica → CORRIGIDO
  - Validação comum de produto extraída para
    services/produtos_service.py:_validar_campos_obrigatorios (mantendo
    deliberadamente a diferença pré-existente entre criar e atualizar —
    atualizar não valida tamanho de nome nem categoria, como no original).
  - Serialização de produto centralizada em
    repositories/produtos_repository.py:_serialize.
  - Montagem de pedidos com itens centralizada em
    services/pedidos_service.py:_montar_pedidos (usada por
    get_pedidos_usuario e get_todos_pedidos).

[LOW] print() como logging → CORRIGIDO
  Todo print() de diagnóstico/notificação substituído por `logging`
  (configurado em app.py com basicConfig).

[LOW] Magic numbers/listas sem constante → CORRIGIDO
  CATEGORIAS_VALIDAS, STATUS_VALIDOS e FAIXAS_DESCONTO movidos para
  constants.py.

[LOW] Nomenclatura pouco expressiva (cursor2/cursor3) → CORRIGIDO
  Eliminado junto da reestruturação em repositories (cursores nomeados
  implicitamente pela função que os usa; não há mais cursores auxiliares
  soltos em loops aninhados).

[LOW] Informação de ambiente inconsistente em /health → NÃO ALTERADO (decisão do usuário)
  Endpoint /health preservado integralmente.

Validação funcional executada
- `python -c "import app"` — importação limpa, migração de senha executada
  sem erro.
- Servidor iniciado (`python app.py`) e testado manualmente via curl:
  GET /, GET /health, GET /produtos, GET /produtos/<id> (200 e 404),
  GET /produtos/busca?q=..., POST /produtos (incl. payload de SQL
  injection no nome — não afetou o banco), PUT /produtos/<id>,
  DELETE /produtos/<id>, GET /usuarios (campo senha = hash),
  POST /login (credenciais corretas, incorretas e payload de injeção no
  email — todos com o status esperado), POST /pedidos, GET
  /pedidos/usuario/<id>, PUT /pedidos/<id>/status, GET /relatorios/vendas,
  POST /admin/query.
- Todas as respostas mantiveram exatamente as mesmas rotas, métodos,
  campos e status codes do baseline da Fase 1, exceto o valor (não o
  campo) de "senha" em GET /usuarios/GET /usuarios/<id>, alteração
  aprovada explicitamente pelo usuário.

Mudanças de contrato/comportamento avaliadas e NÃO aplicadas (por decisão do usuário)
- Autenticação em /admin/reset-db e /admin/query.
- Remoção de secret_key/debug da resposta de /health.
- Remoção do campo senha de GET /usuarios e GET /usuarios/<id>.
- Autenticação/autorização sistêmica nos endpoints de escrita.
- Validação de tipo para preco/estoque (mudaria 500→400 em entrada inválida).

Essas 5 pendências continuam registradas como riscos conhecidos no
relatório de auditoria (reports/audit-2026-08-18.md) e requerem aprovação
explícita adicional caso o usuário queira corrigi-las em uma próxima
iteração.
================================
