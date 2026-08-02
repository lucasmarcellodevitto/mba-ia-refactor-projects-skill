# Criação de Skills — Refatoração Arquitetural Automatizada

## Análise Manual

### Projeto 1 — code-smells-project 

| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL | SQL Injection | `models.py:28`| vulnerabilidade de SQL Injection devido ao tratamento inadequado de entradas do usuário em consultas ao banco de dados |
| CRITICAL | SQL Injection | `models.py:48`| vulnerabilidade de SQL Injection devido ao tratamento inadequado de entradas do usuário em consultas ao banco de dados |
| CRITICAL | SQL Injection | `models.py:110`| vulnerabilidade de SQL Injection devido ao tratamento inadequado de entradas do usuário em consultas ao banco de dados |
| CRITICAL | SQL Injection | `models.py:291`| vulnerabilidade de SQL Injection devido ao tratamento inadequado de entradas do usuário em consultas ao banco de dados |
| CRITICAL | Endpoints com função de admin sem autenticação: `reset-db` (DELETE em massa) e `query` (SQL cru do body) | `app.py:47-78` | Qualquer pessoa apaga o banco ou executa SQL arbitrário|
| MEDIUM | Queries N+1 em listagens de pedidos e relatório de vendas | `models.py:171-233` | Cursores aninhados em loop; degrada de ms para segundos em produção. |
| MEDIUM | Código duplicado de validação `if "nome" not in dados`| `controllers.py: 30-35` `controllers.py: 72-74` | A mesma lógica aparece em vários endpoints. |
|LOW|	Magic numbers | `models.py:257`| valores numéricos fixos escritos diretamente no código, sem uma explicação ou um nome que indique seu significado |
|LOW|	Logs não estruturados com uso de `ptint()`| `controllers.py:8-11-57...`| Sem níveis, timestamps |

### Projeto 2 - ecommerce-api-legacy

| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL | **Secrets hardcoded**  | `src/utils.js:3-5` | senha de banco "de produção" e chave live de gateway no código |
| CRITICAL |Exposição de dados sensíveis via log| `src/AppManager.js:45`| número do cartão e a chave do gateway impressos em log|
| CRITICAL | God Class misturando banco, rotas e regras de negócio | `src/AppManager.js:4-139` | uma única classe concentra responsabilidades demais, tornando-se responsável por praticamente toda a lógica da aplicação |
| MEDIUM | Queries N+1 no relatório financeiro: 1 query por curso + 1 por matrícula (usuário) + 1 por matrícula (pagamento)| `src/AppManager.js:83-128` | Muitas consultas ao banco em vez de JOINs |
| MEDIUM | Falta de validação de `payment.amount` | `src/AppManager.js:4-139` | Pode resultar em NaN ou cálculos incorretos no relatório financeiro. |
|LOW| Magic number | `src/AppManager.js:46`| valores numéricos fixos escritos diretamente no código, sem uma explicação ou um nome que indique seu significado |
| LOW | Código morto: `totalRevenue`, `globalCache`| `src/utils.js:9-10` | Engana o desenvolvedor sobre o que o sistema realmente faz. |
|LOW| meaningful names - Nomenclatura pouco descritiva | `src/AppManager.js:29-33`|variáveis `u`, `e`, `p`, `cid`, `cc`|

### Projeto 3 - task-manager-api

| Severidade | Problema | Localização | Observações |
|:----------:|:--------:|:-----------:|:-----------:|
| CRITICAL | Uso de MD5 para senhas (`set_password`/`check_password`) | `models/user.py:29` `models/user.py:32` | MD5 é rápido e sujeito a rainbow tables. O ideal é usar uma biblioteca própria para senhas|
| CRITICAL | Senha exposta no `to_dict()` | `models/user.py:16-25` | O hash trafega em respostas (inclusive login),|
| MEDIUM | Uso do `datetime.utcnow()` que é uma API deprecated | `routes/task_routes.py:31` | API deprecada partir do Python 3.12, risco em upgrades. |
| MEDIUM | Repetição de codigo para da regra de `overdue` | `routes/task_routes.py:30-39,71-80,283-287`| Poderia ser abstraido para um unico método|
| LOW | Import desnecessário | `task.py:3`| import json não usado|
| LOW | Datas usando str() em vez de isoformat() | `task.py:32`| |