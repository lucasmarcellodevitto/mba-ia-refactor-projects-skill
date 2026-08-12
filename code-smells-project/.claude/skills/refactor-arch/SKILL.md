---
name: refactor-arch
description: >
  Audita e refatora projetos de software para o padrão MVC sendo agnostico em relação a tecnologia detectando linguagem, framework, banco de dados e domínio realizando o processo em 3 fases sequenciais: — Análise: etapa que detecta stack e arquitetura — Auditoria: etapa que cruza o código contra um catálogo de anti-patterns gerando um relatório classificado por gravidade que aponta exatamente o arquivo e a linha do problema  — Refatoração: etapa que ocorre após confirmação explícita do usuário e refatora o projeto
---

# refactor-arch — Auditoria e Refatoração Arquitetural (MVC)

Você atua como um arquiteto de software sênior, especializado em analisar, auditar e refatorar sistemas legados, com foco na identificação de problemas arquiteturais e na migração estruturada para o padrão MVC.

## REGRAS INVIOLÁVEIS

1 = Execute as 3 fases abaixo em ordem sequencial. Nunca pule ou altere a ordem de uma fase. 

2 - Nunca modifique nenhum arquivo do projeto antes que o usuário confirme essa ação explicitamente ao final da Fase 2.

3 - A refatoração DEVE preservar integralmente o comportamento observável no projeto.

Isso significa que, por padrão, o agente NÃO DEVE alterar:

- as rotas e endpoints existentes;
- os métodos HTTP utilizados;
- os parâmetros de entrada;
- os contratos e formatos das requisições (request);
- os contratos e formatos das respostas (response);
- os códigos de status HTTP;
- os campos, tipos e estruturas dos dados retornados;
- os comportamentos funcionais atualmente expostos aos consumidores da API.

Qualquer alteração no comportamento, contrato ou interface pública do projeto somente poderá ser realizada quando for aprovado pelo usuário.

Na ausência de uma autorização explícita presuma que o comportamento existente deve permanecer inalterado.

Se uma refatoração estrutural exigir uma mudança de comportamento ou contrato que não esteja aprovada, não realize essa alteração. Interrompa a etapa afetada e informe ao usuário a necessidade de aprovação prévia.

---

## Fase 1 — Análise

1 - Leia [project-analysis.md](references/project-analysis.md) e siga as heurísticas contidas no arquivo.

2 - Liste todos os arquivos e diretórios relevantes do projeto, ignorando obrigatoriamente:
- `node_modules/`
- `venv/`
- `.git/`
- `__pycache__/`
- `.claude/`
- arquivos de lock de dependências, como:
  - `package-lock.json`
  - `yarn.lock`
  - `pnpm-lock.yaml`
  - `poetry.lock`
  - `Pipfile.lock`
  - equivalentes de outras tecnologias

3 - **Mapeie a arquitetura atual do projeto:** identifique as camadas existentes, a responsabilidade efetiva de cada arquivo (com base no código, não apenas no nome ou na estrutura esperada) e o fluxo completo de uma request, desde a rota até o acesso ao banco de dados.

4 - **Registre o baseline de execução:** identifique o comando usado para iniciar a aplicação, a porta em que ela é executada e liste todos os endpoints atualmente disponíveis, informando **método HTTP + path**. Esse baseline será usado como critério de validação na Fase 3.

5 - **Gere o resumo da Fase 1:** siga exatamente o formato definido em [project-analysis.md](references/project-analysis.md) e apresente o resultado sob o título **"Resumo da Fase 1"**.

> **Importante:** a Fase 1 é apenas uma fotografia do estado atual do projeto. Não faça julgamentos, não proponha melhorias e não registre problemas ou inconsistências nesta etapa.

---

## Fase 2 — Auditoria

1 - Leia os arquios 
[antipattern-catalog.md](references/antipattern-catalog.md) e [report-template.md](references/report-template.md)

2 - Leia integralmente todos os arquivos-fonte do projeto ignorando obrigatoriamente:
- `node_modules/`
- `venv/`
- `.git/`
- `__pycache__/`
- `.claude/`
- arquivos de lock de dependências, como:
  - `package-lock.json`
  - `yarn.lock`
  - `pnpm-lock.yaml`
  - `poetry.lock`
  - `Pipfile.lock`
  - equivalentes de outras tecnologias

3 - Compare cada linha de código com cada anti-pattern do catálogo.

4 - Classifique cada problema encontrado pela severidade de forma ordenada (CRITICAL -> HIGH -> MEDIUM -> LOW) e gere um relatório seguindo exatamente o template de [report-template.md](references/report-template.md) dentro da pasta reports/.

5 - Ao registrar o problema seja especifico registrando o arquivo e a linha(s) exatos.

6 - Encontre e registre no mínimo 5 problemas com pelo menos 1 CRITICAL/HIGH.

7 - Inclua verificação de APIs deprecated da linguagem/framework detectados.

8 - Após finalizar a analise e criação do relatório pare e Pergunte ao usuário, usando a ferramenta de pergunta se disponível ou uma mensagem direta questionando se pode seguir para a fase 3 - Refatoração.
Use como pegunta a seguinte mensagem:

```Fase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n] ? ```

9 - Considere apenas as respostas s para seguir para a proxima etapa e n para encerrar o processo. Caso a resposta seja algo diferente dessas duas opções repita por mais 3 vezes e finalize o processo caso não obtenha e resposta correta em nenhuma das tentativas e exiba a seguinte mensagem: 

```Finalizando o processo sem executar o step de Refatoração```

## Fase 2 — Refatoração

1 - Leia [mvc-guidelines.md](eferences/mvc-guidelines.md) e [refactoring-playbook.md](references/refactoring-playbook.md).

2 - Aplique as refatorações necessárias para cada problema do relatório gerado na Fase 2, do CRITICAL ao LOW. Corrija a arquitetura e os problemas pontuais (segurança, N+1, duplicação, nomenclatura). Resolver um problema significa mudar o código para que o problema deixe de existir — não basta reorganizar em MVC nem repetir a recomendação.

3 - Para cada correção, use o padrão de transformação correspondente do playbook.

4 - Garanta com que as aplicações refatoradas estejam funcionand. Se a validação falhar, corrija antes de declarar concluído — nunca entregue a aplicação quebrada.


