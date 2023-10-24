# Instrumentation

*stamina* tries to do give you the best-possible observability of your application's retrying without any configuration.


## *prometheus-client*

If [*prometheus-client*](https://github.com/prometheus/client_python) is installed, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/#counter) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx.ConnectError`.


## *structlog*

If [*structlog*] is installed, retries are logged using a *structlog* logger at warning level with the following keys:

- `callable`: The name of the decorated callable.
- `args`: The positional arguments passed to the callable.
- `kwargs`: The keyword arguments passed to the callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `idle_for`: The time stamina *will* have waited in *total* before the next retry.
  In other words, the retry time of every retry is added to this value *before* waiting.
- `caused_by`: The {func}`repr` of the exception that caused the retry.


## Standard Library's `logging`

If *structlog* is **not** installed, the scheduled retry is logged using the standard library's {mod}`logging` module.

Logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.idle_for`: The time stamina *will* have waited in *total* before the next retry.
  In other words, the retry time of every retry is added to this value *before* waiting.
- `stamina.caused_by`: The {func}`repr` of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.

We recommend the usage of [*structlog*] instead.

[*structlog*]: https://www.structlog.org/
