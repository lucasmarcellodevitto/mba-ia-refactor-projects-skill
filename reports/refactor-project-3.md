================================
FASE 3: REGISTRO DA REFATORAÇÃO
================================
Project: task-manager-api
Baseado em: reports/architecture-audit-report.md (Fase 2, 17 findings)

Aprovações do usuário antes de iniciar (mudanças de contrato/comportamento
exigem aprovação explícita — ver regras invioláveis da skill):
- Remover o campo `password` das respostas da API: REPROVADO pelo usuário.
- Implementar autenticação/autorização real nas rotas: REPROVADO pelo usuário.
Como consequência, os findings CRITICAL #4 (senha exposta na resposta) e
CRITICAL #5 (operações sem controle de acesso) permanecem NÃO corrigidos,
preservando o comportamento/contrato atual exatamente como estava.

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

Findings NÃO corrigidos (reprovados pelo usuário):
- [CRITICAL] Exposição de dados sensíveis na resposta (senha) — campo
  `password` mantido em `User.to_dict()` por decisão do usuário.
- [CRITICAL] Operações críticas sem controle de acesso — nenhuma rota recebeu
  autenticação/autorização, por decisão do usuário; `/login` continua
  emitindo um token fictício não verificado.

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
- Os dois findings CRITICAL relacionados a segurança de autenticação
  permanecem em aberto por decisão explícita do usuário e requerem nova
  aprovação para serem corrigidos no futuro.
================================
