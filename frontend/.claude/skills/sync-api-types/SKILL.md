---
name: sync-api-types
description: Regenerate TypeScript types from the backend OpenAPI schema and check the hand-written frontend API types for drift. Use when a backend schema (backend/schemas/*.py) changes, when adding/altering an API request or response, or to audit frontend/src/lib/types.ts against the live contract.
---

# Sync frontend API types with the backend

`frontend/src/lib/types.ts` and `frontend/src/lib/api.ts` are **100% hand-written**.
`api.ts` casts raw JSON with `as T` (no runtime validation), so a backend/frontend
shape mismatch fails **silently at runtime**, not at compile time. There is no
codegen in the build — this skill adds an on-demand generator to catch drift.

Backend field naming is plain snake_case (no aliases), so generated types line up
1:1 with today's hand-written field names — adoption is low-friction.

## Regenerate (backend must be running on :5000)

```bash
cd frontend
npm install                 # ensures openapi-typescript (devDependency) is present
npm run gen:api-types       # openapi-typescript http://localhost:5000/openapi.json -o src/lib/api-types.gen.ts
```

`src/lib/api-types.gen.ts` is **git-ignored and regenerate-on-demand** — it is the
source-of-truth reference, NOT imported by the app. `types.ts` stays the type the app
uses; the generated file is the yardstick you diff against. (Start the backend via the
`run-graph-ai` skill if it isn't up.)

## Check for drift

Compare each `components["schemas"]["XxxResponse"]` in the generated file to its
hand-written counterpart in `types.ts`. The names don't match mechanically — use this
map:

| Backend schema (generated) | Hand-written (`types.ts`) |
| --- | --- |
| `*Response` | bare name (`WorkflowResponse`→`Workflow`, `LLMProviderResponse`→`LlmProvider`) |
| `*Create` | `*Payload` (`NodeCreate`→`NodeCreatePayload`) |
| `NodeExecutionResponse` | `NodeExecutionResult` |
| `ExecutionInputPayload` | `RunInputPayload` |

**Proven drift (why this skill exists):** `types.ts` declares
`prefect_flow_run_id: string | null` on the `Execution` interface, but the generated
`ExecutionResponse` has no such field (0 occurrences) — a dead field nothing flagged.
The generator also **tightens enums**: generated `NodeType` is
`"input" | "llm" | "web_search" | ...`, while `types.ts` has `type NodeType = string`
(invalid values wouldn't be caught). Adopting the generated unions is a real fix.

## Carve-outs — NOT derivable from OpenAPI (keep hand-maintained)

- **SSE stream events** — `TokenStreamEvent`, `TokenResetStreamEvent`,
  `StatusStreamEvent`, `ExpiredStreamEvent` in `types.ts` have no Pydantic schema; the
  backend hand-serializes them as raw dicts in `backend/usecases/execution.py`
  (`json.dumps({"type": "token", ...})`). They never appear in `/openapi.json`.
- **Loosely-typed enum fields** you may deliberately keep as `string`
  (`NodeType`, `LlmProvider.type`, `ExecutionStatus`) — the generator will propose
  unions; adopt or ignore per case.

## Workflow when a backend schema changes

1. Rebuild/restart backend so `/openapi.json` is current.
2. `npm run gen:api-types`.
3. Diff the affected `components["schemas"]` entry vs its `types.ts` counterpart (use
   the name map). Update `types.ts` (and any consuming hook/component) by hand.
4. `docker compose exec -T frontend npx tsc -b` (or `npm run build`) to confirm.

## Verify (done when authoring this skill)

`npm install` added `openapi-typescript@^7`; `npm run gen:api-types` generated
`src/lib/api-types.gen.ts` from the live schema; the diff surfaced the stale
`prefect_flow_run_id`; `tsc -b` still passes with the generated file present.
