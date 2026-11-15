# SPDX-FileCopyrightText: 2022 Hynek Schlawack <hs@ox.cx>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

from ._data import RetryDetails, RetryHook, RetryHookFactory


def init_logging(log_level: int = 30) -> RetryHook:
    """
    Initialize logging using the standard library.

    Returned hook logs scheduled retries at *log_level*.

    !!! version-added "Added in 23.2.0"
    """
    import logging

    logger = logging.getLogger("stamina")

    def log_retries(details: RetryDetails) -> None:
        logger.log(
            log_level,
            "stamina.retry_scheduled",
            extra={
                "stamina.callable": details.name,
                "stamina.args": tuple(repr(a) for a in details.args),
                "stamina.kwargs": dict(details.kwargs.items()),
                "stamina.retry_num": details.retry_num,
                "stamina.caused_by": repr(details.caused_by),
                "stamina.wait_for": round(details.wait_for, 2),
                "stamina.waited_so_far": round(details.waited_so_far, 2),
            },
        )

    return log_retries


LoggingOnRetryHook = RetryHookFactory(init_logging)
"""
Pass this object to
[`set_on_retry_hooks()`][stamina.instrumentation.set_on_retry_hooks] to
activate [`logging`][logging] integration.

Is active by default if *structlog* can **not** be imported.

!!! info "See also"
    [Standard library's `logging`](instrumentation.md#logging)

!!! version-added "Added in 23.2.0"
"""
