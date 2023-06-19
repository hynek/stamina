# Usage

The API consists mainly of the `stamina.retry()` decorator for retrying functions and methods, and the `stamina.retry_context()` iterator / context manager combo for retrying arbitrary code blocks:

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

for attempt in stamina.retry_context(on=httpx.HTTPError):
    with attempt:
        resp = httpx.get(f"https://httpbin.org/status/404")
        resp.raise_for_status()
```

Async works with the exact same functions and arguments:

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

Both `retry()` and `retry_context()` take the following arguments (unless stated otherwise, **all time-based arguments are floats of seconds or [`datetime.timedelta`](https://docs.python.org/3/library/datetime.html#datetime.timedelta)s**):

**on**: An Exception or a tuple of Exceptions on which the decorated callable will be retried.
There is no default – you _must_ pass this explicitly.

**attempts**: Maximum number of attempts (default: `10`).

**timeout**: Maximum time for all retries.
Can be combined with *attempts* (default: `45`).

**wait_initial**: Minimum first backoff before first retry (default: `0.1`).

**wait_max**: Maximum backoff time between retries (default: `5`).

**wait_jitter**: Maximum _jitter_ that is added to retry back-off delays (the actual jitter added is a random number between 0 and *wait_jitter*) (default: `1`).

**wait_exp_base**: The exponential base used to compute the retry backoff (default: `2`).

The backoff for retry attempt number _attempt_ is computed as:

```
wait_initial * wait_exp_base ** (attempt - 1) + random(0, wait_jitter)
```

Since `x**0` is always 1, the first backoff is within the interval `[wait_initial,wait_initial+wait_jitter]`.
Thus, with default values between 0.1 and 1.1 seconds.

---

If all retries fail, the *last* exception is let through.


## Global Settings

There's two helpers for controlling and inspecting whether retrying is active:
`stamina.is_active()` and `stamina.set_active()` (it's idempotent: you can call `set_active(True)` as many times as you want in a row).
This is useful in tests.
For example, here's a *pytest* fixture that automatically disables retries at the beginning of a test run:

```python
@pytest.fixture(autouse=True, scope="session")
def deactivate_retries():
    stamina.set_active(False)
```
