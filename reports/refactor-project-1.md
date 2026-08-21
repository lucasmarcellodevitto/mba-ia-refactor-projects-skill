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

## Rotas protegidas com `@require_admin_auth`

| Rota | Método | Observação |
|---|---|---|
| `/admin/reset-db` | POST | ponto original solicitado |
| `/admin/query` | POST | ponto original solicitado |
| `/produtos` | POST | criação de produto |
| `/produtos/<id>` | PUT | atualização de produto |
| `/produtos/<id>` | DELETE | exclusão de produto |
| `/usuarios` | GET | listagem — expunha hash da senha |
| `/usuarios/<id>` | GET | busca — expunha hash da senha |
| `/pedidos` | GET | listagem de todos os pedidos |
| `/pedidos/usuario/<id>` | GET | listagem de pedidos por usuário |
| `/pedidos/<id>/status` | PUT | alteração de status do pedido |
| `/relatorios/vendas` | GET | relatório de vendas |

Rotas de catálogo/checkout público **não foram alteradas**: `GET /produtos`,
`GET /produtos/<id>`, `GET /produtos/busca`, `POST /usuarios` (cadastro),
`POST /login`, `POST /pedidos` (criar pedido).

## O que mudou

- Anti-pattern corrigido: **Falta de autenticação/autorização** (item 4 do
  `refactoring-playbook.md`).
- Novo módulo [`auth.py`](../auth.py): decorator `require_admin_auth`,
  reutilizável, aplicado em todas as rotas da tabela acima.
- [`controllers/sistema_controller.py`](../controllers/sistema_controller.py):
  `reset_database` e `executar_query` agora usam `@require_admin_auth`. Os
  comentários que documentavam a exceção de autenticação foram removidos —
  não fazem mais sentido, o gap foi corrigido.
- [`controllers/produtos_controller.py`](../controllers/produtos_controller.py),
  [`controllers/usuarios_controller.py`](../controllers/usuarios_controller.py),
  [`controllers/pedidos_controller.py`](../controllers/pedidos_controller.py) e
  [`controllers/relatorios_controller.py`](../controllers/relatorios_controller.py):
  handlers da tabela acima decorados com `@require_admin_auth`.
- [`config.py`](../config.py): nova configuração `ADMIN_API_KEY`, lida de
  variável de ambiente (mesmo padrão já usado por `SECRET_KEY` e `DB_PATH`).

### Exemplos de chamada — referência completa

Em todos os exemplos, substitua `<ADMIN_API_KEY>` pelo valor real (o
configurado via variável de ambiente, ou o gerado no console em modo dev).

**`POST /admin/reset-db`**
```bash
curl -X POST http://localhost:5000/admin/reset-db \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`POST /admin/query`**
```bash
curl -X POST http://localhost:5000/admin/query \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT COUNT(*) FROM produtos"}'
```

**`POST /produtos`** (criar produto)
```bash
curl -X POST http://localhost:5000/produtos \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Produto X", "descricao": "Descrição", "preco": 10.0, "estoque": 5, "categoria": "geral"}'
```

**`PUT /produtos/<id>`** (atualizar produto)
```bash
curl -X PUT http://localhost:5000/produtos/1 \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"nome": "Produto X atualizado", "descricao": "Descrição", "preco": 12.5, "estoque": 8, "categoria": "geral"}'
```

**`DELETE /produtos/<id>`**
```bash
curl -X DELETE http://localhost:5000/produtos/1 \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`GET /usuarios`** (listar usuários)
```bash
curl http://localhost:5000/usuarios \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`GET /usuarios/<id>`** (buscar usuário)
```bash
curl http://localhost:5000/usuarios/1 \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`GET /pedidos`** (listar todos os pedidos)
```bash
curl http://localhost:5000/pedidos \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`GET /pedidos/usuario/<id>`** (listar pedidos de um usuário)
```bash
curl http://localhost:5000/pedidos/usuario/1 \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

**`PUT /pedidos/<id>/status`** (atualizar status do pedido)
```bash
curl -X PUT http://localhost:5000/pedidos/1/status \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"status": "aprovado"}'
```

**`GET /relatorios/vendas`**
```bash
curl http://localhost:5000/relatorios/vendas \
  -H "X-Admin-Api-Key: <ADMIN_API_KEY>"
```

Sem o header, ou com um valor incorreto, a resposta passa a ser:

```json
{"erro": "Autenticação necessária", "sucesso": false}
```
com status `401`.

## Mudança de contrato (aprovada pelo usuário)

Todas as rotas da tabela acima deixam de aceitar chamadas anônimas — antes
retornavam `200`/`201` para qualquer requisição, agora exigem o header
`X-Admin-Api-Key` válido e retornam `401` caso contrário. Para `/admin/reset-db`
e `/admin/query` essa mudança reverte a exceção registrada anteriormente no
relatório de auditoria; para as demais rotas (produtos, usuários, pedidos,
relatórios) foi solicitada e aprovada explicitamente pelo usuário durante esta
tarefa (via pergunta de confirmação), após a apresentação da lista de pontos
adicionais encontrados. Nenhum outro aspecto do contrato (método HTTP, path,
formato de request/response em caso de sucesso) foi alterado.

**Atenção — impacto em `GET /pedidos/usuario/<id>`:** esse endpoint era usado
por um cliente final para consultar os próprios pedidos. Como o projeto não
tem sessão/token de usuário (ver limitação abaixo), a única forma disponível
de protegê-lo foi a mesma API key de administrador. Na prática, isso remove o
acesso de clientes comuns a esse endpoint — só quem tiver `ADMIN_API_KEY`
consegue consultá-lo agora. Se o comportamento esperado é o cliente ver os
próprios pedidos, será necessário implementar autenticação de usuário
(sessão/token) antes desta rota poder ser reaberta para clientes.

## Validações executadas

- Sintaxe (`ast.parse`) de `auth.py`, `config.py` e dos cinco controllers
  alterados.
- Aplicação iniciada localmente (`ADMIN_API_KEY` de teste via env var):
  - Rotas protegidas sem header ou com chave incorreta → `401` em todas
    (`/admin/reset-db`, `/admin/query`, `POST /produtos`, `GET /usuarios`,
    `GET /pedidos`, `PUT /pedidos/<id>/status`, `GET /relatorios/vendas`).
  - Rotas protegidas com chave correta → status original preservado
    (`200`/`201`), mesmo payload de resposta de antes.
  - Rotas públicas mantidas sem alteração: `GET /produtos`,
    `GET /produtos/<id>`, `GET /produtos/busca`, `POST /usuarios` (cadastro),
    `POST /login`, `POST /pedidos` (criar pedido) → continuam `200`/`201` sem
    exigir header.
  - `GET /health` (rota não tocada) → `200`, confirmando que nada mais foi
    afetado.

## Limitação conhecida

Não existe, hoje, nenhuma infraestrutura de autenticação/sessão/token de
usuário no projeto (o endpoint `/login` apenas valida email/senha e devolve os
dados do usuário, sem emitir sessão ou token — ver
`services/usuarios_service.py`). Por isso toda a proteção usa uma única API
key estática de administrador, e não um guard ligado a um usuário autenticado
real (`current_user`/`is_admin` como no exemplo do playbook) nem verificação
de ownership (ex.: cliente só vê o próprio pedido). Se o projeto evoluir para
autenticação de usuário via sessão/token, `require_admin_auth` deve ser
revisado — e possivelmente desdobrado em `require_auth` (usuário autenticado)
+ `require_admin` (role admin) + verificação de ownership, conforme o padrão
do playbook — para distinguir "qualquer admin" de "o próprio usuário".

## Pontos ainda sem autenticação (fora do escopo aprovado)

- `GET /health` — expõe `secret_key` (`config.SECRET_KEY`) e `debug: True` no
  corpo da resposta. Isso é exposição de segredo (item 2/3 do playbook), não
  falta de autenticação — foi notado na varredura mas não fazia parte da
  pergunta de aprovação, então não foi alterado.
- O hash da senha (`repositories/usuarios_repository.py:38-46`) continua
  sendo incluído no payload de `GET /usuarios` e `GET /usuarios/<id>` — agora
  protegido por `ADMIN_API_KEY`, mas o campo `senha` (hash) em si não foi
  removido da serialização. Corrigir isso é uma refatoração diferente (DTO
  allowlist, item 3 do playbook) e não foi solicitada.


================================
