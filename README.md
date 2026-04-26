# Mini API de Cadastro de Cotista (RBAC + Observabilidade)

API simples em FastAPI para demonstrar:
- 2 endpoints de negocio (`GET /cotistas/{id}` e `POST /cotistas`);
- autorizacao RBAC simulada com politica JSON;
- observabilidade local com logs estruturados e metricas internas de latencia/erros.

## Escopo MVP fechado
- `GET /cotistas/{id}`: consulta de cotista por ID.
- `POST /cotistas`: cadastro de cotista em repositorio em memoria.
- RBAC local por `x-role`, com permissao por recurso/acao (`cotistas:read`, `cotistas:create`).
- Validacao de CNPJ numerico (legado): sanitizacao (`.`, `/`, `-`, espacos) e digitos verificadores modulo 11.
- Logs estruturados JSON por requisicao.
- Metricas locais de requests, erros e latencia media por rota (uso interno no middleware, sem endpoint publico).

## Arquitetura
- `app/main.py`: cria a API, registra rotas e dependencias.
- `app/auth.py`: avaliador RBAC e dependencia de autorizacao.
- `app/service.py`: regra de negocio do fluxo de cotista.
- `app/repository.py`: persistencia em memoria.
- `app/observability.py`: middleware de logs estruturados + metricas locais.
- `policies/rbac_policy.json`: papeis e permissoes.

## Como executar
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Executar testes
```bash
python -m pytest -q
```

## Cenarios de demo
1. **Sucesso de autorizacao**
   - `POST /cotistas` com `x-role: admin`.
   - `GET /cotistas/{id}` com `x-role: analista`.
2. **Erro de autorizacao**
   - `POST /cotistas` com `x-role: viewer` (esperado `403`).
3. **Validacao de CNPJ**
   - Demonstrar 1 CNPJ valido (mascarado ou nao) e 1 invalido (esperado `422`).
4. **Observabilidade**
   - Mostrar linha de log JSON no terminal apos chamada.
   - Explicar que a API contabiliza latencia/erros internamente no middleware.

## Exemplo rapido (curl)
```bash
curl -X POST "http://127.0.0.1:8000/cotistas" ^
  -H "Content-Type: application/json" ^
  -H "x-role: admin" ^
  -d "{\"nome\":\"Maria\",\"documento\":\"11.444.777/0001-61\"}"
```

## Proximos passos
- Autorização com IAM (roles e policies).
- Substituir repositorio em memoria por banco (RDS/DynamoDB).
- Suportar **CNPJ alfanumerico** (novas inscricoes): regra oficial de DV e testes de conformidade.
- Publicar em ambiente cloud com dashboard/alertas.
