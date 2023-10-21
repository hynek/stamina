# Tutorial

:::{tip}
If you're not sure why you should use retries in general or _stamina_ in particular, head over to {doc}`motivation` first.
:::


## Decorators

The easiest way to add smart retries to your code is to decorate a callable with {func}`stamina.retry()`:

```python
import datetime as dt

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
Since retrying on {class}`Exception` is an [*attractive nuisance*](https://blog.ganssle.io/articles/2023/01/attractive-nuisances.html), *stamina* doesn't do it by default and forces you to be explicit.

To give you observability of your application's retrying, *stamina* will count the retries using [*prometheus-client*](https://github.com/prometheus/client_python) in the `stamina_retries_total` counter and log them out using [*structlog*](https://www.structlog.org/), if they're installed.


## Arbitrary Code Blocks

Sometimes you only want to retry a part of a function.

Since iterators can't catch exceptions and context managers can't execute the same block multiple times, we need both to achieve that.
*stamina* gives you the {func}`stamina.retry_context()` iterator which yields the necessary context managers:

```python
for attempt in stamina.retry_context(on=httpx.HTTPError):
    with attempt:
        resp = httpx.get(f"https://httpbin.org/status/404")
        resp.raise_for_status()
```


## Async

Async works with the same functions and arguments -- you just have to use async functions and `async for`:

```python
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


## Deactivating Retries Globally

Occasionally it's handy to turn off retries globally -- for instance, in tests.
*stamina* has two helpers for controlling and inspecting whether retrying is active:
{func}`stamina.is_active()` and {func}`stamina.set_active()` (it's idempotent: you can call `set_active(True)` as many times as you want in a row).
For example, here's a *pytest* fixture that automatically turns off retries at the beginning of a test run:

```python
@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```
