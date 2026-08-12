# Guidelines de Arquitetura MVC  

## Objetivo

Este documento define guidelines para identificar, implementar e revisar aplicações que utilizam o padrão arquitetural MVC (Model-View-Controller). A skill deve usar estas regras como referência para preservar a separação de responsabilidades, reduzir acoplamento e manter o código organizado.

## 1. Responsabilidades

### Model

Responsável pelos dados e pelas regras de negócio relacionadas ao domínio.

- Representar entidades e seu estado.
- Definir validações e regras de negócio pertencentes ao domínio.
- Gerenciar persistência quando essa responsabilidade fizer parte do padrão adotado pelo framework.
- Não depender de `Controller` ou `View`.
- Evitar lógica específica de apresentação ou HTTP.

### View

Responsável exclusivamente pela apresentação dos dados ao usuário.

- Renderizar dados recebidos do `Controller`.
- Conter lógica mínima necessária para apresentação.
- Não executar regras de negócio.
- Não acessar diretamente banco de dados ou serviços de infraestrutura.
- Evitar chamadas diretas ao `Model` quando isso criar acoplamento desnecessário.

### Controller

Responsável por coordenar o fluxo entre entrada, aplicação e resposta.

- Receber e interpretar requisições.
- Validar ou delegar validações de entrada.
- Chamar os serviços ou componentes necessários.
- Preparar os dados necessários para a `View`.
- Retornar a resposta apropriada.
- Evitar conter regras de negócio complexas.
- Evitar acesso direto ao banco quando existir uma camada de serviço/repositório.

## 2. Fluxo esperado

O fluxo preferencial deve seguir:

`Request → Controller → Service/Model → Controller → View/Response`

Quando a aplicação não possuir uma camada de `Service`, o `Controller` pode interagir diretamente com o `Model`, desde que isso esteja alinhado ao padrão existente do projeto.

A skill não deve introduzir novas camadas apenas para seguir este documento quando o projeto já possui uma estrutura consistente.

## 3. Regras de separação

- `Controller` não deve conter regras de negócio complexas.
- `View` não deve conter regras de negócio ou acesso a dados.
- `Model` não deve conhecer detalhes de HTTP, UI ou apresentação.
- Evite duplicar regras de negócio entre `Controller`, `View` e `Model`.
- Responsabilidades compartilhadas devem ser extraídas para componentes apropriados.
- Dependências devem seguir a direção natural da arquitetura existente.
- Não misture responsabilidades apenas para reduzir o número de arquivos.

## 4. Controllers

Controllers devem permanecer pequenos e orientados à orquestração.

Preferir:

1. Receber a entrada.
2. Validar ou delegar a validação.
3. Invocar o caso de uso, serviço ou model apropriado.
4. Preparar a resposta.
5. Retornar a resposta.

Evitar:

- Consultas SQL extensas.
- Regras de negócio complexas.
- Transformações excessivas de dados.
- Lógica reutilizável específica de domínio.
- Dependências desnecessárias.
- Métodos excessivamente grandes.

## 5. Models

Models devem concentrar responsabilidades relacionadas ao domínio e aos dados.

- Manter invariantes e regras diretamente relacionadas à entidade.
- Encapsular operações específicas do modelo quando apropriado.
- Evitar dependências de apresentação.
- Evitar assumir responsabilidades pertencentes ao `Controller`.
- Não transformar o `Model` em um objeto que concentra toda a lógica da aplicação.

Quando o projeto utilizar ORM, respeitar os padrões e convenções do ORM existente.

## 6. Views

Views devem receber dados preparados para apresentação.

- Manter templates simples.
- Evitar chamadas ao banco ou serviços externos.
- Evitar regras de negócio.
- Evitar lógica complexa de transformação.
- Reutilizar componentes de apresentação quando disponíveis.

## 7. Services e Repository

MVC pode utilizar camadas auxiliares quando a complexidade do projeto justificar.

### Service

Utilizar `Service` para:

- Casos de uso.
- Regras de negócio que envolvem múltiplos Models.
- Orquestração de operações complexas.
- Processos reutilizados por diferentes Controllers.

### Repository

Utilizar `Repository` quando houver necessidade de:

- Isolar acesso a dados.
- Encapsular consultas complexas.
- Abstrair uma fonte de dados.
- Reutilizar operações de persistência.

Não criar `Service` ou `Repository` apenas por convenção se isso adicionar complexidade sem benefício.

## 8. Validação e tratamento de erros

- Validação de entrada deve ocorrer próximo à fronteira da aplicação.
- Regras de negócio devem ser validadas na camada responsável pelo domínio.
- Erros devem ser tratados de forma consistente com o framework.
- Controllers devem evitar implementar estratégias diferentes de tratamento para erros equivalentes.
- Não expor detalhes internos, SQL, stack traces ou informações sensíveis nas respostas.
