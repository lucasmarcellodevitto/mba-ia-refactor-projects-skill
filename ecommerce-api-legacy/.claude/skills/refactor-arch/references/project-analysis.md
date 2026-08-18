# Análise de Projeto — Heurísticas de Detecção

Heurísticas de detecção para classificação de stack, banco de dados, domínio e arquitetura. Toda conclusão deve derivar de evidências encontradas no repositório — nunca de suposições. 

## 1. Detecção de linguagem

Procure arquivos de manifesto na raiz do projeto ignorando `node_modules/`, `venv/`, `.venv/`, `.git/`, `__pycache__/`, `dist/`, `build/`,`claude/`, `lockfiles`. 

| Arquivo | Linguagem | Gerenciador |
|---|---|---|
| `package.json` | JavaScript/TypeScript | npm/yarn/pnpm (confirme pelo lockfile) |
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python | pip/poetry/pipenv |
| `go.mod` | Go | go modules |
| `pom.xml`, `build.gradle` | Java/Kotlin | maven/gradle |
| `Gemfile` | Ruby | bundler |
| `composer.json` | PHP | composer |
| `build.sbt` | Scala | sbt |
| `build.boot` | Clojure | Boot |

A linguagem dominante é a com mais arquivos-fonte. Caso exista mais de uma, reporte a principal e mencione as secundárias.


## 2. Detecção de framework

Objetivo: identificar o framework principal do projeto com base nos sinais encontrados no código e, quando possível, confirmar a evidência em arquivos de configuração ou dependências.

| Linguagem | Sinal e Framework |
|---|---|
| Java | `org.springframework.*` imports, `@SpringBootApplication` |
| Node.js | `require('express')`, `import fastify`, `require('koa')`, `@nestjs/*` decorators |
| PHP | `Illuminate\*` (Laravel), `Symfony\*` |
| Ruby | `Rails.application`, `class * < ApplicationController` |
| Python | `import bottle`, `from flask import`, `import django`, `from fastapi import` |
| Go | `github.com/gin-gonic/gin` imports, `gin.Default()`, `gin.New()` |

## 3. Detecção de banco de dados e camada de acesso

Objetivo: identificar o banco de dados utilizado e como a aplicação acessa os dados. Procure sinais no código, configurações e dependências, distinguindo ORM, driver direto e configurações de conexão. Registre apenas tecnologias com evidência no projeto.

| Sinal | Banco / Camada |
|---|---|
| String de conexão em config (`DATABASE_URI`, `:memory:`) | anote a origem dos dados |
| `SQLAlchemy`, `db.Model`, `db.Column` | ORM SQLAlchemy |
| `psycopg2`, `pg`, `mysql2` | Postgres/MySQL, driver direto |
| `pymongo`, `mongoose` | MongoDB |
| `sequelize`, `prisma`, `typeorm` | ORM Node.js |
| `sqlite3.connect(...)`, `require('sqlite3')` | SQLite, acesso direto (sem ORM) |

## Mapeamento da arquitetura

## 4. Detecção de arquitetura

**Objetivo:** identificar o padrão arquitetural predominante do projeto com base na estrutura de diretórios, organização dos módulos, responsabilidades das classes e fluxo de dependências. Priorize evidências concretas no código e registre a arquitetura apenas quando houver sinais suficientes para sustentá-la.

| Sinal | Arquitetura |
| ----- | ----------- |
| `controllers/`, `services/`, `repositories/`, `models/` com responsabilidades separadas | Layered Architecture |
| `domain/`, `application/`, `infrastructure/`, `interfaces/` | Clean Architecture |
| `entities/`, `usecases/`, `adapters/`, `frameworks/` | Hexagonal / Ports and Adapters |
| `domain/`, `application/`, `infrastructure/` com dependências direcionadas para o domínio | Clean Architecture |
| `modules/` ou `features/` agrupando controller, service, model e demais componentes por funcionalidade | Modular Architecture |
| `commands/`, `queries/`, handlers separados para leitura e escrita | CQRS |
| `events/`, `handlers/`, `publishers/`, `subscribers/` com comunicação baseada em eventos | Event-Driven Architecture |
| Serviços independentes, comunicação via HTTP, mensageria ou APIs entre aplicações | Microservices |
| Frontend e backend claramente separados, comunicando-se por API | Client-Server / API Architecture |
| `models/`, `views/`, `controllers/` com responsabilidades correspondentes | MVC |

**Procedimento:** analise primeiro a estrutura do projeto e depois confirme os padrões no código. Considere múltiplos sinais antes de classificar a arquitetura e, quando houver padrões combinados, registre a arquitetura principal e as secundárias identificadas.

 ## Resumo da Fase 1
 
 ```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <language + version>
Framework:     <framework + version>
Dependencies:  <key deps>
Domain:        <one-line business domain>
Architecture:  <classification + one-line evidence>
Source files:  <N> files analyzed
DB tables:     <tables>
================================
```

Exemplo
```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```