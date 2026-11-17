# Standard library's `logging`

If standard library's [`logging`][logging] integration is active, logging happens at warning level and includes the following *extra fields*:

- `stamina.callable`: The name of the decorated callable or the [operation name](index.md#operation-names).
- `stamina.args`: The positional arguments passed to the callable.
- `stamina.kwargs`: The keyword arguments passed to the callable.
- `stamina.retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `stamina.wait_for`: The time stamina will wait before the current scheduled attempt.
- `stamina.waited_so_far`: The time *stamina* has spent waiting before the current retry.
  In other words, if the current retry succeeds, *stamina* will have spent `stamina.wait_for` + `stamina.waited_so_far` waiting.
- `stamina.caused_by`: The [`repr()`][repr] of the exception that caused the retry.

Please note that extra fields don't appear in log messages by default and require configuration.
We recommend using [*structlog*](structlog.md) instead.

You can activate it manually by adding [`stamina.instrumentation.LoggingOnRetryHook`][] to the list of hooks passed to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks].
