# Instrumentation

*stamina* tries to do give you the best-possible observability of your application's retrying without any configuration.

*stamina* runs instrumentations whenever a retry is scheduled, but **before** it waits for the backoff.
That way, you learn immediately that something went wrong and when *stamina* will try again.


## *prometheus-client*

If [*prometheus-client*](https://github.com/prometheus/client_python) is installed, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/#counter) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx.ConnectError`.


## *structlog*

If [*structlog*] is installed, scheduled retries are logged using a *structlog* logger at warning level with the following keys:

- `callable`: The name of the decorated callable.
- `args`: The positional arguments passed to the callable.
- `kwargs`: The keyword arguments passed to the callable.
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `wait_for`: The time stamina will wait before the current scheduled attempt.
- `waited_so_far`: The time stamina has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* would've spent `wait_for` + `waited_so_far` waiting.
- `caused_by`: The {func}`repr` of the exception that caused the retry.


## Standard Library's `logging`

If *structlog* is **not** installed, scheduled retries are logged using the standard library's {mod}`logging` module.

Logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable.
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.wait_for`: The time stamina will wait before the current scheduled attempt.
- `stamina.waited_so_far`: The time stamina has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* would've spent `stamina.wait_for` + `stamina.waited_so_far` waiting.
- `stamina.caused_by`: The {func}`repr` of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.

We recommend the usage of [*structlog*] instead.

[*structlog*]: https://www.structlog.org/
