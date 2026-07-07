---
name: db-migration
description: Create and apply Alembic database migrations for the Graph AI backend (autogenerate a revision, add a Postgres enum value, upgrade/downgrade). Use when a SQLAlchemy model changes, a new model or table is added, or a new enum value is needed and the DB schema must follow.
---

# DB migrations (Alembic)

Backend uses SQLAlchemy + Alembic against Postgres. Migrations live in
`backend/db/migrations/versions/`; the DB URL is injected at runtime in
`backend/db/migrations/env.py:18` from `backend/settings/postgres.py`
(`target_metadata = Base.metadata`, imported from `backend/db/models`). Migrations are
applied automatically on container boot (`backend/entrypoint.sh` runs
`alembic upgrade head`).

> All commands run from `backend/`. `uv` must be installed (`pip install uv` +
> `uv sync`) — the Makefile target calls bare `alembic`, but `uv run alembic` is the
> reliable form.

## Preconditions (all required, or autogenerate misbehaves)

1. **Postgres reachable at `localhost:5432`.** In Docker the host is the compose
   service name `postgres`; from your shell you must use `localhost`. Start it:
   `docker compose up -d postgres` (from repo root).
2. **DB already at `head`** — else the new revision diffs against a stale schema and
   includes everything unapplied: `POSTGRES_HOST=localhost uv run alembic upgrade head`.
3. **Any new model is exported in `backend/db/models/__init__.py`** — autogenerate
   only sees models imported into `Base.metadata`. A new table not exported there is
   silently missed.

## Generate a revision

Makefile wrapper (handles the `.env` dance automatically):

```bash
# from repo root — backs up .env, copies .env.example, rewrites POSTGRES_HOST=localhost,
# runs autogenerate, then restores your .env via an EXIT trap (see Makefile:21)
MSG="add_widget_table" make back-migrate
```

Non-clobbering manual equivalent (does not touch your `.env`):

```bash
cd backend && POSTGRES_HOST=localhost uv run alembic revision --autogenerate -m "add_widget_table"
```

Head / current for setting `down_revision` or checking state:

```bash
POSTGRES_HOST=localhost uv run alembic heads      # e.g. 8f3a5d1c7b92 (head)
POSTGRES_HOST=localhost uv run alembic current
```

## ALWAYS review the generated file — autogenerate is noisy

Verified: running autogenerate with **no model changes at all** still emitted a
spurious `op.alter_column('node_executions', 'node_id', ...)` (a column
comment/type nuance). Autogenerate also mis-handles enum edits, `server_default`
changes, and comment-only diffs. **Open the new file in
`db/migrations/versions/` and delete every op you didn't intend** before keeping it.

## Enum values — autogenerate CANNOT do these (hand-write them)

`NodeType`, `LLMProviderType`, `ExecutionStatus` are native Postgres enums storing
member **names**. Adding a value needs a hand-written migration — autogenerate emits
nothing for it, and inserting the new value 500s (`invalid input value for enum ...`)
until applied:

```python
def upgrade() -> None:
    op.execute("ALTER TYPE nodetype ADD VALUE IF NOT EXISTS 'MY_VALUE'")

def downgrade() -> None:
    # PostgreSQL enum values are not safely removable in-place.
    pass
```

Template: `db/migrations/versions/2b7e5f9a0d14_add_skipped_execution_status.py`.
Keep `ALTER TYPE ... ADD VALUE` in its own migration (it can't run in the same
transaction that then uses the value).

## Apply / roll back

```bash
POSTGRES_HOST=localhost uv run alembic upgrade head          # apply
POSTGRES_HOST=localhost uv run alembic downgrade <revision>  # roll back to a revision
```

In the normal Docker flow you don't apply manually — the backend container runs
`alembic upgrade head` on boot, so `docker compose up -d --build backend` applies
pending migrations.

## Gotchas (verified)

- **`localhost`, not `postgres`.** Without the host rewrite, autogenerate hangs/fails
  to connect from your shell.
- **`make back-migrate` overwrites `.env` with `.env.example`** for the duration of
  the run (restored on exit via trap). If you have local secrets in `.env`, they're
  swapped out only transiently — but if `.env` didn't exist at all, the trap restores
  an empty one.
- **DB not at head → bloated diff.** Always `upgrade head` first.
- The migration `env.py` runs in **online** mode (real async engine connect), so a
  live DB is mandatory even just to autogenerate.

## Verify

The flow above was exercised end-to-end: created a real enum-add migration
(`ALTER TYPE nodetype ADD VALUE 'UPPERCASE'`), `alembic upgrade head` applied it
(confirmed the label appeared in `pg_enum`), `alembic downgrade` rolled the version
back, and a no-op autogenerate produced the spurious `node_executions.node_id` diff
noted above (then deleted).
