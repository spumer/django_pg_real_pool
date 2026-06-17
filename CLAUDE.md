# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`django-pg-real-pool` is a Django PostgreSQL database backend that returns a pooled connection to
the pool **As Soon As Possible** — right after each query outside of an `atomic()` block, instead
of holding it for the whole request/context. Extracted from the `tochka/npd` project to be
published on PyPI.

## Commands

Tooling is **uv** (not Poetry, despite reference projects). A PostgreSQL server is required for the
test suite.

```bash
uv sync                              # create .venv and install dev deps (PEP 735 'dev' group)
docker compose up -d                 # PostgreSQL on host port 5433 (5432 is often taken)

# Tests target ONE backend per run, selected by env var (default: native):
PGPORT=5433 uv run pytest
DJANGO_PG_REAL_POOL_BACKEND=dj_db_conn_pool PGPORT=5433 uv run pytest

# A single test:
PGPORT=5433 uv run pytest tests/test_django_pg_real_pool.py::test_atomic__release_after_commit

uv run ruff check src tests examples     # lint
uv run ruff format src tests examples    # format
uv run mypy src                          # type-check (src only)

# Full Python × Django × backend matrix (needs PostgreSQL):
PGPORT=5433 uv run tox
PGPORT=5433 uv run tox -e py313-dj60-native      # a single matrix cell

uv build                                  # build sdist + wheel
uv run --group docs mkdocs build -f docs/mkdocs.yml --strict   # build docs site
```

## Architecture

The package is deliberately tiny; the value is *when* the connection is released, not how much
code there is.

- **`_release.py` — the only real logic.** `ConnectionReleaseMixin` overrides `_cursor`,
  `commit`, and `rollback`. Outside a transaction it wraps the cursor in
  `AutoConnectionReleaseCursor`, which calls `DatabaseWrapper.close()` when the cursor closes;
  inside `atomic()` it holds the connection until the block ends. The mixin **never talks to a
  specific pool** — it relies only on `close()` returning the connection to the pool, which both
  supported backends do. This is why the same mixin (and the same test suite) works on both.
- **Two engines, both = `ConnectionReleaseMixin` + a pooled `DatabaseWrapper`:**
  - `native/base.py` → on top of Django's built-in psycopg pool. This is the **default** engine
    (`ENGINE = 'django_pg_real_pool'`, re-exported by `base.py`). Requires Django ≥ 5.1, psycopg 3,
    `OPTIONS={'pool': ...}`, and `CONN_MAX_AGE = 0`.
  - `dj_db_conn_pool/base.py` → on top of the third-party `django-db-connection-pool`
    (SQLAlchemy `QueuePool`). **Optional** (`ENGINE = 'django_pg_real_pool.dj_db_conn_pool'`,
    install the `dj-db-conn-pool` extra). The `from dj_db_conn_pool...` import resolves to the
    *external* package, not this sub-package (Python 3 absolute imports).
- `native/base.py` adds a **fail-fast guard**: using the native engine without `OPTIONS['pool']`
  raises `ImproperlyConfigured` (except for `NO_DB_ALIAS`, which must keep working for test-DB
  creation).

The `ConnectionReleaseMixin` uses a `TYPE_CHECKING`-only base (`django...postgresql...DatabaseWrapper`)
so type checkers resolve `self.connection`/`self.close()` etc.; at runtime the base is `object`, so
the real MRO is `DatabaseWrapper(ConnectionReleaseMixin, <pooled DatabaseWrapper>)`.

## Conventions & gotchas

- **`tests/` is a directory, not a package** — no `__init__.py`. The settings module is plain
  `settings` (via `pythonpath = ["src", "tests"]`), not `tests.settings`. Do **not** add
  `from tests... import`; tests get shared code through pytest fixtures (`conftest.py`) or
  module-level helpers in the test file.
- **One backend per test run**, chosen by `DJANGO_PG_REAL_POOL_BACKEND` (`native` |
  `dj_db_conn_pool`). The tox matrix and CI run the suite once per backend. Tests use a
  **single-connection pool on purpose** so "acquired" vs "released" is directly observable via the
  pool's idle count (`get_pool_size` duck-types `get_stats()` vs `checkedin()`).
- **Quote style is single** (`ruff format` + `flake8-quotes` both set to single). Don't let an
  editor flip everything to double quotes.
- **`psycopg[pool]` is a hard dependency** (not an extra) because the native engine is the default
  and must work on a bare `pip install`.
- **`uv_build>=0.11,<0.12` pin is intentional** (uv's own guidance for the pre-1.0 backend) — do
  not widen it.
- Supported matrix: Python 3.10–3.14 × Django 5.1 / 5.2 LTS / 6.0, both backends; only valid
  Python×Django pairs (Django 6.0 needs Python ≥ 3.12; Django 5.1 supports up to 3.13).
