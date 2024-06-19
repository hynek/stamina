# Tutorial

:::{tip}
If you're not sure why you should use retries in general or _stamina_ in particular, head over to {doc}`motivation` first.
:::


## Decorators

The easiest way to add smart retries to your code is to decorate a callable with {func}`stamina.retry()`:

```python
import httpx

import stamina


@stamina.retry(on=httpx.HTTPError, attempts=3)
def do_it(code: int) -> httpx.Response:
    resp = httpx.get(f"https://httpbin.org/status/{code}")
    resp.raise_for_status()

    return resp

# reveal_type(do_it)
# note: Revealed type is "def (code: builtins.int) -> httpx._models.Response"
```

This will retry the function up to 3 times if it raises an {class}`httpx.HTTPError` (or any subclass thereof).
Since retrying on {class}`Exception` is an [attractive nuisance](https://blog.ganssle.io/articles/2023/01/attractive-nuisances.html), *stamina* doesn't do it by default and forces you to be explicit.

To give you observability of your application's retrying, *stamina* will count the retries using [*prometheus-client*](https://github.com/prometheus/client_python) in the `stamina_retries_total` counter (if installed) and log them out using [*structlog*](https://www.structlog.org/) with a fallback to {mod}`logging`.


## Arbitrary Code Blocks

Sometimes you only want to retry a part of a function.

Since iterators can't catch exceptions and context managers can't execute the same block multiple times, we need to combine them to achieve that.
*stamina* gives you the {func}`stamina.retry_context()` iterator which yields the necessary context managers:

```python
for attempt in stamina.retry_context(on=httpx.HTTPError):
    with attempt:
        resp = httpx.get(f"https://httpbin.org/status/404")
        resp.raise_for_status()
```


## Retry One Function or Method Call

If you want to retry just one function or method call, *stamina* comes with an even easier way in the shape of {class}`stamina.RetryingCaller` and {class}`stamina.AsyncRetryingCaller`:

```python
def do_something_with_url(url, some_kw):
    resp = httpx.get(url)
    resp.raise_for_status()
    ...

rc = stamina.RetryingCaller(attempts=5)

rc(httpx.HTTPError, do_something_with_url, f"https://httpbin.org/status/404", some_kw=42)

# You can also create a caller with a pre-bound exception type:
bound_rc = rc.on(httpx.HTTPError)

bound_rc(do_something_with_url, f"https://httpbin.org/status/404", some_kw=42)
```

Both `rc` and `bound_rc` run:

```python
do_something_with_url(f"https://httpbin.org/status/404", some_kw=42)
```

and retry on `httpx.HTTPError` and as before, the type hints are preserved.
It's up to you whether you want to share only the retry configuration or the exception type to retry on, too.


## Async

Async works with the same functions and arguments for both [`asyncio`](https://docs.python.org/3/library/asyncio.html) and [Trio](https://trio.readthedocs.io/).
Just use async functions and `async for`:

```python
import datetime as dt


@stamina.retry(
    on=httpx.HTTPError, attempts=3, timeout=dt.timedelta(seconds=10)
)
async def do_it_async(code: int) -> httpx.Response:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://httpbin.org/status/{code}")
    resp.raise_for_status()

    return resp

# reveal_type(do_it_async)
# note: Revealed type is "def (code: builtins.int) -> typing.Coroutine[Any, Any, httpx._models.Response]"

async def with_block(code: int) -> httpx.Response:
    async for attempt in stamina.retry_context(on=httpx.HTTPError, attempts=3):
        with attempt:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"https://httpbin.org/status/{code}")
            resp.raise_for_status()

    return resp
```

Note how you can also pass {class}`datetime.timedelta` objects to *timeout*, *wait_initial*, *wait_max*, and *wait_jitter*.


## Deactivating Retries Globally

Occasionally, turning off retries globally is handy -- for instance, in tests.
*stamina* has two helpers for controlling and inspecting whether retrying is active:
{func}`stamina.is_active()` and {func}`stamina.set_active()` (it's idempotent: you can call `set_active(True)` as many times as you want in a row).
For example, here's a *pytest* fixture that automatically turns off retries at the beginning of a test run:

```python
import pytest
import stamina

@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```
