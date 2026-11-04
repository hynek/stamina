# Instrumentation

*stamina* calls instrumentation hooks whenever a retry is scheduled, but **before** it waits for the backoff.
That way, you learn immediately that something went wrong and when *stamina* will try again.

You can set the hooks using {func}`stamina.instrumentation.set_on_retry_hooks` and retrieve them using {func}`stamina.instrumentation.get_on_retry_hooks`.
A hook is a callable, like a function, that takes a single argument: a {class}`stamina.instrumentation.RetryDetails` object.

Its return value is ignored, unless it's a **context manager**.
Context managers are entered when the retry is scheduled and exited right before the retry is attempted.
This allows you, for example, to emit spans for the time spent sleeping.

---

Sometimes (for example, in CLI tools) you may want to delay the initialization of the instrumentation until the first retry is scheduled.
In that case, write a callable that creates and returns a retry hook, and pass it to {func}`stamina.instrumentation.set_on_retry_hooks` wrapped in a {class}`stamina.instrumentation.RetryHookFactory`.


## Defaults

*stamina* tries to do give you the best-possible observability of your application's retrying without any configuration.

That means that if it detects [*prometheus-client*] or [*structlog*] installed, it will automatically use them.
If *structlog* is missing, it falls back to the standard library's {mod}`logging` module.

To disable instrumentation, set the on-retry hooks to an empty iterable using {func}`stamina.instrumentation.set_on_retry_hooks`:

```python
stamina.instrumentation.set_on_retry_hooks([])
```


## Operation names

{func}`stamina.retry_context`, {class}`stamina.RetryingCaller`, and {class}`stamina.AsyncRetryingCaller` accept an optional keyword-only *name* for instrumentation.
The default is `<context block>`.
Callers returned by `.on()` retain the name.

```python
retry_api = stamina.RetryingCaller(name="fetch-catalog").on(OSError)
```

The name is passed to retry hooks as {attr}`stamina.instrumentation.RetryDetails.name`, including the `callable` label in Prometheus and the callable fields in logs.
Choose a stable operation name rather than a per-request ID to avoid creating an unbounded number of metric labels.


(prometheus)=

## Prometheus

*stamina* offers Prometheus integration using the official [*prometheus-client*].
When it's active, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable or the operation name.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx2.ConnectError`.

You can access the counter using {func}`stamina.instrumentation.get_prometheus_counter`.
Note that it's `None` until the first retry is scheduled or you call {func}`stamina.instrumentation.get_on_retry_hooks`.

You can activate it manually by adding {data}`stamina.instrumentation.PrometheusOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.

(structlog)=

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
- `caused_by`: The {func}`repr` of the exception that caused the retry.

You can activate it manually by adding {data}`stamina.instrumentation.StructlogOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.

:::{warning}
*structlog* integration does **not** work with the deprecated `structlog.stdlib.AsyncBoundLogger` because it won't await log method calls.
Use `structlog.stdlib.BoundLogger` and explicit async methods like `ainfo()` instead of `info()`.
:::


(logging)=

## Standard library's `logging`

If standard library's `logging` integration is active, logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable or the operation name.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.wait_for`: The time stamina will wait before the current scheduled attempt.
- `stamina.waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `stamina.wait_for` + `stamina.waited_so_far` waiting.
- `stamina.caused_by`: The {func}`repr` of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.
We recommend using [*structlog*] instead.

You can activate it manually by adding {data}`stamina.instrumentation.LoggingOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.


## Processing retry details

To change the {class}`stamina.instrumentation.RetryDetails` before *stamina* passes them to the hooks, use {func}`stamina.instrumentation.set_process_details`.
*stamina* calls your callable once for each scheduled retry.
All hooks get the {class}`~stamina.instrumentation.RetryDetails` that it returns – including the default ones.

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

:::{warning}
**Modifying `args` or `kwargs` modifies the arguments of the next attempt.**

`args` and `kwargs` are the same objects that *stamina* passes to the next attempt.
If you change them or anything inside them, you change the arguments of the next attempt.
Build new objects instead – like the new `kwargs` dict in the example above – and put them into a new {class}`~stamina.instrumentation.RetryDetails`.
:::

[*structlog*]: https://www.structlog.org/
[*prometheus-client*]: https://github.com/prometheus/client_python
