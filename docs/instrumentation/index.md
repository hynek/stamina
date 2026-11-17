---
icon: material/chart-line
---

# Instrumentation

*stamina* calls instrumentation hooks whenever a retry is scheduled, but **before** it waits for the backoff.
That way, you learn immediately that something went wrong and when *stamina* will try again.

You can set the hooks using [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks] and retrieve them using [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].
A hook is a callable, like a function, that takes a single argument: a [`stamina.instrumentation.RetryDetails`][] object.

Three integrations ship with *stamina*:

- [Prometheus](prometheus.md): a counter of all retries.
- [*structlog*](structlog.md): a log entry for each scheduled retry.
- [Standard library's `logging`](logging.md): a log entry for each scheduled retry, if *structlog* is missing.

You can also write your own; see [Custom Hooks](custom.md).


## Defaults

*stamina* tries to give you the best-possible observability of your application's retrying without any configuration.

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
