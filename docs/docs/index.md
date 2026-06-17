# django-pg-real-pool

A Django PostgreSQL database backend that releases pooled connections **As Soon As Possible**.

## TL;DR

A plain connection pool hands a connection to a thread and keeps it checked out for the whole
request/context — even if a single query was made early and the rest of the work never touches
the database. Under load, threads fight over a small set of connections that mostly sit idle
while still "in use".

`django-pg-real-pool` returns the connection to the pool **right after each query** when you are
*not* inside a transaction, and holds it only for the duration of an `atomic()` block (or a
manually controlled transaction). The result: far fewer connections are needed to serve the same
concurrency.

```python
# settings.py
DATABASES = {
    "default": {
        "ENGINE": "django_pg_real_pool",          # native psycopg pool (Django 5.1+)
        "NAME": "mydb", "USER": "...", "PASSWORD": "...", "HOST": "...", "PORT": "5432",
        "CONN_MAX_AGE": 0,                          # pooling forbids persistent connections
        "OPTIONS": {"pool": {"min_size": 2, "max_size": 10}},
    }
}
```

That's it. Your code uses the ORM exactly as before; connections are just held for less time.

## Motivation

When you run a multi-threaded Django app (Gunicorn threads, dramatiq workers, Celery
prefork+threads, ASGI, …) every thread normally keeps its own DB connection for the lifetime of
the request. With a pool in front, the pool still won't reclaim a connection until the caller
releases it — which Django does only at the end of the request. So a request that does one quick
`SELECT` and then spends 200 ms calling an external API keeps a database connection pinned that
entire time.

```
Without ASAP release:   |== SELECT ==|···· 200 ms external call ····|  connection held the whole time
With ASAP release:      |== SELECT ==| connection returned to pool   ← available to other threads
```

`django-pg-real-pool` changes the release point: the connection goes back to the pool after each
cursor finishes, except inside transactions where it must stay (correctness first). The connection
is transparently re-acquired the next time the ORM needs it.

## What you get

- A drop-in `ENGINE` — no code changes beyond `settings.py`.
- Works on Django's **native** psycopg pool (default) or the optional third-party
  `django-db-connection-pool`.
- Transaction-safe: `atomic()`, savepoints, server-side cursors and `on_commit` hooks all behave
  exactly as Django expects.

Continue to [How it works](how-it-works.md) for the internals, or jump to
[Installation](installation.md) and [Configuration](configuration.md).
