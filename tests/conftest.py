"""Shared pytest fixtures.

pytest auto-discovers this file; tests receive the fixtures by dependency
injection — nothing here is imported directly. The fixtures are backend-agnostic
(they duck-type the pool object) so the same suite runs against both the native
and the third-party pool.
"""

import pytest


@pytest.fixture
def connection():
    """The default-alias database wrapper under test."""
    from django.db import transaction

    return transaction.get_connection()


@pytest.fixture
def pool(connection):
    """The pool object backing the connection (native or third-party)."""
    # Touch the connection once so the pool is created/opened before introspection.
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1')

    native_pool = getattr(connection, 'pool', None)
    if native_pool is not None:
        return native_pool

    from dj_db_conn_pool.core import pool_container

    pool = pool_container.get(connection.alias)
    assert pool is not None
    return pool
