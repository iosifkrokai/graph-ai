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
4. **No global node-output size cap**, and per-attempt LLM streaming duplicates
   tokens to the client on retry.
5. **No frontend tests**, no undo/redo/multi-select, no React Query — all data
   fetching is hand-rolled `useState`/`useEffect`.
6. **Timezone-less datetime columns**, missing unique constraints on `edges`/
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

## Phase 3 — Richer graph & node types ✅ done

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
- [x] **Condition/Router node**: binary if/else branching (`NodeType.CONDITION`,
      `nodes/condition.py`) — evaluates `contains`/`equals`/`regex`/`not_empty`
      against upstream text and routes to a `true`/`false` output handle.
      Required real engine work: `NodeHandler.execute` now returns a
      `NodeExecutionResult(output, selected_handle)` instead of a bare string;
      edges carry an optional `source_handle` (new column + `NodeGraphSpec.
      output_handles`); the wave/serial schedulers propagate per-node
      liveness so only the taken branch executes — the other gets a
      `SKIPPED` `node_executions` row and is excluded from downstream
      `parent_values`, with a clear failure if no live path reaches OUTPUT.
      Frontend renders one named `Handle` per branch (`CustomNodes.tsx`) and
      threads `sourceHandle` through edge create/load
      (`useGraphState.ts`/`GraphCanvas.tsx`). `NodeFieldVisibility` gained a
      `not_equals` sibling to `equals` for the value field's visibility rule.
- [x] **Code/Transform node**: user-authored Python (`NodeType.CODE_TRANSFORM`,
      `nodes/code_transform.py`) run against `RestrictedPython`
      (`compile_restricted` + `safe_globals`/`safe_builtins` +
      `safer_getattr`/guarded getitem/getiter, plus a small extra-builtins
      allowlist including `json`) on a worker thread (`asyncio.to_thread`, so
      an infinite loop can't block the event loop — it does leak the thread,
      a known/documented limitation). Reads `input`, expects the script to
      assign `output`; non-string output is JSON-serialized. Syntax/runtime
      errors and a missing `output` assignment surface as
      `ExecutionGraphValidationError`.
- [x] **RAG / Vector search**: two node types, `Vector Ingest`
      (`nodes/vector_ingest.py`) and `Vector Search` (`nodes/vector_search.py`),
      backed by a new Qdrant service (`docker-compose.yml`) and local CPU
      embeddings via `fastembed` (`rag/embeddings.py`, no LLM provider needed).
      Ingest chunks the upstream text (fixed 800/100 char size/overlap,
      `rag/qdrant.py`), embeds, and upserts into a named collection
      (auto-created); Search embeds the upstream text as a query and returns
      the top-k matching chunks joined for downstream nodes (e.g. an LLM
      prompt). Collection names are free text, shared globally, no dedup on
      re-ingest — deliberately minimal for v1. **Known gap:** no way to feed
      a document in except pasting its text through an Input node (or
      fetching it via HTTP Request) — no file upload — tracked in Phase 6.

## Phase 4 — UX consolidation ✅ done

First pass:
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
- [x] **Unified `InspectorPanel.tsx`/`CreateNodeDialog.tsx` field rendering**
      into one shared `NodeFieldsForm.tsx`: the widget set
      (`TextField`/`NumberField`/`SelectField`/`ProviderField`/`ModelField`/
      `TelegramBotField`/...), the visibility filter, and the `updateField`
      clear-on-hide logic now live in one place. `NodeFieldsForm` also owns
      the `useLlmProviders`/`useProviderModels`/`useTelegramBots` hook calls,
      so `InspectorPanel`'s three hand-rolled `useEffect` fetches (manual
      `cancelled` flags) are gone — both surfaces get the same data-fetching
      path `CreateNodeDialog` already used correctly. Generalized the old
      provider-branch special case (`updateField('model', '')` called
      manually alongside the provider change) into a `datasource.depends_on`
      clear rule, so any field whose data source depends on the one just
      changed resets automatically. Each caller still owns its own
      persistence/error timing (`InspectorPanel` autosaves and shows errors
      live; `CreateNodeDialog` validates on submit) — only rendering was
      unified, not that behavior.

Second pass (closed out everything remaining):
- [x] **Migrated `CreateNodeDialog` onto the shared `Modal`** — it was a
      standalone `fixed inset-0` div with no Escape/click-outside handling;
      now wrapped in `Modal.tsx` so it behaves consistently with
      `SettingsModal` (Escape or click-outside calls `onCancel`).
- [x] Added `role="dialog"`, `aria-modal`, and a Tab/Shift+Tab focus trap to
      `Modal.tsx`, plus focus-on-open (first focusable element, or the panel
      itself) and focus-restore-on-close.
- [x] Confirmed destructive single-click deletes: node/edge delete
      (`NodeContextMenu.tsx`'s "Delete" now becomes an inline "Confirm
      delete"/"Cancel" pair), LLM provider and Telegram bot delete
      (`ProviderSettings.tsx`/`TelegramSettings.tsx`, same `confirmDeleteId`
      inline ✓/✕ pattern already used for workflow delete in
      `WorkflowSidebar.tsx`).
- [x] De-duplicated `ACTIVE_STATUSES` — now a single exported const in
      `lib/types.ts`, imported by `useExecutions.ts` and `ChatPanel.tsx`
      instead of each declaring its own copy.
- [x] Chat's live view now shows only the Output node's streamed tokens
      (`findOutputNodeId`/`liveOutputText` in `ChatPanel.tsx`, resolved from
      `nodeMetaByNodeId`) instead of concatenating every node's tokens into
      one blob; auto-scroll now only fires when the scroll container is
      already within 120px of the bottom, so it no longer yanks the viewport
      away from history the user scrolled up to read.
- [x] Surfaced run-validity (`runDisabledReason`) in Build mode too — a small
      "Can't run: ..." pill floats over the canvas (`GraphCanvas.tsx`) once a
      workflow is selected, instead of only learning about it after switching
      to History/Chat.
- [x] Normalized network-level fetch failures to `ApiError` in `lib/api.ts`'s
      `request()` — the `fetch()` call is now wrapped in a try/catch that
      turns a raw `TypeError` (dropped connection, DNS, CORS, offline) into
      the same `{ message, status }` shape as an HTTP error response
      (`status: 0` for "no response received"), so error handlers only ever
      see one shape.
- [x] Dismissible/auto-expiring error banner (`AppShell.tsx`) — a ✕ button
      clears it immediately (`onDismissError`), and it now also auto-clears
      after 8s if left untouched, instead of staying up permanently.
- [x] Fixed clearing a required number field silently saving as `0` —
      `NumberField` (`NodeFieldsForm.tsx`) now keeps an explicitly cleared
      field as `''` instead of coercing it via `Number('') === 0`, so the
      existing `requiredError` check in `validateFields` (which already
      special-cased non-number values) correctly flags it instead of
      silently accepting zero.
- [x] Warn when a node references a since-deleted LLM provider/model (or
      Telegram bot) — `NodeFieldsForm.tsx`'s `referenceWarning` checks a
      saved id/name against the loaded provider/model/bot list once fetching
      has settled (`useProviderModels` gained a `loading` flag to make this
      race-free) and shows "no longer exists"/"no longer available" instead
      of just a blank dropdown with the dead id silently retained.

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
- [ ] **Vector Ingest has no real document intake** — the only way to feed a
      document in today is pasting its full text through an Input node (or
      fetching it via HTTP Request); there's no file upload (PDF/docx/etc.),
      no way to browse/delete what's already in a Qdrant collection from the
      UI, and no dedup on re-ingest (re-running the same document appends
      duplicate chunks).

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
