---
name: run-graph-ai
description: Build, launch, and drive the Graph AI full-stack app (FastAPI backend + React/Vite frontend + Postgres/Redis/Qdrant/Ollama). Use to run, start, boot, smoke-test, or screenshot the app and verify a change works in the real running stack (auth screen → workflow builder), not just in tests.
---

# Run Graph AI

Graph AI is a visual graph-based AI workflow builder: a **React/Vite SPA** (`:3000`)
that proxies `/api` to a **FastAPI backend** (`:5000`), backed by Postgres, Redis,
Qdrant, and (for LLM execution) Ollama + an ARQ worker. The whole stack runs via
**docker compose** from the repo root.

The interactive surface is the browser. Drive it headlessly with the committed
Playwright driver: **`.claude/skills/run-graph-ai/driver.mjs`**. It registers a
user through the real UI, lands on the workflow builder, creates a workflow, and
writes screenshots to `.claude/skills/run-graph-ai/shots/`.

> All paths below are relative to the **repo root** (`<unit>/`).

## Prerequisites

Already present in this container: Docker + Compose v2, Node 24, Python 3.12.
The browser driver needs Chromium and its system libs (one-time):

```bash
cd .claude/skills/run-graph-ai
npm install                                  # installs playwright into the skill dir (~18M)
npx playwright install chromium              # downloads the Chromium headless shell
sudo npx playwright install-deps chromium    # installs libatk/libnss/etc — REQUIRED, or Chromium won't launch
cd -
```

## Build & launch the stack (agent path)

`make run` (= `docker compose up --build`) boots **all** services including an
Ollama container that pulls a ~1GB model — slow, and nothing in the core app
depends on it being healthy. For a fast bring-up, build only the core services;
add `ollama worker` later only when you need to actually execute an LLM node.

```bash
cp .env.example .env                                             # compose reads .env
docker compose up -d --build postgres redis qdrant backend frontend
```

Wait until both tiers answer (backend runs Alembic migrations on start, so give it a moment):

```bash
for i in $(seq 1 60); do
  curl -sf http://localhost:5000/health/readiness >/dev/null \
    && curl -sf http://localhost:3000 >/dev/null && { echo "ready"; break; }
  sleep 1
done
curl -s http://localhost:5000/health/readiness   # {"services":[postgres,redis,qdrant all true],"status":true}
```

| Service  | URL                          |
| -------- | ---------------------------- |
| Frontend | http://localhost:3000        |
| Swagger  | http://localhost:5000/docs   |

## Drive it & screenshot (agent path)

```bash
cd .claude/skills/run-graph-ai
node driver.mjs                    # register → builder → create workflow; screenshots to ./shots/
```

Expected output ends with `✓ driver flow complete` and three PNGs in `shots/`:
`01-auth.png` (Pixel Flow Studio login), `02-builder.png`, `03-workflow.png`
(canvas with the created "Demo Flow" and the node catalog). **Open the PNGs** —
a blank page or `error.png` means a step failed.

Useful flags / env:

```bash
node driver.mjs --email you@graph.ai --password secret123   # explicit creds
BASE=http://localhost:3000 node driver.mjs                  # override target URL
```

## Direct invocation (backend, no browser)

Most backend PRs can be verified with `curl` against `:5000` — the driver isn't
needed. Auth is `/auth/register` then `/auth/login` (Bearer token):

```bash
curl -s -X POST http://localhost:5000/auth/register \
  -H 'Content-Type: application/json' -d '{"email":"a@b.co","password":"pw12345678"}'
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login \
  -H 'Content-Type: application/json' -d '{"email":"a@b.co","password":"pw12345678"}' \
  | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
curl -s http://localhost:5000/workflows -H "Authorization: Bearer $TOKEN"   # [] for a fresh user
```

Full API surface: http://localhost:5000/docs.

## Tests

Frontend — run inside the running container (deps already installed there):

```bash
docker compose exec -T frontend npm run lint    # eslint, clean
docker compose exec -T frontend npx tsc -b       # typecheck, exit 0
```

Backend — `make back-test` uses `uv` + testcontainers (spins up its own Postgres via
the Docker daemon). Install `uv` first if missing (`pip install uv`), then:

```bash
cd backend && uv sync && uv run pytest tests/ -q   # what `make back-test` runs → 200 passed (~1m45s)
```

## Run (human path)

`make run` boots the entire stack (incl. Ollama model pull + worker) in the
foreground; Ctrl-C stops it. Useless headless beyond confirming it boots — use
the driver above to actually see/verify the UI.

## Gotchas

- **`.claude/settings.json` is the only git-ignored path under `.claude/`** (not
  the whole dir) — this skill and its `driver.mjs` are tracked. `node_modules/`
  and `shots/` are ignored via the skill-local `.gitignore`.
- **Nothing depends on Ollama being healthy.** The backend `depends_on` is only
  postgres/redis/qdrant, so the core stack comes up without waiting for the model
  pull. Ollama + the `worker` service are only needed to actually *run* an LLM node.
- **The logged-in email is not in the top bar** — it lives inside the (closed)
  "Profile" dropdown. The driver waits on the top-bar **"Settings"** button as the
  post-auth signal, not the email text.
- **Register auto-logs-in.** `handleRegister` calls `handleLogin` on success
  (`frontend/src/hooks/useAuthSession.ts`), so there's no separate login step.
- **Create a workflow** by filling the sidebar's "New workflow" input and clicking
  **"Add"** (not a "+" button). The canvas shows "workflow must contain exactly one
  input node" until you add Input/Output nodes.
- **Frontend proxies `/api` → `backend:5000`** over the compose network
  (`vite.config.ts`). Drive the browser at `:3000`; it reaches the backend itself.
- Vite runs in dev mode with HMR and bind-mounts `frontend/src`, so frontend edits
  hot-reload without a rebuild. Backend is **not** mounted — rebuild its image to
  pick up Python changes.

## Troubleshooting

- **`error while loading shared libraries: libatk-1.0.so.0`** when running the
  driver → you skipped `sudo npx playwright install-deps chromium`. Run it.
- **Driver times out waiting for the builder** → registration failed (e.g. email
  already taken). The driver defaults to a per-run unique email (`demo+<pid>@graph.ai`);
  check `shots/error.png`. Pass a fresh `--email` if needed.
- **`readiness` returns 503 / a service `false`** → that dependency isn't up yet;
  `docker compose ps` and re-check. Backend logs: `docker compose logs backend`.
- **Port already allocated** → an old stack is running: `docker compose down` first.
