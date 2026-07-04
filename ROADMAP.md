# Graph AI — Roadmap

Visual graph-based AI workflow builder (FastAPI + React + PostgreSQL). This document
tracks where the product is today and the prioritized plan to grow it — both new
capabilities and hardening of what already exists. There is no separate
breadth/depth split anymore: everything below is one prioritized list, verified
against the actual code as of this writing (not carried forward from stale notes).

## Where we are today

- **Backend** — layered `router → usecase → repository`, ARQ + Redis background
  execution, 8 entities (User, Workflow, Node, Edge, Execution, NodeExecution,
  LLMProvider, TelegramBot), JWT auth, encrypted secrets (Fernet), typed ports,
  workflow versioning, Telegram bot polling + reply integration.
- **Frontend** — React 19 + React Flow graph editor, catalog-driven node inspector
  and node-creation dialog, a unified Chat view (merged with what used to be a
  separate Executions history: per-turn version pill, timestamps, and a per-node
  "Details" expansion via a generic `OutputRenderer`), a single Settings modal
  (LLM Providers + Telegram Bots as tabs, on a shared `Modal` primitive).
- **Execution engine** (`backend/usecases/execution.py`) — 6 node types (`INPUT`,
  `LLM`, `WEB_SEARCH`, `TEMPLATE`, `HTTP_REQUEST`, `OUTPUT`), async execution with
  retries/backoff/reaper, wave-parallel scheduling, per-node result persistence
  (`node_executions`), SSE streaming with a polling fallback, workflow versioning
  with pinned reruns.
- **Integrations** — multi-provider LLM (Ollama/OpenAI/Anthropic/OpenAI-compatible)
  with token streaming; Telegram bots (per-user, encrypted token) that can trigger a
  workflow from an incoming message and receive the reply, including a manually
  pinned chat ID for non-Telegram-triggered runs.

## Key limitations driving priorities

1. **No rate limiting anywhere** — login/register are guessable/DoS-able.
2. **No CORS middleware** — the shipped SPA can't be served from a different origin
   without the usual unsafe `allow_origins=["*"]` workaround.
3. **Multi-step operations aren't atomic** — a crash between two commits (e.g.
   register's user+provider, or execution create-then-enqueue) leaves orphaned state
   that nothing reaps.
4. **Two independent field-rendering implementations on the frontend**
   (`InspectorPanel.tsx` and `CreateNodeDialog.tsx` each hand-roll the same
   `TextField`/`NumberField`/`ProviderField`/... set) — a new widget needs updating
   in two places, exactly the trap the `visible_when` mechanism was built to avoid
   for field *visibility*, but not yet solved for field *rendering*.
5. **No global node-output size cap**, and per-attempt LLM streaming duplicates
   tokens to the client on retry.
6. **Destructive actions are inconsistently confirmed** — workflow delete and account
   delete confirm inline; node/edge/provider/bot delete do not.
7. **No frontend tests**, no undo/redo/multi-select, no React Query — all data
   fetching is hand-rolled `useState`/`useEffect`.
8. **Timezone-less datetime columns**, missing unique constraints on `edges`/
   `llm_providers`, and pinned reruns can't record per-node results for nodes that
   were since deleted.

---

## Phase 0 — Hygiene & foundation ✅ done

- [x] Fail-fast when default JWT secret / Fernet key is used outside `local`/`test`
      (`settings/environment.py`, `settings/auth.py`, `settings/encryption.py`).
- [x] Catch non-`BaseError` in `create_execution`, roll back, mark `FAILED`.
- [x] Structured logging with execution-id context.
- [x] Migrations run + checked in CI (`alembic upgrade head` + `alembic check`).

## Phase 1 — Asynchronous execution ✅ done

- [x] ARQ + Redis background execution; `POST /executions` returns `202` immediately.
- [x] Per-node result table (`node_executions`) + `GET /executions/{id}/nodes`,
      now actually consumed by the frontend (Chat view's per-turn "Details").
- [x] Per-node retries with backoff (retryable errors only) + per-node timeout.
- [x] Idempotent enqueue (`_job_id="execution:{id}"`); stuck-execution reaper cron.
- [x] Wave-parallel scheduling for independent branches, isolated sessions.
- [x] SSE streaming (`GET /executions/{id}/stream`) with a client-side polling
      fallback when the stream ends early or is unsupported.

## Phase 2 — Multi-provider LLM + secrets ✅ done

- [x] Fernet-encrypted, write-only `LLMProvider.api_key`; never returned in responses.
- [x] OpenAI / Anthropic / OpenAI-compatible clients alongside Ollama.
- [x] Per-node generation params (`temperature`, `max_tokens`, `top_p`), opt-in via
      the `optional_number` widget.
- [x] Token streaming provider → worker (Redis pub/sub) → SSE → frontend
      (`useExecutions.liveTokens`).

## Phase 3 — Richer graph & node types ✅ done (core), 🟡 extension in progress

- [x] Typed ports (`PortType` = text/json/file/list) with edge-level compatibility
      checks (`ports_compatible`, currently exact-match only — the intended
      extension point for a future coercion table).
- [x] Prompt/Template and HTTP Request nodes; plugin-based node registration
      (`NodeDefinition` + `nodes/registry.py` — one module + one list entry per node).
- [x] Workflow versioning: each run snapshots the live graph
      (`workflow_versions`), pinned via `executions.version_id`, rerunnable by
      `version_id`. **Known gap:** a pinned rerun whose nodes were *deleted* (not
      edited) still can't record `node_executions` rows — `node_id` is a hard FK to
      the live `nodes` table (see Data layer, below).
- [x] **Telegram bot integration** (new since the last roadmap pass): per-user
      `TelegramBot` entity (encrypted token), Input node polls a bot for incoming
      messages via an ARQ cron (`poll_telegram_updates`, every 10s), Output node
      replies via the bot after execution finishes, with an optional pinned
      `telegram_chat_id` for manual (non-Telegram-triggered) runs. Field
      visibility (`visible_when`) is fully declarative — adding a future format
      doesn't require new frontend branches.
- [ ] Condition/Router, Code/Transform, RAG/Vector search, Loop/Map — deferred,
      need dedicated engine work (branch selection, sandboxing, vector DB).

## Phase 4 — UX consolidation ✅ done (first pass), items below still open

Done this pass:
- [x] Merged the standalone Executions history modal into Chat mode — one place
      to browse + interact with runs, with per-turn version/timestamp/duration and
      a per-node result breakdown (`ChatPanel.tsx`, `OutputRenderer.tsx`).
- [x] Consolidated Providers + Telegram Bots into one Settings modal
      (`SettingsModal.tsx`, vertical tabs) on a shared `Modal` primitive
      (`Modal.tsx`), replacing three separate header buttons and three
      hand-rolled modal shells.
- [x] Forward-compatible output rendering: `OutputRenderer` dispatches on
      `PortType`, degrading gracefully to plain text for `file`/`list` until a
      real node type produces them.

Still open:
- [ ] **Unify `InspectorPanel.tsx` and `CreateNodeDialog.tsx` field rendering.**
      Both independently define the same `TextField`/`NumberField`/`SelectField`/
      `ProviderField`/`ModelField`/`TelegramBotField` set and the same
      `updateField` clear-on-hide logic. Extract one shared field-renderer
      component/hook so a new widget type is added once, not twice.
- [ ] **`InspectorPanel` should use the existing `useLlmProviders`/
      `useProviderModels`/`useTelegramBots` hooks** instead of its own three
      hand-rolled `useEffect` fetches with manual `cancelled` flags —
      `CreateNodeDialog` already does this correctly; make `InspectorPanel` match.
- [ ] **Migrate `CreateNodeDialog` onto the shared `Modal`** (Escape + click-outside
      + eventual focus-trap) — it's still a standalone `fixed inset-0` div, so
      Escape/click-outside behave inconsistently between it and `SettingsModal`.
- [ ] Add `role="dialog"`, `aria-modal`, and a focus trap to `Modal.tsx`.
- [ ] Confirm destructive single-click deletes: node, edge, LLM provider, Telegram
      bot (workflow and account delete already confirm inline — reuse that pattern).
- [ ] De-duplicate `ACTIVE_STATUSES` (`useExecutions.ts` and `ChatPanel.tsx` each
      declare it separately).
- [ ] Chat's live view still concatenates *every* node's streamed tokens into one
      blob (`joinLiveTokens`) instead of streaming only the Output node's tokens;
      auto-scroll fires on every token with no near-bottom check, so it can yank
      the viewport during a long stream.
- [ ] Surface run-validity (`runDisabledReason`) in Build mode too, not just Chat —
      right now you only learn a graph can't run by switching tabs.
- [ ] Normalize network-level fetch failures (not just HTTP error responses) to
      `ApiError` in `lib/api.ts`'s `request()` — a dropped connection currently
      throws a raw `TypeError` that error handlers don't expect.
- [ ] Dismissible/auto-expiring error banner (today: one global, permanent,
      non-dismissible banner for any error).
- [ ] Clearing a required number field silently saves as `0` (`Number('') === 0`)
      and passes validation — `NumberInput`/`validateFields` should treat an empty
      required numeric field as invalid, not `0`.
- [ ] Warn (or block) when a node references a since-deleted LLM provider/model —
      today the dropdown just shows a blank placeholder while the dead id is
      silently retained in the node's saved config.

## Phase 5 — Security & data hardening (none of this started)

- [ ] **Rate limiting** on `/auth/login` and `/auth/register` (Redis token bucket —
      Redis is already a dependency).
- [ ] **CORS middleware** with an explicit origin allowlist from settings.
- [ ] **Password length bounds** on `UserCreate.password` (bcrypt silently
      truncates past 72 bytes today).
- [ ] **Registration doesn't leak account existence** — currently a 409 on
      duplicate email; login is already safely generic.
- [ ] **JWT hardening** — add `iat`/`jti` now (cheap, forward-compatible), then a
      refresh token + revocation list; currently a single 30-minute token with no
      way to log out server-side.
- [ ] **Unit-of-work commits.** Every repository write commits individually
      (`db/repositories/base.py`); `register` commits the user then the default
      provider as two separate operations, and `create_execution` commits then
      enqueues — a crash between steps leaves orphaned state (a providerless user;
      a `CREATED` execution the reaper never reaps, since it only scans `RUNNING`).
      Fix: flush-not-commit repos + one commit per usecase, and have the reaper
      also consider stale `CREATED` rows.
- [ ] **Timezone-aware datetime columns** (`DateTime(timezone=True)` everywhere) —
      correctness today depends on the DB session timezone being UTC.
- [ ] **Missing unique constraints** — `edges(workflow_id, source_node_id,
      target_node_id)` and `llm_providers(user_id, name)` allow silent duplicates.
- [ ] **Decouple `node_executions` from live `nodes`** so a pinned rerun of a
      version whose nodes were since *deleted* (not edited) can still record
      per-node results — either denormalize node identity or key on
      `(version_id, snapshot_node_id)`.
- [ ] **`BaseError` execution-failure path doesn't roll back the session** before
      marking `FAILED`, unlike the generic-`Exception` branch beside it — a
      poisoned transaction can make the failure-status commit itself throw.
- [ ] **No global node-output size cap** — only the HTTP node truncates (10k
      chars, silently, no marker); LLM/web_search/template/output write unbounded
      text into `node_executions.output`.
- [ ] **Parallel wave partial-failure surfaces one arbitrary error** and writes no
      rows for nodes that were never reached — aggregate wave errors, write
      `SKIPPED` rows so the UI can distinguish "failed" from "never ran".
- [ ] **LLM streaming retries duplicate tokens to the client** — a retried attempt
      re-streams from scratch through the same token sink with no "attempt reset"
      marker.
- [ ] **Stuck-execution timeout is absolute start-age, not heartbeat-based** — a
      legitimately long multi-node run can be reaped as if it were actually stuck.
- [ ] **Readiness probe never checks Redis and always returns 200** regardless of
      dependency health — executions can't even enqueue without Redis.
- [ ] **No length/size bounds** on `WorkflowCreate.name`, `ExecutionInputPayload.value`,
      `LLMProviderCreate.name`/`config`, `UserCreate.password`.
- [ ] **Untyped node fields skip validation entirely** — fields declared with
      `validators={}` (LLM `system_prompt`, HTTP `headers`/`body`) get no type
      check at save time, failing only at run time.
- [ ] **Streaming pins a pooled DB connection for the whole SSE lifetime** — open/
      close a short-lived session per poll iteration instead of holding the
      request-scoped one.

## Phase 6 — Node handler depth (usability, not new node types)

- [ ] **"Web Search" isn't a real web search** — it only reads DuckDuckGo's
      Instant Answer API (`AbstractText`/`RelatedTopics`), which is empty for most
      real queries. Use the HTML/lite results endpoint or make the provider
      configurable.
- [ ] **HTTP node: unencoded `{{input}}` URL substitution** breaks any value with
      spaces/`&`/`#`; response truncation at 10k chars has no marker and ignores
      content-type. URL-encode on substitution, add a truncation marker, allow
      `{{input}}` in headers.
- [ ] **Template node: single exact-match `{{input}}`** — `{{ input }}` or
      `{{INPUT}}` silently drops the entire upstream text with no error, and
      there's no way to reference an individual parent by index.

## Phase 7 — Product breadth (parallel track)

- [ ] Undo/redo, copy-paste, multi-select, auto-layout in the graph editor.
- [ ] React Query in place of hand-rolled `useState`/`useEffect` data fetching.
- [ ] Workflow template library, JSON export/import, duplication.
- [ ] Frontend tests (Vitest + Testing Library) — currently zero.
- [ ] Multi-tenant quotas, audit log, cost observability (tokens/latency per run).
- [ ] Metrics (Prometheus) + error tracking (Sentry).

---

### North star

From a synchronous, single-user Ollama editor → an asynchronous, multi-provider,
multi-channel (chat + Telegram) orchestration platform with typed data, streaming,
and production-grade hardening — where the UI stays declarative and scales to new
node types and integrations without per-feature frontend rewrites.
