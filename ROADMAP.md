# Graph AI — Roadmap

Visual graph-based AI workflow builder (FastAPI + React + PostgreSQL).
This document tracks where the product is today and the sequenced plan to grow it
into an async, multi-provider orchestration platform.

## Where we are today

- **Backend** — layered `router → usecase → repository`, 6 entities (User, Workflow,
  Node, Edge, Execution, LLMProvider), JWT auth, ~34 API tests on testcontainers.
- **Frontend** — React 19 + React Flow graph editor, catalog-driven node inspector,
  4 node types, pixel-art theme.
- **Execution engine** (`backend/usecases/execution.py`) — 4 node types
  (`INPUT`, `LLM`, `WEB_SEARCH`, `OUTPUT`), correct graph validation
  (single input/output, acyclic via Kahn, connectivity via DFS).

## Key limitations driving priorities

1. Execution is **fully synchronous, inside the HTTP request** — no queue/worker;
   the client never observes `RUNNING`; long LLM calls block the worker.
2. **Ollama only** — no cloud providers.
3. **No secret storage** — `utils/crypto.py` is bcrypt-for-passwords only; the
   provider has no `api_key` field, and `config` (JSONB) is returned to the client.
4. **Intermediate node outputs are not persisted** — only the final output is stored;
   on mid-graph failure only a free-text `error` survives.
5. **No retries / backoff / stuck-execution reaper** — a non-domain exception can
   strand an execution in `RUNNING` forever.
6. **No observability** — no logging, metrics, error tracking, or rate limiting.
7. **Data is strictly `str`, format only `txt`** — no typed ports, files, or multimodality.
8. **No frontend tests**; plain `useState` state, no undo/redo, copy-paste, or auto-layout.
9. **No streaming** — Ollama is called with `stream: False`.

---

## Phase 0 — Hygiene & foundation ✅ done

Cheap changes that de-risk everything else.

- [x] Fail-fast when the default JWT secret is used in production (`settings/auth.py`,
      gated by `ENVIRONMENT`).
- [x] Catch non-`BaseError` in `create_execution`, roll back, and mark `FAILED` so an
      execution can no longer strand in `RUNNING` (`usecases/execution.py`).
- [x] Structured logging with execution-id context (`logging_config.py`, wired in `main.py`).
- [x] Refresh `backend/AGENTS.md` (removed Prefect, `flows/`, `integrations/`, `models/`).
- [x] Run Alembic migrations in CI: `alembic upgrade head` + `alembic check` catches
      model↔migration drift (`.github/workflows/backend.yml`).
- [x] LLM node happy-path test with mocked Ollama chat (`tests/test_api/test_execution.py`).

## Phase 1 — Asynchronous execution (main architectural shift, 3–5 weeks)

Unblocks streaming, long pipelines, and scale.

- [ ] Move execution off the request path: task queue (ARQ/Celery/Dramatiq on Redis) + worker.
      API returns `RUNNING` immediately.
- [x] Per-node result table (`node_executions`: status, output, timings, error) with
      per-node persistence in the runner and a `GET /executions/{id}/nodes` endpoint —
      pinpointed failures and the foundation for resumability + per-node UI status.
- [ ] Per-node retries with backoff and timeouts; idempotency.
- [ ] Reaper for executions stuck in `RUNNING` (e.g. worker/process crash mid-run) —
      belongs here rather than Phase 0, since only async execution can strand a run.
- [ ] Parallelize independent branches (today the topological order runs strictly serially).
- [ ] Frontend: move from 5s polling to SSE/WebSocket with per-node status.

## Phase 2 — Multi-provider LLM + secrets (2–4 weeks)

- [ ] Real key encryption (Fernet/KMS) + `LLMProvider.api_key` migration; stop returning `config`.
- [ ] OpenAI / Anthropic / OpenAI-compatible clients (the `BaseLLMClient` protocol is ready;
      needs an enum value + factory branch in `llm/__init__.py`).
- [ ] Generation params per node: `temperature`, `max_tokens`, `top_p`.
- [ ] Token streaming from provider through to the UI.

## Phase 3 — Richer graph & node types (4–6 weeks)

- [ ] Typed ports (text / json / file / list) instead of `str`-only; edge type-compat validation.
- [ ] New nodes: Prompt/Template, Condition/Router, Code/Transform, HTTP Request, RAG/Vector search, Loop/Map.
- [ ] Plugin-based node registration (today manual in 3 places: enum, `registry.py`, `catalog.py`).
- [ ] Workflow versioning + run a specific version (today edits mutate the live graph).

## Phase 4 — Product UX (parallel, 3–5 weeks)

- [ ] Undo/redo, copy-paste, multi-select, auto-layout in the editor.
- [ ] Execution panel: active/failed node highlighting, per-node inline output, live log.
- [ ] React Query in place of hand-rolled `useState`/`useEffect` (cache, invalidation, optimistic updates).
- [ ] Workflow template library, JSON export/import, duplication.
- [ ] Frontend tests (Vitest + Testing Library) — currently zero.

## Phase 5 — Production readiness (cross-cutting)

- [ ] Auth: refresh tokens (today a single 30-min access token), login rate limiting,
      optional roles, logout/revocation.
- [ ] Observability: metrics (Prometheus), error tracking (Sentry), readiness that also
      checks Ollama/providers.
- [ ] Multi-tenant quotas, audit log, CORS middleware (absent in `main.py`).
- [ ] Cost observability — tokens/latency per execution.

---

### Quick wins this week

Default `secret_key` fail-fast · catch all exceptions in execution · logging ·
migrations in CI · LLM node test · fix `AGENTS.md`.

### North star

From a synchronous, single-user Ollama editor → an **asynchronous, multi-provider
orchestration platform** with typed data, streaming, and observability.
