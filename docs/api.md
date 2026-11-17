---
icon: material/api
---

# API Reference

::: stamina
    options:
      members:
        - retry
        - retry_context
        - Attempt
        - RetryingCaller
        - BoundRetryingCaller
        - AsyncRetryingCaller
        - BoundAsyncRetryingCaller


## Activation and deactivation

::: stamina
    options:
      members:
        - set_active
        - is_active


## Testing

!!! info "See also"
    [Testing](testing.md)

::: stamina
    options:
      members:
        - set_testing
        - is_testing


## Instrumentation

!!! info "See also"
    [Instrumentation](instrumentation/index.md)

::: stamina.instrumentation
    options:
      members:
        - set_on_retry_hooks
        - get_on_retry_hooks
        - set_process_details
        - get_process_details
        - RetryHook
        - RetryHookFactory
        - RetryDetails


### Integrations

::: stamina.instrumentation
    options:
      heading_level: 4
      members:
        - StructlogOnRetryHook
        - LoggingOnRetryHook
        - PrometheusOnRetryHook
        - get_prometheus_counter


## Exceptions

::: stamina.exceptions
    options:
      members:
        - TryAgain
