"""Default engine for ``ENGINE = 'django_pg_real_pool'``.

Points at the native Django pool (Django >= 5.1, ``psycopg[pool]``). For the
optional third-party pool use ``ENGINE = 'django_pg_real_pool.dj_db_conn_pool'``.
"""

from django_pg_real_pool.native.base import DatabaseWrapper

__all__ = ['DatabaseWrapper']
