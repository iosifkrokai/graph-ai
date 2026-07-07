---
name: add-node-type
description: Add a new workflow node type to Graph AI end-to-end (backend handler + registry + Postgres enum migration + frontend icon). Use when asked to add, create, or scaffold a new node (e.g. a transform, tool, or integration node) in the graph/workflow builder.
---

# Add a workflow node type

The app is built around a **single registration point**: a node type is one
`NodeDefinition` co-located with its handler in `backend/nodes/<type>.py`, added to
the `NODE_DEFINITIONS` tuple in `backend/nodes/registry.py`. From that tuple the
execution handler map, the `/nodes/catalog` UI metadata, and edge port-compatibility
are all auto-derived. The **frontend fetches the catalog at runtime**, so
`NodeType` on the frontend is just `type NodeType = string` — no union to extend;
the only required UI change is an icon.

**Template to copy: `backend/nodes/web_search.py`** (clean single-input/single-output
node). For a multi-field / `SELECT` / `JSON`-validator example see
`backend/nodes/http_request.py`; for branching outputs see `backend/nodes/condition.py`.

> Paths are relative to the repo root. Backend is **not** bind-mounted in Docker, so
> rebuild it to load a new node: `docker compose up -d --build backend worker`.
> The frontend **is** bind-mounted (Vite HMR) — icon changes hot-reload.

## Mandatory edits (text-in / text-out node reusing existing widgets)

1. **`backend/enums/node.py`** — add a member to `NodeType(StrEnum)`, e.g.
   `MY_NODE = auto()` (value = lowercase name, `"my_node"`).

2. **`backend/nodes/my_node.py`** — copy `web_search.py`. Three parts:
   - Handler class with `async def execute(self, context: NodeExecutionContext) ->
     NodeExecutionResult`. Read config from `context.node_data`, upstream text from
     `context.parent_values` (list) / `context.input_value`; optional streaming via
     `context.on_token`. Return `NodeExecutionResult(output=...)` (set
     `selected_handle=` only for branching nodes).
   - `def _build_handler(deps: NodeHandlerDeps) -> MyNodeHandler:` factory (`del deps`
     if unused; `deps.llm_provider_repository` is available).
   - `DEFINITION = NodeDefinition(type=NodeType.MY_NODE, label=..., icon_key="my_node",
     graph=NodeGraphSpec(has_input, has_output, input_port=PortType.TEXT,
     output_port=PortType.TEXT), fields=(NodeFieldSpec(...),...), build_handler=_build_handler)`.
     Convention: first field is always `"label"`. `icon_key` MUST match the frontend
     icon key (step 4).

3. **`backend/nodes/registry.py`** — two edits: add
   `from nodes.my_node import DEFINITION as MY_NODE_DEFINITION` and add
   `MY_NODE_DEFINITION,` to the `NODE_DEFINITIONS` tuple. (No dispatch `if/elif` —
   it's a dict lookup keyed by `NodeType`.)

4. **DB migration — REQUIRED, and autogenerate will NOT create it.** `NodeType` is
   persisted as a **Postgres enum** (`nodetype`), stored by member **name**
   (`MY_NODE` → label `MY_NODE`). Without this an insert fails with
   `invalid input value for enum nodetype: "MY_NODE"` (HTTP 500 on `POST /nodes`).
   Hand-write a migration in `backend/db/migrations/versions/` (revises the current
   head — `cd backend && POSTGRES_HOST=localhost uv run alembic heads`):
   ```python
   def upgrade() -> None:
       op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'MY_NODE'")
   def downgrade() -> None:  # PG enum values aren't safely removable
       pass
   ```
   Model this on `backend/db/migrations/versions/2b7e5f9a0d14_add_skipped_execution_status.py`.
   See the `db-migration` skill for applying it. (`ALTER TYPE ADD VALUE` cannot run
   inside a transaction that also uses the value — keep it its own migration.)

5. **`frontend/src/components/NodeIcons.tsx`** — add an exported `MyNodeIcon`
   (copy `WebSearchIcon`) and a branch in `NodeIcon`:
   `if (iconKey === 'my_node') { return <MyNodeIcon /> }`. Must match `icon_key`.
   Omitting it isn't fatal — the node falls back to `InputIcon`.

## Optional

- `backend/exceptions/node.py` (+ `exceptions/__init__.py`) — typed error (like
  `WebSearchConnectionError`); else reuse `ExecutionGraphValidationError`.
- `backend/nodes/__init__.py` — export the handler (registration doesn't need it).
- `frontend/src/components/WorkflowSidebar.tsx` — add the type string to a
  `NODE_CATEGORIES` group. If you skip it the node still shows, under an
  auto-generated **"Other"** group at the bottom of the palette.

## Only-if table (new capability, not just a new node)

| You need… | Also edit |
| --- | --- |
| New field **widget** | `backend/schemas/node.py::NodeFieldWidget` + `frontend/.../NodeFieldsForm.tsx` |
| New **validator** | `backend/enums/validator.py` + `backend/usecases/node.py::_validate_node_field` + `frontend/.../validation.ts` |
| New **datasource** (dynamic options) | `NodeFieldDataSourceKind` (schemas) + `usecases/node.py::_validate_external_references` + form |
| New **port type** | `backend/enums/node.py::PortType` + `frontend/.../lib/types.ts` + `frontend/.../OutputRenderer.tsx` |
| **Branching** outputs | set `output_handles` in `NodeGraphSpec`, return `selected_handle` (see `condition.py`) |

## Do NOT touch (auto-derived from the definition)

`backend/worker.py`, `backend/usecases/execution.py`, `backend/api/routers/node.py`,
and on the frontend the catalog hook, `CustomNodes.tsx`, `NodeFieldsForm.tsx`
(unless new widget), `CreateNodeDialog.tsx`, `lib/types.ts` (`NodeType` is `string`).

## Verify (this is how the pattern above was confirmed)

Rebuild + drive the real stack (needs it running — see the `run-graph-ai` skill):

```bash
docker compose up -d --build backend worker
# apply the enum migration:
cd backend && POSTGRES_HOST=localhost uv run alembic upgrade head && cd ..
# confirm it's in the catalog:
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"a@b.co","password":"pw12345678"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s http://localhost:5000/nodes/catalog -H "Authorization: Bearer $TOKEN" \
  | python3 -c 'import sys,json;print([n["type"] for n in json.load(sys.stdin)])'
```

Then build an `Input → <your node> → Output` workflow and run it (reuse the API flow
in `.claude/skills/run-graph-ai/smoke.mjs`) and assert the output. A throwaway
`uppercase` node built this way ran end-to-end and returned the input upper-cased —
which is exactly how the **enum-migration requirement** (step 4) was discovered:
without it, `POST /nodes` 500s.
