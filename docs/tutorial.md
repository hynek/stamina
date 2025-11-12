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

---

Sometimes, an exception is too broad, though.
For example, *httpx* raises [`httpx.HTTPStatusError`](https://www.python-httpx.org/exceptions/) on all HTTP errors.
But some errors, like 404 (Not Found) or 403 (Forbidden), usually shouldn't be retried!

To solve problems like this, you can pass a *backoff hook* to `on`.
A backoff hook is a callable that's called with the exception that was raised and whose return value will be used to decide whether to retry or not.

So, calling the following `do_it` function will only retry if <https://httpbin.org> returns a 5xx status code:

```python
def retry_only_on_real_errors(exc: Exception) -> bool:
    # If the error is an HTTP status error, only retry on 5xx errors.
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code >= 500

    # Otherwise retry on all httpx errors.
    return isinstance(exc, httpx.HTTPError)

@stamina.retry(on=retry_only_on_real_errors, attempts=3)
def do_it(code: int) -> httpx.Response:
    resp = httpx.get(f"https://httpbin.org/status/{code}")
    resp.raise_for_status()

    return resp
```

If you need more control, you can return a float or a {class}`datetime.timedelta` to specify a custom backoff that overrides the default backoff instead of a boolean.
This is useful when the error carries information like a [`Retry-After`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Retry-After) header.
A custom backoff is **not** part of the exponential backoff machinery so none of the other backoff parameters apply to it.

---

To give you observability of your application's retrying, *stamina* will count the retries using [*prometheus-client*](https://github.com/prometheus/client_python) in the `stamina_retries_total` counter (if installed) and log them out using [*structlog*](https://www.structlog.org/) with a fallback to {mod}`logging`.


## Arbitrary code blocks

Sometimes you only want to retry a part of a function.

Since iterators can't catch exceptions and context managers can't execute the same block multiple times, we need to combine them to achieve that.
*stamina* gives you the {func}`stamina.retry_context()` iterator which yields the necessary context managers:

```python
for attempt in stamina.retry_context(on=httpx.HTTPError):
    with attempt:
        resp = httpx.get(f"https://httpbin.org/status/404")
        resp.raise_for_status()
```


## Retry one function or method call

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


## Testing

Testing software with retries can be tricky, so *stamina* comes with dedicated testing helpers to make your life easier.

You can *globally* turn them off altogether, remove backoff, and limit the number of retries.

Check out {doc}`testing` to learn more!
