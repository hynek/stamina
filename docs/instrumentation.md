# Instrumentation

*stamina* calls instrumentation hooks whenever a retry is scheduled, but **before** it waits for the backoff.
That way, you learn immediately that something went wrong and when *stamina* will try again.

You can set the hooks using [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks] and retrieve them using [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].
A hook is a callable, like a function, that takes a single argument: a [`stamina.instrumentation.RetryDetails`][] object.

Its return value is ignored, unless it's a **context manager**.
Context managers are entered when the retry is scheduled and exited right before the retry is attempted.
This allows you, for example, to emit spans for the time spent sleeping.

---

Sometimes (for example, in CLI tools) you may want to delay the initialization of the instrumentation until the first retry is scheduled.
In that case, write a callable that creates and returns a retry hook, and pass it to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks] wrapped in a [`stamina.instrumentation.RetryHookFactory`][].


## Defaults

*stamina* tries to do give you the best-possible observability of your application's retrying without any configuration.

That means that if it detects [*prometheus-client*] or [*structlog*] installed, it will automatically use them.
If *structlog* is missing, it falls back to the standard library's [`logging`][logging] module.

To disable instrumentation, set the on-retry hooks to an empty iterable using [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks]:

```python
stamina.instrumentation.set_on_retry_hooks([])
```


## Operation names

[`stamina.retry_context()`][stamina.retry_context], [`stamina.RetryingCaller`][], and [`stamina.AsyncRetryingCaller`][] accept an optional keyword-only *name* for instrumentation.
The default is `<context block>`.
Callers returned by `.on()` retain the name.

```python
retry_api = stamina.RetryingCaller(name="fetch-catalog").on(OSError)
```

The name is passed to retry hooks as the `name` attribute of [`RetryDetails`][stamina.instrumentation.RetryDetails], including the `callable` label in Prometheus and the callable fields in logs.
Choose a stable operation name rather than a per-request ID to avoid creating an unbounded number of metric labels.


## Prometheus

*stamina* offers Prometheus integration using the official [*prometheus-client*].
When it's active, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable or the operation name.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx2.ConnectError`.

You can access the counter using [`stamina.instrumentation.get_prometheus_counter()`][stamina.instrumentation.get_prometheus_counter].
Note that it's `None` until the first retry is scheduled or you call [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].

You can activate it manually by adding [`stamina.instrumentation.PrometheusOnRetryHook`][] to the list of hooks passed to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks].

## *structlog*

If *structlog* instrumentation is active, scheduled retries are logged using a *structlog* logger at warning level with the following keys:

- `callable`: The name of the decorated callable or the operation name.
- `args`: The positional arguments passed to the callable.
- `kwargs`: The keyword arguments passed to the callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `wait_for`: The time stamina will wait before the current scheduled attempt.
- `waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `wait_for` + `waited_so_far` waiting.
- `caused_by`: The [`repr()`][repr] of the exception that caused the retry.

You can activate it manually by adding [`stamina.instrumentation.StructlogOnRetryHook`][] to the list of hooks passed to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks].

!!! warning
    *structlog* integration does **not** work with the deprecated `structlog.stdlib.AsyncBoundLogger` because it won't await log method calls.
    Use `structlog.stdlib.BoundLogger` and explicit async methods like `ainfo()` instead of `info()`.


## Standard library's `logging` { #logging }

If standard library's `logging` integration is active, logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable or the operation name.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.wait_for`: The time stamina will wait before the current scheduled attempt.
- `stamina.waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `stamina.wait_for` + `stamina.waited_so_far` waiting.
- `stamina.caused_by`: The [`repr()`][repr] of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.
We recommend using [*structlog*] instead.

You can activate it manually by adding [`stamina.instrumentation.LoggingOnRetryHook`][] to the list of hooks passed to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks].


## Writing your own hooks

If the instrumentation hooks shipped by _stamina_ don't fit your needs, you can easily implement your own, because a hook is just a callable that takes a [`RetryDetails`][stamina.instrumentation.RetryDetails] and does whatever it wants.

For example, this hook prints the details of each scheduled retry:

```python
import stamina


def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
    print("Retry scheduled:", details)


stamina.instrumentation.set_on_retry_hooks([print_hook])
```


### Context managers

If you need to know when the backoff ends (for example, to emit a span for the time spent waiting) a hook can also return a context manager.
*stamina* enters it when it schedules the retry and exits it right before the next attempt.
The easiest way is [`contextlib.contextmanager`][]:

```python
import contextlib
import time

from collections.abc import Iterator

import stamina


@contextlib.contextmanager
def print_wait_hook(
    details: stamina.instrumentation.RetryDetails,
) -> Iterator[None]:
    print("Waiting before retry:", details)
    start = time.monotonic()

    yield

    print(f"Retrying now after {time.monotonic() - start:.2f}s.")


stamina.instrumentation.set_on_retry_hooks([print_wait_hook])
```

!!! note
    *stamina* only supports synchronous context managers.


### Hook factories

If your hook needs setup that is expensive, wrap a function that creates the hook in a [`RetryHookFactory`][stamina.instrumentation.RetryHookFactory].
*stamina* calls the factory only once: when it schedules the first retry or an earlier call to [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].

```python
import stamina


def make_print_hook() -> stamina.instrumentation.RetryHook:
    print("Initializing the print hook.")

    def print_hook(details: stamina.instrumentation.RetryDetails) -> None:
        print("Retry scheduled:", details)

    return print_hook


stamina.instrumentation.set_on_retry_hooks(
    [stamina.instrumentation.RetryHookFactory(make_print_hook)]
)
```

Now, if you run something like this:

```python
@stamina.retry(on=Exception)
def do_it(arg, kw):
    raise ValueError(arg)


do_it(67, kw=42)
```

You get output like this:

```plain
Initializing the print hook.
Retry scheduled: RetryDetails(name='__main__.do_it', args=(67,), kwargs={'kw': 42}, retry_num=1, wait_for=1.0369990140298804, waited_so_far=0.0, caused_by=ValueError(67))
Retry scheduled: RetryDetails(name='__main__.do_it', args=(67,), kwargs={'kw': 42}, retry_num=2, wait_for=0.2118614697618475, waited_so_far=1.0369990140298804, caused_by=ValueError(67))
...
```


## Processing retry details

To change the [`stamina.instrumentation.RetryDetails`][] before *stamina* passes them to the hooks, use [`stamina.instrumentation.set_process_details()`][stamina.instrumentation.set_process_details].
*stamina* calls your callable once for each scheduled retry.
All hooks get the [`RetryDetails`][stamina.instrumentation.RetryDetails] that it returns – including the default ones.

For example, you can remove secrets from the arguments before they are logged:

```python
import dataclasses

import stamina


def remove_secrets(
    details: stamina.instrumentation.RetryDetails,
) -> stamina.instrumentation.RetryDetails:
    return dataclasses.replace(
        details,
        kwargs={
            k: "[REDACTED]" if k == "password" else v
            for k, v in details.kwargs.items()
        },
    )


stamina.instrumentation.set_process_details(remove_secrets)
```

!!! warning
    **Modifying `args` or `kwargs` modifies the arguments of the next attempt.**

    `args` and `kwargs` are the same objects that *stamina* passes to the next attempt.
    If you change them or anything inside them, you change the arguments of the next attempt.
    Build new objects instead – like the new `kwargs` dict in the example above – and put them into a new [`RetryDetails`][stamina.instrumentation.RetryDetails].

[*structlog*]: https://www.structlog.org/
[*prometheus-client*]: https://github.com/prometheus/client_python
