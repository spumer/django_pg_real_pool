"""Example: native Django pool (default engine, Django 5.1+, psycopg 3).

Install: pip install django-pg-real-pool
"""

DATABASES = {
    'default': {
        'ENGINE': 'django_pg_real_pool',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'secret',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        # Pooling forbids Django persistent connections — must be 0.
        'CONN_MAX_AGE': 0,
        'OPTIONS': {
            # Passed straight through to psycopg_pool.ConnectionPool.
            'pool': {
                'min_size': 2,
                'max_size': 10,
                'timeout': 10,
                'max_lifetime': 3600,
                'max_idle': 600,
            },
        },
    },
}
