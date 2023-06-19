# Tutorial

*stamina* consists mainly of the {func}`stamina.retry()` decorator for retrying functions and methods:

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

## Arbitrary Code Blocks

Since iterators can't catch exceptions and context managers can't execute the same block multiple times, both are necessary.
*stamina* gives you the {func}`stamina.retry_context()` iterator which yields the necessary context managers:

```python
for attempt in stamina.retry_context(on=httpx.HTTPError):
    with attempt:
        resp = httpx.get(f"https://httpbin.org/status/404")
        resp.raise_for_status()
```


## Async

Async works with the exact same functions and arguments -- you just have to use async functions and `async for`:

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


## Globally Disabling Retries

There's two helpers for controlling and inspecting whether retrying is active:
{func}`stamina.is_active()` and {func}`stamina.set_active()` (it's idempotent: you can call `set_active(True)` as many times as you want in a row).
This is useful in tests.
For example, here's a *pytest* fixture that automatically disables retries at the beginning of a test run:

```python
@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```
