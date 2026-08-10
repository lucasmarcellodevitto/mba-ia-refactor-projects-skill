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
