# Installation

## Native pool (default)

```bash
pip install django-pg-real-pool
```

This pulls in Django (≥ 5.1) and `psycopg[pool]` (psycopg 3 + `psycopg_pool`), which is everything
the default engine needs. For most production deployments you will want the binary build of
psycopg:

```bash
pip install django-pg-real-pool 'psycopg[binary,pool]'
```

## Third-party pool (optional extra)

If you cannot use the native pool (Django < 5.1, or you are on psycopg 2), or you already use
`django-db-connection-pool`, install the extra:

```bash
pip install 'django-pg-real-pool[dj-db-conn-pool]'
```

This adds `django-db-connection-pool` (which brings SQLAlchemy and `sqlparams`).

## With uv

```bash
uv add django-pg-real-pool
# or with the optional backend:
uv add 'django-pg-real-pool[dj-db-conn-pool]'
```

## Verify

```python
import django_pg_real_pool
print(django_pg_real_pool.__version__)
```

Next: [Configuration](configuration.md).
