````md
# Playbook de Refatoração

Guia operacional para transformar os anti-patterns identificados durante a
análise em correções concretas. Cada procedimento descreve uma estratégia de
refatoração, apresenta exemplos em Python e Node.js quando relevante e indica
cuidados necessários para preservar comportamento, contratos e compatibilidade.

As transformações devem ser interpretadas de forma **agnóstica à tecnologia**:
o código apresentado serve como demonstração do princípio, enquanto a
implementação final deve utilizar os mecanismos equivalentes disponíveis na
stack analisada.

## Princípios de execução

- Corrija primeiro problemas que representam risco de segurança, integridade ou
  perda de dados.
- Faça mudanças pequenas e isoladas sempre que possível.
- Preserve contratos públicos, comportamento esperado e regras de negócio.
- Antes de criar uma nova abstração, procure por uma implementação existente
  que possa ser reutilizada.
- Não introduza dependências, frameworks ou padrões arquiteturais sem
  necessidade.
- Após cada transformação relevante, verifique se o código continua compilável,
  inicializável ou executável.
- Execute os testes existentes relacionados à área modificada.
- Quando não houver testes, faça pelo menos uma validação funcional do fluxo
  afetado.
- Não considere uma refatoração concluída apenas porque o código "parece
  melhor"; confirme que o comportamento anterior foi preservado, exceto quando
  a correção exige explicitamente uma mudança de comportamento.
- Mudanças que alteram contratos externos, permissões ou comportamento funcional
  devem ser destacadas no finding ou relatório de refatoração.

---

## 1. SQL Injection → Parametrização de valores

Substitua SQL construído dinamicamente com dados externos por consultas
parametrizadas ou pelos mecanismos seguros equivalentes da biblioteca/ORM.

**Antes (Python):**
```python
email = request.args["email"]

cursor.execute(
    f"SELECT id FROM users WHERE email = '{email}'"
)
````

**Depois:**

```python
email = request.args["email"]

cursor.execute(
    "SELECT id FROM users WHERE email = ?",
    (email,)
)
```

**Antes (Node.js):**

```js
const email = req.query.email;

db.get(
  `SELECT id FROM users WHERE email = '${email}'`,
  (err, user) => {
    // ...
  }
);
```

**Depois:**

```js
const email = req.query.email;

db.get(
  "SELECT id FROM users WHERE email = ?",
  [email],
  (err, user) => {
    // ...
  }
);
```

Em ORMs e query builders, utilize os mecanismos de binding fornecidos pela
biblioteca. Não substitua parametrização por escaping manual quando a API já
oferecer suporte nativo a parâmetros.

**Validação:** testar entradas contendo aspas, caracteres especiais e payloads
de injeção e confirmar que são tratadas exclusivamente como valores.

---

## 2. Secrets no código → Configuração externa

Remova credenciais, tokens, chaves privadas e outros valores secretos do código
e faça a aplicação obtê-los por configuração externa apropriada.

**Antes:**

```python
DATABASE_PASSWORD = "prod_password_123"
API_KEY = "sk_live_example"
```

**Depois:**

```python
import os

DATABASE_PASSWORD = os.environ["DATABASE_PASSWORD"]
API_KEY = os.environ["API_KEY"]
```

**Node.js:**

```js
const config = {
  databasePassword: process.env.DATABASE_PASSWORD,
  apiKey: process.env.API_KEY,
};
```

Para valores obrigatórios, prefira falhar explicitamente durante a inicialização
quando a configuração não estiver disponível.

Crie documentação ou um arquivo de exemplo contendo apenas os nomes das
variáveis necessárias:

```text
DATABASE_PASSWORD=
API_KEY=
```

O arquivo que contém os valores reais não deve fazer parte do controle de
versão.

**Validação:** procurar novamente por padrões de secrets no código e verificar
que nenhum valor sensível continua presente em logs, respostas ou arquivos
versionados.

---

## 3. Dados sensíveis expostos → DTO/serializer com allowlist

Evite serializar automaticamente objetos completos quando eles contêm campos
que pertencem apenas ao contexto interno da aplicação.

**Antes (Python):**

```python
def serialize_user(user):
    return user.__dict__
```

**Depois:**

```python
def serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
    }
```

**Antes (Node.js):**

```js
res.json(user);
```

**Depois:**

```js
res.json({
  id: user.id,
  name: user.name,
  email: user.email,
});
```

Prefira uma lista explícita dos campos permitidos em respostas públicas em vez
de remover individualmente campos considerados perigosos.

**Atenção:** verificar consumidores existentes antes de remover propriedades.
Se um campo fazia parte de um contrato público, a alteração deve ser tratada
como mudança de contrato.

---

## 4. Falta de autenticação/autorização → Middleware ou guard reutilizável

Centralize verificações de identidade e permissão em mecanismos reutilizáveis,
em vez de duplicá-las em cada handler.

**Antes (Node.js):**

```js
router.delete("/users/:id", async (req, res) => {
  await userRepository.delete(req.params.id);
  res.sendStatus(204);
});
```

**Depois:**

```js
router.delete(
  "/users/:id",
  requireAuth,
  requireAdmin,
  async (req, res) => {
    await userRepository.delete(req.params.id);
    res.sendStatus(204);
  }
);
```

**Exemplo conceitual (Python):**

```python
@require_auth
@require_admin
def delete_user(user_id):
    user_service.delete(user_id)
    return "", 204
```

Se já existir infraestrutura de autenticação, autorização ou ownership,
reutilize-a em vez de criar uma segunda implementação.

A proteção deve considerar também autorização sobre o recurso:

```python
if resource.owner_id != current_user.id and not current_user.is_admin:
    raise ForbiddenError()
```

**Validação mínima:**

* acessar a operação sem autenticação;
* acessar com usuário autenticado sem a permissão necessária;
* acessar recurso pertencente a outro usuário;
* verificar que campos privilegiados enviados pelo cliente não alteram
  diretamente permissões ou roles.

---

## 5. Operação multi-etapa → Unidade transacional

Quando várias alterações precisam ser tratadas como uma única operação lógica,
garanta que uma falha não deixe o sistema em estado parcialmente atualizado.

**Antes:**

```python
create_order(order)

for item in items:
    create_order_item(item)

update_inventory(items)
```

**Depois:**

```python
try:
    begin_transaction()

    create_order(order)

    for item in items:
        create_order_item(item)

    update_inventory(items)

    commit_transaction()

except Exception:
    rollback_transaction()
    raise
```

Em Node.js, utilize a API transacional fornecida pelo driver ou ORM e garanta
que qualquer erro interrompa a operação e provoque rollback.

**Atenção:** não adicione commits individuais dentro de uma operação que deveria
ser atômica. O limite da transação deve corresponder à unidade lógica que não
pode ser parcialmente aplicada.

**Validação:** provocar uma falha no meio da operação e confirmar que nenhuma
das alterações que deveriam ser atômicas permanece aplicada.

---

## 6. N+1 → Carregamento em lote

Identifique operações executadas repetidamente dentro de loops e substitua-as
por carregamento antecipado, joins, agregações ou consultas em lote.

**Antes:**

```python
users = get_users()

for user in users:
    orders = get_orders_by_user(user.id)
```

**Depois:**

```python
users = get_users()
orders_by_user = get_orders_for_users(
    [user.id for user in users]
)

for user in users:
    orders = orders_by_user.get(user.id, [])
```

**Node.js:**

```js
for (const user of users) {
  user.orders = await orderRepository.findByUserId(user.id);
}
```

pode ser transformado em:

```js
const userIds = users.map(user => user.id);
const orders = await orderRepository.findByUserIds(userIds);
```

O mecanismo específico pode ser `JOIN`, eager loading, `IN (...)`, DataLoader,
batching ou equivalente da tecnologia utilizada.

**Validação:** medir ou observar a quantidade de operações antes e depois.
Uma coleção de `N` elementos não deve gerar `N` consultas adicionais quando a
informação puder ser obtida em lote.

---

## 7. Regra de negócio no controller → Serviço de domínio

Controllers, routes e handlers devem coordenar a entrada e saída da aplicação,
não concentrar regras de negócio complexas.

**Antes:**

```python
def create_order():
    data = request.get_json()

    if not data["items"]:
        return {"error": "Pedido vazio"}, 400

    total = sum(
        item["price"] * item["quantity"]
        for item in data["items"]
    )

    if total > 1000:
        send_notification(data["user_id"])

    save_order(data, total)

    return {"total": total}, 201
```

**Depois:**

```python
# services/order_service.py

class OrderService:
    def create(self, user_id, items):
        if not items:
            raise ValidationError("Pedido vazio")

        total = calculate_total(items)

        order = self.repository.create(
            user_id=user_id,
            items=items,
            total=total,
        )

        if total > 1000:
            self.notification_service.notify(user_id)

        return order
```

```python
# controller

def create_order():
    data = request.get_json()

    order = order_service.create(
        data["user_id"],
        data["items"],
    )

    return jsonify(order), 201
```

A camada extraída deve ser testável sem depender diretamente do framework HTTP.

---

## 8. Dependências concretas → Injeção de dependência

Quando uma regra de negócio cria diretamente seus colaboradores, extraia essas
dependências para o limite do componente.

**Antes:**

```python
class CheckoutService:
    def __init__(self):
        self.database = Database()
        self.payment = PaymentGateway()
```

**Depois:**

```python
class CheckoutService:
    def __init__(self, database, payment):
        self.database = database
        self.payment = payment
```

A composição fica responsável por fornecer as implementações:

```python
service = CheckoutService(
    database=database,
    payment=payment_gateway,
)
```

**Node.js:**

```js
class CheckoutService {
  constructor(orderRepository, paymentGateway) {
    this.orderRepository = orderRepository;
    this.paymentGateway = paymentGateway;
  }
}
```

O objetivo não é criar interfaces ou containers de dependência
desnecessariamente. A refatoração deve apenas remover o acoplamento que impede
substituição, teste ou reutilização.

---

## 9. Duplicação → Fonte única de comportamento

Quando uma mesma regra aparece em vários lugares, extraia o comportamento para
um ponto compartilhado e substitua as implementações duplicadas por chamadas a
esse ponto.

**Antes:**

```python
if user.status == "active" and user.email_verified:
    allow_access()
```

A mesma condição aparece em vários controllers.

**Depois:**

```python
def can_access(user):
    return (
        user.status == "active"
        and user.email_verified
    )
```

Uso:

```python
if can_access(user):
    allow_access()
```

**Node.js:**

```js
// Antes
if (account.status === "active" && account.verified === true) {
  // ...
}

// Depois
function canAccess(account) {
  return account.status === "active" && account.verified === true;
}
```

Antes de criar o helper, procure funções, métodos ou serviços existentes que já
representem a mesma regra.

**Atenção:** não force uma abstração quando as implementações apenas parecem
semelhantes, mas possuem regras de negócio diferentes.

---

## 10. Tratamento genérico de exceções → Erros específicos

Substitua capturas amplas que escondem falhas ou retornam informações internas
por tratamento explícito de situações conhecidas.

**Antes:**

```python
try:
    process_payment()
except Exception as error:
    return {
        "error": str(error)
    }, 500
```

**Depois:**

```python
try:
    process_payment()
except PaymentDeclinedError:
    return {"error": "Pagamento recusado"}, 402
except ValidationError as error:
    return {"error": str(error)}, 400
except Exception:
    logger.exception("Unexpected payment error")
    return {"error": "Erro interno"}, 500
```

**Node.js:**

```js
try {
  await processPayment();
} catch (error) {
  if (error instanceof PaymentDeclinedError) {
    return res.status(402).json({
      error: "Pagamento recusado",
    });
  }

  logger.error(error);
  return res.status(500).json({
    error: "Erro interno",
  });
}
```

Não exponha stack traces, mensagens de banco, credenciais ou detalhes de
infraestrutura para clientes externos.

---

## 11. API obsoleta → API suportada pela versão atual

Antes de substituir uma API marcada como deprecated, confirme a versão real da
linguagem, runtime, framework ou biblioteca utilizada pelo projeto.

**Python:**

```python
# Antes
created_at = datetime.utcnow()
```

```python
# Depois
from datetime import datetime, timezone

created_at = datetime.now(timezone.utc)
```

**Node.js:**

```js
// Antes
const buffer = new Buffer(value);
```

```js
// Depois
const buffer = Buffer.from(value);
```

A substituição deve considerar o comportamento da versão instalada e possíveis
diferenças de API.

**Validação:** consultar manifesto/lockfile/configuração do projeto e executar
os testes relacionados após a alteração.

---

## 12. God Object → Separação por responsabilidade

Quando um componente concentra diferentes áreas do sistema, divida-o por
responsabilidades coerentes.

**Antes:**

```js
class ApplicationManager {
  connectDatabase() {}
  authenticateUser() {}
  createOrder() {}
  sendEmail() {}
  generateReport() {}
  registerRoutes() {}
}
```

**Depois:**

```js
class UserService {
  authenticateUser() {}
}

class OrderService {
  createOrder() {}
}

class NotificationService {
  sendEmail() {}
}

class ReportService {
  generateReport() {}
}
```

A camada de composição pode conectar os componentes:

```js
const notificationService = new NotificationService();

const orderService = new OrderService(
  orderRepository,
  notificationService
);
```

A divisão deve seguir responsabilidades e coesão, não simplesmente criar vários
arquivos pequenos. Evite substituir um God Object por dezenas de classes sem
responsabilidade clara.

---

## 13. Estado global mutável → Estado controlado

Remova estado compartilhado entre operações quando ele puder causar
interferência, condições de corrida ou comportamento dependente da ordem das
requisições.

**Antes:**

```python
current_user = None

def login(user):
    global current_user
    current_user = user
```

**Depois:**

```python
def login(user):
    session["user_id"] = user.id
```

**Node.js:**

```js
let currentUser;

app.post("/login", (req, res) => {
  currentUser = authenticate(req.body);
});
```

deve utilizar o mecanismo apropriado de sessão, token ou contexto de request:

```js
app.post("/login", (req, res) => {
  const user = authenticate(req.body);

  req.session.userId = user.id;

  res.sendStatus(204);
});
```

**Atenção:** caches, pools e singletons podem ser intencionais. O objetivo não é
eliminar todo estado global, mas remover estado de aplicação que deveria ser
isolado por request, usuário ou operação.

---

## 14. Magic numbers → Constantes semânticas

Substitua valores cujo significado depende do domínio por nomes que expressem
sua intenção.

**Antes:**

```python
if retry_count >= 3:
    disable_account()
```

**Depois:**

```python
MAX_LOGIN_RETRIES = 3

if retry_count >= MAX_LOGIN_RETRIES:
    disable_account()
```

**Node.js:**

```js
const SESSION_TIMEOUT_MS = 30 * 60 * 1000;

setTimeout(expireSession, SESSION_TIMEOUT_MS);
```

O objetivo é tornar o significado explícito e evitar que o mesmo valor seja
replicado sem contexto.

Não transforme automaticamente todos os números literais em constantes.

---

## 15. Código morto → Remoção após confirmação

Remova imports, funções, branches, variáveis e código temporário que não possuem
mais uso, mas confirme primeiro que não existe utilização indireta.

**Antes:**

```python
import legacy_reports

def calculate_total(items):
    return sum(item.price for item in items)

def old_calculate_total(items):
    # implementação antiga
    return 0
```

**Depois:**

```python
def calculate_total(items):
    return sum(item.price for item in items)
```

Antes de remover código, verificar referências, exports, entry points, comandos
de CLI, carregamento dinâmico e integrações que possam não aparecer em buscas
simples.

**Atenção:** comentários explicando uma decisão arquitetural não são código
morto e não devem ser removidos apenas por não participarem da execução.

---

## Ordem recomendada de aplicação

A sequência deve considerar dependências entre as mudanças e o risco de cada
transformação.

1. **Preservar uma baseline funcional** — executar testes existentes e registrar
   o estado inicial.
2. **CRITICAL** — corrigir vulnerabilidades, exposição de secrets, permissões
   ausentes e operações que possam comprometer dados.
3. **Integridade e confiabilidade** — corrigir transações, tratamento de erros e
   validações que possam deixar o sistema inconsistente.
4. **HIGH** — reduzir acoplamento, separar responsabilidades e mover regras de
   negócio para componentes adequados.
5. **MEDIUM** — eliminar N+1, duplicações e APIs obsoletas.
6. **LOW** — melhorar nomenclatura, constantes, organização e remover ruído.
7. **Validação final** — executar testes, verificar alterações de contrato e
   revisar o diff completo.

Quando uma transformação estrutural for pré-requisito para outras correções,
ela pode ser antecipada. A ordem de severidade é uma diretriz de prioridade,
não uma regra que obrigue mudanças independentes a serem aplicadas em sequência.

## Regra de segurança da refatoração

Nunca considere uma transformação concluída somente pela alteração do código.
Para cada mudança relevante, registrar:

* anti-pattern corrigido;
* arquivos/componentes afetados;
* transformação realizada;
* comportamento que deve permanecer igual;
* eventual mudança de contrato ou comportamento;
* validações executadas;
* testes aprovados ou limitações conhecidas.

Se a correção não puder ser validada com segurança, **não mascarar a incerteza**:
registrar a limitação e evitar alterações especulativas.

```
```
