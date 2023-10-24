# Instrumentation

*stamina* tries to do the right thing without configuration.


## Metrics

If [*prometheus-client*](https://github.com/prometheus/client_python) is installed, retries are counted using the *Prometheus* counter `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx.ConnectError`.


## Logging

If [*structlog*](https://www.structlog.org/) is installed, retries are logged using a *structlog* logger at warning level.
If *structlog* is not installed, the scheduled retry is logged using the standard library's {mod}`logging` module.

Logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.idle_for`: The time stamina *will* have waited in *total* before the next retry.
  In other words, the retry time of every retry is added to this value *before* waiting.
- `stamina.caused_by`: The {func}`repr` of the exception that caused the retry.

---

*structlog* uses the same names for its keys with the `stamina.` prefix removed.
