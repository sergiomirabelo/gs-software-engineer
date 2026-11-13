# GS2026.2 — CitizenTech Mobilidade (Engenharia de Software · 2CCPY-2026)

Serviço da Secretaria de Mobilidade para consultar pontos de ônibus (status e alternativa) e fazer perguntas em linguagem natural, com IA atrás de uma porta/adaptador.

## Índice do dossiê
| Arquivo | Conteúdo |
|---|---|
| `1_visao_produto.md` | Persona, problema, RF, RNF com número, critérios de aceite, fora de escopo, riscos |
| `2_contrato_api.yaml` | OpenAPI 3.1.0 (escrito antes do código) |
| `3_arquitetura.md` | Diagramas, fronteira porta/adaptador, ADRs, observabilidade, segurança |
| `4_slice/` | Código (`src/domain`, `src/infra`, `src/api`), `tests/`, `evals/`, CI |
| `5_evals_de_ia.md` | Casos, métrica, guardrails, regressão e rollout |
| `7_demo_video_url.txt`, `8_certificacao.txt`, `9_Chat_Log.txt` | Vídeo, certificação e uso de IA |

## Como rodar (a partir de `4_slice/`)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest --cov=src --cov-fail-under=70                # testes (sem LLM real)
ruff check .                                         # lint
openapi-spec-validator openapi/2_contrato_api.yaml   # valida o contrato
python -m evals.run_evals                            # evals, 30 casos (LLM_PROVIDER=fake por padrão)
python -m evals.measure_latency                      # p95 local do serviço (sem LLM real)
uvicorn src.api.main:app --port 8000                 # sobe o serviço
```
Alternativa: `docker compose up` (porta 8000). Para usar o Ollama: `LLM_PROVIDER=ollama OLLAMA_MODEL=llama3.2`.

`openapi/2_contrato_api.yaml` é cópia idêntica de `2_contrato_api.yaml` (a raiz do zip), mantida dentro de `4_slice/` para o CI do repositório enxergar o contrato. Para o CI do GitHub, use o conteúdo de `4_slice/` como raiz do repositório.

## Requisições reais (executadas com `uvicorn`)
```
$ curl -i localhost:8000/stops/pt-003
HTTP/1.1 200 OK
{"id":"pt-003","name":"Praça da Sé","lines":["1018-10","407Y-10"],"status":"SUSPENDED","alternative_stop_id":"pt-004","note":"Desvio por evento até as 18h"}

$ curl -i localhost:8000/stops/xx
HTTP/1.1 404 Not Found
{"code":"NOT_FOUND","message":"Ponto 'xx' não encontrado","details":[]}

$ curl -X POST localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"A Praça da Sé está funcionando?"}'
{"answer":"O ponto Praça da Sé (linhas 1018-10, 407Y-10) está suspenso. Alternativa: Largo São Francisco (pt-004). Aviso: Desvio por evento até as 18h.","stop_id":"pt-003","refused":false}
```

## Evidências de execução
**Local (execução real em 07/11/2026):**
- `ruff check .` → `All checks passed!`
- `openapi-spec-validator openapi/2_contrato_api.yaml` → `OK`
- `pytest --cov=src --cov-fail-under=70` → `29 passed`, cobertura total 76%
- `python -m evals.run_evals` (provedor `fake`) → `30/30 (100%)`, recusas corretas `11/11`
- `python -m evals.measure_latency` (fake, TestClient, 300 chamadas) → p95 `GET /stops/pt-003` ≈ 2,5 ms e p95 `POST /ask` ≈ 2,2 ms. Isso mede só o overhead do serviço; a latência com LLM real (meta < 4 s) precisa ser medida com Ollama.

**CI do GitHub Actions:** 

<img width="1229" height="116" alt="image" src="https://github.com/user-attachments/assets/9424d0db-2e6b-4364-8269-8fefa7efa799" />

Repositório: https://github.com/sergiomirabelo/gs-software-engineer.git

## Decisões principais
Resumo (detalhes em `3_arquitetura.md`): porta própria para a IA (ADR-001), prompt ancorado em dados em vez de RAG (ADR-002), `fake` por padrão e Ollama opcional (ADR-003), contrato antes do código com teste de contrato automatizado (ADR-004). Docker Compose e teste de contrato (schema × resposta) estão incluídos como extras.

## Mapa requisito → contrato → código → teste
| Requisito | Contrato | Código | Teste |
|---|---|---|---|
| RF-03 / CA-01, CA-02 | `GET /stops/{stop_id}` | `StopService.get` | `test_get_stop_ok`, `test_get_stop_not_found_returns_standard_error` |
| RF-01, RF-02 / CA-03 | `GET /stops` | `list_stops` | `test_list_stops_*` |
| RF-04, RF-05 / CA-04 | `POST /ask` | `AskService.ask` | `test_guardrail_no_context_*`, `test_ask_*` |
| RF-06 / CA-06 | `AskResponse.refused` | guardrail PII | `test_guardrail_blocks_personal_data_in_output` |
| RF-07 / CA-05, CA-07 | respostas 400/404/422/503 | handlers em `app.py` | `test_ask_when_llm_down_returns_503`, `test_error_bodies_match_error_schema` |
