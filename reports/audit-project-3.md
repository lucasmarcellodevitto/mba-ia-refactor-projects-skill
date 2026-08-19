================================
PHASE 1: PROJECT ANALYSIS
================================
Project: task-manager-api
Language:      Python 3
Framework:     Flask 3.0.0 (flask-sqlalchemy 3.1.1, flask-cors 4.0.0)
Dependencies:  flask, flask-sqlalchemy, flask-cors, marshmallow, requests, python-dotenv
Domain:        Task Manager API (usuários, tasks, categorias, relatórios)
Architecture:  Layered parcial — models/, routes/ e services/ existem, mas rotas concentram validação, acesso a dados e serialização (Blueprints agindo como Controller+Service+Repository)
Source files:  15 files analyzed (.py)
DB tables:     tasks, users, categories (SQLite via SQLAlchemy ORM, arquivo tasks.db)
================================


================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3.10 + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLite)
Files:   15 analyzed | ~1158 lines of code

Summary
CRITICAL: 5 | HIGH: 2 | MEDIUM: 6 | LOW: 4

Findings

[CRITICAL] Exposição de credenciais ou dados sensíveis (SECRET_KEY)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` está hardcoded
             diretamente no código-fonte versionado.
Impact: Chave usada por Flask para assinar sessões/tokens fica exposta a
        qualquer pessoa com acesso ao repositório, permitindo forjar sessões.
Recommendation: Carregar via variável de ambiente (`os.environ['SECRET_KEY']`),
                nunca commitar o valor real.

[CRITICAL] Exposição de credenciais ou dados sensíveis (SMTP)
File: services/notification_service.py:7-10
Description: Host, usuário e senha de e-mail (`senha123`) hardcoded na classe
             `NotificationService`.
Impact: Credenciais de uma conta de e-mail real expostas no repositório.
Recommendation: Externalizar para variáveis de ambiente / secret manager.

[CRITICAL] Senha armazenada com hash criptográfico quebrado
File: models/user.py:29,32
Description: `set_password`/`check_password` usam MD5 sem salt
             (`hashlib.md5(pwd.encode()).hexdigest()`) para senhas de usuário.
Impact: MD5 é criptograficamente quebrado e reversível via rainbow tables;
        um vazamento do banco compromete todas as senhas dos usuários.
Recommendation: Usar `werkzeug.security.generate_password_hash` (bcrypt/scrypt)
                ou `passlib`, com salt único por usuário.

[CRITICAL] Exposição de dados sensíveis na resposta da API (senha)
File: models/user.py:16-25 (campo 'password' no to_dict); propagado em
      routes/user_routes.py:33, 86, 129, 209
Description: `User.to_dict()` inclui o campo `password` (o hash) e é retornado
             diretamente em `GET /users/<id>`, `POST /users`, `PUT /users/<id>`
             e `POST /login`.
Impact: O hash da senha de qualquer usuário fica exposto a qualquer client
        que consiga consultar/criar/logar um usuário — facilita ataques
        offline de quebra de hash.
Recommendation: Remover `password` da serialização pública; se necessário,
                criar um `to_dict(include_sensitive=False)` por padrão.

[CRITICAL] Operações críticas sem controle de acesso
File: routes/user_routes.py:92-151 (update_user/delete_user),
      routes/task_routes.py:225-238 (delete_task),
      routes/report_routes.py:211-223 (delete_category),
      routes/user_routes.py:185-211 (login)
Description: Nenhuma rota do projeto (nenhum arquivo em routes/) possui
             verificação de autenticação/autorização. `DELETE /users/<id>`
             apaga qualquer usuário e todas as suas tasks (linhas 140-151);
             `PUT /users/<id>` permite qualquer chamador alterar o `role`
             de qualquer usuário para 'admin' (linhas 119-122) sem checar
             identidade/permissão do requisitante. O `/login` (linhas
             185-211) gera um token fictício (`'fake-jwt-token-' + id`) que
             nunca é validado em nenhum outro endpoint — a "autenticação"
             existe apenas na aparência.
Impact: Qualquer cliente não autenticado pode deletar usuários/tasks/
        categorias de terceiros ou escalar privilégios de qualquer conta.
Recommendation: Implementar autenticação real (JWT assinado e verificado) e
                middleware/decorator de autorização nas rotas destrutivas e
                administrativas antes de expor a API.

[HIGH] Responsabilidade excessiva em classes ou funções (God Routes)
File: routes/task_routes.py:11-300, routes/user_routes.py:10-212,
      routes/report_routes.py:12-224
Description: Todos os handlers de rota concentram parsing de request,
             validação de regras de negócio, acesso direto ao ORM
             (`Model.query`, `db.session.add/commit/rollback`) e montagem
             manual da resposta na mesma função — não existe camada de
             Controller, Service ou Repository. Exemplo representativo:
             `create_task` (task_routes.py:85-154) e `summary_report`
             (report_routes.py:12-101, ~90 linhas numa única função
             agregando 6 domínios de estatística diferentes).
Impact: Impossível testar regras de negócio isoladamente do Flask/ORM;
        qualquer mudança de contrato ou de storage exige tocar na rota.
Recommendation: Extrair Services (regra de negócio) e Repositories (acesso
                a dados), mantendo a rota apenas como Controller fino.

[HIGH] Acoplamento forte a implementações concretas
File: routes/task_routes.py (ex.: 14,42,51,67,117,122,158,188,195,227,247),
      routes/user_routes.py (ex.: 12,29,35,67,94,109,136,140,155,159,197),
      routes/report_routes.py (ex.: 15-30,105,109,159,163,192,213)
Description: As rotas acessam diretamente `Model.query` e `db.session` do
             SQLAlchemy em vez de dependerem de uma abstração (repositório/
             serviço) injetável.
Impact: Impossível trocar a fonte de dados ou usar dublês de teste sem
        reescrever cada rota; a lógica de negócio fica presa ao ORM.
Recommendation: Introduzir uma camada de repositório por entidade
                (TaskRepository, UserRepository, CategoryRepository) usada
                pelos services.

[MEDIUM] Queries N+1
File: routes/task_routes.py:16-59 (get_tasks), linhas 42 e 51 dentro do loop
Description: Para cada task retornada, `User.query.get(t.user_id)` (linha 42)
             e `Category.query.get(t.category_id)` (linha 51) disparam uma
             query adicional por registro.
Impact: Tempo de resposta cresce linearmente com o número de tasks.
Recommendation: Usar `join`/`joinedload` para carregar usuário e categoria
                junto da query principal.

[MEDIUM] Queries N+1
File: routes/report_routes.py:53-68 (user_stats), linha 56 dentro do loop
Description: Para cada usuário, `Task.query.filter_by(user_id=u.id).all()`
             é executada dentro do laço `for u in users`.
Impact: Relatório de produtividade fica O(N) queries para N usuários.
Recommendation: Agregar com uma única query (`GROUP BY user_id`) ou
                pré-carregar as tasks de todos os usuários de uma vez.

[MEDIUM] Duplicação significativa de lógica de validação
File: routes/task_routes.py:96-114 (create_task) e 166-184 (update_task);
      duplicado novamente e nunca usado em models/task.py:38-48
      (validate_status/validate_priority) e utils/helpers.py:57-108
      (process_task_data)
Description: A validação de título (3-200 chars), status válido e faixa de
             prioridade (1-5) é reescrita manualmente em `create_task` e
             `update_task`, enquanto já existem implementações prontas
             (porém nunca chamadas) em `Task.validate_status`/
             `validate_priority` e em `process_task_data`.
Impact: Regra pode divergir entre create/update ao ser alterada em apenas
        um dos pontos; código morto paralelo aumenta confusão.
Recommendation: Centralizar a validação em um único ponto (service ou
                schema) e remover as implementações duplicadas não usadas.

[MEDIUM] Validação/tratamento de erro insuficiente (bare except)
File: routes/task_routes.py:62-63, 136-137, 204-205, 236-238;
      routes/user_routes.py:130-132, 149-151;
      routes/report_routes.py:186-188, 207-209, 221-223
Description: Blocos `except:` genéricos capturam qualquer exceção (incluindo
             erros de programação) e retornam uma mensagem genérica, sem
             logar a causa real.
Impact: Erros inesperados (bugs, falhas de conexão) ficam mascarados como
        "Erro interno"/"Erro ao atualizar", dificultando diagnóstico.
Recommendation: Capturar exceções específicas e logar o erro original antes
                de responder ao cliente.

[MEDIUM] Uso de API deprecated da linguagem (datetime.utcnow)
File: models/task.py:15-16,52; models/user.py:14,29,32; models/category.py:11;
      routes/task_routes.py (múltiplas ocorrências); routes/report_routes.py
      (múltiplas ocorrências)
Description: `datetime.utcnow()` é usado em todo o projeto. Esse método está
             deprecated desde Python 3.12 (retorna datetime naive, sem
             timezone) e a documentação oficial já recomenda
             `datetime.now(timezone.utc)`. O ambiente atual roda Python 3.10.12,
             então ainda funciona, mas quebrará (emitirá DeprecationWarning e
             será removido em versões futuras) ao migrar o interpretador.
Impact: Risco de quebra futura ao atualizar o Python; datetimes naive
        também são propensos a bugs de fuso horário.
Recommendation: Migrar para `datetime.now(timezone.utc)` de forma centralizada.

[MEDIUM] Uso de API legada do SQLAlchemy (Model.query.get)
File: routes/task_routes.py:67,117,122,158,188,195,227;
      routes/user_routes.py:29,94,136,155,197;
      routes/report_routes.py:105,192,213
Description: `Model.query.get(id)` é o padrão "legacy query" do SQLAlchemy
             1.x, mantido por compatibilidade no SQLAlchemy 2.0/Flask-SQLAlchemy
             3.x mas descontinuado em favor de `db.session.get(Model, id)`.
Impact: Uso consistente do padrão legado em toda a base dificulta a futura
        migração para o estilo 2.0 e pode gerar warnings de depreciação.
Recommendation: Substituir por `db.session.get(Model, id)`.

[LOW] Nomenclatura pouco expressiva
File: routes/report_routes.py:24-28 (p1..p5); loops de uma letra em
      routes/task_routes.py (ex.: `for t in tasks`), routes/user_routes.py
      (`for u in users`), routes/report_routes.py (`for t in all_tasks`,
      `for u in users`, `for c in categories`)
Description: Variáveis como `p1`-`p5` para contadores de prioridade não
             comunicam o significado (crítico/alto/médio/...) sem consultar
             o dicionário de saída logo abaixo.
Impact: Reduz legibilidade e aumenta chance de erro ao mapear prioridade
        para rótulo.
Recommendation: Nomear por significado (`critical_count`, `high_count`, ...)
                ou iterar sobre um mapeamento priority→label.

[LOW] Código morto
File: services/notification_service.py:1-49 (classe inteira nunca
      importada/instanciada); utils/helpers.py:19-23,25-29,31-34,36-41,
      52-55,57-108,110-116 (funções e constantes nunca chamadas);
      models/task.py:38-48 (validate_status/validate_priority nunca
      chamados); routes/report_routes.py:7 (import de format_date e
      calculate_percentage nunca usados no arquivo)
Description: Verificado via grep em todo o projeto — nenhuma dessas
             funções/classe é referenciada fora de sua própria definição.
Impact: Aumenta a superfície de código a manter/entender sem entregar
        valor; passa falsa impressão de que a validação está centralizada.
Recommendation: Remover o código não utilizado ou passar a utilizá-lo como
                única fonte de verdade (ver finding de duplicação acima).

[LOW] print() de debug no fluxo de produção
File: routes/task_routes.py:149,153,219,234; routes/user_routes.py:83,89,147
Description: Chamadas `print(...)` usadas como logging de sucesso/erro em
             vez de um logger configurado.
Impact: Sem controle de nível/formatação/destino de log; polui stdout em
        produção.
Recommendation: Substituir por `logging` (ou `app.logger`).

[LOW] Magic numbers duplicados
File: routes/task_routes.py:96,99,167,169 (limites de título 3/200);
      routes/task_routes.py:113-114,182-183 (faixa de prioridade 1-5)
Description: Os limites de tamanho de título e faixa de prioridade são
             literais repetidos em vários pontos, embora já existam as
             constantes `MIN_TITLE_LENGTH`, `MAX_TITLE_LENGTH` em
             utils/helpers.py:112-113 (não utilizadas — ver finding de
             código morto).
Impact: Alterar a regra de negócio exige encontrar e sincronizar todas as
        ocorrências manualmente.
Recommendation: Usar as constantes já existentes em vez dos literais.

================================
Total: 17 findings
================================

Fase 3 (refatoração): ver reports/phase3-refactoring-report.md
