"""Example: third-party pool via django-db-connection-pool (optional extra).

Install: pip install 'django-pg-real-pool[dj-db-conn-pool]'

Use this when you cannot run the native pool (Django < 5.1 or psycopg 2) or you have
already standardised on django-db-connection-pool / SQLAlchemy QueuePool.
"""

DATABASES = {
    'default': {
        'ENGINE': 'django_pg_real_pool.dj_db_conn_pool',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'secret',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        # Keys are UPPERCASE; mapped onto SQLAlchemy QueuePool.
        'POOL_OPTIONS': {
            'POOL_SIZE': 3,
            'MAX_OVERFLOW': 7,
            'RECYCLE': 24 * 60 * 60,
        },
    },
}
