================================
FASE 3: REGISTRO DA REFATORAÇÃO
================================
Project: task-manager-api
Baseado em: reports/architecture-audit-report.md (Fase 2, 17 findings)

Aprovações do usuário antes de iniciar (mudanças de contrato/comportamento
exigem aprovação explícita — ver regras invioláveis da skill):
- Remover o campo `password` das respostas da API: REPROVADO pelo usuário.

Arquitetura resultante (MVC + Service + Repository, alinhada a
mvc-guidelines.md):
- `models/` — entidades e regras do domínio (validação de status/prioridade,
  `is_overdue()`), sem dependência de HTTP.
- `repositories/` (novo) — isola acesso a dados via SQLAlchemy
  (`db.session.get`, queries agregadas), usado pelos services.
- `services/` (novo/reaproveitado) — regras de negócio, validação e
  orquestração; levanta exceções tipadas (`services/errors.py`).
- `routes/` — controllers finos: parseiam request, chamam o service, mapeiam
  exceções para o status HTTP e a mensagem originais, retornam JSON.

Findings corrigidos:

[CRITICAL] SECRET_KEY hardcoded (app.py:13)
Transformação: valor movido para variável de ambiente `SECRET_KEY`, carregada
via `python-dotenv` (`app.py`); app falha explicitamente na inicialização se
ausente. `.env` (não versionado) e `.env.example` adicionados; `.gitignore`
criado.
Comportamento preservado: mesmas rotas, mesma sessão/assinatura Flask;
`python app.py` continua subindo na porta 5000 com o `.env` fornecido.
Validação: `python -c "import app"` sem erros; servidor sobe e responde.

[CRITICAL] Credenciais SMTP hardcoded + código morto (services/notification_service.py)
Transformação: arquivo removido — a classe nunca era importada/instanciada em
nenhum ponto do projeto (confirmado via grep). Resolve simultaneamente a
exposição de credenciais e o finding LOW de código morto.
Comportamento preservado: nenhuma rota ou fluxo dependia dessa classe.
Validação: grep confirmando ausência de referências antes da remoção;
suite de smoke tests dos endpoints sem regressão.

[CRITICAL] Senha com hash MD5 sem salt (models/user.py)
Transformação: `set_password`/`check_password` passaram a usar
`werkzeug.security.generate_password_hash`/`check_password_hash` (scrypt).
Comportamento preservado: mesma assinatura de método, mesmo contrato de
request/response de `/login`, `/users`, `/users/<id>`; apenas o algoritmo de
hash interno mudou. Banco de dev foi resemeado (`seed.py`) para gerar hashes
no novo formato.
Validação: `POST /login` com credenciais corretas → 200; com senha errada →
401 "Credenciais inválidas" (mensagem e status idênticos ao original).

[HIGH] Responsabilidade excessiva nas rotas (God Routes)
Transformação: lógica de validação, regras de negócio e acesso a dados
extraída para `services/task_service.py`, `user_service.py`,
`category_service.py`, `report_service.py`; rotas (`routes/*.py`) reduzidas a
parsing de request + chamada ao service + mapeamento de erro/status.
Comportamento preservado: mesmas rotas, mesmos parâmetros, mesmas respostas
(validado campo a campo via smoke test).

[HIGH] Acoplamento forte a `Model.query`/`db.session` nas rotas
Transformação: acesso a dados centralizado em `repositories/*.py`
(`TaskRepository`, `UserRepository`, `CategoryRepository`); rotas e services
não referenciam mais o ORM diretamente.
Comportamento preservado: mesmas queries e resultados; apenas a camada que as
executa mudou.

[MEDIUM] N+1 em GET /tasks (routes/task_routes.py:41-57 original)
Transformação: `TaskService.list_tasks()` carrega todos os `user_id`/
`category_id` em duas queries batched (`UserRepository.get_by_ids`,
`CategoryRepository.get_by_ids`) em vez de uma query por task.
Mesma otimização aplicada, por consistência, a `GET /users` (task_count via
`TaskRepository.count_by_user()`) e `GET /categories` (task_count via
`TaskRepository.count_by_category()`), que tinham o mesmo padrão N+1 não
listado individualmente no relatório original mas mesma causa raiz.
Comportamento preservado: mesmos campos e valores em cada resposta.

[MEDIUM] N+1 em GET /reports/summary (user_stats)
Transformação: `ReportService.summary_report()` usa
`TaskRepository.count_by_user()`/`count_done_by_user()` (queries agregadas)
em vez de uma query de tasks por usuário dentro do loop.
Comportamento preservado: mesma estrutura e mesmos números no
`user_productivity`.

[MEDIUM] Duplicação de validação entre create/update e código morto paralelo
Transformação: validação de título usa `MIN_TITLE_LENGTH`/`MAX_TITLE_LENGTH`;
validação de status/prioridade usa `Task.validate_status`/`validate_priority`
(agora `@staticmethod`, efetivamente usados pela primeira vez); validação de
e-mail usa `utils.helpers.validate_email` em vez de regex duplicada em 3
lugares; `process_task_data` (não utilizável de forma consistente com as
regras de FK) foi removido junto com as demais funções mortas de
`utils/helpers.py`.
Comportamento preservado: mesmas mensagens de erro, mesma ordem de validação,
mesmos status codes (validado via smoke test de casos de erro).

[MEDIUM] `except:` genérico mascarando a causa real
Transformação: exceções amplas substituídas por `except Exception:` restrito
exatamente ao mesmo bloco que já existia no código original (só ao redor da
persistência, não da validação), com `logger.exception(...)` registrando a
causa real antes de mapear para a mesma mensagem/status HTTP de antes
(`services/errors.py: PersistenceError`).
Comportamento preservado: mesmo texto de erro e status code por endpoint;
diferença é que agora a exceção real fica no log em vez de silenciada.
Validação: logs verificados durante o smoke test — nenhuma exceção
inesperada, apenas os `INFO` de sucesso/erro esperados.

[MEDIUM] `datetime.utcnow()` deprecated
Transformação: helper `utils.helpers.utcnow()` (`datetime.now(timezone.utc)`
convertido para naive) substitui todas as chamadas a `datetime.utcnow()`.
Comportamento preservado: como o helper retorna datetime naive idêntico ao
anterior, a representação string (`created_at`, `updated_at`, `due_date`,
`generated_at`) e as comparações com colunas naive do banco permanecem
byte-a-byte iguais. Validado nas respostas do smoke test.

[MEDIUM] `Model.query.get()` legado
Transformação: repositórios usam `db.session.get(Model, id)`.
Comportamento preservado: mesmo retorno (`None` quando não encontrado, mesmo
objeto quando encontrado).

[LOW] Nomenclatura pouco expressiva (p1..p5)
Transformação: contadores renomeados para chaves diretas em
`tasks_by_priority` (`critical`, `high`, `medium`, `low`, `minimal`) via
`TaskRepository.count_by_priority(n)`, sem variáveis intermediárias de uma
letra.
Comportamento preservado: mesmas chaves e valores no JSON de resposta.

[LOW] Código morto
Transformação: removidos `services/notification_service.py`,
`utils/helpers.sanitize_string/generate_id/log_action/is_valid_color/
process_task_data/parse_date`; `format_date`/`calculate_percentage` deixaram
de ser mortos (passaram a ser usados em models/services); import não utilizado
de `report_routes.py` removido junto da reescrita do arquivo.
Comportamento preservado: nenhuma dessas funções era referenciada em runtime.

[LOW] `print()` de debug
Transformação: substituídos por `logging` (`logger.info`/`logger.exception`),
configurado em `app.py` via `logging.basicConfig`.
Comportamento preservado: nenhuma resposta HTTP dependia da saída do
`print()`; apenas o destino/estrutura do log mudou.

[LOW] Magic numbers duplicados
Transformação: limites de título e faixa de prioridade passaram a usar
`MIN_TITLE_LENGTH`/`MAX_TITLE_LENGTH`/`MIN_PRIORITY`/`MAX_PRIORITY` de
`utils/helpers.py` em vez de literais repetidos.
Comportamento preservado: mesmos limites (3/200 caracteres, prioridade 1-5).


Validações executadas (não havia suite de testes automatizados no projeto):
- `python -c "import app"` — importação sem erros.
- `python seed.py` — popula o banco do zero sem erros, com o novo esquema de
  hash de senha.
- Servidor iniciado (`python app.py`) e testado manualmente via `curl` contra
  todos os 22 endpoints do baseline da Fase 1: casos de sucesso (200/201) e
  de erro (400/401/403/404/409) para cada rota de escrita, comparando
  status code, mensagem e formato de resposta com o comportamento original.
- Logs do servidor inspecionados durante os testes: sem stack traces ou
  exceções não tratadas.
- Banco de dados de desenvolvimento resemeado ao final para deixá-lo no
  estado padrão do `README.md`.

Limitações conhecidas:
- Não havia testes automatizados no projeto original; a validação de
  paridade comportamental foi feita via smoke test manual endpoint a
  endpoint, não por suíte de regressão.

- [CRITICAL] Exposição de dados sensíveis na resposta (senha) — mantida por
  decisão anterior do usuário.
- [CRITICAL] Operações críticas sem controle de acesso — mantida por decisão
  anterior do usuário; `/login` emitia um token fictício não verificado.

Durante a implementação foram identificados dois outros pontos de
autorização não cobertos pelo finding CRITICAL original — `POST`/`PUT
/tasks` sem autenticação (permitindo reatribuir uma task a qualquer
usuário) e `POST`/`PUT /categories` sem autenticação (inconsistente com o
`DELETE`, que já era admin-only). Esses pontos foram apresentados ao usuário
separadamente, que aprovou corrigi-los também.

--------------------------------
MUDANÇA DE CONTRATO (autorizada)
--------------------------------
- O campo `password` deixou de ser retornado em qualquer resposta da API
  (`GET /users/<id>`, `POST /users`, `PUT /users/<id>`, `POST /login`).
- `POST /login` agora retorna um JWT real (assinado com `SECRET_KEY`,
  HS256, expiração de 24h) em vez do token fictício `'fake-jwt-token-' + id`.
- `PUT /users/<id>` e `DELETE /users/<id>` passaram a exigir autenticação
  (header `Authorization: Bearer <token>`) e autorização (dono do recurso
  ou admin). Antes, qualquer chamador sem autenticação podia executar essas
  operações.
- `PUT /users/<id>` passou a rejeitar alteração do campo `role` por quem não
  é admin (bloqueia a escalação de privilégio descrita no finding original).
- `DELETE /tasks/<id>` passou a exigir autenticação e autorização (dono da
  task ou admin).
- `POST /tasks` e `PUT /tasks/<id>` passaram a exigir autenticação; só o
  dono da task (`user_id`) ou um admin pode atualizá-la, e só é possível
  atribuir/reatribuir uma task para outro usuário sendo admin (achado extra,
  aprovado pelo usuário — ver seção "Pontos adicionais" abaixo).
- `POST /categories` e `PUT /categories/<id>` passaram a exigir autenticação
  e papel `admin`, ficando consistentes com o `DELETE /categories/<id>`
  (achado extra, aprovado pelo usuário).
- `DELETE /categories/<id>` passou a exigir autenticação e papel `admin`
  (categorias não têm dono individual).
- Todos os demais endpoints (listagens, `GET /tasks`, `GET /categories`,
  `POST /users`, relatórios) permanecem exatamente como antes — não fizeram
  parte de nenhum finding e não foram alterados.

--------------------------------
FINDINGS CORRIGIDOS
--------------------------------

[CRITICAL] Exposição de dados sensíveis na resposta da API (senha)
File: models/user.py (`User.to_dict`)
Transformação: aplicado o padrão "DTO/serializer com allowlist" do
refactoring-playbook (item 3) — `to_dict()` deixou de incluir o campo
`password`, retornando apenas os campos públicos (`id`, `name`, `email`,
`role`, `active`, `created_at`).
Comportamento preservado: mesma estrutura de resposta, exceto pela ausência
do campo `password` (mudança de contrato explicitamente aprovada).
Validação: `POST /login`, `GET /users/<id>`, `POST /users` e
`PUT /users/<id>` testados via curl — nenhum retorna mais o hash da senha.

[CRITICAL] Operações críticas sem controle de acesso
Files: utils/auth.py (novo), services/user_service.py, services/task_service.py,
routes/user_routes.py, routes/task_routes.py, routes/report_routes.py
Transformação: aplicado o padrão "Middleware/guard reutilizável" do
refactoring-playbook (item 4):
- `utils/auth.py` centraliza emissão (`generate_token`) e verificação de JWT,
  além dos decorators `require_auth` (exige token válido, injeta
  `g.current_user`) e `require_admin` (exige `current_user.is_admin()`).
- `POST /login` (services/user_service.py) passou a emitir um JWT real via
  `generate_token`, assinado com a mesma `SECRET_KEY` da aplicação.
- `PUT /users/<id>` e `DELETE /users/<id>` usam `@require_auth`; a
  autorização por dono/admin é verificada em `UserService` (dono do recurso
  ou `current_user.is_admin()`), seguindo o exemplo de autorização por
  ownership do playbook (`if resource.owner_id != current_user.id and not
  current_user.is_admin(): raise ForbiddenError()`).
- `DELETE /tasks/<id>` usa `@require_auth`; `TaskService.delete_task` valida
  que `current_user` é o dono da task (`task.user_id`) ou admin.
- `DELETE /categories/<id>` usa `@require_auth` + `@require_admin` (recurso
  sem dono individual).
Comportamento preservado: mesmos endpoints, métodos HTTP, parâmetros e
formatos de sucesso; a diferença observável é que chamadas sem token válido
ou sem permissão agora recebem 401/403 em vez de serem executadas.
Validação (smoke test manual via curl, servidor local):
- `DELETE /users/<id>` sem token → 401.
- `DELETE /users/<id>` com token de outro usuário não-admin → 403.
- `PUT /users/<id>` tentando o próprio usuário alterar `role` → 403.
- `PUT /users/<id>` alterando o próprio nome → 200 (comportamento normal).
- `DELETE /tasks/<id>` sem token → 401; com token de usuário que não é dono
  → 403; com token do dono → 200.
- `DELETE /categories/<id>` sem token → 401; com token não-admin → 403; com
  token admin → 200.
- Token inválido/malformado em qualquer rota protegida → 401.
- Endpoints não listados no finding (`GET /tasks`, `GET /users`,
  `GET /categories`, `GET /reports/summary`, `POST /users`, `POST /login`
  com credenciais erradas) seguem retornando exatamente os mesmos status
  codes de antes.

--------------------------------
PONTOS ADICIONAIS (fora do finding original, aprovados pelo usuário)
--------------------------------

[Ponto adicional] Criação/reatribuição de task sem controle de acesso
Files: services/task_service.py (`create_task`, `update_task`),
routes/task_routes.py
Descrição: `POST /tasks` e `PUT /tasks/<id>` não exigiam autenticação;
qualquer chamador podia criar ou reatribuir uma task para qualquer
`user_id`. Não estava no finding CRITICAL original (que só cobria
`DELETE /tasks/<id>`), mas usa a mesma falha de autorização.
Transformação: `@require_auth` adicionado às duas rotas.
`TaskService.create_task`/`update_task` passaram a receber `current_user` e
rejeitam (`ForbiddenError`, 403) a definição de `user_id` diferente do
chamador, a menos que seja admin. `update_task` também exige que o
chamador seja o dono atual da task ou admin para qualquer alteração,
espelhando a regra já usada em `delete_task`.
Comportamento preservado: mesmos campos/validações de negócio; a diferença
observável é que chamadas sem token, ou tentando atribuir/editar a task de
outro usuário sem ser admin, agora recebem 401/403.
Validação: `POST /tasks` sem token → 401; como usuária criando task para si
→ 201; tentando atribuir a outro usuário sem ser admin → 403; `PUT
/tasks/<id>` de uma task de outro usuário → 403; da própria task → 200.

[Ponto adicional] Criação/edição de categoria sem controle de acesso
Files: routes/report_routes.py
Descrição: `POST /categories` e `PUT /categories/<id>` não exigiam
autenticação, enquanto `DELETE /categories/<id>` (finding original) já
havia ficado admin-only — inconsistência de autorização no mesmo recurso.
Transformação: `@require_auth` + `@require_admin` adicionados às duas
rotas, mesmo padrão já usado no `DELETE`.
Comportamento preservado: mesmos campos e validações; a diferença
observável é que criar/editar categoria agora exige token de administrador.
Validação: `POST /categories` sem token → 401; com token não-admin → 403;
com token admin → 201. Mesmo padrão validado para `PUT /categories/<id>`.

--------------------------------
DEPENDÊNCIA ADICIONADA
--------------------------------
`PyJWT==2.9.0` adicionado a requirements.txt (instalado no venv do projeto)
para geração/validação de JWT real, conforme recomendação do finding original
("Implementar autenticação real (JWT assinado e verificado)").

--------------------------------
LIMITAÇÕES CONHECIDAS
--------------------------------
- Não havia suíte de testes automatizados no projeto; a validação foi feita
  via smoke test manual com curl (mesma limitação já registrada na Fase 3
  anterior).
- O token não possui mecanismo de revogação/blacklist (logout apenas invalida
  no cliente); expira automaticamente em 24h.
- `SECRET_KEY` continua sendo um segredo compartilhado carregado via `.env`
  (já corrigido em refatoração anterior); nenhuma mudança adicional foi feita
  nesse ponto.

================================
COMO AUTENTICAR NAS APIS APÓS O AJUSTE
================================

1. Obtenha um token chamando `POST /login` com email e senha de um usuário
   existente (veja `seed.py` para usuários de exemplo).
2. O campo `token` da resposta é um JWT. Envie-o em todas as chamadas a
   endpoints protegidos no header:

   Authorization: Bearer <token>

3. Endpoints protegidos e regra de autorização:

   | Endpoint                       | Requer login | Regra adicional                          |
   |---------------------------------|:------------:|-------------------------------------------|
   | PUT    /users/<id>              | Sim          | Dono do recurso OU admin; só admin altera `role` |
   | DELETE /users/<id>              | Sim          | Dono do recurso OU admin                  |
   | POST   /tasks                   | Sim          | Só pode criar task para si mesmo, salvo admin |
   | PUT    /tasks/<id>              | Sim          | Dono da task OU admin; reatribuir a outro usuário exige admin |
   | DELETE /tasks/<id>              | Sim          | Dono da task (`user_id`) OU admin         |
   | POST   /categories              | Sim          | Somente admin                             |
   | PUT    /categories/<id>         | Sim          | Somente admin                             |
   | DELETE /categories/<id>         | Sim          | Somente admin                             |
   | Todos os demais endpoints       | Não          | Sem alteração — continuam públicos        |

4. Sem o header `Authorization`, ou com um token inválido/expirado, os
   endpoints protegidos retornam `401`. Com token válido mas sem a
   permissão necessária, retornam `403`.

5. Usuários de exemplo (após `python seed.py`):
   - joao@email.com / 1234 (role: admin, id: 1)
   - maria@email.com / abcd (role: user, id: 2)
   - pedro@email.com / pass (role: manager, id: 3)

================================
EXEMPLOS DE CURL — TODOS OS ENDPOINTS
================================
Assumindo o servidor rodando em http://localhost:5000.

--- Saúde / raiz (públicos) ---

# GET /health
curl -s http://localhost:5000/health

# GET /
curl -s http://localhost:5000/

--- Autenticação ---

# POST /login — obtém o token JWT
curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}'

# Guarde o token retornado em uma variável para os exemplos seguintes
TOKEN=$(curl -s -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

--- Usuários (routes/user_routes.py) ---

# GET /users — público
curl -s http://localhost:5000/users

# GET /users/<id> — público
curl -s http://localhost:5000/users/1

# POST /users — público (cadastro)
curl -s -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"name":"Novo Usuário","email":"novo@email.com","password":"1234"}'

# PUT /users/<id> — requer autenticação (dono ou admin)
curl -s -X PUT http://localhost:5000/users/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"João Silva Atualizado"}'

# DELETE /users/<id> — requer autenticação (dono ou admin)
curl -s -X DELETE http://localhost:5000/users/1 \
  -H "Authorization: Bearer $TOKEN"

# GET /users/<id>/tasks — público
curl -s http://localhost:5000/users/1/tasks

--- Tasks (routes/task_routes.py) ---

# GET /tasks — público
curl -s http://localhost:5000/tasks

# GET /tasks/<id> — público
curl -s http://localhost:5000/tasks/1

# POST /tasks — requer autenticação (user_id só pode ser o do próprio token,
# a menos que o chamador seja admin)
curl -s -X POST http://localhost:5000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Nova task","user_id":1,"category_id":1}'

# PUT /tasks/<id> — requer autenticação (dono da task ou admin)
curl -s -X PUT http://localhost:5000/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'

# DELETE /tasks/<id> — requer autenticação (dono da task ou admin)
curl -s -X DELETE http://localhost:5000/tasks/1 \
  -H "Authorization: Bearer $TOKEN"

# GET /tasks/search — público
curl -s "http://localhost:5000/tasks/search?q=login&status=pending"

# GET /tasks/stats — público
curl -s http://localhost:5000/tasks/stats

--- Categorias e relatórios (routes/report_routes.py) ---

# GET /reports/summary — público
curl -s http://localhost:5000/reports/summary

# GET /reports/user/<id> — público
curl -s http://localhost:5000/reports/user/1

# GET /categories — público
curl -s http://localhost:5000/categories

# POST /categories — requer autenticação + role admin
curl -s -X POST http://localhost:5000/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Nova categoria","color":"#ff0000"}'

# PUT /categories/<id> — requer autenticação + role admin
curl -s -X PUT http://localhost:5000/categories/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"description":"Descrição atualizada"}'

# DELETE /categories/<id> — requer autenticação + role admin
curl -s -X DELETE http://localhost:5000/categories/1 \
  -H "Authorization: Bearer $TOKEN"

================================


================================
