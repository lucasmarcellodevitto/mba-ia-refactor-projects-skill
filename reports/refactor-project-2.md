# Relatório de Refatoração — Fase 3

Projeto: ecommerce-api-legacy (Frankenstein LMS)
Stack: Node.js + Express 4.18.2 + sqlite3
Baseado em: [architecture-audit-report.md](architecture-audit-report.md)

## Arquitetura resultante

De um único God Object (`AppManager.js`) concentrando rotas, regras de negócio e
acesso a dados, para uma separação em camadas (MVC):

```
src/
  app.js                 → composition root (bootstrap, injeção de dependências)
  routes/                → mapeamento HTTP → controller
  controllers/           → orquestração da requisição/resposta
  services/               → regras de negócio (checkout, relatório financeiro)
  repositories/           → acesso a dados (Model / persistência)
  db/                     → conexão sqlite3 e schema/seed
  utils/                  → hashing de senha e cache, isolados e injetáveis
```

Fluxo: `Request → routes → controller → service → repository → db`.

## Correções aplicadas (sem alteração de contrato público)

Rotas, métodos HTTP, parâmetros, formatos de request/response, códigos de
status e comportamento funcional exposto foram integralmente preservados e
validados por execução manual dos 3 endpoints após cada bloco de mudanças.

| Severidade | Achado | Arquivo(s) originais | Transformação aplicada | Arquivo(s) novos |
|---|---|---|---|---|
| CRITICAL | Credenciais hardcoded (`dbUser`, `dbPass`, `paymentGatewayKey`, `smtpUser`) | `src/utils.js:2-6` | Nenhuma delas era usada fora do log removido a seguir; removidas por completo (nenhuma exige config externa hoje) | — |
| CRITICAL | Log de dados sensíveis (PAN do cartão + chave do gateway) | `src/AppManager.js:45` | `console.log` removido do fluxo de checkout | `src/services/checkoutService.js` |
| CRITICAL | Hashing de senha quebrado (`badCrypto`, Base64 repetido) | `src/utils.js:17-23` | Substituído por `bcryptjs` (hash + salt, custo 10); seed também re-hasheada | `src/utils/passwordHasher.js`, `src/db/schema.js` |
| HIGH | God Class / responsabilidade excessiva | `src/AppManager.js:1-141` | Dividido em repositories (dados), services (regras de negócio) e controllers (HTTP) | `src/repositories/*`, `src/services/*`, `src/controllers/*` |
| HIGH | Acoplamento forte ao SQLite (`new sqlite3.Database` direto na classe) | `src/AppManager.js:7` | Conexão isolada em classe `Database` (Promise-based) e injetada via construtor em cada repository | `src/db/database.js` |
| HIGH | Estado global mutável (`globalCache`) | `src/utils.js:9,14` | Substituído por classe `Cache`, instanciada uma única vez na composition root e injetada — sem módulo mutável compartilhado implicitamente | `src/utils/cache.js` |
| MEDIUM | Queries N+1 no relatório financeiro | `src/AppManager.js:83-128` | Loops aninhados substituídos por uma única query com `LEFT JOIN` (cursos → matrículas → usuários → pagamentos) | `src/repositories/financialReportRepository.js`, `src/services/financialReportService.js` |
| LOW | Nomenclatura pouco expressiva (`u,e,p,cid,cc`) | `src/AppManager.js:29-33` | Renomeado para `username, email, password, courseId, cardNumber` | `src/services/checkoutService.js` |
| LOW | Código morto (`totalRevenue` importado e nunca usado) | `src/AppManager.js:2` | Removido (a variável de origem em `utils.js` também nunca era lida) | — |
| LOW | Magic numbers (`10000`, `"4"`) | `src/utils.js:19`, `src/AppManager.js:46` | Extraídos para constantes `SALT_ROUNDS` e `VISA_CARD_PREFIX` | `src/utils/passwordHasher.js`, `src/services/checkoutService.js` |
| LOW | Ruído de desenvolvimento (`console.log` de cache) | `src/utils.js:13` | Removido junto da reescrita do cache | `src/utils/cache.js` |

## Validações executadas

Servidor iniciado com `npm start` (porta 3000 preservada, mensagem de boot
idêntica) e os 3 endpoints testados manualmente após a refatoração:

- `POST /api/checkout` (sucesso) → `200 {"msg":"Sucesso","enrollment_id":N}` ✅
- `POST /api/checkout` (cartão recusado) → `400 "Pagamento recusado"` ✅
- `POST /api/checkout` (campos ausentes) → `400 "Bad Request"` ✅
- `POST /api/checkout` (curso inexistente) → `404 "Curso não encontrado"` ✅
- `GET /api/admin/financial-report` → `200`, mesmo formato agregado
  (`[{course, revenue, students:[{student, paid}]}]`) ✅
- `DELETE /api/users/:id` (existente e inexistente) → `200`, mesma mensagem em
  ambos os casos ✅

Todas as respostas conferem com o baseline registrado na Fase 1.

## Mudança de dependência

Adicionado `bcryptjs` (`package.json`) — única dependência nova, necessária
para corrigir o hashing de senha quebrado. É usada apenas internamente
(persistência de senha); não altera nenhum endpoint público.

## Achados deixados como estavam (aprovação recusada pelo usuário)

As correções abaixo exigiriam quebrar o contrato público hoje observável pelos
consumidores da API. Foram apresentadas ao usuário antes da refatoração, que
optou por **preservar o comportamento atual**. Nenhum código relacionado a
esses três pontos foi alterado.

| Severidade | Achado | Motivo para não aplicar | Mudança que seria necessária |
|---|---|---|---|
| CRITICAL | `GET /api/admin/financial-report` e `DELETE /api/users/:id` sem autenticação/autorização | Adicionar auth faria requisições hoje aceitas (200) passarem a receber 401/403 | Middleware de autenticação/autorização (ex.: API key ou token) nessas duas rotas |
| MEDIUM | Checkout aceita `pwd` ausente (default `"123456"`) e não valida formato de email/cartão | Tornar estrito rejeitaria (400) requisições hoje aceitas (200) | Exigir `pwd` explícito e validar formato de email/cartão |
| MEDIUM | `DELETE /api/users/:id` sempre responde 200 (mesmo se o usuário não existir) e não cascateia `enrollments`/`payments` | Checar existência e cascatear mudaria o status/efeito de casos hoje "bem-sucedidos" | Checagem de existência (404 se ausente) + exclusão em cascata dos registros relacionados |

Essas três pendências permanecem como débito de segurança/integridade
conhecido e documentado, à espera de aprovação explícita para uma mudança de
contrato.
