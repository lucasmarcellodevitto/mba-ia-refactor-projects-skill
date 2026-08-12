# Catálogo de Anti-Patterns

Use este arquivo como referência para identificar, avaliar e classificar **anti-patterns de código** durante a análise de cada arquivo-fonte. Os critérios de detecção devem permanecer **agnósticos de linguagem, framework e tecnologia**, utilizando exemplos específicos apenas para demonstrar como o mesmo problema pode se manifestar em diferentes stacks.

O catálogo organiza os anti-patterns por **severidade**, fornecendo sinais objetivos que auxiliam na identificação dos problemas e evitam classificações baseadas apenas em preferência de estilo ou opinião. Quando um padrão depender de características específicas de uma linguagem ou versão de tecnologia, isso deve ser indicado explicitamente no próprio anti-pattern.

## Escala de severidade

- **CRITICAL** — Problemas com impacto grave na segurança, integridade dos dados, funcionamento do sistema ou arquitetura. Inclui vulnerabilidades exploráveis, exposição de informações sensíveis, operações perigosas sem proteção e violações arquiteturais capazes de comprometer significativamente o sistema.

- **HIGH** — Problemas com impacto relevante na arquitetura, manutenção, testabilidade, confiabilidade ou evolução do código. Normalmente representam violações significativas de princípios de design, forte acoplamento, responsabilidades excessivas ou comportamentos que tornam mudanças futuras arriscadas e custosas.

- **MEDIUM** — Problemas que prejudicam qualidade, performance, consistência ou manutenção, mas cujo impacto tende a ser localizado ou controlável. Inclui duplicação, validações incompletas, uso inadequado de APIs, ineficiências e padrões que podem evoluir para problemas maiores.

- **LOW** — Problemas de menor impacto, principalmente relacionados à legibilidade, clareza, organização e consistência do código. Inclui nomenclatura pouco expressiva, literais sem contexto, código morto, ruído e outras práticas que dificultam a compreensão sem representar risco significativo ao funcionamento do sistema.

--- 

## CRITICAL

### 1. Injeção de comandos ou consultas
**Sinais:** entrada controlada pelo usuário concatenada ou interpolada diretamente em SQL, comandos de sistema, consultas ou interpretadores: f-strings/`+` em SQL bruto no Python; template literals/concatenação em queries no Node.js; `os.system(...)`, `subprocess` com shell habilitado ou `child_process.exec(...)` recebendo input externo. Ausência de parametrização, escaping apropriado ou APIs seguras para o contexto.
**Atenção:** nem toda interpolação representa vulnerabilidade. Só reporte quando o valor controlado pelo usuário alcançar um interpretador ou mecanismo de execução de forma que permita alterar sua estrutura ou comportamento.

### 2. Exposição de credenciais ou dados sensíveis
**Sinais:** secrets, tokens, senhas, chaves privadas ou credenciais armazenados diretamente no código ou retornados por endpoints: `SECRET_KEY = "..."`, `password = "..."`, `apiKey: "..."`; valores sensíveis presentes em logs (`print(...)`, `console.log(...)`), respostas HTTP, mensagens de erro ou arquivos de configuração versionados.
**Atenção:** constantes públicas, identificadores não secretos e configurações sem informação sensível não devem ser classificados como credenciais expostas. Considere também exposição indireta causada por serialização automática de objetos.

### 3. Operação crítica sem controle de acesso
**Sinais:** endpoints, comandos ou funções capazes de apagar dados, alterar configurações críticas, executar tarefas administrativas ou acessar informações sensíveis sem autenticação ou autorização adequada. Exemplos: rota `DELETE` que remove dados de qualquer usuário sem verificar identidade/permissão; função administrativa acessível diretamente; endpoint de manutenção/reset exposto sem proteção; `admin=true` confiado diretamente a partir do request.
**Atenção:** a existência de uma operação destrutiva não é suficiente para caracterizar o problema. O finding deve indicar a ausência ou insuficiência de uma barreira de autenticação/autorização necessária para aquela operação.


## HIGH

### 4. Responsabilidade excessiva em classes ou funções
**Sinais:** uma mesma classe, módulo ou função concentra responsabilidades de diferentes domínios, como acesso a banco, validação, regras de negócio, chamadas externas, transformação de dados e apresentação. Exemplos: função Python que recebe uma requisição, executa queries, calcula regras, envia e-mail e monta a resposta; classe Node.js responsável simultaneamente por persistência, autenticação e processamento de negócio.
**Atenção:** tamanho isoladamente não determina o anti-pattern. Considere principalmente a quantidade e a independência das responsabilidades concentradas no mesmo componente.

### 5. Acoplamento forte a implementações concretas
**Sinais:** componentes criam ou acessam diretamente suas dependências concretas em vez de recebê-las ou depender de abstrações: `Database()` instanciado dentro de serviços Python; `new StripeClient()` ou `new Repository()` criado diretamente dentro de uma regra de negócio Node.js; imports de singletons globais espalhados pelas camadas; dificuldade evidente para substituir ou simular dependências em testes.
**Atenção:** não reporte simplesmente porque uma dependência foi importada ou instanciada. O problema ocorre quando o acoplamento impede isolamento, substituição ou reutilização adequada do componente.

### 6. Estado global mutável compartilhado
**Sinais:** dados mutáveis em escopo de módulo/processo utilizados como fonte de estado da aplicação: `cache = {}` ou listas globais alteradas durante requests em Python; objetos exportados e modificados entre módulos Node.js; contadores, sessões ou dados de usuários mantidos em memória global sem controle adequado de concorrência ou ciclo de vida.
**Atenção:** constantes imutáveis, configurações somente leitura e caches deliberadamente projetados não devem ser classificados automaticamente. O risco está no compartilhamento de estado mutável que afeta o comportamento de diferentes operações ou requisições.


## MEDIUM

### 7. Queries N+1 e operações repetitivas
**Sinais:** consulta ou chamada externa executada dentro de um loop sobre resultados anteriores: `for user in users: load_orders(user.id)`; `User.query.get(item.user_id)` durante a serialização de cada item; `await repository.findById(id)` dentro de um `for...of` no Node.js; uma requisição HTTP realizada individualmente para cada registro de uma coleção.
**Atenção:** loops não são necessariamente N+1. O padrão deve ser reportado quando uma operação que poderia ser agrupada, pré-carregada ou agregada é repetida proporcionalmente ao número de elementos processados.

### 8. Validação ou tratamento de erro insuficiente
**Sinais:** entrada externa utilizada sem verificar presença, tipo, formato, faixa ou valores permitidos; `int(value)` sem tratamento quando o valor pode ser inválido; acesso direto a propriedades opcionais como `req.body.user.id`; `except Exception:` ou `catch (error) {}` ignorando a causa; retorno de erro interno diretamente para o cliente.
**Atenção:** considere o contexto e o limite de confiança da entrada. Não reporte validação duplicada quando uma camada anterior claramente garante o contrato esperado.

### 9. Duplicação significativa de lógica
**Sinais:** mesma regra de negócio, transformação, validação ou fluxo implementado em múltiplos pontos: validação de e-mail repetida em várias funções Python; mesma construção de payload copiada entre controllers Node.js; blocos quase idênticos para `create` e `update`; mesma regra alterada independentemente em diferentes módulos.
**Atenção:** pequenas repetições ou código estruturalmente semelhante não são suficientes. O finding deve indicar duplicação relevante que possa gerar inconsistência ou aumentar o custo de manutenção.


## LOW

### 10. Magic numbers e literais sem contexto
**Sinais:** números, strings ou listas com significado de negócio escritos diretamente na lógica: `if retries > 3`, `if status == "pending"`, `price * 0.15`, `setTimeout(..., 30000)`; valores semelhantes repetidos em diferentes pontos sem constantes, enums ou nomes que expliquem sua finalidade.
**Atenção:** literais óbvios e inerentes à operação, como `0`, `1` ou índices simples, não devem ser classificados automaticamente. O foco são valores cujo significado não é evidente no contexto.

### 11. Nomenclatura pouco expressiva
**Sinais:** nomes que dificultam compreender intenção ou domínio: `x`, `tmp`, `data2`, `obj`, `foo`, `a` ou `b` em lógica de negócio; funções chamadas `process()`, `handle()` ou `doStuff()` sem contexto suficiente; abreviações ambíguas; variáveis com nomes diferentes representando o mesmo conceito.
**Atenção:** nomes curtos podem ser aceitáveis em escopos pequenos e contextos óbvios, como iteradores simples. Reporte quando a nomenclatura realmente prejudicar a compreensão do código.

### 12. Código morto e ruído de desenvolvimento
**Sinais:** imports não utilizados, variáveis nunca lidas, funções ou métodos sem referências, branches inalcançáveis, comentários com código antigo, `print()`/`console.log()` deixados para debug, código temporário ou flags de teste esquecidas no fluxo de produção.
**Atenção:** código aparentemente não utilizado pode possuir função em entry points, plugins, reflection ou contratos externos. Confirme o contexto antes de classificar como código morto.

---

## Regras de reporte

1. Cada problema encontrado deve ter a referencia com **arquivo:linha(s) exatos** — releia o trecho para confirmar o número antes de reportar.
2. Reporte todos problemas encontrados mesmo que um anti-pattern esteja presente em vários pontos. Não infle a contagem.
3. Ordene CRITICAL → HIGH → MEDIUM → LOW.
4. Mínimo esperado num projeto legado: 5+ problemas com pelo menos 1 CRITICAL/HIGH. Se encontrar menos que isso, releia os arquivos — provavelmente algo passou.