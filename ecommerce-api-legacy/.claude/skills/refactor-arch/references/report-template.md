# Template do Relatório de Auditoria - Fase 2

Use **exatamente** esta estrutura, tanto na impressão no chat quanto no arquivo salvo. Substitua os `<placeholders>` sem adicionar ou remover seções.

```

================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

Findings

[CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL,
             validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

[CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

PFase 2 concluída. Prosseguir com a refatoração (Fase 3)? [s/n] ?

```