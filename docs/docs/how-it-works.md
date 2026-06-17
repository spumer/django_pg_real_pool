# How it works

The package is intentionally tiny: one mixin and one cursor proxy. All the value is in *when* the
connection is returned to the pool.

## The release point

Django's `BaseDatabaseWrapper` keeps `self.connection` set to the live driver connection for as
long as the wrapper is "connected". A pooled backend only returns the connection to its pool when
`DatabaseWrapper.close()` is called. Vanilla Django calls `close()` at the end of the request (via
`close_old_connections`), so the connection stays checked out the whole time.

`ConnectionReleaseMixin` moves that `close()` earlier:

```python
class ConnectionReleaseMixin:
    def _cursor(self, *args, **kwargs):
        must_close = self.connection is None      # connection was freshly acquired for this cursor
        if self.in_atomic_block:
            must_close = False                     # inside a transaction: keep it until the block ends
        cursor = super()._cursor(*args, **kwargs)
        if must_close:
            return AutoConnectionReleaseCursor(self, cursor)
        return cursor
```

- **Outside a transaction** — the cursor is wrapped in `AutoConnectionReleaseCursor`. When that
  cursor is closed (which Django does as soon as the query's results are consumed), the wrapper's
  `close()` runs and the connection goes back to the pool.
- **Inside `atomic()`** — nothing is wrapped; the connection is held normally until the block
  commits or rolls back.

## Releasing on commit / rollback

When *you* (or `atomic()`) end a transaction, the connection is released too:

```python
def commit(self):
    super().commit()
    if not self.in_atomic_block and self.settings_dict["AUTOCOMMIT"]:
        self.set_autocommit(True)   # run on_commit hooks like Django does, with the connection live
    self.close()                    # return the connection to the pool
    self.closed_in_transaction = True   # don't let it be instantly re-acquired

def rollback(self):
    super().rollback()
    self.close()
    self.closed_in_transaction = True
```

`closed_in_transaction = True` prevents Django from immediately re-opening the connection during
the same teardown; the next ORM call re-acquires it from the pool and restores the connection's
default settings.

## The cursor proxy

`AutoConnectionReleaseCursor` is a thin proxy around the real cursor. It forwards everything
(`execute`, iteration, attribute access) and adds one behaviour: when the cursor closes, it also
releases the connection.

```python
class AutoConnectionReleaseCursor:
    def __exit__(self, *exc):
        self.__cursor.__exit__(*exc)
        self.close()

    def close(self):
        try:
            self.__cursor.close()
        except self.__connection.Database.InterfaceError:
            pass                       # already closed
        finally:
            self.__connection.close()  # ← return the connection to the pool
```

## Why it is backend-agnostic

The mixin never talks to a specific pool. It only calls `DatabaseWrapper.close()`, and **both**
supported backends return the connection to their pool on `close()`:

| Backend | `close()` returns connection via |
|---|---|
| Native (`psycopg_pool`) | `_close()` → `connection._pool.putconn(connection)` |
| `dj_db_conn_pool` (SQLAlchemy) | SQLAlchemy `QueuePool` connection-proxy release |

That is why the same `ConnectionReleaseMixin` is layered on top of either base wrapper, and why the
identical behavioural test suite passes against both.

!!! note "psycopg 3 and `close()`"
    In psycopg 3, using a raw connection as a context manager (`with conn:`) *closes* it (psycopg 2
    only ended the transaction). This package never relies on that — it goes through Django's
    `DatabaseWrapper.close()`, which performs a pool `putconn`, so the connection is recycled, not
    destroyed.
