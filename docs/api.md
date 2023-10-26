# API Reference

```{eval-rst}
.. module:: stamina

.. autofunction:: retry
.. autofunction:: retry_context
.. autoclass:: Attempt
   :members: num
```


## Activation and Deactivation

```{eval-rst}
.. autofunction:: set_active
.. autofunction:: is_active
```


## Instrumentation

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
