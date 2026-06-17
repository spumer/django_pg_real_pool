"""Engine wiring and fail-fast guards (no database access)."""

import pytest


def test_version_exposed():
    import django_pg_real_pool

    assert django_pg_real_pool.__version__


def test_default_engine_is_native():
    import django_pg_real_pool.base as default
    import django_pg_real_pool.native.base as native

    assert default.DatabaseWrapper is native.DatabaseWrapper


def test_release_mixin_in_mro():
    from django_pg_real_pool import ConnectionReleaseMixin
    from django_pg_real_pool.native.base import DatabaseWrapper

    assert ConnectionReleaseMixin in DatabaseWrapper.__mro__


def test_native_engine_requires_pool_enabled():
    from django.core.exceptions import ImproperlyConfigured

    from django_pg_real_pool.native.base import DatabaseWrapper

    settings_dict = {
        'ENGINE': 'django_pg_real_pool',
        'NAME': 'unused',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': {},  # pooling NOT enabled
        'CONN_MAX_AGE': 0,
    }
    wrapper = DatabaseWrapper(settings_dict, alias='no_pool')
    with pytest.raises(ImproperlyConfigured, match='requires connection pooling'):
        wrapper.get_new_connection({})


def test_active_engine_matches_selected_backend():
    """The DJANGO_PG_REAL_POOL_BACKEND env var actually drives the configured ENGINE."""
    import os

    from django.conf import settings

    backend = os.environ.get('DJANGO_PG_REAL_POOL_BACKEND', 'native')
    engine = settings.DATABASES['default']['ENGINE']
    if backend == 'native':
        assert engine == 'django_pg_real_pool'
    else:
        assert engine == 'django_pg_real_pool.dj_db_conn_pool'


class _FakeDatabase:
    class InterfaceError(Exception):
        pass


class _FakeConnection:
    Database = _FakeDatabase

    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_cursor_release__interface_error_on_close_is_swallowed():
    """If the cursor is already closed (InterfaceError), the connection is still released."""
    from django_pg_real_pool._release import AutoConnectionReleaseCursor

    class _ClosedCursor:
        def close(self):
            raise _FakeDatabase.InterfaceError('already closed')

    conn = _FakeConnection()
    cursor = AutoConnectionReleaseCursor(conn, _ClosedCursor())

    cursor.close()

    assert conn.closed is True  # released despite the cursor raising


def test_cursor_release__exit_releases_even_when_cursor_exit_raises():
    """__exit__ must return the connection to the pool even if the cursor's exit raises."""
    from django_pg_real_pool._release import AutoConnectionReleaseCursor

    class _BoomCursor:
        def __init__(self):
            self.closed = False

        def __exit__(self, *exc):
            raise ValueError('exit boom')

        def close(self):
            self.closed = True

    conn = _FakeConnection()
    raw = _BoomCursor()
    cursor = AutoConnectionReleaseCursor(conn, raw)

    with pytest.raises(ValueError, match='exit boom'):
        cursor.__exit__(None, None, None)

    assert raw.closed is True
    assert conn.closed is True  # released despite __exit__ raising


def test_cursor_proxy__attribute_access_forwards_to_underlying_cursor():
    """Reads and writes (other than close) are proxied to the wrapped cursor."""
    from django_pg_real_pool._release import AutoConnectionReleaseCursor

    class _Cursor:
        rowcount = 7

    raw = _Cursor()
    cursor = AutoConnectionReleaseCursor(_FakeConnection(), raw)

    assert cursor.rowcount == 7  # __getattr__ forwards reads
    cursor.arraysize = 100  # __setattr__ forwards writes
    assert raw.arraysize == 100
