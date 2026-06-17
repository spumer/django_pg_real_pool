# Compatibility

## Supported versions

| | Versions |
|---|---|
| Python | 3.10, 3.11, 3.12, 3.13, 3.14 |
| Django | 5.1, 5.2 LTS, 6.0 |
| PostgreSQL | any supported by your Django / psycopg |
| Driver | psycopg 3 (`psycopg[pool]`) for the native engine |

The native pool was introduced in **Django 5.1**, which is the floor for the default engine. The
third-party engine works on older Django too, but this package advertises and tests the matrix
above.

!!! note "Django 5.1 is EOL upstream"
    5.1 reached end of life upstream; it is supported here because it introduced the native pool
    and proves the mixin's lower bound. Prefer **5.2 LTS** or **6.0** for production.

## Tested matrix

Every combination below is exercised in CI against a real PostgreSQL, for **both** pool backends
(native and `dj_db_conn_pool`). Only valid Python × Django pairs are run:

| Python | Django 5.1 | Django 5.2 | Django 6.0 |
|---|:---:|:---:|:---:|
| 3.10 | ✅ | ✅ | — |
| 3.11 | ✅ | ✅ | — |
| 3.12 | ✅ | ✅ | ✅ |
| 3.13 | ✅ | ✅ | ✅ |
| 3.14 | — | ✅ | ✅ |

- Django 6.0 requires Python ≥ 3.12.
- Django 5.1 supports Python up to 3.13.

## Running the matrix locally

```bash
docker compose up -d                     # PostgreSQL on host port 5433
PGPORT=5433 uv run tox                    # full matrix
PGPORT=5433 uv run tox -e py313-dj60-native
```
