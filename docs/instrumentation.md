# Instrumentation

*stamina* calls instrumentation hooks whenever a retry is scheduled, but **before** it waits for the backoff.
That way, you learn immediately that something went wrong and when *stamina* will try again.

You can set the hooks using {func}`stamina.instrumentation.set_on_retry_hooks` and retrieve them using {func}`stamina.instrumentation.get_on_retry_hooks`.
A hook is a callable, like a function, that takes a single argument: a {class}`stamina.instrumentation.RetryDetails` object.
Its return value is ignored.

Sometimes (for example, in CLI tools) you may want to delay the initialization of the instrumentation until the first retry is scheduled.
In that case, write a callable that creates and returns a retry hook, and pass it to {func}`stamina.instrumentation.set_on_retry_hooks` wrapped in a {class}`stamina.instrumentation.RetryHookFactory`.


## Defaults

*stamina* tries to do give you the best-possible observability of your application's retrying without any configuration.

That means that if it detects [*prometheus-client*](https://github.com/prometheus/client_python) or [*structlog*] installed, it will automatically use them.
If *structlog* is missing, it falls back to the standard library's {mod}`logging` module.

If you want to disable instrumentation, you can do so by setting {func}`stamina.instrumentation.set_on_retry_hooks` to an empty iterable:

```python
stamina.instrumentation.set_on_retry_hooks([])
```

(prometheus)=

## Prometheus

*stamina* offers Prometheus integration using the official [Python client](https://github.com/prometheus/client_python).
When it's active, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/#counter) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx.ConnectError`.

You can access the counter using {func}`stamina.instrumentation.get_prometheus_counter`.
Note that it's `None` until the first retry is scheduled or you call {func}`stamina.instrumentation.get_on_retry_hooks`.

You can activate it manually by adding {data}`stamina.instrumentation.PrometheusOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.

(structlog)=

## *structlog*

If *structlog* instrumentation is active, scheduled retries are logged using a *structlog* logger at warning level with the following keys:

- `callable`: The name of the decorated callable.
- `args`: The positional arguments passed to the callable.
- `kwargs`: The keyword arguments passed to the callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `wait_for`: The time stamina will wait before the current scheduled attempt.
- `waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `wait_for` + `waited_so_far` waiting.
- `caused_by`: The {func}`repr` of the exception that caused the retry.

You can activate it manually by adding {data}`stamina.instrumentation.StructlogOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.

(logging)=

## Standard Library's `logging`

If standard library's `logging` integration is active, logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.wait_for`: The time stamina will wait before the current scheduled attempt.
- `stamina.waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `stamina.wait_for` + `stamina.waited_so_far` waiting.
- `stamina.caused_by`: The {func}`repr` of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.
We recommend the usage of [*structlog*] instead.

You can activate it manually by adding {data}`stamina.instrumentation.LoggingOnRetryHook` to the list of hooks passed to {func}`stamina.instrumentation.set_on_retry_hooks`.

[*structlog*]: https://www.structlog.org/


## API Reference

```{eval-rst}
.. module:: stamina.instrumentation

.. autofunction:: set_on_retry_hooks
.. autofunction:: get_on_retry_hooks

.. autoclass:: RetryHook()
.. autoclass:: RetryHookFactory
.. autoclass:: RetryDetails
```

### Integrations

```{eval-rst}
.. data:: StructlogOnRetryHook

  Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate *structlog* integration.

  Is active by default if *structlog* can be imported.

  .. seealso:: :ref:`structlog`

  .. versionadded:: 23.2.0

.. data:: LoggingOnRetryHook

   Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate :mod:`logging` integration.

   Is active by default if *structlog* can **not** be imported.

   .. seealso:: :ref:`logging`

   .. versionadded:: 23.2.0

.. data:: PrometheusOnRetryHook

   Pass this object to :func:`stamina.instrumentation.set_on_retry_hooks` to activate Prometheus integration.

   Is active by default if *prometheus-client* can be imported.

   .. seealso:: :ref:`prometheus`

   .. versionadded:: 23.2.0
.. autofunction:: get_prometheus_counter
```
