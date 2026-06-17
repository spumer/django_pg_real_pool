"""Django settings for the test suite.

The pool backend under test is selected by the ``DJANGO_PG_REAL_POOL_BACKEND``
environment variable (``native`` — default — or ``dj_db_conn_pool``). The suite is
run once per backend (see tox factors), so a single run always targets one backend.

A single-connection pool (size 1) is used on purpose: it makes "connection acquired
from the pool" vs "connection released to the pool" directly observable through the
pool's idle-connection count.
"""

import os

BACKEND = os.environ.get('DJANGO_PG_REAL_POOL_BACKEND', 'native')

_DB_COMMON = {
    'NAME': os.environ.get('PGDATABASE', 'django_pg_real_pool'),
    'USER': os.environ.get('PGUSER', 'postgres'),
    'PASSWORD': os.environ.get('PGPASSWORD', 'postgres'),
    'HOST': os.environ.get('PGHOST', '127.0.0.1'),
    'PORT': os.environ.get('PGPORT', '5432'),
    'DISABLE_SERVER_SIDE_CURSORS': True,
}

if BACKEND == 'native':
    _default = {
        **_DB_COMMON,
        'ENGINE': 'django_pg_real_pool',
        'CONN_MAX_AGE': 0,  # pooling forbids persistent connections
        'OPTIONS': {'pool': {'min_size': 1, 'max_size': 1}},
    }
elif BACKEND == 'dj_db_conn_pool':
    _default = {
        **_DB_COMMON,
        'ENGINE': 'django_pg_real_pool.dj_db_conn_pool',
        'POOL_OPTIONS': {'POOL_SIZE': 1, 'MAX_OVERFLOW': 0},
    }
else:
    raise ValueError(
        f'Unknown DJANGO_PG_REAL_POOL_BACKEND={BACKEND!r}; expected "native" or "dj_db_conn_pool".'
    )

DATABASES = {'default': _default}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
]

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'
USE_TZ = True
SECRET_KEY = 'django-pg-real-pool-tests'
