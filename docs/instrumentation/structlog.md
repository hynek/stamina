# *structlog*

If [*structlog*](https://www.structlog.org/) instrumentation is active, scheduled retries are logged using a *structlog* logger at warning level with the following keys:

- `callable`: The name of the decorated callable or the [operation name](index.md#operation-names).
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
