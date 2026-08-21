================================
PHASE 1: PROJECT ANALYSIS
================================

Project: code-smells-project

Language:      Python 3.10

Framework:     Flask 3.1.1 (+ flask-cors 5.0.1)

Dependencies:  flask, flask-cors

Domain:        E-commerce API (produtos, usuários, pedidos, relatório 
de vendas)

Architecture:  Layered incompleta (app.py = rotas + 2 endpoints admin 
com lógica embutida; controllers.py = camada de controller; models.py = mistura lógica de negócio com SQL cru; database.py = conexão + schema + seed). Sem separação Model/Repository.
Source files:  4 files analyzed (app.py, controllers.py, database.py, models.py)

DB tables:     produtos, usuarios, pedidos, itens_pedido

================================

--- 

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python 3.10 + Flask 3.1.1
Files:   4 analyzed | 780 lines of code

Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 4

Findings

[CRITICAL] SQL Injection via concatenação de strings
File: models.py:48-50, 58-61, 109-111, 127-129, 291-297, 140, 148-151, 155, 158-166
Description: Entrada vinda do corpo/querystring da requisição (nome, descricao,
             categoria, email, senha, tipo, termo, produto_id, quantidade,
             usuario_id) é concatenada diretamente em comandos SQL, sem
             parametrização (`?`) nem escaping. Afeta criar_produto,
             atualizar_produto, login_usuario, criar_usuario, buscar_produtos
             e criar_pedido.
Impact: Permite bypass de autenticação (ex.: `login_usuario` com
        `email' OR '1'='1`), leitura/alteração/exclusão arbitrária de dados
        e comprometimento total do banco.
Recommendation: Usar queries parametrizadas (`cursor.execute(query, (params,))`)
                em todos os pontos citados.

[CRITICAL] Endpoint de execução de SQL arbitrário sem autenticação
File: app.py:59-78
Description: Rota POST /admin/query recebe uma string SQL livre no corpo da
             requisição (`dados.get("sql", "")`) e executa diretamente via
             `cursor.execute(query)`, sem autenticação, autorização ou
             qualquer restrição de comando.
Impact: Qualquer cliente pode ler, alterar ou apagar todo o banco de dados
        (incluindo `DROP TABLE`), ou explorar `PRAGMA`/funções do SQLite.
        É a vulnerabilidade mais grave do sistema.
Recommendation: Remover o endpoint de produção ou restringi-lo com
                autenticação forte + allowlist de operações, nunca aceitar
                SQL livre do cliente.

[CRITICAL] Endpoint de reset total do banco sem autenticação
File: app.py:47-57
Description: Rota POST /admin/reset-db apaga todos os registros de
             `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem exigir
             autenticação, autorização ou confirmação.
Impact: Qualquer requisição não autenticada destrói todos os dados da
        aplicação em produção.
Recommendation: Proteger com autenticação/autorização de administrador e,
                idealmente, remover de builds de produção.

[CRITICAL] SECRET_KEY hardcoded no código-fonte
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"`
             está fixo no código-fonte versionado.
Impact: Compromete assinatura de sessão/cookies; qualquer pessoa com acesso
        ao repositório pode forjar sessões ou tokens assinados pela chave.
Recommendation: Carregar SECRET_KEY de variável de ambiente/secret manager,
                nunca commitar no código.

[CRITICAL] Exposição de secret_key e modo debug em endpoint público
File: controllers.py:276-290
Description: O endpoint GET /health retorna no corpo da resposta
             `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"`
             diretamente ao cliente.
Impact: Vaza a chave secreta da aplicação e confirma que o modo debug
        (Werkzeug debugger interativo) está ativo, facilitando RCE via
        debugger do Flask caso exposto.
Recommendation: Nunca incluir segredos ou flags internas em respostas de
                health check; retornar apenas status agregados não sensíveis.

[CRITICAL] Senha armazenada em texto plano e exposta em respostas da API
File: database.py:31, models.py:79-87, 94-103, 122-131
Description: A coluna `senha` não possui hashing (schema em database.py:31 é
             `TEXT` puro); `criar_usuario` (models.py:122-131) grava a senha
             recebida sem hash; `get_todos_usuarios` e `get_usuario_por_id`
             (models.py:79-87, 94-103) devolvem o campo `senha` em texto
             plano nas respostas de GET /usuarios e GET /usuarios/<id>.
Impact: Vazamento de credenciais de todos os usuários via API pública e
        exposição total em caso de acesso ao banco.
Recommendation: Aplicar hash (ex.: bcrypt/argon2) ao gravar a senha e nunca
                incluir o campo senha nas respostas serializadas.

[HIGH] Responsabilidade excessiva concentrada em models.py (God Module)
File: models.py:1-315
Description: Um único módulo concentra acesso a dados via SQL cru, regras
             de negócio (cálculo de total de pedido, validação de estoque,
             cálculo de desconto no relatório) e formatação de resposta
             para 4 domínios distintos (produtos, usuários, pedidos,
             relatórios), sem separação em repositórios/serviços por domínio.
Impact: Impossível testar regras de negócio isoladamente do banco; qualquer
        mudança em um domínio arrisca efeitos colaterais nos demais.
Recommendation: Separar em Model (regra de negócio) e Repository (acesso a
                dados) por domínio, conforme mvc-guidelines.md.

[HIGH] Responsabilidade excessiva nos controllers (mistura de camadas)
File: controllers.py:24-62, 188-220
Description: `criar_produto` mistura parsing de request, validação de regra
             de negócio (categorias válidas, tamanho de nome) e formatação
             de resposta. `criar_pedido` (188-220) ainda orquestra o "envio"
             de notificações (email/SMS/push simulados via print nas linhas
             208-210) diretamente no controller HTTP.
Impact: Regras de negócio e efeitos colaterais ficam acoplados ao
        transporte HTTP, dificultando reuso e testes automatizados.
Recommendation: Mover validação de negócio para a camada de Model/serviço e
                extrair notificações para um componente dedicado.

[HIGH] Acoplamento forte à implementação concreta do banco
File: database.py:1-11, app.py:49, 66, models.py (todas as funções)
Description: Toda a aplicação depende diretamente da função `get_db()` e da
             conexão SQLite global, sem interface/abstração de repositório
             entre camadas.
Impact: Impossível substituir o banco ou simular (mock) a camada de dados
        em testes unitários sem subir um SQLite real.
Recommendation: Introduzir uma camada de repositório/abstração injetável
                entre controllers/models e a conexão concreta.

[HIGH] Estado global mutável compartilhado (conexão de banco)
File: database.py:4, 8-10
Description: `db_connection` é uma variável global de módulo, criada uma
             única vez (padrão singleton manual) e reutilizada por todas as
             requisições concorrentes, sem controle de concorrência.
Impact: Sob concorrência (Flask threaded), acessos simultâneos à mesma
        conexão podem causar condição de corrida e resultados inconsistentes.
Recommendation: Usar conexão por request (padrão `g` do Flask) ou pool de
                conexões apropriado.

[HIGH] Ausência sistêmica de autenticação/autorização na API
File: app.py:11-30, controllers.py:167-186
Description: POST /login apenas valida email/senha e retorna os dados do
             usuário, sem emitir token/sessão; nenhuma rota de escrita
             (criar/atualizar/deletar produtos, pedidos, status) exige
             identidade autenticada em nenhuma etapa subsequente.
Impact: Qualquer cliente pode executar todas as operações da API,
        incluindo as de domínio sensível, sem se autenticar.
Recommendation: Implementar emissão/verificação de token (ex.: JWT/sessão)
                e middleware de autenticação nas rotas que exigem identidade.

[MEDIUM] Queries N+1 ao montar pedidos
File: models.py:187-199, 219-231
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam, para cada
             pedido, uma query de itens e, para cada item, mais uma query
             para buscar o nome do produto — loop aninhado de 3 níveis de
             consultas ao banco.
Impact: Número de queries cresce proporcionalmente a pedidos × itens,
        degradando performance conforme o volume de dados cresce.
Recommendation: Substituir por JOIN único (pedidos + itens_pedido +
                produtos) ou pré-carregamento em lote.

[MEDIUM] Queries repetidas e redundantes em criar_pedido
File: models.py:139-146, 154-166
Description: O produto de cada item é buscado uma vez no loop de validação
             de estoque (139-146) e buscado novamente no loop de inserção
             (154-166), apesar do preço já ter sido obtido na primeira
             consulta.
Impact: Dobra o número de leituras ao banco desnecessariamente por item do
        pedido.
Recommendation: Reaproveitar o resultado da primeira consulta (preço) ao
                montar os itens do pedido, eliminando a segunda leitura.

[MEDIUM] Tratamento de erro genérico expõe detalhes internos ao cliente
File: controllers.py:12, 22, 62, 96, 109, 126, 134, 144, 165, 186, 220, 227, 235, 255, 262; app.py:77
Description: Todos os blocos `except Exception as e` retornam
             `jsonify({"erro": str(e)})` com a mensagem crua da exceção
             (podendo conter detalhes de SQL/stack) diretamente na resposta
             HTTP com status 500.
Impact: Vazamento de informação interna (estrutura de banco, stack trace)
        que facilita reconhecimento e exploração por um atacante.
Recommendation: Logar o erro detalhado no servidor e retornar ao cliente
                uma mensagem genérica e um código de erro interno.

[MEDIUM] Validação insuficiente de tipos de entrada
File: controllers.py:39-46, 195-201
Description: `preco` e `estoque` (criar_produto) e os campos de cada item de
             `itens` (criar_pedido: `produto_id`, `quantidade`) são usados
             sem validar tipo/formato antes de comparações numéricas ou de
             acesso a chave, podendo estourar exceção não tratada
             especificamente (cai no `except Exception` genérico, retornando
             500 em vez de 400).
Impact: Entradas malformadas geram erro 500 (falha de servidor) em vez de
        400 (erro de cliente), e mascaram a causa real do problema.
Recommendation: Validar tipo/presença de cada campo explicitamente antes de
                usá-lo, retornando 400 com mensagem específica.

[MEDIUM] Duplicação significativa de lógica
File: controllers.py:24-54 vs 64-90; models.py:9-21, 31-40, 304-313; models.py:187-199 vs 219-231
Description: A validação de produto em `criar_produto` e `atualizar_produto`
             é quase idêntica; a formatação do dicionário de produto se
             repete em `get_todos_produtos`, `get_produto_por_id` e
             `buscar_produtos`; a montagem de itens de pedido se repete em
             `get_pedidos_usuario` e `get_todos_pedidos`.
Impact: Qualquer mudança de regra (novo campo, nova validação) precisa ser
        replicada manualmente em múltiplos pontos, com risco de
        inconsistência.
Recommendation: Extrair funções auxiliares únicas de validação e de
                serialização, reutilizadas pelos pontos duplicados.

[LOW] print() usado como mecanismo de logging em produção
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250; app.py:56, 83-86
Description: Mensagens de diagnóstico e "notificações" simuladas são
             emitidas via `print()` em vez de um logger configurável.
Impact: Sem controle de nível de log, formato ou destino; polui stdout em
        produção e não integra com ferramentas de observabilidade.
Recommendation: Substituir por `logging` padrão do Python com níveis
                apropriados.

[LOW] Listas de valores válidos e limiares numéricos hardcoded sem constante
File: controllers.py:52, 242; models.py:257-262
Description: `categorias_validas` e a lista de status válidos são recriadas
             como literais dentro da função a cada chamada; os limiares de
             desconto do relatório (10000, 5000, 1000, 0.1, 0.05, 0.02) são
             números mágicos sem nome.
Impact: Regra de negócio fica implícita no código, difícil de localizar e
        de manter consistente entre os pontos que a usam.
Recommendation: Extrair para constantes de módulo nomeadas (ex.:
                `CATEGORIAS_VALIDAS`, `FAIXAS_DESCONTO`).

[LOW] Nomenclatura pouco expressiva para cursors auxiliares
File: models.py:187, 191, 219, 223
Description: Cursors adicionais são nomeados `cursor2` e `cursor3`, sem
             indicar seu propósito (buscar itens do pedido / buscar nome do
             produto).
Impact: Reduz a legibilidade do fluxo de consultas aninhadas.
Recommendation: Nomear pelo propósito, ex.: `cursor_itens`, `cursor_produto`.

[LOW] Informação de ambiente inconsistente/enganosa exposta
File: controllers.py:286; app.py:8
Description: O endpoint /health reporta `"ambiente": "producao"` fixo,
             enquanto `app.config["DEBUG"] = True` está ativo — sinal
             contraditório sobre o ambiente real de execução.
Impact: Pode induzir a erro operacional (achar que debug está desligado em
        produção) e reforça a exposição do endpoint (ver finding CRITICAL
        de secret_key/debug).
Recommendation: Derivar o valor de ambiente de configuração real (variável
                de ambiente), não de um literal fixo.

Verificação de APIs deprecated: nenhuma API deprecated do Flask 3.1.1 ou do
Python 3.10 foi identificada no código analisado.

================================
Total: 20 findings
================================

