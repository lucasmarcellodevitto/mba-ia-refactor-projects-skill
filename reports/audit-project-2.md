================================
PHASE 1: PROJECT ANALYSIS
================================

Project: ecommerce-api-legacy (Frankenstein LMS)

Language:      JavaScript (Node.js)

Framework:     Express 4.18.2

Dependencies:  express, sqlite3

Domain:        Plataforma de cursos/matrículas com checkout (LMS) — apesar do nome da pasta "ecommerce-api-legacy", o código/log identificam-na como "Frankenstein LMS" (cursos, matrículas, pagamentos)

Architecture:  Monolítica sem separação de camadas — bootstrap em app.js, e toda a lógica de rotas, regras de negócio e acesso a dados concentrada em uma única classe "God Object" (AppManager.js); utils.js mistura config (com segredos hardcoded) e helpers
Source files:  3 files analyzed (src/app.js, src/AppManager.js, src/utils.js)

DB tables:     users, courses, enrollments, payments, audit_logs
================================

---

================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy (Frankenstein LMS)
Stack:   Node.js + Express 4.18.2 + sqlite3

Files:   3 analyzed | ~180 lines of code

Summary
CRITICAL: 5 | HIGH: 3 | MEDIUM: 3 | LOW: 4

Findings

[CRITICAL] Exposição de credenciais hardcoded
File: src/utils.js:2-4
Description: `dbUser`, `dbPass` e `paymentGatewayKey` estão escritos diretamente
             no código-fonte, incluindo uma chave de gateway de pagamento com
             prefixo `pk_live_` (produção). `dbUser`/`dbPass` sequer são usados
             em qualquer lugar do projeto — segredos mortos e ainda assim expostos.
Impact: Qualquer pessoa com acesso ao repositório obtém credenciais de produção,
        permitindo acesso não autorizado ao banco e ao gateway de pagamento.
Recommendation: Mover para variáveis de ambiente (.env não versionado) e remover
                do controle de versão; remover credenciais não utilizadas.

[CRITICAL] Log de dados sensíveis (PCI) em texto claro
File: src/AppManager.js:45
Description: `console.log` imprime o número completo do cartão de crédito (`cc`)
             junto com a chave do gateway de pagamento (`config.paymentGatewayKey`)
             a cada checkout.
Impact: Dados de cartão (PAN completo) ficam expostos em logs — violação grave de
        PCI-DSS — e podem vazar por qualquer sistema de agregação de logs.
Recommendation: Remover o log ou mascarar o PAN (ex.: exibir apenas os 4 últimos
                dígitos) e nunca logar segredos de configuração.

[CRITICAL] Hashing de senha quebrado (criptografia insegura)
File: src/utils.js:17-23 (usado em src/AppManager.js:68)
Description: `badCrypto` não é uma função de hash: repete a codificação Base64 do
             valor 10.000 vezes e trunca para 10 caracteres. É reversível
             trivialmente (basta decodificar Base64) e não usa salt, tornando a
             senha armazenada praticamente equivalente a texto plano.
Impact: Compromete a confidencialidade de todas as senhas de usuários; qualquer
        vazamento do banco expõe senhas originais com esforço mínimo.
Recommendation: Substituir por um algoritmo de hash de senha adequado (bcrypt,
                scrypt ou argon2) com salt e fator de custo configurável.

[CRITICAL] Endpoint administrativo sem controle de acesso
File: src/AppManager.js:80-129
Description: `GET /api/admin/financial-report` expõe receita e dados de alunos
             (nome, email, valores pagos) de todos os cursos sem nenhuma
             verificação de autenticação ou autorização.
Impact: Qualquer requisição não autenticada obtém dados financeiros e pessoais
        sensíveis da plataforma.
Recommendation: Exigir autenticação e autorização de administrador antes de
                processar a rota (middleware de auth + checagem de papel/role).

[CRITICAL] Exclusão de usuário sem controle de acesso
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` remove qualquer usuário pelo `id` informado
             na URL, sem autenticação, autorização, ou verificação de que o
             solicitante é o próprio usuário ou um administrador.
Impact: Qualquer cliente pode apagar a conta de qualquer outro usuário do sistema.
Recommendation: Exigir autenticação e autorização adequadas (dono do recurso ou
                admin) antes de executar a exclusão.

[HIGH] God Class / responsabilidade excessiva
File: src/AppManager.js:1-141
Description: A classe `AppManager` concentra roteamento HTTP, regras de negócio
             (checkout, cálculo de relatório financeiro), acesso direto ao banco
             (SQL bruto) e orquestração de efeitos colaterais (log/cache) — tudo
             em um único arquivo/classe, sem separação entre controller, service
             e camada de dados.
Impact: Impossível testar regras de negócio isoladamente do HTTP/DB; qualquer
        mudança em uma responsabilidade arrisca quebrar as demais.
Recommendation: Separar em controllers (HTTP), services (regras de negócio) e
                repositories (acesso a dados), conforme MVC.

[HIGH] Acoplamento forte a implementação concreta do banco
File: src/AppManager.js:7 (uso disseminado em 28-137)
Description: `AppManager` instancia `sqlite3.Database` diretamente no construtor
             e cada handler de rota executa SQL bruto contra `this.db`
             diretamente, sem repositório ou abstração de acesso a dados.
Impact: Impossível substituir o banco ou simular (mock) a persistência em testes
        sem depender de uma instância real de SQLite.
Recommendation: Extrair um repositório/DAO por entidade (UserRepository,
                CourseRepository, etc.) e injetar a dependência no serviço.

[HIGH] Estado global mutável compartilhado
File: src/utils.js:9,14 (uso em src/AppManager.js:59)
Description: `globalCache`, declarado no escopo do módulo, é mutado por
             `logAndCache` a cada checkout e compartilhado entre todas as
             requisições concorrentes, sem controle de concorrência ou ciclo
             de vida.
Impact: Estado de uma requisição pode vazar ou ser sobrescrito por outra em
        processamento concorrente, gerando comportamento inconsistente.
Recommendation: Eliminar o cache global mutável ou substituí-lo por uma
                solução com escopo e ciclo de vida explícitos (ex.: cache
                dedicado por requisição ou serviço externo).

[MEDIUM] Queries N+1 no relatório financeiro
File: src/AppManager.js:83-128
Description: Para cada curso é disparada uma query de matrículas; para cada
             matrícula, mais duas queries (usuário e pagamento) — todas dentro
             de loops aninhados, multiplicando o número de chamadas ao banco
             proporcionalmente ao volume de dados.
Impact: Degradação de performance severa à medida que o número de cursos,
        matrículas e pagamentos cresce.
Recommendation: Substituir por consultas agregadas (JOIN) que tragam cursos,
                matrículas, usuários e pagamentos em uma única operação.

[MEDIUM] Validação de entrada insuficiente no checkout
File: src/AppManager.js:35,68
Description: A rota valida apenas a presença de `usr`, `eml`, `c_id` e `card`
             (linha 35), sem checar formato de email, formato/tamanho do
             cartão, ou faixa válida de `c_id`. Quando `pwd` não é enviado, a
             senha do novo usuário recebe silenciosamente o valor fixo
             `"123456"` (linha 68).
Impact: Usuários podem ser criados com senha previsível e dados malformados
        sem qualquer rejeição pela API.
Recommendation: Validar formato/tipo de cada campo de entrada e exigir senha
                explícita ao invés de aplicar um valor padrão fraco.

[MEDIUM] Exclusão sem verificação de existência e integridade referencial
File: src/AppManager.js:131-137
Description: O DELETE não verifica se o usuário existe antes de responder com
             sucesso, nem trata registros relacionados (`enrollments`,
             `payments`) — o próprio texto da resposta assume o dado órfão
             ("ficaram sujos no banco").
Impact: Respostas de sucesso enganosas para IDs inexistentes e inconsistência
        de dados relacionados após a exclusão.
Recommendation: Verificar existência do usuário antes de excluir e tratar
                explicitamente (cascata ou bloqueio) os registros dependentes.

[LOW] Nomenclatura pouco expressiva
File: src/AppManager.js:29-33
Description: Variáveis de entrada da requisição são nomeadas com abreviações
             ambíguas: `u`, `e`, `p`, `cid`, `cc`.
Impact: Reduz a legibilidade e dificulta o entendimento do fluxo de checkout.
Recommendation: Renomear para nomes descritivos (`username`, `email`,
                `password`, `courseId`, `cardNumber`).

[LOW] Código morto — importação não utilizada
File: src/AppManager.js:2
Description: `totalRevenue` é importado de `utils.js` mas nunca é lido ou
             utilizado em nenhum ponto do arquivo.
Impact: Ruído que confunde o leitor sobre onde a receita total é de fato
        calculada/acumulada.
Recommendation: Remover a importação não utilizada.

[LOW] Magic numbers sem contexto
File: src/utils.js:19; src/AppManager.js:46
Description: O laço de `badCrypto` usa o literal `10000` sem explicação
             (utils.js:19), e a aprovação de pagamento depende do literal
             mágico `"4"` (`cc.startsWith("4")`, AppManager.js:46) sem
             constante ou comentário que explique a regra.
Impact: Dificulta entender e ajustar as regras sem revisitar a lógica interna.
Recommendation: Extrair para constantes nomeadas (ex.: `HASH_ITERATIONS`,
                `VISA_CARD_PREFIX`).

[LOW] Ruído de desenvolvimento (console.log)
File: src/utils.js:13
Description: `logAndCache` imprime uma linha de log a cada chamada
             (`[LOG] Salvando no cache: ...`) sem nível/flag configurável.
Impact: Polui a saída padrão em produção e não pode ser desativado.
Recommendation: Utilizar um logger configurável com níveis (debug/info) ou
                remover o log de depuração.

================================
Total: 15 findings
================================

Nota sobre APIs deprecated: foi verificado o uso de APIs deprecated do
Node.js/Express/sqlite3 (ex.: `new Buffer()`, `body-parser` legado,
callbacks deprecated do driver). Nenhuma API deprecated foi encontrada no
projeto — `Buffer.from(...)` e `express.json()` (nativo do Express 4.16+)
já são as formas recomendadas atualmente em uso.

Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n] ?
