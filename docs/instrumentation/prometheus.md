# Prometheus

*stamina* offers Prometheus integration using the official [*prometheus-client*](https://github.com/prometheus/client_python).
When it's active, retries are counted using the [counter](https://prometheus.io/docs/concepts/metric_types/) `stamina_retries_total` with the following labels:

- `callable`: The name of the decorated callable or the [operation name](index.md#operation-names).
- `retry_num`: The number of the current *retry*.
  So, if your callable failed once, this is set to 1.
- `error_type`: The name of the exception **class** that caused the retry.
  For example, `httpx2.ConnectError`.

You can access the counter using [`stamina.instrumentation.get_prometheus_counter()`][stamina.instrumentation.get_prometheus_counter].
Note that it's `None` until the first retry is scheduled or you call [`stamina.instrumentation.get_on_retry_hooks()`][stamina.instrumentation.get_on_retry_hooks].

You can activate it manually by adding [`stamina.instrumentation.PrometheusOnRetryHook`][] to the list of hooks passed to [`stamina.instrumentation.set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks].
